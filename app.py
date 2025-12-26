"""
Interfaz Streamlit para Automatización de Reportes MP
"""
import streamlit as st
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Configurar logging para capturar en la UI
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S'
)

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_config, reset_config
from src.workflow import ReportWorkflow, StepResult
from src.tableau_client import TableauClient
from src.sql_client import DEADWHClient


# Configuración de la página
st.set_page_config(
    page_title="Reportes MP - Automatización",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para tema Light
st.markdown("""
<style>
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        margin: 0.5rem 0;
        color: #1b5e20;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        margin: 0.5rem 0;
        color: #b71c1c;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        margin: 0.5rem 0;
        color: #0d47a1;
    }
    .step-running {
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    /* Logo DEACERO */
    .sidebar-logo {
        filter: none;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Inicializa el estado de la sesión"""
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'last_result' not in st.session_state:
        st.session_state.last_result = None
    if 'steps' not in st.session_state:
        st.session_state.steps = []


def add_log(message: str, level: str = "INFO"):
    """Agrega un mensaje al log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append({
        'timestamp': timestamp,
        'level': level,
        'message': message
    })


def on_step_complete(result: StepResult):
    """Callback cuando se completa un paso"""
    st.session_state.steps.append(result)
    level = "INFO" if result.success else "ERROR"
    icon = "✅" if result.success else "❌"
    add_log(f"{icon} {result.nombre}: {result.mensaje}", level)


def render_sidebar():
    """Renderiza la barra lateral"""
    with st.sidebar:
        st.title("⚙️ Configuración")
        
        # Botón para recargar configuración
        if st.button("🔄 Recargar Configuración", use_container_width=True, type="secondary"):
            reset_config()
            st.rerun()
        
        # Estado de configuración
        config = get_config()
        is_valid, errors = config.validate()
        
        if is_valid:
            st.success("✅ Configuración válida")
        else:
            st.error("❌ Configuración incompleta")
            for error in errors:
                st.warning(f"⚠️ {error}")
        
        st.divider()
        
        # Info de conexión
        st.subheader("🔗 Conexiones")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tableau", "Conectado" if config.tableau.user else "❌")
        with col2:
            st.metric("SQL Server", "Conectado" if config.sql_infocentral.password else "❌")
        
        # Jira
        jira_valid, _ = config.validate_jira()
        st.metric("Jira", "Conectado" if jira_valid else "⚠️ Opcional")
        
        st.divider()
        
        # Información de correos y reportes
        st.subheader("📧 Configuración de Correos")
        
        with st.expander("📨 Destinatarios de Alertas", expanded=False):
            st.write("**Alertas de Error:**")
            if config.email.error_recipients:
                st.success(f"✅ {config.email.error_recipients}")
            else:
                st.warning("⚠️ No configurado")
            
            st.write("**Notificaciones de Éxito:**")
            if config.email.success_recipients:
                st.success(f"✅ {config.email.success_recipients}")
            else:
                st.warning("⚠️ No configurado")
        
        with st.expander("📊 Reportes PDF - Destinatarios", expanded=False):
            try:
                deadwh = DEADWHClient()
                reportes = deadwh.obtener_configuracion_reportes()
                
                if reportes:
                    st.write(f"**Total de reportes configurados:** {len(reportes)}")
                    
                    # Mostrar tabla de reportes
                    import pandas as pd
                    df_reportes = pd.DataFrame(reportes)
                    st.dataframe(
                        df_reportes[['ClaReporte', 'NombreReporte', 'Para', 'CC', 'CorreoPrueba']],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Mostrar todos los destinatarios únicos
                    destinatarios = deadwh.obtener_todos_destinatarios()
                    if destinatarios:
                        st.write(f"**Destinatarios únicos:** {len(destinatarios)}")
                        st.text(", ".join(destinatarios[:10]))  # Mostrar primeros 10
                        if len(destinatarios) > 10:
                            st.caption(f"... y {len(destinatarios) - 10} más")
                else:
                    st.info("No se pudo obtener la configuración de reportes")
            except Exception as e:
                st.error(f"Error obteniendo configuración: {str(e)}")
                st.caption("💡 Verifica la conexión a SQL Server (DEADWH)")
        
        st.divider()
        
        # Información
        st.subheader("ℹ️ Información")
        st.text(f"Datasource: {config.tableau.datasource_name}")
        st.text(f"Proyecto Jira: {config.jira.project_key}")


def render_header():
    """Renderiza el encabezado"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("Automatización Reportes MP")
        st.caption("Sistema de validación y envío de reportes de Materias Primas")
    
    with col3:
        st.metric(
            "Estado",
            "🟢 Listo" if not st.session_state.running else "🔄 Ejecutando",
            delta=None
        )


def render_actions():
    """Renderiza los botones de acción"""
    st.subheader("Acciones")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button(
            "🔍 Validar Extracto",
            disabled=st.session_state.running,
            use_container_width=True,
            type="secondary"
        ):
            run_validation()
    
    with col2:
        if st.button(
            "🚀 Proceso Completo",
            disabled=st.session_state.running,
            use_container_width=True,
            type="primary"
        ):
            run_full_workflow()
    
    with col3:
        if st.button(
            "📧 Solo Enviar Correos",
            disabled=st.session_state.running,
            use_container_width=True,
            type="secondary"
        ):
            run_send_only()
    
    with col4:
        if st.button(
            "🗑️ Limpiar Logs",
            disabled=st.session_state.running,
            use_container_width=True
        ):
            st.session_state.logs = []
            st.session_state.steps = []
            st.session_state.last_result = None
            st.rerun()


def run_validation():
    """Ejecuta solo la validación"""
    st.session_state.running = True
    st.session_state.steps = []
    add_log("Iniciando validación de extracto...", "INFO")
    
    try:
        workflow = ReportWorkflow(on_step_complete=on_step_complete)
        success, message = workflow.run_validation_only()
        
        st.session_state.last_result = {
            'success': success,
            'message': message,
            'summary': workflow.get_summary()
        }
        
        if success:
            add_log(f"✅ Validación exitosa: {message}", "INFO")
        else:
            add_log(f"❌ Validación fallida: {message}", "ERROR")
            
    except Exception as e:
        add_log(f"❌ Error: {str(e)}", "ERROR")
        st.session_state.last_result = {'success': False, 'message': str(e)}
    finally:
        st.session_state.running = False
        st.rerun()


def run_full_workflow():
    """Ejecuta el flujo completo"""
    st.session_state.running = True
    st.session_state.steps = []
    add_log("Iniciando proceso completo...", "INFO")
    
    try:
        workflow = ReportWorkflow(on_step_complete=on_step_complete)
        success, message = workflow.run_full()
        
        st.session_state.last_result = {
            'success': success,
            'message': message,
            'summary': workflow.get_summary()
        }
        
        if success:
            add_log(f"✅ Proceso completado: {message}", "INFO")
        else:
            add_log(f"❌ Proceso fallido: {message}", "ERROR")
            
    except Exception as e:
        add_log(f"❌ Error: {str(e)}", "ERROR")
        st.session_state.last_result = {'success': False, 'message': str(e)}
    finally:
        st.session_state.running = False
        st.rerun()


def run_send_only():
    """Ejecuta solo el envío de correos"""
    st.session_state.running = True
    st.session_state.steps = []
    add_log("Iniciando envío de correos...", "INFO")
    
    try:
        workflow = ReportWorkflow(on_step_complete=on_step_complete)
        success, message = workflow.run_send_only()
        
        st.session_state.last_result = {
            'success': success,
            'message': message,
            'summary': workflow.get_summary()
        }
        
        if success:
            add_log(f"✅ Envío exitoso: {message}", "INFO")
        else:
            add_log(f"❌ Envío fallido: {message}", "ERROR")
            
    except Exception as e:
        add_log(f"❌ Error: {str(e)}", "ERROR")
        st.session_state.last_result = {'success': False, 'message': str(e)}
    finally:
        st.session_state.running = False
        st.rerun()


def render_status():
    """Renderiza el estado actual y resultado"""
    if st.session_state.last_result:
        result = st.session_state.last_result
        
        if result['success']:
            st.success(f"**Resultado Exitoso:** {result['message']}")
        else:
            st.error(f"**Error:** {result['message']}")
        
        # Mostrar resumen si está disponible
        if 'summary' in result:
            summary = result['summary']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Pasos", summary.get('total_pasos', 0))
            with col2:
                st.metric("Exitosos", summary.get('pasos_exitosos', 0))
            with col3:
                st.metric("Fallidos", summary.get('pasos_fallidos', 0))
            with col4:
                tiempo = summary.get('tiempo_total', 0)
                st.metric("Tiempo", f"{tiempo:.1f}s")
            
            if summary.get('ticket_jira'):
                config = get_config()
                jira_url = f"{config.jira.server}/browse/{summary['ticket_jira']}"
                st.info(f"🎫 Ticket creado: [{summary['ticket_jira']}]({jira_url})")


def render_steps():
    """Renderiza los pasos ejecutados"""
    if st.session_state.steps:
        st.subheader("Pasos Ejecutados")
        
        for step in st.session_state.steps:
            icon = "✅" if step.success else "❌"
            color = "green" if step.success else "red"
            
            with st.expander(f"{icon} {step.nombre} ({step.duracion:.2f}s)", expanded=not step.success):
                st.write(f"**Estado:** {step.mensaje}")
                if step.detalles:
                    # Mostrar información de fecha de actualización de forma más clara
                    if 'last_updated_utc' in step.detalles or 'last_updated' in step.detalles:
                        st.write("**Última Actualización:**")
                        col1, col2 = st.columns(2)
                        with col1:
                            if 'last_updated_local' in step.detalles:
                                st.success(f"🕐 Hora Local (Monterrey): {step.detalles['last_updated_local']}")
                            elif 'last_updated' in step.detalles:
                                st.info(f"🕐 Hora: {step.detalles['last_updated']}")
                        with col2:
                            if 'last_updated_utc' in step.detalles:
                                st.info(f"🌐 UTC: {step.detalles['last_updated_utc']}")
                            if 'timezone' in step.detalles:
                                st.caption(f"Zona horaria: {step.detalles['timezone']}")
                    
                    # Mostrar otros detalles que no sean de fecha
                    otros_detalles = {k: v for k, v in step.detalles.items() 
                                    if k not in ['last_updated', 'last_updated_utc', 'last_updated_local', 'timezone']}
                    if otros_detalles:
                        st.json(otros_detalles)


def render_logs():
    """Renderiza los logs"""
    st.subheader("Logs")
    
    log_container = st.container()
    
    with log_container:
        if st.session_state.logs:
            # Mostrar logs en orden inverso (más reciente primero)
            for log in reversed(st.session_state.logs[-50:]):  # Últimos 50 logs
                level_colors = {
                    'INFO': '🔵',
                    'WARNING': '🟡',
                    'ERROR': '🔴',
                    'DEBUG': '⚪'
                }
                icon = level_colors.get(log['level'], '⚪')
                st.text(f"{log['timestamp']} {icon} {log['message']}")
        else:
            st.info("No hay logs disponibles. Ejecuta una acción para ver los resultados.")


def main():
    """Función principal"""
    init_session_state()
    
    render_sidebar()
    render_header()
    
    st.divider()
    
    render_actions()
    
    st.divider()
    
    # Layout principal
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_status()
        render_steps()
    
    with col2:
        render_logs()
    
    # Footer
    st.divider()
    st.caption("Sistema de Automatización de Reportes MP v1.0 | Equipo de Datos y Analítica")


if __name__ == "__main__":
    main()

