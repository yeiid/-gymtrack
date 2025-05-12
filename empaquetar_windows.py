#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import os
import sys
import shutil
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

# Asegurarse de que el directorio de trabajo sea el directorio del script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def print_color(text, color=Fore.WHITE):
    """Imprimir texto con color"""
    print(f"{color}{text}{Style.RESET_ALL}")

def limpiar_archivos_temporales():
    """Eliminar archivos temporales antes de empaquetar"""
    print_color("[INFO] Limpiando archivos temporales...", Fore.BLUE)
    
    # Extensiones de archivos a eliminar
    extensions = ['.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.spec']
    
    # Directorios a eliminar
    directories = ['build/', 'dist/', '__pycache__/']
    
    # Contar archivos eliminados
    count = 0
    
    # Eliminar directorios
    for directory in directories:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print_color(f"[INFO] Eliminado directorio de construcción anterior: {directory}", Fore.BLUE)
                count += 1
            except Exception as e:
                print_color(f"[ERROR] No se pudo eliminar {directory}: {str(e)}", Fore.RED)
    
    # Eliminar archivos .spec
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            try:
                os.remove(file)
                print_color(f"[INFO] Eliminado archivo: {file}", Fore.BLUE)
                count += 1
            except Exception as e:
                print_color(f"[ERROR] No se pudo eliminar {file}: {str(e)}", Fore.RED)
    
    # Recorrer recursivamente todos los directorios y eliminar archivos con extensiones específicas
    for root, dirs, files in os.walk('.'):
        for file in files:
            for ext in extensions:
                if file.endswith(ext):
                    try:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                        print_color(f"[INFO] Eliminado archivo {file_path}", Fore.BLUE)
                        count += 1
                    except Exception as e:
                        print_color(f"[ERROR] No se pudo eliminar {file_path}: {str(e)}", Fore.RED)
                    break
        
        # También eliminar directorios __pycache__ encontrados durante la búsqueda
        for dir_name in dirs[:]:  # Usamos una copia para poder modificar la lista original
            if dir_name == '__pycache__':
                try:
                    dir_path = os.path.join(root, dir_name)
                    shutil.rmtree(dir_path)
                    print_color(f"[INFO] Eliminado directorio {dir_path}", Fore.BLUE)
                    count += 1
                    dirs.remove(dir_name)  # Evitamos que os.walk entre en este directorio
                except Exception as e:
                    print_color(f"[ERROR] No se pudo eliminar {dir_path}: {str(e)}", Fore.RED)
                    
    return count

def empaquetar_para_windows():
    """Empaquetar la aplicación específicamente para Windows desde Linux"""
    print_color("[INFO] Iniciando empaquetado para Windows...", Fore.BLUE)
    
    # Limpiar archivos temporales antes de empaquetar
    limpiar_archivos_temporales()
    
    # Crear archivo .spec personalizado para Windows
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('INSTRUCCIONES_ANTIVIRUS.md', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_sqlalchemy',
        'sqlite3',
        'webbrowser',
        'sqlalchemy.sql.default_comparator',
        'jinja2.ext',
        'routes',
        'services'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GimnasioDB_windows',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=['vcruntime140.dll', 'python*.dll', 'VCRUNTIME140.dll', 'msvcp140.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/img/favicon.ico',
)
"""
    
    # Escribir el archivo .spec
    with open('GimnasioDB_windows.spec', 'w') as f:
        f.write(spec_content)
    
    print_color("[INFO] Archivo .spec para Windows creado", Fore.GREEN)
    
    # Ejecutar PyInstaller con el archivo .spec
    pyinstaller_cmd = [
        'pyinstaller',
        '--noconfirm',
        '--clean',
        'GimnasioDB_windows.spec'
    ]
    
    print_color("[INFO] Ejecutando PyInstaller para Windows...", Fore.BLUE)
    print_color(f"[INFO] Comando: {' '.join(pyinstaller_cmd)}", Fore.BLUE)
    
    try:
        result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)
        
        # Mostrar salida
        print(result.stdout)
        
        if result.returncode != 0:
            print_color("[ERROR] Error al empaquetar para Windows", Fore.RED)
            print_color(result.stderr, Fore.RED)
            return False
        else:
            print_color("[ÉXITO] ¡Compilación completada correctamente!", Fore.GREEN)
            print_color(f"[INFO] El ejecutable se encuentra en: {os.path.abspath('dist/GimnasioDB_windows.exe')}", Fore.GREEN)
            return True
            
    except Exception as e:
        print_color(f"[ERROR] Error al ejecutar PyInstaller: {str(e)}", Fore.RED)
        return False

if __name__ == "__main__":
    print_color("============================================================", Fore.YELLOW)
    print_color("            EMPAQUETADOR PARA WINDOWS DESDE LINUX           ", Fore.YELLOW)
    print_color("============================================================", Fore.YELLOW)
    
    success = empaquetar_para_windows()
    
    print_color("============================================================", Fore.YELLOW)
    print_color("                 RESUMEN DE EMPAQUETADO                     ", Fore.YELLOW)
    print_color("============================================================", Fore.YELLOW)
    
    if success:
        print_color("Se creó 1 ejecutable correctamente.", Fore.GREEN)
        print_color("¡Proceso de empaquetado completado con éxito!", Fore.GREEN)
        print_color("El ejecutable se encuentra en la carpeta 'dist/'", Fore.GREEN)
    else:
        print_color("Fallaron 1 creaciones de ejecutables.", Fore.RED)
        print_color("El proceso de empaquetado falló. Revise los mensajes de error anteriores.", Fore.RED)
    
    sys.exit(0 if success else 1) 