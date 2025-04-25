@echo off
echo ===== EMPAQUETANDO APLICACION GIMNASIO DB =====
echo.

REM Verificar si existe la carpeta dist
if not exist "dist\GimnasioDB" (
    echo ERROR: No se ha encontrado la carpeta dist\GimnasioDB
    echo Primero debe ejecutar build_windows.bat para compilar la aplicación
    pause
    exit /b 1
)

echo Verificando requisitos...

REM Verificar si PowerShell está disponible
where powershell >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: PowerShell no está disponible en este sistema
    pause
    exit /b 1
)

echo Creando archivo ZIP...

REM Obtener la fecha actual en formato YYYYMMDD
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set datetime=%%a
set fecha=%datetime:~0,8%

set nombre_zip=GimnasioDB_%fecha%.zip

REM Crear archivo ZIP usando PowerShell
powershell -command "Compress-Archive -Path 'dist\GimnasioDB' -DestinationPath '%nombre_zip%' -Force"

if %ERRORLEVEL% neq 0 (
    echo ERROR: No se pudo crear el archivo ZIP
    pause
    exit /b 1
)

echo.
echo ¡Empaquetado exitoso!
echo El archivo %nombre_zip% ha sido creado en la carpeta actual.
echo.
echo Este archivo contiene la aplicación lista para ser distribuida.
echo Para usar la aplicación, descomprima el archivo y ejecute GimnasioDB.exe
echo.

pause 