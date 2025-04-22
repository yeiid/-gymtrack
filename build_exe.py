#!/usr/bin/env python
import os
import shutil
import subprocess
import platform
import sys

def build_executable():
    """
    Construye el ejecutable usando PyInstaller
    """
    print("Construyendo el ejecutable de GimnasioDB...")
    
    # Limpiar directorios de construcción anteriores
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Compilar el ejecutable
    try:
        subprocess.check_call(["pyinstaller", "GimnasioDB.spec"])
        print("\n¡Compilación exitosa!\n")
        
        # Determinar el ejecutable creado
        if platform.system() == "Windows":
            exe_path = os.path.join("dist", "GimnasioDB", "GimnasioDB.exe")
        else:
            exe_path = os.path.join("dist", "GimnasioDB")
        
        # Verificar si el ejecutable existe
        if os.path.exists(exe_path):
            print(f"Ejecutable creado en: {os.path.abspath(exe_path)}")
            print("\nPara usar el sistema:")
            print(f"1. Ejecute {os.path.basename(exe_path)}")
            print("2. Se abrirá automáticamente un navegador con la aplicación")
            print("3. Si el navegador no se abre, ingrese a http://127.0.0.1:5000 en su navegador")
        else:
            print(f"Error: No se encontró el ejecutable en {exe_path}")
            return False
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al compilar: {e}")
        return False

if __name__ == "__main__":
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("run_app.py"):
        print("Error: Este script debe ejecutarse desde el directorio principal del proyecto")
        sys.exit(1)
    
    # Verificar que PyInstaller está instalado
    try:
        subprocess.check_call(["pyinstaller", "--version"], stdout=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: PyInstaller no está instalado. Instálelo con 'pip install pyinstaller'")
        sys.exit(1)
    
    # Construir el ejecutable
    success = build_executable()
    
    if success:
        print("\nEl proceso de construcción ha finalizado correctamente.")
    else:
        print("\nEl proceso de construcción ha fallado. Revise los errores.")
        sys.exit(1) 