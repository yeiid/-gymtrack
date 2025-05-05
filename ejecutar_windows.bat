@echo off
echo ======================================
echo  INICIANDO GIMNASIO DB - NEURALJIRA_DEV
echo ======================================
echo.
echo Verificando si Python esta instalado...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado o no esta en el PATH.
    echo Por favor, instale Python 3.7 o superior desde:
    echo https://www.python.org/downloads/
    echo.
    echo Presione cualquier tecla para salir...
    pause >nul
    exit /b 1
)

echo Verificando entorno virtual...
if not exist venv (
    echo Creando entorno virtual...
    python -m venv venv
    echo Instalando dependencias...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    echo Entorno virtual ya existe.
    call venv\Scripts\activate.bat
)

echo Iniciando la aplicacion...
python app_launcher.py

echo Presione cualquier tecla para salir...
pause >nul
exit /b 0
