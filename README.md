# 📊 Automatización de Reportes MP - DEACERO

Sistema unificado para la validación de extractos de Tableau y envío automático de reportes de Materias Primas.

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Flujo de Ejecución](#-flujo-de-ejecución)
- [Configuración de Correos](#-configuración-de-correos)
- [Troubleshooting](#-troubleshooting)
- [Soporte](#-soporte)

## 🎯 Descripción

Este sistema automatiza el proceso completo de validación y envío de reportes de Materias Primas:

1. **Valida** que los extractos de Tableau estén actualizados
2. **Verifica** la integridad de los datos en SQL Server
3. **Descarga** los reportes en formato PDF desde Tableau
4. **Distribuye** los PDFs a una carpeta compartida
5. **Envía** los reportes por correo electrónico a los destinatarios configurados
6. **Notifica** el resultado del proceso y crea tickets en Jira si hay errores

## 🚀 Características

- ✅ **Validación automática** de extractos de Tableau Server
- 🔄 **Refresh automático** de extractos desactualizados
- 📥 **Descarga automática** de reportes en PDF desde Tableau
- 📧 **Envío automático** de correos con reportes adjuntos
- 🎫 **Creación automática** de tickets en Jira cuando hay errores
- 🖥️ **Interfaz web** con Streamlit para ejecución manual
- ⌨️ **CLI** para ejecución programada (Task Scheduler)
- 📊 **Monitoreo** de estado de conexiones y configuración
- 🔔 **Notificaciones** por correo de éxito/error

## 📋 Requisitos Previos

### Software
- **Python 3.10 o superior**
- **Git** (para clonar el repositorio)

### Accesos y Permisos
- ✅ Acceso a **Tableau Server** con permisos para:
  - Ver y descargar reportes
  - Refrescar extractos
- ✅ Acceso a **SQL Server** (InfoCentral, DEADWH, SrvCubosOfi) con permisos para:
  - Ejecutar stored procedures
  - Ejecutar SQL Agent Jobs
  - Leer/escribir en carpetas compartidas
- ✅ (Opcional) Token de API de **Jira** para creación automática de tickets
- ✅ Acceso a **carpeta compartida** `\\DEADWH\ReportesMateriasPrimas\` (escritura)

### Red
- Acceso a la red corporativa de DEACERO
- Conectividad con los servidores SQL Server

## 🛠️ Instalación

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/daislasc/MP-Solucion.git
cd MP-Solucion
```

### Paso 2: Crear Entorno Virtual

**Windows:**
```bash
# Crear entorno virtual
py -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1
```

**⚠️ Si tienes problemas con la política de ejecución de PowerShell:**
1. Abre PowerShell como **Administrador**
2. Ejecuta: `Set-ExecutionPolicy Unrestricted`
3. Cierra y vuelve a abrir PowerShell
4. Intenta activar el entorno virtual nuevamente

**Linux/Mac:**
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate
```

**Verificación:** Deberías ver `(venv)` al inicio de tu prompt.

### Paso 3: Instalar Dependencias

```bash
# Asegúrate de que el entorno virtual esté activado
pip install --upgrade pip
pip install -r requirements.txt
```

**Tiempo estimado:** 2-5 minutos dependiendo de tu conexión.

### Paso 4: Configurar Variables de Entorno

```bash
# Windows
copy env.example.txt .env

# Linux/Mac
cp env.example.txt .env
```

Luego edita el archivo `.env` con tus credenciales reales.

## ⚙️ Configuración

### Archivo `.env`

El archivo `.env` contiene todas las configuraciones necesarias. **NUNCA** subas este archivo al repositorio.

#### Configuración Mínima Requerida

```env
# Tableau Server (REQUERIDO)
TABLEAU_SERVER=https://tableau.deacero.com/
TABLEAU_USER=tu_usuario_tableau
TABLEAU_PASSWORD=tu_password_tableau
TABLEAU_SITE=
TABLEAU_DATASOURCE_NAME=Datamart Materias Primas

# SQL Server - InfoCentral (REQUERIDO)
SQL_INFOCENTRAL_SERVER=INFOCENTRAL
SQL_INFOCENTRAL_USER=sa
SQL_INFOCENTRAL_PWD=tu_password_infocentral

# SQL Server - DEADWH (REQUERIDO)
SQL_DEADWH_SERVER=DEADWH
SQL_DEADWH_USER=sa
SQL_DEADWH_PWD=tu_password_deadwh

# SQL Server - Email (REQUERIDO para notificaciones)
SQL_EMAIL_SERVER=SRVMODMEM.gpodeacero.corp
SQL_EMAIL_USER=TYDUsr
SQL_EMAIL_PWD=tu_password_email
SQL_EMAIL_DATABASE=MEM
SQL_EMAIL_PROFILE=MEM_Profile

# Notificaciones (REQUERIDO)
ERROR_EMAIL_TO=tu_email@deacero.com
SUCCESS_EMAIL_TO=tu_email@deacero.com
```

#### Configuración Opcional

```env
# Jira (OPCIONAL - solo si quieres tickets automáticos)
JIRA_SERVER=https://deacero.atlassian.net
JIRA_USER=tu_email@deacero.com
JIRA_API_TOKEN=tu_token_jira
JIRA_PROJECT_KEY=DDF

# SQL Server - SrvCubosOfi (OPCIONAL)
SQL_CUBOSOFI_SERVER=SrvCubosOfi
SQL_CUBOSOFI_USER=artus
SQL_CUBOSOFI_PWD=tu_password_cubosofi

# Rutas (ajustar si es necesario)
PDF_SOURCE_PATH=C:/pythonPrograms/Reportes MP/Reportes/
PDF_DEST_PATH=//DEADWH/ReportesMateriasPrimas/

# Configuración de validación (opcional)
MAX_EXTRACT_AGE_HOURS=24
MAX_REFRESH_RETRIES=3
REFRESH_WAIT_SECONDS=60
```

### Verificar Configuración

Después de configurar el `.env`, puedes verificar que todo esté correcto:

```bash
# Ejecutar Streamlit y revisar el sidebar "Configuración"
streamlit run app.py
```

O ejecutar una validación rápida:

```bash
python run_workflow.py --validate
```

## 🖥️ Uso

### Interfaz Web (Streamlit) - Recomendado

La interfaz web es la forma más fácil de usar el sistema.

#### Iniciar la Aplicación

```bash
# 1. Activar entorno virtual (si no está activado)
.\venv\Scripts\Activate.ps1  # Windows
# o
source venv/bin/activate     # Linux/Mac

# 2. Ejecutar Streamlit
streamlit run app.py
```

#### Acceder a la Interfaz

Abre tu navegador en: **http://localhost:8501**

#### Funcionalidades en Streamlit

**Sidebar - Configuración:**
- Estado de la configuración (válida/incompleta)
- Estado de conexiones (Tableau, SQL Server, Jira)
- Destinatarios de correos configurados
- Información de reportes PDF

**Botones de Acción:**

1. **🔍 Validar Extracto**
   - Solo valida si el extracto de Tableau está actualizado
   - Si está desactualizado, intenta hacer refresh automático
   - No descarga ni envía reportes

2. **🚀 Proceso Completo**
   - Ejecuta todo el flujo: validación → descarga → envío
   - Incluye validación de extracto, datos SQL, descarga de PDFs, copia a carpeta compartida y envío de correos
   - Envía notificación de éxito/error al finalizar

3. **📧 Solo Enviar Correos**
   - Solo ejecuta el envío de correos (asume que los PDFs ya están listos)
   - Útil para reenviar reportes sin ejecutar todo el proceso
   - Envía notificación de éxito/error

4. **🗑️ Limpiar Logs**
   - Limpia los logs y resultados mostrados en pantalla

**Secciones Principales:**
- **Estado:** Muestra el resultado de la última ejecución
- **Pasos Ejecutados:** Detalle de cada paso con su duración
- **Logs:** Registro en tiempo real de la ejecución

### Línea de Comandos (CLI)

Ideal para ejecución programada o scripts automatizados.

#### Comandos Disponibles

```bash
# Proceso completo (recomendado para producción)
python run_workflow.py --full

# Solo validar extracto
python run_workflow.py --validate

# Solo enviar correos (asume PDFs ya listos)
python run_workflow.py --send

# Enviar reporte específico (por clave)
python run_workflow.py --send --reporte 5

# Modo prueba (envía a correos de prueba)
python run_workflow.py --send --prueba
```

#### Ejemplos de Uso

```bash
# Validar extracto antes de ejecutar proceso completo
python run_workflow.py --validate

# Si la validación es exitosa, ejecutar proceso completo
python run_workflow.py --full

# Reenviar solo el reporte de "Compras Nacionales + Importaciones" (clave 5)
python run_workflow.py --send --reporte 5

# Probar el envío a correos de prueba
python run_workflow.py --send --prueba
```

## 📁 Estructura del Proyecto

```
MP-Solucion/
├── .env                    # Configuración local (NO en git)
├── .gitignore             # Archivos ignorados por git
├── .streamlit/
│   └── config.toml        # Configuración de tema Streamlit
├── requirements.txt        # Dependencias Python
├── README.md              # Esta documentación
├── env.example.txt        # Template de configuración
├── queries_exploracion_reportes.sql  # Queries SQL útiles
│
├── src/                   # Código fuente
│   ├── __init__.py
│   ├── config.py          # Gestión de configuración y variables de entorno
│   ├── workflow.py         # Orquestador principal del flujo
│   ├── tableau_client.py  # Cliente para Tableau Server API
│   ├── sql_client.py      # Clientes para SQL Server (InfoCentral, DEADWH, etc.)
│   ├── jira_client.py     # Cliente para API de Jira
│   └── notifier.py        # Envío de notificaciones por correo
│
├── app.py                 # Interfaz web Streamlit
├── run_workflow.py        # CLI para ejecución programada
│
└── logs/                  # Logs de ejecución (generados automáticamente)
    └── workflow_YYYYMMDD.log
```

### Descripción de Módulos

- **`config.py`**: Carga y valida todas las variables de entorno desde `.env`
- **`workflow.py`**: Orquesta el flujo completo de automatización
- **`tableau_client.py`**: Maneja conexión, validación y descarga desde Tableau Server
- **`sql_client.py`**: Gestiona conexiones y ejecución de SPs en múltiples servidores SQL
- **`jira_client.py`**: Crea tickets automáticamente cuando hay errores
- **`notifier.py`**: Envía correos de notificación usando SQL Server Database Mail
- **`app.py`**: Interfaz web interactiva con Streamlit
- **`run_workflow.py`**: Punto de entrada para ejecución desde línea de comandos

## 🔄 Flujo de Ejecución

El sistema ejecuta los siguientes pasos en orden:

```
┌─────────────────────────────────────────────────────────┐
│ 1. Validar Extracto Tableau                            │
│    ├─ Verificar fecha de última actualización          │
│    ├─ Si desactualizado → Intentar Refresh             │
│    └─ Si falla → Crear Ticket Jira + Notificar        │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Validar Datos SQL Server (InfoCentral)              │
│    ├─ Verificar diferencias en inventario              │
│    ├─ Si hay diferencias → Ejecutar Jobs Correctivos   │
│    └─ Actualizar cubo de datos                         │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Descargar PDFs de Tableau                           │
│    └─ Descargar todos los reportes configurados        │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Copiar a Carpeta Compartida                         │
│    └─ Copiar PDFs a //DEADWH/ReportesMateriasPrimas/   │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Enviar Correos vía Stored Procedure                 │
│    └─ Ejecutar TiEnvioReportesTableauProc              │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Notificar Resultado                                  │
│    ├─ Enviar correo de éxito/error                      │
│    └─ Incluir resumen de pasos ejecutados              │
└─────────────────────────────────────────────────────────┘
```

## 📧 Configuración de Correos

### Tipos de Correos

El sistema envía dos tipos de correos:

#### 1. Notificaciones del Sistema
Se configuran en el archivo `.env`:

- **`ERROR_EMAIL_TO`**: Correos que reciben alertas cuando hay errores
- **`SUCCESS_EMAIL_TO`**: Correos que reciben notificaciones de éxito

**Ejemplo:**
```env
ERROR_EMAIL_TO=admin@deacero.com;soporte@deacero.com
SUCCESS_EMAIL_TO=admin@deacero.com
```

#### 2. Reportes PDF
Los destinatarios de los reportes PDF se configuran en SQL Server, en la tabla `TiTraEnvioReportesTableau` de la base de datos `TiMonitorSQL` (servidor DEADWH).

**Para ver/actualizar destinatarios:**
1. Conéctate a SQL Server Management Studio
2. Base de datos: `TiMonitorSQL`
3. Tabla: `dbo.TiTraEnvioReportesTableau`
4. Consulta los queries en `queries_exploracion_reportes.sql`

**Columnas relevantes:**
- `Para`: Destinatarios principales
- `CC`: Con copia
- `CCO`: Con copia oculta
- `CorreosPrueba`: Correos para modo prueba

### Cuándo se Envían las Notificaciones

| Acción | Notificación de Éxito | Notificación de Error |
|--------|----------------------|----------------------|
| Validar Extracto | ❌ No | ❌ No |
| Proceso Completo | ✅ Sí | ✅ Sí |
| Solo Enviar Correos | ✅ Sí | ✅ Sí |

## 📊 Reportes Incluidos

El sistema procesa los siguientes reportes:

| Reporte | Orientación | Frecuencia | Clave |
|---------|-------------|------------|-------|
| Reporte Inventario Diario | Portrait | Diario | - |
| Reporte Compra Chatarra Prom Dia Habil | Landscape | Diario | - |
| Reporte de Compras e Inventario por Tipo de Material | Portrait | Diario | - |
| Reporte NUEVO Patios - Compras Nacionales + Importaciones | Portrait | Mar-Dom | 5 |
| Reporte Costo Puesto en Patios | Portrait | Mar-Dom | - |

**Nota:** Los reportes se descargan según condiciones de fecha (día de la semana, inicio de semana, etc.)

## ⚙️ Configuración Avanzada

### Variables de Entorno Opcionales

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `MAX_EXTRACT_AGE_HOURS` | Máxima antigüedad del extracto en horas antes de considerarlo desactualizado | 24 |
| `MAX_REFRESH_RETRIES` | Número de intentos para refrescar el extracto si falla | 3 |
| `REFRESH_WAIT_SECONDS` | Segundos de espera entre intentos de refresh | 60 |

### Ejecución Programada (Task Scheduler - Windows)

Para automatizar la ejecución diaria:

1. Abre **"Task Scheduler"** (Programador de tareas)
2. Clic en **"Crear tarea básica"**
3. **Nombre:** "Automatización Reportes MP"
4. **Trigger:** Diario a las 8:00 AM (o la hora que prefieras)
5. **Acción:** Iniciar un programa
   - **Programa:** `C:\ruta\al\venv\Scripts\python.exe`
   - **Argumentos:** `run_workflow.py --full`
   - **Iniciar en:** `C:\ruta\al\MP-Solucion`
6. **Condiciones:** 
   - ✅ Iniciar la tarea solo si el equipo está conectado a la alimentación de CA
   - ✅ Despertar el equipo para ejecutar esta tarea
7. **Configuración:**
   - ✅ Permitir ejecutar la tarea a petición
   - ✅ Si la tarea en ejecución no finaliza cuando se solicita, forzar su detención

**Alternativa con script batch:**
```batch
@echo off
cd /d C:\ruta\al\MP-Solucion
call venv\Scripts\activate.bat
python run_workflow.py --full
```

## 🐛 Troubleshooting

### Error: "Configuración incompleta"

**Causa:** Faltan variables de entorno requeridas en el archivo `.env`.

**Solución:**
1. Verifica que el archivo `.env` existe en la raíz del proyecto
2. Compara con `env.example.txt` para asegurarte de que todas las variables están presentes
3. En Streamlit, haz clic en "🔄 Recargar Configuración"

### Error: "Acceso denegado a \\DEADWH\ReportesMateriasPrimas"

**Causa:** Tu usuario no tiene permisos de escritura en la carpeta compartida.

**Solución:**
1. Verifica que puedes acceder a la carpeta desde el Explorador de Windows
2. Solicita permisos de escritura al administrador del servidor DEADWH
3. Asegúrate de estar conectado a la red corporativa

### Error: "Datasource no encontrado"

**Causa:** El nombre del datasource en `.env` no coincide con el nombre en Tableau Server.

**Solución:**
1. Verifica el nombre exacto del datasource en Tableau Server
2. Actualiza `TABLEAU_DATASOURCE_NAME` en `.env`
3. El nombre es case-sensitive (distingue mayúsculas/minúsculas)

### Error: "Extracto desactualizado"

**Causa:** El extracto no se ha actualizado en las últimas 24 horas (o el tiempo configurado).

**Solución:**
1. El sistema intentará hacer refresh automáticamente
2. Si falla, verifica permisos en Tableau Server
3. Revisa los logs para más detalles
4. Puedes hacer refresh manual desde Tableau Server

### Error: "Jira API Token inválido"

**Causa:** El token de Jira es incorrecto o ha expirado.

**Solución:**
1. Ve a https://id.atlassian.com/manage-profile/security/api-tokens
2. Crea un nuevo token
3. Copia el token (solo se muestra una vez)
4. Actualiza `JIRA_API_TOKEN` en `.env`

### Error: "No se puede conectar a SQL Server"

**Causa:** Problemas de red, credenciales incorrectas o servidor inaccesible.

**Solución:**
1. Verifica que estás en la red corporativa
2. Prueba conectarte con SQL Server Management Studio
3. Verifica las credenciales en `.env`
4. Verifica que el servidor está accesible (ping)

### Error: "Streamlit no se reconoce como comando"

**Causa:** El entorno virtual no está activado o Streamlit no está instalado.

**Solución:**
```bash
# Activar entorno virtual
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Verificar instalación
pip list | findstr streamlit  # Windows
pip list | grep streamlit     # Linux/Mac

# Si no está instalado
pip install -r requirements.txt
```

### Los correos no llegan

**Verificación:**
1. Revisa `ERROR_EMAIL_TO` y `SUCCESS_EMAIL_TO` en `.env`
2. Verifica que el SP `TiEnvioReportesTableauProc` se ejecutó correctamente
3. Revisa los logs en `logs/workflow_YYYYMMDD.log`
4. Verifica la configuración de Database Mail en SQL Server

