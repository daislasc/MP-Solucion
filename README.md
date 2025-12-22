# 📊 Automatización de Reportes MP - DEACERO

Sistema unificado para la validación de extractos de Tableau y envío automático de reportes de Materias Primas.

## 🚀 Características

- ✅ Validación automática de extractos de Tableau Server
- 🔄 Refresh automático de extractos desactualizados
- 📥 Descarga de reportes en PDF desde Tableau
- 📧 Envío de correos con reportes adjuntos
- 🎫 Creación automática de tickets en Jira cuando hay errores
- 🖥️ Interfaz con Streamlit
- ⌨️ CLI para ejecución programada

## 📋 Requisitos Previos

- Python 3.10 o superior
- Acceso a Tableau Server
- Acceso a SQL Server (InfoCentral, DEADWH, SrvCubosOfi)
- (Opcional) Token de API de Jira para creación de tickets

## 🛠️ Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd DEAC-79072
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Windows
copy env.example.txt .env

# Linux/Mac
cp env.example.txt .env
```

Edita el archivo `.env` con tus credenciales:

```env
# Tableau Server
TABLEAU_USER=tu_usuario
TABLEAU_PASSWORD=tu_password

# SQL Server
SQL_INFOCENTRAL_PWD=tu_password
SQL_DEADWH_PWD=tu_password

# Jira (opcional)
JIRA_USER=tu_email@deacero.com
JIRA_API_TOKEN=tu_token
```

## 🖥️ Uso

### Interfaz Web (Streamlit)

```bash
streamlit run app.py
```

Abre tu navegador en `http://localhost:8501`

![Streamlit UI](docs/streamlit-ui.png)

### Línea de Comandos (CLI)

```bash
# Proceso completo
python run_workflow.py --full

# Solo validar extracto
python run_workflow.py --validate

# Solo enviar correos
python run_workflow.py --send

# Enviar reporte específico
python run_workflow.py --send --reporte 5

# Modo prueba
python run_workflow.py --send --prueba
```

## 📁 Estructura del Proyecto

```
DEAC-79072/
├── .env                    # Configuración (no incluido en git)
├── .gitignore
├── requirements.txt
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── config.py           # Carga de configuración
│   ├── tableau_client.py   # Cliente Tableau Server
│   ├── sql_client.py       # Clientes SQL Server
│   ├── jira_client.py      # Cliente Jira
│   ├── notifier.py         # Envío de notificaciones
│   └── workflow.py         # Orquestador del flujo
│
├── app.py                  # Interfaz Streamlit
├── run_workflow.py         # CLI
│
└── logs/                   # Logs de ejecución
```

## 🔄 Flujo de Ejecución

```
1. Validar Extracto Tableau
   └── Si desactualizado → Intentar Refresh
       └── Si falla → Crear Ticket Jira + Notificar

2. Validar Datos SQL Server
   └── Si hay diferencias → Ejecutar Jobs Correctivos
       └── Si falla → Crear Ticket Jira + Notificar

3. Descargar PDFs de Tableau

4. Copiar a Carpeta Compartida (DEADWH)

5. Enviar Correos vía SP

6. Notificar Resultado
```

## 📊 Reportes Incluidos

| Reporte | Orientación | Frecuencia |
|---------|-------------|------------|
| Reporte Inventario Diario | Portrait | Diario |
| Reporte Compra Chatarra Prom Dia Habil | Landscape | Diario |
| Reporte de Compras e Inventario por Tipo de Material | Portrait | Diario |
| Reporte NUEVO Patios - Compras Nacionales + Importaciones | Portrait | Mar-Dom |
| Reporte Costo Puesto en Patios | Portrait | Mar-Dom |

## ⚙️ Configuración Avanzada

### Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `MAX_EXTRACT_AGE_HOURS` | Máxima antigüedad del extracto en horas | 24 |
| `MAX_REFRESH_RETRIES` | Intentos de refresh del extracto | 3 |
| `REFRESH_WAIT_SECONDS` | Espera entre intentos de refresh | 60 |

### Ejecución Programada (Task Scheduler)

Para configurar ejecución automática en Windows:

1. Abre "Task Scheduler"
2. Crear tarea básica
3. Configurar trigger (ej: diario a las 8:00 AM)
4. Acción: Iniciar programa
   - Programa: `python`
   - Argumentos: `run_workflow.py --full`
   - Iniciar en: `C:\ruta\al\proyecto`

## 🐛 Troubleshooting

### Error: "Acceso denegado a \\DEADWH\ReportesMateriasPrimas"

Tu usuario no tiene permisos de escritura en la carpeta compartida. Solicita acceso al administrador del servidor.

### Error: "Datasource no encontrado"

Verifica que el nombre del datasource en `.env` coincida exactamente con el nombre en Tableau Server.

### Error: "Jira API Token inválido"

1. Ve a https://id.atlassian.com/manage-profile/security/api-tokens
2. Crea un nuevo token
3. Actualiza `JIRA_API_TOKEN` en `.env`

## 📞 Soporte

- **Problemas con Tableau**: Contactar a Javier Osvaldo Aguila Cantu
- **Problemas con el sistema**: Crear ticket en proyecto DDF

## 📜 Changelog

### v1.0.0 (2024-12-22)
- Versión inicial
- Integración de scripts existentes
- Nueva interfaz Streamlit
- Integración con Jira

---

Desarrollado por el Equipo de Datos y Analítica - DEACERO

