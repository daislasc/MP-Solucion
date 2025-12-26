"""
Workflow Orquestador - Flujo principal de automatización
"""
import os
import shutil
import time
import logging
from datetime import datetime
from typing import Callable, Optional
from dataclasses import dataclass, field

from .config import get_config
from .tableau_client import TableauClient
from .sql_client import InfoCentralClient, DEADWHClient, CubosOfiClient
from .jira_client import JiraClient
from .notifier import Notifier

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Resultado de un paso del workflow"""
    nombre: str
    success: bool
    mensaje: str
    duracion: float = 0.0
    detalles: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'nombre': self.nombre,
            'success': self.success,
            'estado': self.mensaje,
            'duracion': f"{self.duracion:.2f}s",
            'detalles': self.detalles
        }


class ReportWorkflow:
    """
    Orquestador del flujo de automatización de reportes MP.
    
    Flujo completo:
    1. Validar extracto de Tableau
    2. Si desactualizado, intentar refresh
    3. Validar datos en SQL Server (InfoCentral)
    4. Si hay diferencias, ejecutar jobs correctivos
    5. Descargar PDFs de Tableau
    6. Copiar PDFs a carpeta compartida
    7. Ejecutar SP de envío de correos
    """
    
    def __init__(self, on_step_complete: Callable[[StepResult], None] = None):
        """
        Args:
            on_step_complete: Callback ejecutado al completar cada paso (para UI)
        """
        self.config = get_config()
        self.on_step_complete = on_step_complete or (lambda x: None)
        self.steps: list[StepResult] = []
        self.start_time: Optional[float] = None
        self.ticket_jira: Optional[str] = None
    
    def _execute_step(self, nombre: str, func: Callable) -> StepResult:
        """Ejecuta un paso y registra el resultado"""
        logger.info(f"=== Ejecutando: {nombre} ===")
        start = time.time()
        
        try:
            success, mensaje, detalles = func()
            result = StepResult(
                nombre=nombre,
                success=success,
                mensaje=mensaje,
                duracion=time.time() - start,
                detalles=detalles or {}
            )
        except Exception as e:
            logger.error(f"Error en {nombre}: {e}")
            result = StepResult(
                nombre=nombre,
                success=False,
                mensaje=str(e),
                duracion=time.time() - start
            )
        
        self.steps.append(result)
        self.on_step_complete(result)
        
        log_func = logger.info if result.success else logger.error
        log_func(f"{nombre}: {'OK' if result.success else 'FAIL'} {result.mensaje}")
        
        return result
    
    def _handle_error(self, paso_fallido: str, error: str):
        """Maneja un error creando ticket de Jira y enviando notificación"""
        logger.error(f"Error en workflow: {paso_fallido} - {error}")
        
        # Crear ticket en Jira
        jira = JiraClient()
        success, msg, ticket_key = jira.crear_ticket_error(
            titulo=f"[AUTO] Error en Reportes MP: {paso_fallido}",
            descripcion=error
        )
        
        if success:
            self.ticket_jira = ticket_key
            logger.info(f"Ticket Jira creado: {ticket_key}")
        
        # Enviar notificación de error
        notifier = Notifier()
        notifier.enviar_alerta_error(
            titulo=f"Error en: {paso_fallido}",
            mensaje=error,
            ticket_jira=self.ticket_jira
        )
    
    def run_validation_only(self) -> tuple[bool, str]:
        """
        Ejecuta solo la validación del extracto.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        logger.info("=== Iniciando validación de extracto ===")
        self.start_time = time.time()
        self.steps = []
        
        with TableauClient() as tableau:
            result = self._execute_step(
                "Validar Extracto Tableau",
                lambda: self._wrap_validacion(tableau.validar_extracto())
            )
            
            if result.success:
                return (True, result.mensaje)
            
            # Intentar refresh
            result = self._execute_step(
                "Refresh Extracto",
                lambda: (*tableau.refresh_extracto(), {})
            )
            
            if result.success:
                # Revalidar
                result = self._execute_step(
                    "Revalidar Extracto",
                    lambda: self._wrap_validacion(tableau.validar_extracto())
                )
                return (result.success, result.mensaje)
            
            return (False, result.mensaje)
    
    def run_send_only(self, es_prueba: int = 0, reporte: int = 0) -> tuple[bool, str]:
        """
        Ejecuta solo el envío de correos (asume que los PDFs ya están listos).
        
        Args:
            es_prueba: 0=oficial, 1=prueba
            reporte: 0=todos, 5=Compras Nacionales, etc.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        logger.info("=== Iniciando envío de reportes ===")
        self.start_time = time.time()
        self.steps = []
        
        try:
            deadwh = DEADWHClient()
            result = self._execute_step(
                "Enviar Correos",
                lambda: (*deadwh.enviar_reportes(es_prueba, reporte), {})
            )
            
            if not result.success:
                self._handle_error("Envío de Correos", result.mensaje)
                return (False, result.mensaje)
            
            # === ÉXITO ===
            tiempo_total = time.time() - self.start_time
            logger.info("=" * 60)
            logger.info(f"ENVÍO DE CORREOS COMPLETADO en {tiempo_total:.2f}s")
            logger.info("=" * 60)
            
            # Enviar notificación de éxito
            notifier = Notifier()
            notifier.enviar_resumen_proceso(
                exito=True,
                pasos_ejecutados=[s.to_dict() for s in self.steps],
                tiempo_total=tiempo_total
            )
            
            return (True, f"Correos enviados exitosamente en {tiempo_total:.2f}s")
            
        except Exception as e:
            logger.exception(f"Error inesperado en envío de correos: {e}")
            self._handle_error("Error Inesperado", str(e))
            return (False, str(e))
    
    def run_full(self) -> tuple[bool, str]:
        """
        Ejecuta el flujo completo de automatización.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        logger.info("=" * 60)
        logger.info("INICIANDO FLUJO COMPLETO DE AUTOMATIZACIÓN")
        logger.info("=" * 60)
        
        self.start_time = time.time()
        self.steps = []
        self.ticket_jira = None
        
        try:
            # === PASO 1: Validar extracto de Tableau ===
            with TableauClient() as tableau:
                result = self._execute_step(
                    "1. Validar Extracto Tableau",
                    lambda: self._wrap_validacion(tableau.validar_extracto())
                )
                
                if not result.success:
                    # Intentar refresh
                    result = self._execute_step(
                        "1.1 Refresh Extracto",
                        lambda: (*tableau.refresh_extracto(), {})
                    )
                    
                    if not result.success:
                        self._handle_error("Refresh de Extracto", result.mensaje)
                        return (False, f"Error en extracto: {result.mensaje}")
                    
                    # Revalidar después del refresh
                    result = self._execute_step(
                        "1.2 Revalidar Extracto",
                        lambda: self._wrap_validacion(tableau.validar_extracto())
                    )
                    
                    if not result.success:
                        self._handle_error("Validación post-refresh", result.mensaje)
                        return (False, f"Extracto sigue desactualizado: {result.mensaje}")
            
            # === PASO 2: Validar datos en SQL Server ===
            infocentral = InfoCentralClient()
            hay_diferencias = False
            acciones = []
            
            result = self._execute_step(
                "2. Validar Inventario SQL",
                lambda: self._validar_inventario(infocentral)
            )
            
            if not result.success and result.detalles.get('hay_diferencias'):
                hay_diferencias = True
                acciones = result.detalles.get('acciones', [])
                
                # Ejecutar jobs correctivos
                result = self._execute_step(
                    "2.1 Ejecutar Jobs Correctivos",
                    lambda: self._ejecutar_jobs_correctivos(infocentral, acciones)
                )
                
                if not result.success:
                    self._handle_error("Jobs Correctivos", result.mensaje)
                    return (False, f"Error en jobs correctivos: {result.mensaje}")
                
                # Actualizar cubo
                cubosofi = CubosOfiClient()
                result = self._execute_step(
                    "2.2 Actualizar Cubo",
                    lambda: (*cubosofi.ejecutar_job_inventario(), {})
                )
                
                if not result.success:
                    self._handle_error("Actualización de Cubo", result.mensaje)
                    return (False, f"Error actualizando cubo: {result.mensaje}")
            
            # === PASO 3: Descargar PDFs de Tableau ===
            with TableauClient() as tableau:
                result = self._execute_step(
                    "3. Descargar PDFs",
                    lambda: self._descargar_pdfs(tableau)
                )
                
                if not result.success:
                    self._handle_error("Descarga de PDFs", result.mensaje)
                    return (False, f"Error descargando PDFs: {result.mensaje}")
                
                archivos_descargados = result.detalles.get('archivos', [])
            
            # === PASO 4: Copiar a carpeta compartida ===
            result = self._execute_step(
                "4. Copiar a DEADWH",
                lambda: self._copiar_archivos()
            )
            
            if not result.success:
                self._handle_error("Copia de Archivos", result.mensaje)
                return (False, f"Error copiando archivos: {result.mensaje}")
            
            # === PASO 5: Enviar correos ===
            deadwh = DEADWHClient()
            result = self._execute_step(
                "5. Enviar Correos",
                lambda: (*deadwh.enviar_reportes(0, 0), {})
            )
            
            if not result.success:
                self._handle_error("Envío de Correos", result.mensaje)
                return (False, f"Error enviando correos: {result.mensaje}")
            
            # === ÉXITO ===
            tiempo_total = time.time() - self.start_time
            logger.info("=" * 60)
            logger.info(f"FLUJO COMPLETADO EXITOSAMENTE en {tiempo_total:.2f}s")
            logger.info("=" * 60)
            
            # Enviar notificación de éxito
            notifier = Notifier()
            notifier.enviar_resumen_proceso(
                exito=True,
                pasos_ejecutados=[s.to_dict() for s in self.steps],
                tiempo_total=tiempo_total
            )
            
            return (True, f"Proceso completado en {tiempo_total:.2f}s")
            
        except Exception as e:
            logger.exception(f"Error inesperado en workflow: {e}")
            self._handle_error("Error Inesperado", str(e))
            return (False, str(e))
    
    def _wrap_validacion(self, result: tuple) -> tuple[bool, str, dict]:
        """Convierte resultado de validar_extracto a formato (success, msg, dict)"""
        is_valid, message, last_updated = result
        detalles = {}
        
        if last_updated:
            # Convertir a hora local (Monterrey, México - UTC-6)
            from datetime import timezone, timedelta
            tz_monterrey = timezone(timedelta(hours=-6))  # CST (Central Standard Time)
            
            # Convertir UTC a hora local
            last_updated_local = last_updated.astimezone(tz_monterrey)
            
            detalles = {
                'last_updated_utc': str(last_updated),
                'last_updated_local': last_updated_local.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'timezone': 'America/Monterrey (UTC-6)'
            }
        
        return (is_valid, message, detalles)
    
    def _validar_inventario(self, client: InfoCentralClient) -> tuple[bool, str, dict]:
        """Valida inventario y retorna resultado estructurado"""
        hay_diferencias, mensaje, acciones = client.validar_inventario()
        
        if not hay_diferencias:
            return (True, mensaje, {})
        
        return (
            False,
            mensaje,
            {'hay_diferencias': True, 'acciones': acciones}
        )
    
    def _ejecutar_jobs_correctivos(self, client: InfoCentralClient, 
                                   acciones: list) -> tuple[bool, str, dict]:
        """Ejecuta los jobs correctivos para cada ubicación con diferencias"""
        errores = []
        
        for accion in acciones:
            accion1 = accion.get('Accion1', '')
            accion2 = accion.get('Accion2', '')
            ubicacion = accion.get('NombreUbicacion', 'Desconocida')
            
            if accion1:
                logger.info(f"Ejecutando {accion1} para {ubicacion}")
                success, msg = client.execute_job(accion1)
                if not success:
                    errores.append(f"{accion1}: {msg}")
            
            if accion2:
                logger.info(f"Ejecutando {accion2} para {ubicacion}")
                success, msg = client.execute_job(accion2)
                if not success:
                    errores.append(f"{accion2}: {msg}")
        
        if errores:
            return (False, f"Errores en jobs: {'; '.join(errores)}", {})
        
        return (True, f"{len(acciones)} ubicaciones corregidas", {})
    
    def _descargar_pdfs(self, tableau: TableauClient) -> tuple[bool, str, dict]:
        """Descarga todos los PDFs"""
        source_path = self.config.paths.pdf_source
        
        # Limpiar carpeta de origen
        if os.path.exists(source_path):
            for f in os.listdir(source_path):
                os.remove(os.path.join(source_path, f))
        else:
            os.makedirs(source_path, exist_ok=True)
        
        success, msg, archivos = tableau.descargar_todos_reportes(source_path)
        
        return (success, msg, {'archivos': archivos})
    
    def _copiar_archivos(self) -> tuple[bool, str, dict]:
        """Copia archivos de origen a destino"""
        source = self.config.paths.pdf_source
        dest = self.config.paths.pdf_dest
        
        try:
            # Verificar acceso al destino
            if not os.path.exists(dest):
                return (False, f"Carpeta destino no accesible: {dest}", {})
            
            # Limpiar destino
            for f in os.listdir(dest):
                filepath = os.path.join(dest, f)
                if os.path.isfile(filepath):
                    os.remove(filepath)
            
            # Copiar archivos
            archivos_copiados = []
            for f in os.listdir(source):
                src_path = os.path.join(source, f)
                dst_path = os.path.join(dest, f)
                shutil.copy2(src_path, dst_path)
                archivos_copiados.append(f)
            
            return (True, f"{len(archivos_copiados)} archivos copiados", 
                    {'archivos': archivos_copiados})
            
        except PermissionError as e:
            return (False, f"Sin permisos para escribir en {dest}: {e}", {})
        except Exception as e:
            return (False, str(e), {})
    
    def get_summary(self) -> dict:
        """Retorna un resumen de la ejecución"""
        tiempo_total = time.time() - self.start_time if self.start_time else 0
        
        return {
            'total_pasos': len(self.steps),
            'pasos_exitosos': sum(1 for s in self.steps if s.success),
            'pasos_fallidos': sum(1 for s in self.steps if not s.success),
            'tiempo_total': tiempo_total,
            'ticket_jira': self.ticket_jira,
            'pasos': [s.to_dict() for s in self.steps]
        }

