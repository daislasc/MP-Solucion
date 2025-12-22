"""
Cliente SQL Server - Conexiones y ejecución de queries/jobs
"""
import time
import logging
from typing import Optional, Any
import pymssql

from .config import get_config, SQLServerConfig

logger = logging.getLogger(__name__)


class SQLClient:
    """Cliente para conexiones a SQL Server"""
    
    def __init__(self, config: SQLServerConfig):
        self.config = config
    
    def execute_query(self, query: str, params: tuple = (), database: str = None) -> list[dict]:
        """Ejecuta una query y retorna los resultados como lista de diccionarios"""
        db = database or self.config.database
        
        logger.info(f"Conectando a {self.config.server}/{db}")
        
        try:
            with pymssql.connect(
                server=self.config.server,
                user=self.config.user,
                password=self.config.password,
                database=db,
                tds_version='7.0',
                autocommit=True
            ) as conn:
                with conn.cursor(as_dict=True) as cursor:
                    logger.debug(f"Ejecutando: {query[:100]}...")
                    cursor.execute(query, params)
                    try:
                        result = cursor.fetchall()
                        return result
                    except Exception:
                        return []
        except Exception as e:
            logger.error(f"Error ejecutando query en {self.config.server}: {e}")
            raise
    
    def execute_sp(self, sp_name: str, params: tuple = (), database: str = None) -> list[dict]:
        """Ejecuta un stored procedure"""
        query = f"EXEC {sp_name}"
        if params:
            placeholders = ", ".join(["%s"] * len(params))
            query = f"EXEC {sp_name} {placeholders}"
        
        return self.execute_query(query, params, database)
    
    def execute_job(self, job_name: str, wait_for_completion: bool = True, 
                    check_interval: int = 10, max_wait: int = 600) -> tuple[bool, str]:
        """
        Ejecuta un SQL Agent Job y opcionalmente espera a que termine.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        logger.info(f"Iniciando job: {job_name}")
        
        try:
            # Iniciar el job
            self.execute_query(
                f"EXEC msdb.dbo.sp_start_job @job_name = %s",
                (job_name,),
                database="msdb"
            )
            logger.info(f"Job '{job_name}' iniciado")
            
            if not wait_for_completion:
                return (True, "Job iniciado (sin esperar)")
            
            # Esperar a que termine
            total_waited = 0
            while total_waited < max_wait:
                time.sleep(check_interval)
                total_waited += check_interval
                
                result = self.execute_query(f"""
                    SELECT TOP 1
                        ja.run_requested_date,
                        ja.stop_execution_date,
                        CASE 
                            WHEN ja.stop_execution_date IS NULL THEN 'Running'
                            ELSE 'Completed'
                        END AS job_status
                    FROM msdb.dbo.sysjobs j
                    JOIN msdb.dbo.sysjobactivity ja ON j.job_id = ja.job_id
                    WHERE j.name = %s
                    AND ja.run_requested_date IS NOT NULL
                    AND CONVERT(VARCHAR(10), ja.run_requested_date, 112) = CONVERT(VARCHAR(10), GETDATE(), 112)
                    ORDER BY ja.run_requested_date DESC
                """, (job_name,), database="msdb")
                
                if result:
                    status = result[0].get('job_status', 'Unknown')
                    if status == 'Completed':
                        logger.info(f"Job '{job_name}' completado")
                        return (True, "Job completado exitosamente")
                    elif status == 'Running':
                        logger.debug(f"Job '{job_name}' aún en ejecución... ({total_waited}s)")
                else:
                    logger.warning(f"No se pudo obtener estado del job '{job_name}'")
            
            return (False, f"Timeout esperando job después de {max_wait}s")
            
        except Exception as e:
            logger.error(f"Error ejecutando job '{job_name}': {e}")
            return (False, str(e))


class InfoCentralClient(SQLClient):
    """Cliente específico para InfoCentral"""
    
    def __init__(self):
        config = get_config()
        super().__init__(config.sql_infocentral)
    
    def validar_inventario(self) -> tuple[bool, str, list[dict]]:
        """
        Ejecuta el SP de validación de inventario.
        
        Returns:
            tuple: (hay_diferencias: bool, mensaje: str, acciones: list)
        """
        logger.info("Validando inventario en InfoCentral...")
        
        try:
            # Verificar si hay diferencias
            result = self.execute_sp(
                "[db_owner].[RevisarProcesodeInventarioFinalDiario]",
                ("hayDiferencias",)
            )
            
            if result and result[0].get('DiferenciasOrigenDestino') == 'No hay diferencias contra el origen':
                logger.info("No hay diferencias en inventario")
                return (False, "No hay diferencias contra el origen", [])
            
            # Obtener acciones correctivas
            acciones = self.execute_sp(
                "[db_owner].[RevisarProcesodeInventarioFinalDiario]",
                ("obtenerAcciones",)
            )
            
            logger.warning(f"Se encontraron diferencias. Acciones: {len(acciones)}")
            return (True, "Hay diferencias contra el origen", acciones)
            
        except Exception as e:
            logger.error(f"Error validando inventario: {e}")
            raise


class DEADWHClient(SQLClient):
    """Cliente específico para DEADWH"""
    
    def __init__(self):
        config = get_config()
        super().__init__(config.sql_deadwh)
    
    def enviar_reportes(self, es_prueba: int = 0, reporte: int = 0) -> tuple[bool, str]:
        """
        Ejecuta el SP de envío de reportes.
        
        Args:
            es_prueba: 0=oficial, 1=prueba
            reporte: 0=todos, 5=Compras Nacionales+Importaciones, etc.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        logger.info(f"Enviando reportes (prueba={es_prueba}, reporte={reporte})...")
        
        try:
            self.execute_sp(
                "[dbo].[TiEnvioReportesTableauProc]",
                (es_prueba, reporte)
            )
            logger.info("Reportes enviados exitosamente")
            return (True, "Reportes enviados exitosamente")
        except Exception as e:
            logger.error(f"Error enviando reportes: {e}")
            return (False, str(e))


class CubosOfiClient(SQLClient):
    """Cliente específico para SrvCubosOfi"""
    
    def __init__(self):
        config = get_config()
        super().__init__(config.sql_cubosofi)
    
    def ejecutar_job_abastecimientos(self) -> tuple[bool, str]:
        """Ejecuta el job de actualización de datos de abastecimientos"""
        return self.execute_job("BI ABASTECIMIENTOS MP 6:30", wait_for_completion=True)
    
    def ejecutar_job_inventario(self) -> tuple[bool, str]:
        """Ejecuta el job de inventario de chatarra"""
        return self.execute_job("BI Inventario Chatarra 5:15 am", wait_for_completion=True)

