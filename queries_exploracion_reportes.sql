-- ============================================
-- QUERIES PARA EXPLORAR TiTraEnvioReportesTableau
-- Base de datos: TiMonitorSQL (DEADWH)
-- ============================================

-- 1. Ver estructura de la tabla
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo' 
  AND TABLE_NAME = 'TiTraEnvioReportesTableau'
ORDER BY ORDINAL_POSITION;

-- 2. Ver todos los reportes configurados
SELECT *
FROM dbo.TiTraEnvioReportesTableau
ORDER BY ClaveReporte;

-- 3. Ver reportes activos (si hay columna de estado)
SELECT *
FROM dbo.TiTraEnvioReportesTableau
WHERE Activo = 1  -- Ajustar según la columna real
ORDER BY ClaveReporte;

-- 4. Ver destinatarios de cada reporte
SELECT 
    ClaveReporte,
    NombreReporte,  -- Ajustar según columnas reales
    Para,
    CC,
    CCO,
    CorreosPrueba
FROM dbo.TiTraEnvioReportesTableau
ORDER BY ClaveReporte;

-- 5. Contar reportes por tipo de envío
SELECT 
    COUNT(*) as TotalReportes,
    COUNT(CASE WHEN Para IS NOT NULL AND Para != '' THEN 1 END) as ConDestinatarios,
    COUNT(CASE WHEN CorreosPrueba IS NOT NULL AND CorreosPrueba != '' THEN 1 END) as ConPrueba
FROM dbo.TiTraEnvioReportesTableau;

-- 6. Ver reportes con destinatarios específicos (buscar un correo)
SELECT 
    ClaveReporte,
    NombreReporte,
    Para,
    CC,
    CCO,
    CorreosPrueba
FROM dbo.TiTraEnvioReportesTableau
WHERE Para LIKE '%@deacero.com%'
   OR CC LIKE '%@deacero.com%'
   OR CCO LIKE '%@deacero.com%'
   OR CorreosPrueba LIKE '%@deacero.com%'
ORDER BY ClaveReporte;

-- 7. Ver reportes sin destinatarios configurados
SELECT 
    ClaveReporte,
    NombreReporte,
    Para,
    CC,
    CCO
FROM dbo.TiTraEnvioReportesTableau
WHERE (Para IS NULL OR Para = '')
  AND (CC IS NULL OR CC = '')
  AND (CCO IS NULL OR CCO = '')
ORDER BY ClaveReporte;

-- 8. Ver configuración detallada de un reporte específico (ejemplo: ClaveReporte = 5)
SELECT *
FROM dbo.TiTraEnvioReportesTableau
WHERE ClaveReporte = 5;

-- 9. Ver todos los correos únicos que reciben reportes
SELECT DISTINCT
    Para as Correo,
    'Para' as Tipo
FROM dbo.TiTraEnvioReportesTableau
WHERE Para IS NOT NULL AND Para != ''
UNION ALL
SELECT DISTINCT
    CC as Correo,
    'CC' as Tipo
FROM dbo.TiTraEnvioReportesTableau
WHERE CC IS NOT NULL AND CC != ''
UNION ALL
SELECT DISTINCT
    CCO as Correo,
    'CCO' as Tipo
FROM dbo.TiTraEnvioReportesTableau
WHERE CCO IS NOT NULL AND CCO != ''
UNION ALL
SELECT DISTINCT
    CorreosPrueba as Correo,
    'Prueba' as Tipo
FROM dbo.TiTraEnvioReportesTableau
WHERE CorreosPrueba IS NOT NULL AND CorreosPrueba != ''
ORDER BY Correo;

-- 10. Ver reportes con múltiples destinatarios (separados por ; o ,)
SELECT 
    ClaveReporte,
    NombreReporte,
    Para,
    LEN(Para) - LEN(REPLACE(Para, ';', '')) + 1 as NumDestinatariosPara,
    CC,
    LEN(CC) - LEN(REPLACE(CC, ';', '')) + 1 as NumDestinatariosCC
FROM dbo.TiTraEnvioReportesTableau
WHERE Para IS NOT NULL AND Para != ''
ORDER BY NumDestinatariosPara DESC;

-- 11. Verificar formato de correos (validación básica)
SELECT 
    ClaveReporte,
    NombreReporte,
    Para,
    CASE 
        WHEN Para LIKE '%@%.%' THEN 'Formato válido'
        ELSE 'Formato inválido'
    END as ValidacionPara
FROM dbo.TiTraEnvioReportesTableau
WHERE Para IS NOT NULL AND Para != '';

-- 12. Resumen de configuración de reportes
SELECT 
    ClaveReporte,
    NombreReporte,
    CASE 
        WHEN Para IS NOT NULL AND Para != '' THEN 'Sí' 
        ELSE 'No' 
    END as TieneDestinatarios,
    CASE 
        WHEN CC IS NOT NULL AND CC != '' THEN 'Sí' 
        ELSE 'No' 
    END as TieneCC,
    CASE 
        WHEN CCO IS NOT NULL AND CCO != '' THEN 'Sí' 
        ELSE 'No' 
    END as TieneCCO,
    CASE 
        WHEN CorreosPrueba IS NOT NULL AND CorreosPrueba != '' THEN 'Sí' 
        ELSE 'No' 
    END as TienePrueba
