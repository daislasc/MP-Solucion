#!/usr/bin/env python
"""
CLI para ejecutar el workflow de automatización de reportes MP.

Uso:
    python run_workflow.py --full           # Ejecuta el proceso completo
    python run_workflow.py --validate       # Solo valida el extracto
    python run_workflow.py --send           # Solo envía los correos
    python run_workflow.py --send --reporte 5  # Envía solo reporte específico
"""
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path(__file__).parent / 'logs' / f'workflow_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
    ]
)

logger = logging.getLogger(__name__)

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_config
from src.workflow import ReportWorkflow, StepResult


def print_banner():
    """Imprime el banner de inicio"""
    print("""
================================================================
       AUTOMATIZACION DE REPORTES MP - DEACERO                
                                                              
  Sistema de validacion y envio de reportes de Materias Primas
================================================================
    """)


def print_result(success: bool, message: str, summary: dict = None):
    """Imprime el resultado de la ejecución"""
    print("\n" + "=" * 60)
    
    if success:
        print("[OK] PROCESO COMPLETADO EXITOSAMENTE")
    else:
        print("[ERROR] PROCESO FALLIDO")
    
    print(f"   {message}")
    
    if summary:
        print(f"\nResumen:")
        print(f"   - Pasos ejecutados: {summary.get('total_pasos', 0)}")
        print(f"   - Exitosos: {summary.get('pasos_exitosos', 0)}")
        print(f"   - Fallidos: {summary.get('pasos_fallidos', 0)}")
        print(f"   - Tiempo total: {summary.get('tiempo_total', 0):.2f}s")
        
        if summary.get('ticket_jira'):
            config = get_config()
            print(f"   - Ticket Jira: {config.jira.server}/browse/{summary['ticket_jira']}")
    
    print("=" * 60 + "\n")


def on_step_complete(result: StepResult):
    """Callback para mostrar progreso en consola"""
    icon = "[OK]" if result.success else "[FAIL]"
    print(f"  {icon} {result.nombre}: {result.mensaje} ({result.duracion:.2f}s)")


def validate_config() -> bool:
    """Valida la configuración antes de ejecutar"""
    config = get_config()
    is_valid, errors = config.validate()
    
    if not is_valid:
        print("\n❌ Error de configuración:")
        for error in errors:
            print(f"   - {error}")
        print("\nAsegúrate de configurar el archivo .env correctamente.")
        return False
    
    return True


def run_full():
    """Ejecuta el proceso completo"""
    logger.info("Iniciando proceso completo")
    
    workflow = ReportWorkflow(on_step_complete=on_step_complete)
    success, message = workflow.run_full()
    
    print_result(success, message, workflow.get_summary())
    return 0 if success else 1


def run_validation():
    """Ejecuta solo la validación"""
    logger.info("Iniciando validación de extracto")
    
    workflow = ReportWorkflow(on_step_complete=on_step_complete)
    success, message = workflow.run_validation_only()
    
    print_result(success, message, workflow.get_summary())
    return 0 if success else 1


def run_send(reporte: int = 0, prueba: bool = False):
    """Ejecuta solo el envío de correos"""
    logger.info(f"Iniciando envío de correos (reporte={reporte}, prueba={prueba})")
    
    workflow = ReportWorkflow(on_step_complete=on_step_complete)
    success, message = workflow.run_send_only(
        es_prueba=1 if prueba else 0,
        reporte=reporte
    )
    
    print_result(success, message, workflow.get_summary())
    return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(
        description='Automatización de Reportes MP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run_workflow.py --full              Ejecuta todo el proceso
  python run_workflow.py --validate          Solo valida el extracto
  python run_workflow.py --send              Envía todos los reportes
  python run_workflow.py --send --reporte 5  Envía solo Compras Nacionales
  python run_workflow.py --send --prueba     Envía en modo prueba
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--full', action='store_true', 
                      help='Ejecuta el proceso completo')
    group.add_argument('--validate', action='store_true',
                      help='Solo valida el extracto de Tableau')
    group.add_argument('--send', action='store_true',
                      help='Solo envía los correos')
    
    parser.add_argument('--reporte', type=int, default=0,
                       help='ID del reporte a enviar (0=todos, 5=Compras Nacionales)')
    parser.add_argument('--prueba', action='store_true',
                       help='Ejecuta en modo prueba (solo destinatarios de prueba)')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Modo silencioso (menos output)')
    
    args = parser.parse_args()
    
    # Configurar nivel de logging
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    print_banner()
    
    # Validar configuración
    if not validate_config():
        return 1
    
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Ejecutar acción
    try:
        if args.full:
            return run_full()
        elif args.validate:
            return run_validation()
        elif args.send:
            return run_send(args.reporte, args.prueba)
    except KeyboardInterrupt:
        print("\n\n[WARN] Proceso interrumpido por el usuario")
        return 130
    except Exception as e:
        logger.exception(f"Error inesperado: {e}")
        print(f"\n[ERROR] Error inesperado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

