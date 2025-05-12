#!/usr/bin/env python3
import os
import shutil
import sys
from colorama import init, Fore, Style

# Inicializar colorama
init()

def print_color(message, color=Fore.WHITE, style=Style.NORMAL):
    """Imprime un mensaje con color"""
    print(f"{style}{color}{message}{Style.RESET_ALL}")

def limpiar_proyecto():
    """Limpia archivos temporales y de compilación del proyecto"""
    print_color("Iniciando limpieza del proyecto...", Fore.CYAN, Style.BRIGHT)
    
    # Directorios a eliminar
    directorios = [
        'build',
        'dist',
        '__pycache__'
    ]
    
    # Archivos a eliminar
    archivos = [
        # Archivos temporales de PyInstaller
        'GimnasioDB.spec',
        'GimnasioDB_linux.spec',
        'GimnasioDB_macos.spec',
        'GimnasioDB_windows.spec',
        'app_launcher.spec',
        'file_version_info.txt',
        # Archivos temporales diversos
        'cookie_jar.txt',
        'test_var.py'
    ]
    
    # Extensiones de archivos a eliminar
    extensiones = [
        '.pyc',
        '.pyo',
        '.pyd',
        '.so',
        '.dll',
        '.exe',
        '.spec'
    ]
    
    # 1. Eliminar directorios principales
    for directorio in directorios:
        if os.path.exists(directorio):
            try:
                print_color(f"Eliminando directorio: {directorio}", Fore.YELLOW)
                shutil.rmtree(directorio)
                print_color(f"✓ Directorio {directorio} eliminado", Fore.GREEN)
            except Exception as e:
                print_color(f"✗ Error al eliminar {directorio}: {str(e)}", Fore.RED)
    
    # 2. Eliminar archivos específicos
    for archivo in archivos:
        if os.path.exists(archivo):
            try:
                print_color(f"Eliminando archivo: {archivo}", Fore.YELLOW)
                os.remove(archivo)
                print_color(f"✓ Archivo {archivo} eliminado", Fore.GREEN)
            except Exception as e:
                print_color(f"✗ Error al eliminar {archivo}: {str(e)}", Fore.RED)
    
    # 3. Buscar y eliminar directorios __pycache__ recursivamente
    pycache_count = 0
    for root, dirs, files in os.walk('.'):
        # Ignorar directorio venv
        if 'venv' in root.split(os.sep):
            continue
            
        for dir_name in dirs:
            if dir_name == '__pycache__':
                try:
                    dir_path = os.path.join(root, dir_name)
                    print_color(f"Eliminando directorio: {dir_path}", Fore.YELLOW)
                    shutil.rmtree(dir_path)
                    pycache_count += 1
                    print_color(f"✓ Directorio {dir_path} eliminado", Fore.GREEN)
                except Exception as e:
                    print_color(f"✗ Error al eliminar {dir_path}: {str(e)}", Fore.RED)
    
    # 4. Buscar y eliminar archivos por extensión
    extension_count = 0
    for root, dirs, files in os.walk('.'):
        # Ignorar directorio venv
        if 'venv' in root.split(os.sep):
            continue
            
        for file in files:
            if any(file.endswith(ext) for ext in extensiones):
                try:
                    file_path = os.path.join(root, file)
                    print_color(f"Eliminando archivo: {file_path}", Fore.YELLOW)
                    os.remove(file_path)
                    extension_count += 1
                    print_color(f"✓ Archivo {file_path} eliminado", Fore.GREEN)
                except Exception as e:
                    print_color(f"✗ Error al eliminar {file_path}: {str(e)}", Fore.RED)
    
    # Resumen
    print_color("\nResumen de limpieza:", Fore.CYAN, Style.BRIGHT)
    print_color(f"- Directorios __pycache__ eliminados: {pycache_count}", Fore.WHITE)
    print_color(f"- Archivos temporales por extensión eliminados: {extension_count}", Fore.WHITE)
    print_color(f"- Archivos específicos eliminados: {sum(1 for a in archivos if not os.path.exists(a))}", Fore.WHITE)
    print_color(f"- Directorios principales eliminados: {sum(1 for d in directorios if not os.path.exists(d))}", Fore.WHITE)
    print_color("\n¡Limpieza completada!", Fore.GREEN, Style.BRIGHT)

if __name__ == "__main__":
    # Verificar argumentos
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_color("Uso: python limpiar_proyecto.py", Fore.CYAN)
        print_color("Este script elimina archivos temporales y de compilación del proyecto.", Fore.WHITE)
        sys.exit(0)
    
    # Confirmar antes de proceder
    respuesta = input("¿Estás seguro de que deseas eliminar todos los archivos temporales? (s/n): ")
    if respuesta.lower() != 's':
        print_color("Operación cancelada.", Fore.YELLOW)
        sys.exit(0)
    
    limpiar_proyecto() 