FROM dbo.TiTraEnvioReportesTableau
ORDER BY ClaveReporte;

-- 13. Ver reportes que se envían en modo oficial (ClaveReporte = 0 = todos)
-- Este query muestra todos los reportes que se enviarían con EXEC dbo.TiEnvioReportesTableauProc 0,0
SELECT 
    ClaveReporte,
    NombreReporte,
    Para,
    CC,
    CCO,
    Frecuencia,  -- Si existe esta columna
    Activo       -- Si existe esta columna
FROM dbo.TiTraEnvioReportesTableau
WHERE Activo = 1  -- Ajustar según lógica real
ORDER BY ClaveReporte;

-- 14. Ver reportes de prueba (si hay columna que los identifique)
SELECT 
    ClaveReporte,
    NombreReporte,
    CorreosPrueba,
    Para as DestinatariosOficiales
FROM dbo.TiTraEnvioReportesTableau
WHERE CorreosPrueba IS NOT NULL AND CorreosPrueba != ''
ORDER BY ClaveReporte;

-- 15. Query para actualizar destinatarios (EJEMPLO - NO EJECUTAR SIN VERIFICAR)
/*
UPDATE dbo.TiTraEnvioReportesTableau
SET Para = 'nuevo_correo@deacero.com'
WHERE ClaveReporte = 5;

-- O agregar a lista existente (si están separados por ;)
UPDATE dbo.TiTraEnvioReportesTableau
SET Para = Para + ';nuevo_correo@deacero.com'
WHERE ClaveReporte = 5
  AND Para NOT LIKE '%nuevo_correo@deacero.com%';
*/

-- ============================================
-- QUERIES PARA AGREGAR CORREO DE PRUEBA
-- ============================================

-- 16. VERIFICAR ANTES: Ver estado actual de CorreosPrueba
SELECT 
    ClaveReporte,
    NombreReporte,
    CorreosPrueba,
    CASE 
        WHEN CorreosPrueba IS NULL OR CorreosPrueba = '' THEN 'Vacío'
        WHEN CorreosPrueba LIKE '%daislas@deacero.com%' THEN 'Ya incluido'
        ELSE 'Tiene otros correos'
    END as Estado
FROM dbo.TiTraEnvioReportesTableau
ORDER BY ClaveReporte;

-- 17. Agregar tu correo a CorreosPrueba de TODOS los reportes
-- Opción A: Si CorreosPrueba está vacío o es NULL, establecer solo tu correo
UPDATE dbo.TiTraEnvioReportesTableau
SET CorreosPrueba = 'daislas@deacero.com'
WHERE (CorreosPrueba IS NULL OR CorreosPrueba = '')
  AND CorreosPrueba NOT LIKE '%daislas@deacero.com%';

-- Opción B: Si CorreosPrueba ya tiene valores, agregar tu correo al final
UPDATE dbo.TiTraEnvioReportesTableau
SET CorreosPrueba = CorreosPrueba + ';daislas@deacero.com'
WHERE CorreosPrueba IS NOT NULL 
  AND CorreosPrueba != ''
  AND CorreosPrueba NOT LIKE '%daislas@deacero.com%';

-- 18. QUERY COMBINADA (RECOMENDADA): Agregar tu correo a todos los reportes
-- Esta query maneja ambos casos (vacío y con valores existentes)
UPDATE dbo.TiTraEnvioReportesTableau
SET CorreosPrueba = CASE 
    WHEN CorreosPrueba IS NULL OR CorreosPrueba = '' THEN 'daislas@deacero.com'
    WHEN CorreosPrueba NOT LIKE '%daislas@deacero.com%' THEN CorreosPrueba + ';daislas@deacero.com'
    ELSE CorreosPrueba  -- Ya está incluido, no hacer nada
END
WHERE CorreosPrueba NOT LIKE '%daislas@deacero.com%' 
   OR CorreosPrueba IS NULL 
   OR CorreosPrueba = '';

-- 19. VERIFICAR DESPUÉS: Confirmar que se agregó correctamente
SELECT 
    ClaveReporte,
    NombreReporte,
    CorreosPrueba,
    CASE 
        WHEN CorreosPrueba LIKE '%daislas@deacero.com%' THEN '✅ Incluido'
        ELSE '❌ No incluido'
    END as Verificacion
FROM dbo.TiTraEnvioReportesTableau
ORDER BY ClaveReporte;

-- 20. REMOVER tu correo de CorreosPrueba (si necesitas revertir)
/*
UPDATE dbo.TiTraEnvioReportesTableau
SET CorreosPrueba = CASE
    WHEN CorreosPrueba = 'daislas@deacero.com' THEN NULL
    WHEN CorreosPrueba LIKE 'daislas@deacero.com;%' THEN REPLACE(CorreosPrueba, 'daislas@deacero.com;', '')
    WHEN CorreosPrueba LIKE '%;daislas@deacero.com' THEN REPLACE(CorreosPrueba, ';daislas@deacero.com', '')
    WHEN CorreosPrueba LIKE '%;daislas@deacero.com;%' THEN REPLACE(CorreosPrueba, ';daislas@deacero.com;', ';')
    ELSE CorreosPrueba
END
WHERE CorreosPrueba LIKE '%daislas@deacero.com%';
*/

