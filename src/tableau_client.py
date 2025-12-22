"""
Cliente Tableau Server - Validación de extractos y descarga de PDFs
"""
import os
import time
import logging
from io import BytesIO
from datetime import datetime, timezone, timedelta
from typing import Optional

import tableauserverclient as TSC
import PyPDF2

from .config import get_config

logger = logging.getLogger(__name__)


class TableauClient:
    """Cliente para Tableau Server"""
    
    def __init__(self):
        self.config = get_config().tableau
        self.server: Optional[TSC.Server] = None
        self._connected = False
    
    def connect(self) -> bool:
        """Conecta a Tableau Server"""
        try:
            self.server = TSC.Server(
                self.config.server,
                http_options={'verify': False},
                use_server_version=True
            )
            auth = TSC.TableauAuth(
                self.config.user,
                self.config.password,
                self.config.site
            )
            self.server.auth.sign_in(auth)
            self._connected = True
            logger.info(f"Conectado a Tableau Server: {self.config.server}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a Tableau: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Desconecta de Tableau Server"""
        if self.server and self._connected:
            try:
                self.server.auth.sign_out()
                logger.info("Desconectado de Tableau Server")
            except Exception:
                pass
            self._connected = False
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def find_datasource(self, name: str) -> Optional[TSC.DatasourceItem]:
        """Busca un datasource por nombre"""
        if not self._connected:
            raise RuntimeError("No conectado a Tableau Server")
        
        logger.info(f"Buscando datasource: {name}")
        
        all_datasources = list(TSC.Pager(self.server.datasources))
        name_lower = name.lower()
        
        # Búsqueda exacta
        for ds in all_datasources:
            if ds.name.lower() == name_lower:
                if ds.has_extracts:
                    logger.info(f"Datasource encontrado: {ds.name} (id={ds.id})")
                    return ds
        
        # Búsqueda parcial
        for ds in all_datasources:
            if name_lower in ds.name.lower() or ds.name.lower() in name_lower:
                if ds.has_extracts:
                    logger.info(f"Datasource encontrado (parcial): {ds.name} (id={ds.id})")
                    return ds
        
        logger.warning(f"Datasource no encontrado: {name}")
        return None
    
    def validar_extracto(self, datasource_name: str = None, 
                         max_age_hours: float = None) -> tuple[bool, str, Optional[datetime]]:
        """
        Valida que el extracto esté actualizado.
        
        Returns:
            tuple: (is_valid: bool, message: str, last_updated: datetime)
        """
        config = get_config()
        ds_name = datasource_name or self.config.datasource_name
        max_hours = max_age_hours or config.validation.max_extract_age_hours
        
        ds = self.find_datasource(ds_name)
        if not ds:
            return (False, f"Datasource '{ds_name}' no encontrado", None)
        
        if not ds.has_extracts:
            return (False, f"Datasource '{ds_name}' no tiene extracto", None)
        
        last_updated = ds.updated_at
        if last_updated and last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)
        
        if not last_updated:
            return (False, "No se pudo obtener fecha de actualización", None)
        
        now_utc = datetime.now(timezone.utc)
        age = now_utc - last_updated
        age_hours = age.total_seconds() / 3600
        
        logger.info(f"Extracto '{ds_name}': actualizado hace {age_hours:.2f} horas")
        
        if age_hours > max_hours:
            return (
                False,
                f"Extracto desactualizado: {age_hours:.2f}h (máximo: {max_hours}h)",
                last_updated
            )
        
        return (True, f"Extracto válido: {age_hours:.2f}h", last_updated)
    
    def refresh_extracto(self, datasource_name: str = None,
                         max_wait_seconds: int = 300) -> tuple[bool, str]:
        """
        Intenta refrescar el extracto de un datasource.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        ds_name = datasource_name or self.config.datasource_name
        ds = self.find_datasource(ds_name)
        
        if not ds:
            return (False, f"Datasource '{ds_name}' no encontrado")
        
        logger.info(f"Iniciando refresh de extracto: {ds_name}")
        
        try:
            job = self.server.datasources.refresh(ds)
            logger.info(f"Job de refresh iniciado: {job.id}")
            
            # Esperar a que termine
            wait_interval = 10
            total_waited = 0
            
            while total_waited < max_wait_seconds:
                time.sleep(wait_interval)
                total_waited += wait_interval
                
                job = self.server.jobs.get_by_id(job.id)
                
                if job.finish_code == 0:
                    logger.info(f"Refresh completado exitosamente")
                    return (True, "Refresh completado")
                elif job.finish_code == 1:
                    logger.error(f"Refresh falló: {job.notes}")
                    return (False, f"Refresh falló: {job.notes}")
                elif job.finish_code == 2:
                    logger.warning(f"Refresh cancelado")
                    return (False, "Refresh cancelado")
                
                logger.debug(f"Esperando refresh... ({total_waited}s)")
            
            return (False, f"Timeout después de {max_wait_seconds}s")
            
        except Exception as e:
            logger.error(f"Error durante refresh: {e}")
            return (False, str(e))
    
    def descargar_pdf(self, workbook_name: str, output_path: str,
                      orientation: str = 'Portrait') -> tuple[bool, str]:
        """
        Descarga un workbook como PDF combinando todas sus vistas.
        
        Args:
            workbook_name: Nombre del workbook en Tableau
            output_path: Ruta completa del archivo PDF de salida
            orientation: 'Portrait' o 'Landscape'
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self._connected:
            raise RuntimeError("No conectado a Tableau Server")
        
        logger.info(f"Descargando PDF: {workbook_name}")
        
        try:
            # Buscar workbook
            req_option = TSC.RequestOptions()
            req_option.filter.add(TSC.Filter(
                TSC.RequestOptions.Field.Name,
                TSC.RequestOptions.Operator.Equals,
                workbook_name
            ))
            
            workbooks, _ = self.server.workbooks.get(req_option)
            
            if not workbooks:
                return (False, f"Workbook '{workbook_name}' no encontrado")
            
            if len(workbooks) > 1:
                logger.warning(f"Múltiples workbooks encontrados, usando el primero")
            
            workbook = workbooks[0]
            self.server.workbooks.populate_views(workbook)
            
            # Configurar orientación
            orientation_map = {
                'Portrait': TSC.PDFRequestOptions.Orientation.Portrait,
                'Landscape': TSC.PDFRequestOptions.Orientation.Landscape
            }
            pdf_orientation = orientation_map.get(orientation, TSC.PDFRequestOptions.Orientation.Portrait)
            
            # Descargar y combinar PDFs de todas las vistas
            pdf_merger = PyPDF2.PdfMerger()
            
            for view in workbook.views:
                pdf_options = TSC.PDFRequestOptions(
                    page_type=TSC.PDFRequestOptions.PageType.Letter,
                    orientation=pdf_orientation,
                    maxage=1
                )
                self.server.views.populate_pdf(view, pdf_options)
                stream = BytesIO(view.pdf)
                pdf_merger.append(stream)
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Guardar PDF combinado
            pdf_merger.write(output_path)
            pdf_merger.close()
            
            # Validar tamaño
            size = os.path.getsize(output_path)
            if size < 1000:
                return (False, f"PDF generado muy pequeño: {size} bytes")
            
            logger.info(f"PDF descargado: {output_path} ({size} bytes)")
            return (True, output_path)
            
        except Exception as e:
            logger.error(f"Error descargando PDF '{workbook_name}': {e}")
            return (False, str(e))
    
    def descargar_todos_reportes(self, output_dir: str) -> tuple[bool, str, list[str]]:
        """
        Descarga todos los reportes configurados.
        
        Returns:
            tuple: (success: bool, message: str, files: list)
        """
        from datetime import datetime
        
        # Configuración de reportes
        reportes = [
            {'name': 'Reporte Costo Puesto en Patios', 'alias': 'Reporte Costo Puesto en Patios', 
             'orientation': 'Portrait', 'condition': datetime.today().weekday() != 0},
            {'name': 'Reporte Costo Puesto en Patios (Inicio Semana)', 'alias': 'Reporte Costo Puesto en Patios', 
             'orientation': 'Portrait', 'condition': datetime.today().weekday() == 0},
            {'name': 'Reporte Inventario Diario', 'alias': 'Reporte Inventario Diario', 
             'orientation': 'Portrait', 'condition': True},
            {'name': 'Reporte Compra Chatarra Prom Dia Habil', 'alias': 'Reporte Compra Chatarra Prom Dia Habil', 
             'orientation': 'Landscape', 'condition': datetime.today().day != 1},
            {'name': 'Reporte Compra Chatarra Prom Dia Habil Dia Primero', 'alias': 'Reporte Compra Chatarra Prom Dia Habil', 
             'orientation': 'Landscape', 'condition': datetime.today().day == 1},
            {'name': 'Reporte de Compras e Inventario por Tipo de Material', 'alias': 'Reporte de Compras e Inventario por Tipo de Material', 
             'orientation': 'Portrait', 'condition': True},
            {'name': 'Reporte NUEVO Patios - Compras Nacionales + Importaciones', 'alias': 'Reporte NUEVO Patios - Compras Nacionales + Importaciones', 
             'orientation': 'Portrait', 'condition': datetime.today().weekday() != 0},
            {'name': 'Reporte NUEVO Patios - Compras Nacionales + Importaciones_InicioSem', 'alias': 'Reporte NUEVO Patios - Compras Nacionales + Importaciones', 
             'orientation': 'Portrait', 'condition': datetime.today().weekday() == 0}
        ]
        
        downloaded_files = []
        errors = []
        
        for reporte in reportes:
            if not reporte['condition']:
                continue
            
            output_path = os.path.join(output_dir, f"{reporte['alias']}.pdf")
            success, msg = self.descargar_pdf(
                reporte['name'],
                output_path,
                reporte['orientation']
            )
            
            if success:
                downloaded_files.append(output_path)
            else:
                errors.append(f"{reporte['name']}: {msg}")
        
        if errors:
            return (False, f"Errores en {len(errors)} reportes: {'; '.join(errors)}", downloaded_files)
        
        return (True, f"{len(downloaded_files)} reportes descargados", downloaded_files)

