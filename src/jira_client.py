"""
Cliente Jira - Creación automática de tickets
"""
import logging
from typing import Optional
from datetime import datetime

from .config import get_config

logger = logging.getLogger(__name__)


class JiraClient:
    """Cliente para crear tickets en Jira"""
    
    def __init__(self):
        self.config = get_config().jira
        self._client = None
    
    def _get_client(self):
        """Obtiene el cliente de Jira (lazy loading)"""
        if self._client is None:
            try:
                from jira import JIRA
                self._client = JIRA(
                    server=self.config.server,
                    basic_auth=(self.config.user, self.config.api_token)
                )
                logger.info(f"Conectado a Jira: {self.config.server}")
            except ImportError:
                logger.error("Librería 'jira' no instalada. Ejecuta: pip install jira")
                raise
            except Exception as e:
                logger.error(f"Error conectando a Jira: {e}")
                raise
        return self._client
    
    def crear_ticket_error(self, 
                          titulo: str,
                          descripcion: str,
                          componente: str = "Reportes MP",
                          prioridad: str = "High") -> tuple[bool, str, Optional[str]]:
        """
        Crea un ticket de error en Jira.
        
        Args:
            titulo: Título del ticket
            descripcion: Descripción detallada del error
            componente: Componente afectado
            prioridad: 'Highest', 'High', 'Medium', 'Low', 'Lowest'
        
        Returns:
            tuple: (success: bool, message: str, issue_key: str or None)
        """
        # Validar configuración
        is_valid, errors = get_config().validate_jira()
        if not is_valid:
            msg = f"Configuración de Jira incompleta: {', '.join(errors)}"
            logger.warning(msg)
            return (False, msg, None)
        
        logger.info(f"Creando ticket en Jira: {titulo[:50]}...")
        
        try:
            client = self._get_client()
            
            # Construir descripción enriquecida
            descripcion_completa = f"""
h2. Error en Automatización de Reportes MP

*Fecha/Hora:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Componente:* {componente}

h3. Descripción del Error
{descripcion}

h3. Acciones Recomendadas
# Verificar estado del extracto en Tableau Server
# Revisar logs del proceso de automatización
# Contactar al equipo de Datos si persiste

----
_Ticket generado automáticamente por el sistema de automatización de reportes MP_
            """
            
            # Crear el ticket
            issue_dict = {
                'project': {'key': self.config.project_key},
                'summary': titulo,
                'description': descripcion_completa,
                'issuetype': {'name': 'Task'},  # o 'Bug' según preferencia
            }
            
            # Intentar agregar prioridad si está disponible
            try:
                issue_dict['priority'] = {'name': prioridad}
            except Exception:
                pass  # Algunos proyectos no tienen prioridades configuradas
            
            new_issue = client.create_issue(fields=issue_dict)
            
            issue_key = new_issue.key
            issue_url = f"{self.config.server}/browse/{issue_key}"
            
            logger.info(f"Ticket creado: {issue_key} - {issue_url}")
            return (True, f"Ticket creado: {issue_key}", issue_key)
            
        except Exception as e:
            error_msg = f"Error creando ticket en Jira: {e}"
            logger.error(error_msg)
            return (False, error_msg, None)
    
    def crear_ticket_extracto_fallido(self, datasource_name: str, 
                                      error_detail: str) -> tuple[bool, str, Optional[str]]:
        """Crea un ticket específico para fallo de extracto"""
        titulo = f"[AUTO] Error en extracto Tableau: {datasource_name}"
        descripcion = f"""
El sistema de automatización detectó un problema con el extracto de Tableau.

*Datasource:* {datasource_name}
*Error:* {error_detail}

El proceso de envío de reportes MP no pudo completarse debido a este error.
        """
        return self.crear_ticket_error(titulo, descripcion, "Extracto Tableau", "High")
    
    def crear_ticket_envio_fallido(self, error_detail: str) -> tuple[bool, str, Optional[str]]:
        """Crea un ticket específico para fallo de envío"""
        titulo = f"[AUTO] Error en envío de reportes MP"
        descripcion = f"""
El sistema de automatización no pudo enviar los reportes de Materias Primas.

*Error:* {error_detail}

Se requiere intervención manual para completar el envío.
        """
        return self.crear_ticket_error(titulo, descripcion, "Envío de Reportes", "High")
    
    def crear_ticket_datos_fallidos(self, ubicaciones: list) -> tuple[bool, str, Optional[str]]:
        """Crea un ticket específico para diferencias en datos"""
        titulo = f"[AUTO] Diferencias detectadas en inventario MP"
        ubicaciones_str = "\n".join([f"* {u}" for u in ubicaciones[:10]])
        if len(ubicaciones) > 10:
            ubicaciones_str += f"\n* ... y {len(ubicaciones) - 10} más"
        
        descripcion = f"""
El sistema detectó diferencias significativas en los datos de inventario.

*Ubicaciones afectadas:*
{ubicaciones_str}

Los jobs correctivos fueron ejecutados pero el problema persiste.
        """
        return self.crear_ticket_error(titulo, descripcion, "Datos Inventario", "High")

