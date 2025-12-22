"""
Notificador - Envío de correos y alertas
"""
import logging
from typing import Optional
from datetime import datetime

import pymssql

from .config import get_config

logger = logging.getLogger(__name__)


class Notifier:
    """Clase para envío de notificaciones por email"""
    
    def __init__(self):
        self.config = get_config().email
    
    def _send_via_dbmail(self, recipients: str, subject: str, body: str, 
                         body_format: str = 'HTML') -> tuple[bool, str]:
        """Envía email usando SQL Server Database Mail"""
        try:
            with pymssql.connect(
                server=self.config.server,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                tds_version='7.0',
                autocommit=True
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """EXEC [msdb].[dbo].[sp_send_dbmail] 
                           @profile_name = %s, 
                           @recipients = %s, 
                           @body_format = %s, 
                           @body = %s, 
                           @subject = %s""",
                        (self.config.profile, recipients, body_format, body, subject)
                    )
            
            logger.info(f"Email enviado a: {recipients}")
            return (True, "Email enviado exitosamente")
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            return (False, str(e))
    
    def enviar_alerta_error(self, titulo: str, mensaje: str, 
                           detalles: str = "", ticket_jira: str = None) -> tuple[bool, str]:
        """
        Envía una alerta de error por email.
        
        Args:
            titulo: Título del error
            mensaje: Mensaje principal
            detalles: Detalles adicionales (opcional)
            ticket_jira: Key del ticket creado (opcional)
        """
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        ticket_html = ""
        if ticket_jira:
            jira_url = f"{get_config().jira.server}/browse/{ticket_jira}"
            ticket_html = f"""
            <p><strong>🎫 Ticket Jira:</strong> 
               <a href="{jira_url}">{ticket_jira}</a>
            </p>
            """
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background-color: #ffebee; border-left: 4px solid #f44336; padding: 15px; margin-bottom: 20px;">
                <h2 style="color: #c62828; margin: 0;">⚠️ {titulo}</h2>
            </div>
            
            <p><strong>Fecha/Hora:</strong> {fecha}</p>
            <p><strong>Mensaje:</strong> {mensaje}</p>
            
            {f'<div style="background-color: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 4px;"><pre>{detalles}</pre></div>' if detalles else ''}
            
            {ticket_html}
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <h3>Acciones Recomendadas:</h3>
            <ol>
                <li>Verificar el estado del extracto en Tableau Server</li>
                <li>Revisar los logs del proceso</li>
                <li>Ejecutar el proceso manualmente si es necesario</li>
            </ol>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Este es un mensaje automático del Sistema de Automatización de Reportes MP.
            </p>
        </body>
        </html>
        """
        
        subject = f"🔴 ALERTA MP: {titulo}"
        return self._send_via_dbmail(self.config.error_recipients, subject, body)
    
    def enviar_notificacion_exito(self, mensaje: str, 
                                  reportes_enviados: list = None) -> tuple[bool, str]:
        """
        Envía una notificación de éxito por email.
        
        Args:
            mensaje: Mensaje principal
            reportes_enviados: Lista de reportes enviados (opcional)
        """
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        reportes_html = ""
        if reportes_enviados:
            reportes_list = "\n".join([f"<li>{r}</li>" for r in reportes_enviados])
            reportes_html = f"""
            <h3>Reportes Enviados:</h3>
            <ul>{reportes_list}</ul>
            """
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background-color: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin-bottom: 20px;">
                <h2 style="color: #2e7d32; margin: 0;">✅ Proceso Completado Exitosamente</h2>
            </div>
            
            <p><strong>Fecha/Hora:</strong> {fecha}</p>
            <p><strong>Estado:</strong> {mensaje}</p>
            
            {reportes_html}
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Este es un mensaje automático del Sistema de Automatización de Reportes MP.
            </p>
        </body>
        </html>
        """
        
        subject = f"✅ Reportes MP: {mensaje}"
        return self._send_via_dbmail(self.config.success_recipients, subject, body)
    
    def enviar_resumen_proceso(self, 
                               exito: bool,
                               pasos_ejecutados: list[dict],
                               tiempo_total: float,
                               ticket_jira: str = None) -> tuple[bool, str]:
        """
        Envía un resumen detallado del proceso.
        
        Args:
            exito: Si el proceso fue exitoso
            pasos_ejecutados: Lista de pasos con su estado
            tiempo_total: Tiempo total de ejecución en segundos
            ticket_jira: Ticket creado en caso de error
        """
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Construir tabla de pasos
        pasos_rows = ""
        for paso in pasos_ejecutados:
            icon = "✅" if paso.get('success', False) else "❌"
            color = "#4caf50" if paso.get('success', False) else "#f44336"
            pasos_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{paso.get('nombre', 'N/A')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; color: {color};">{icon} {paso.get('estado', 'N/A')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{paso.get('duracion', 'N/A')}</td>
            </tr>
            """
        
        status_color = "#4caf50" if exito else "#f44336"
        status_text = "EXITOSO" if exito else "FALLIDO"
        status_icon = "✅" if exito else "❌"
        
        ticket_html = ""
        if ticket_jira:
            jira_url = f"{get_config().jira.server}/browse/{ticket_jira}"
            ticket_html = f'<p><strong>Ticket Jira:</strong> <a href="{jira_url}">{ticket_jira}</a></p>'
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background-color: {'#e8f5e9' if exito else '#ffebee'}; 
                        border-left: 4px solid {status_color}; padding: 15px; margin-bottom: 20px;">
                <h2 style="color: {status_color}; margin: 0;">
                    {status_icon} Proceso de Reportes MP: {status_text}
                </h2>
            </div>
            
            <p><strong>Fecha/Hora:</strong> {fecha}</p>
            <p><strong>Tiempo Total:</strong> {tiempo_total:.2f} segundos</p>
            {ticket_html}
            
            <h3>Detalle de Ejecución:</h3>
            <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                <thead>
                    <tr style="background-color: #f5f5f5;">
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Paso</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Estado</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Duración</th>
                    </tr>
                </thead>
                <tbody>
                    {pasos_rows}
                </tbody>
            </table>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Sistema de Automatización de Reportes MP
            </p>
        </body>
        </html>
        """
        
        subject = f"{status_icon} Resumen Reportes MP: {status_text} - {fecha}"
        recipients = self.config.error_recipients if not exito else self.config.success_recipients
        
        return self._send_via_dbmail(recipients, subject, body)

