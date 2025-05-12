@echo off
echo =======================================================
echo GENERADOR DE EJECUTABLES MULTISISTEMA - GIMNASIO DB
echo =======================================================
echo.
echo Este script generara ejecutables para diferentes sistemas operativos.
echo.
echo Opciones:
echo 1. Generar ejecutable para Windows
echo 2. Generar ejecutable para Linux
echo 3. Generar ejecutable para macOS
echo 4. Generar ejecutables para todos los sistemas
echo 5. Incluir base de datos en los ejecutables
echo 6. Salir
echo.

set incluir_db=

:menu
set /p opcion="Seleccione una opcion (1-6): "

if "%opcion%"=="1" (
    echo.
    echo Generando ejecutable para Windows...
    python empaquetar_app.py --windows %incluir_db%
    goto fin
)

if "%opcion%"=="2" (
    echo.
    echo Generando ejecutable para Linux...
    python empaquetar_app.py --linux %incluir_db%
    goto fin
)

if "%opcion%"=="3" (
    echo.
    echo Generando ejecutable para macOS...
    python empaquetar_app.py --macos %incluir_db%
    goto fin
)

if "%opcion%"=="4" (
    echo.
    echo Generando ejecutables para todos los sistemas...
    python empaquetar_app.py --all %incluir_db%
    goto fin
)

if "%opcion%"=="5" (
    set incluir_db=--include-db
    echo.
    echo Se incluira la base de datos en los ejecutables.
    goto menu
)

if "%opcion%"=="6" (
    echo.
    echo Saliendo...
    goto salir
)

echo.
echo Opcion invalida. Por favor, seleccione una opcion valida.
goto menu

:fin
echo.
echo ===============================================
echo Proceso de generacion de ejecutables completado
echo ===============================================
echo.
echo Los ejecutables se encuentran en la carpeta 'dist/'
echo.
pause

:salir 