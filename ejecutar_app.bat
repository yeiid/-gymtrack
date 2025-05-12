@echo off
REM Script para ejecutar la aplicación GimnasioDB
REM Este archivo es parte del sistema GimnasioDB

title GimnasioDB - Iniciando...

echo ==============================================
echo        INICIANDO GIMNASIO DB
echo ==============================================
echo.

REM Ejecutar la aplicación con parámetros optimizados
python app_launcher.py --mode=production

echo.
echo La aplicación ha finalizado.
echo.
pause 