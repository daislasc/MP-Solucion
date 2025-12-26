"""
Módulo de configuración - Carga variables de entorno
"""
import os
import sys
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class TableauConfig:
    server: str
    user: str
    password: str
    site: str
    datasource_name: str


@dataclass
class SQLServerConfig:
    server: str
    user: str
    password: str
    database: str = ""


@dataclass
class JiraConfig:
    server: str
    user: str
    api_token: str
    project_key: str


@dataclass
class EmailConfig:
    server: str
    user: str
    password: str
    database: str
    profile: str
    error_recipients: str
    success_recipients: str


@dataclass
class PathsConfig:
    pdf_source: str
    pdf_dest: str


@dataclass
class ValidationConfig:
    max_extract_age_hours: float
    max_refresh_retries: int
    refresh_wait_seconds: int


class Config:
    """Configuración centralizada de la aplicación"""
    
    def __init__(self):
        # Cargar .env desde el directorio raíz del proyecto
        import pathlib
        env_path = pathlib.Path(__file__).parent.parent / '.env'
        load_dotenv(dotenv_path=env_path)
        
        # Tableau
        self.tableau = TableauConfig(
            server=os.getenv("TABLEAU_SERVER", "https://tableau.deacero.com/"),
            user=os.getenv("TABLEAU_USER", ""),
            password=os.getenv("TABLEAU_PASSWORD", ""),
            site=os.getenv("TABLEAU_SITE", ""),
            datasource_name=os.getenv("TABLEAU_DATASOURCE_NAME", "Datamart Materias Primas")
        )
        
        # SQL Servers
        self.sql_infocentral = SQLServerConfig(
            server=os.getenv("SQL_INFOCENTRAL_SERVER", "INFOCENTRAL"),
            user=os.getenv("SQL_INFOCENTRAL_USER", "sa"),
            password=os.getenv("SQL_INFOCENTRAL_PWD", ""),
            database="InfoCentral"
        )
        
        self.sql_deadwh = SQLServerConfig(
            server=os.getenv("SQL_DEADWH_SERVER", "DEADWH"),
            user=os.getenv("SQL_DEADWH_USER", "sa"),
            password=os.getenv("SQL_DEADWH_PWD", ""),
            database="TIMonitorSQL"
        )
        
        self.sql_cubosofi = SQLServerConfig(
            server=os.getenv("SQL_CUBOSOFI_SERVER", "SrvCubosOfi"),
            user=os.getenv("SQL_CUBOSOFI_USER", "artus"),
            password=os.getenv("SQL_CUBOSOFI_PWD", ""),
            database="msdb"
        )
        
        # Email
        self.email = EmailConfig(
            server=os.getenv("SQL_EMAIL_SERVER", "SRVMODMEM.gpodeacero.corp"),
            user=os.getenv("SQL_EMAIL_USER", "TYDUsr"),
            password=os.getenv("SQL_EMAIL_PWD", ""),
            database=os.getenv("SQL_EMAIL_DATABASE", "MEM"),
            profile=os.getenv("SQL_EMAIL_PROFILE", "MEM_Profile"),
            error_recipients=os.getenv("ERROR_EMAIL_TO", ""),
            success_recipients=os.getenv("SUCCESS_EMAIL_TO", "")
        )
        
        # Jira
        self.jira = JiraConfig(
            server=os.getenv("JIRA_SERVER", "https://deacero.atlassian.net"),
            user=os.getenv("JIRA_USER", ""),
            api_token=os.getenv("JIRA_API_TOKEN", ""),
            project_key=os.getenv("JIRA_PROJECT_KEY", "DDF")
        )
        
        # Paths
        self.paths = PathsConfig(
            pdf_source=os.getenv("PDF_SOURCE_PATH", "C:/pythonPrograms/Reportes MP/Reportes/"),
            pdf_dest=os.getenv("PDF_DEST_PATH", "//DEADWH/ReportesMateriasPrimas/")
        )
        
        # Validation
        self.validation = ValidationConfig(
            max_extract_age_hours=float(os.getenv("MAX_EXTRACT_AGE_HOURS", "24")),
            max_refresh_retries=int(os.getenv("MAX_REFRESH_RETRIES", "3")),
            refresh_wait_seconds=int(os.getenv("REFRESH_WAIT_SECONDS", "60"))
        )
    
    def validate(self) -> tuple[bool, list[str]]:
        """Valida que las configuraciones críticas estén presentes"""
        errors = []
        
        if not self.tableau.user:
            errors.append("TABLEAU_USER no configurado")
        if not self.tableau.password:
            errors.append("TABLEAU_PASSWORD no configurado")
        if not self.sql_infocentral.password:
            errors.append("SQL_INFOCENTRAL_PWD no configurado")
        if not self.sql_deadwh.password:
            errors.append("SQL_DEADWH_PWD no configurado")
        
        return (len(errors) == 0, errors)
    
    def validate_jira(self) -> tuple[bool, list[str]]:
        """Valida configuración de Jira (opcional)"""
        errors = []
        
        if not self.jira.user:
            errors.append("JIRA_USER no configurado")
        if not self.jira.api_token:
            errors.append("JIRA_API_TOKEN no configurado")
        
        return (len(errors) == 0, errors)


# Singleton
_config: Optional[Config] = None


def get_config() -> Config:
    """Obtiene la instancia de configuración (singleton)"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config():
    """Resetea el singleton de configuración para forzar recarga"""
    global _config
    _config = None
