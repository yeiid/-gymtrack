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
    
    # Asegurarse de que exista un icono para la aplicación
    if not os.path.exists("static/img/favicon.ico"):
        print("Aviso: No se encontró un icono en static/img/favicon.ico")
    
    # Compilar el ejecutable
    try:
        # Construir el ejecutable
        subprocess.check_call(["pyinstaller", "GimnasioDB.spec"])
        print("\n¡Compilación exitosa!\n")
        
        # Determinar el ejecutable creado - PyInstaller puede crear el ejecutable directamente en dist/
        if platform.system() == "Windows":
            possible_paths = [
                os.path.join("dist", "GimnasioDB", "GimnasioDB.exe"),  # Estructura de carpetas
                os.path.join("dist", "GimnasioDB.exe")                 # Directamente en dist/
            ]
            
            exe_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    exe_path = path
                    break
        else:
            possible_paths = [
                os.path.join("dist", "GimnasioDB", "GimnasioDB"),
                os.path.join("dist", "GimnasioDB")
            ]
            
            exe_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    exe_path = path
                    break
        
        # Verificar si el ejecutable existe
        if exe_path and os.path.exists(exe_path):
            print(f"Ejecutable creado en: {os.path.abspath(exe_path)}")
            
            # Crear un acceso directo en Windows
            if platform.system() == "Windows":
                try:
                    create_windows_shortcut(exe_path)
                except Exception as e:
                    print(f"No se pudo crear acceso directo: {e}")
            
            print("\nPara usar el sistema:")
            print(f"1. Ejecute {os.path.basename(exe_path)}")
            print("2. Se abrirá automáticamente un navegador con la aplicación")
            print("3. Si el navegador no se abre, ingrese a http://127.0.0.1:5000 en su navegador")
            
            return True
        else:
            print(f"Error: No se encontró el ejecutable. Rutas probadas:")
            for path in possible_paths:
                print(f"- {path}")
            return False
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al compilar: {e}")
        return False

def create_windows_shortcut(target_path):
    """
    Crea un acceso directo en Windows para el ejecutable
    """
    if platform.system() != "Windows":
        return
    
    try:
        import win32com.client
        
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop, "GimnasioDB.lnk")
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = os.path.abspath(target_path)
        shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(target_path))
        shortcut.Description = "Sistema de Gestión para Gimnasio"
        if os.path.exists("static/img/favicon.ico"):
            shortcut.IconLocation = os.path.abspath("static/img/favicon.ico")
        shortcut.save()
        
        print(f"Acceso directo creado en: {shortcut_path}")
    except ImportError:
        print("Nota: Para crear accesos directos, instale pywin32 con 'pip install pywin32'")
    except Exception as e:
        print(f"Error al crear acceso directo: {e}")

if __name__ == "__main__":
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("app_launcher.py"):
        print("Error: Este script debe ejecutarse desde el directorio principal del proyecto")
        sys.exit(1)
    
    # Verificar que PyInstaller está instalado
    try:
        subprocess.check_call(["pyinstaller", "--version"], stdout=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: PyInstaller no está instalado. Instálelo con 'pip install pyinstaller'")
        sys.exit(1)
    
    # Para Windows, verificar si pywin32 está instalado
    if platform.system() == "Windows":
        try:
            import win32com.client
        except ImportError:
            print("Aviso: pywin32 no está instalado. No se creará acceso directo.")
            print("Para instalar: pip install pywin32")
    
    # Construir el ejecutable
    success = build_executable()
    
    if success:
        print("\nEl proceso de construcción ha finalizado correctamente.")
    else:
        print("\nEl proceso de construcción ha fallado. Revise los errores.")
        sys.exit(1) 

        