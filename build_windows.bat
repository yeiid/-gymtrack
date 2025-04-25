@echo off
echo ===== CREACION DE EJECUTABLE PARA WINDOWS =====
echo.

REM Verificar si Python está instalado
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor, instale Python desde https://www.python.org/downloads/
    echo Asegúrese de marcar la opción "Add Python to PATH" durante la instalación
    pause
    exit /b 1
)

echo Python encontrado, verificando versión...
python --version

REM Verificar si PyInstaller está instalado
python -c "import PyInstaller" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Instalando PyInstaller...
    pip install pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo ERROR: No se pudo instalar PyInstaller
        pause
        exit /b 1
    )
)

REM Instalar dependencias
echo.
echo Instalando dependencias...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

REM Compilar el ejecutable
echo.
echo Compilando ejecutable...
pyinstaller --noconfirm --clean ^
            --name=GimnasioDB ^
            --icon=static/img/favicon.ico ^
            --add-data=templates;templates ^
            --add-data=static;static ^
            --hidden-import=flask ^
            --hidden-import=flask_sqlalchemy ^
            --hidden-import=sqlalchemy ^
            --onedir ^
            --windowed ^
            run_app.py

if %ERRORLEVEL% neq 0 (
    echo ERROR: La compilación falló
    pause
    exit /b 1
)

echo.
echo ¡Compilación exitosa!
echo.
echo El ejecutable ha sido creado en: %CD%\dist\GimnasioDB\GimnasioDB.exe
echo.
echo Para usar el sistema:
echo 1. Navegue a la carpeta 'dist\GimnasioDB'
echo 2. Ejecute GimnasioDB.exe
echo 3. Se abrirá automáticamente un navegador con la aplicación
echo 4. Si el navegador no se abre, ingrese a http://127.0.0.1:5000 en su navegador
echo.

REM Preguntar si desea ejecutar la aplicación
set /p ejecutar=¿Desea ejecutar la aplicación ahora? (s/n): 
if /i "%ejecutar%"=="s" (
    echo Ejecutando aplicación...
    start dist\GimnasioDB\GimnasioDB.exe
)

pause 