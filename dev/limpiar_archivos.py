#!/usr/bin/env python
"""
Script para limpiar archivos innecesarios o duplicados y moverlos a la carpeta dev
Esto evita que estos archivos se incluyan en la construcción del ejecutable para Windows

Desarrollado por: NEURALJIRA_DEV
"""

import os
import shutil
import sys
import datetime
import re

# Lista de archivos a mover a la carpeta dev
ARCHIVOS_A_MOVER = [
    'app.py',               # Duplica app_launcher.py 
    'app_launcher.py.bak',  # Archivo de respaldo
    'routes.py.bak',        # Archivo de respaldo
    'tag_replacement_1.txt',# Archivo temporal
    'cookies.txt',          # Archivo temporal
    'gunicorn_config.py',   # Solo para despliegue en servidores
    'Procfile',             # Solo para despliegue en Heroku
    'render.yaml',          # Solo para despliegue en Render
    'sign_exe.py',          # Útil solo para firmar ejecutables (desarrollo)
]

# Lista de archivos a eliminar completamente
ARCHIVOS_A_ELIMINAR = [
    'GimnasioDB_Windows_20250430_234126.zip',  # Archivo de distribución antiguo
    'dist.rar',                                # Archivo de distribución comprimido
]

# Directorios a ignorar (no buscar dentro de ellos)
DIRECTORIOS_IGNORADOS = [
    '.git',
    'venv',
    'env',
    '__pycache__',
    'dev',
    'dist',
    'build',
    'backups',
]

# Patrones de archivos duplicados o temporales
PATRONES_ARCHIVOS_TEMPORALES = [
    r'.*\.py[co]$',         # Archivos compilados de Python
    r'.*\.bak$',            # Archivos de respaldo
    r'.*\.tmp$',            # Archivos temporales
    r'.*\.temp$',           # Archivos temporales
    r'.*~$',                # Respaldos de editores de texto
    r'.*\.spec$',           # Archivos de especificación de PyInstaller
    r'.*_test\.py$',        # Scripts de prueba
]

def main():
    """Función principal para limpiar archivos"""
    print("====================================")
    print(" LIMPIEZA DE ARCHIVOS INNECESARIOS ")
    print("====================================")
    print()
    
    # Asegurarse de que la carpeta dev existe
    if not os.path.exists('dev'):
        os.makedirs('dev')
        print("Carpeta 'dev' creada.")
    
    # Crear subcarpeta para archivos temporales
    temp_dir = os.path.join('dev', 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # Crear subcarpeta para respaldos
    backup_dir = os.path.join('dev', 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Mover archivos a la carpeta dev
    archivos_movidos = 0
    for archivo in ARCHIVOS_A_MOVER:
        if os.path.exists(archivo):
            # Si el archivo ya existe en 'dev', hacer copia con timestamp
            destino = os.path.join('dev', archivo)
            if os.path.exists(destino):
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                base, extension = os.path.splitext(archivo)
                nuevo_nombre = f"{base}_{timestamp}{extension}"
                destino = os.path.join('dev', nuevo_nombre)
            
            shutil.move(archivo, destino)
            print(f"✅ Archivo '{archivo}' movido a '{destino}'")
            archivos_movidos += 1
        else:
            print(f"❓ Archivo '{archivo}' no encontrado, omitiendo...")
    
    # Eliminar archivos innecesarios
    archivos_eliminados = 0
    for archivo in ARCHIVOS_A_ELIMINAR:
        if os.path.exists(archivo):
            os.remove(archivo)
            print(f"🗑️ Archivo '{archivo}' eliminado.")
            archivos_eliminados += 1
        else:
            print(f"❓ Archivo '{archivo}' no encontrado, omitiendo...")
    
    # Buscar y mover archivos temporales y duplicados
    temp_encontrados = mover_archivos_temporales(temp_dir)
    
    # Mover archivos de prueba a carpeta dev/test si no están en carpeta test
    test_movidos = mover_archivos_prueba()
    
    # Resumen de la operación
    print("\n====================================")
    print(" RESUMEN DE LA LIMPIEZA")
    print("====================================")
    print(f"✅ Archivos específicos movidos: {archivos_movidos}")
    print(f"🗑️ Archivos eliminados: {archivos_eliminados}")
    print(f"📋 Archivos temporales/duplicados movidos: {temp_encontrados}")
    print(f"🧪 Archivos de prueba movidos: {test_movidos}")
    print("\n¡Limpieza completada!")

def mover_archivos_temporales(temp_dir):
    """Busca y mueve archivos temporales o de respaldo a la carpeta dev/temp"""
    archivos_movidos = 0
    
    # Recorrer directorios y buscar archivos temporales
    for root, dirs, files in os.walk('.'):
        # Filtrar directorios ignorados
        dirs[:] = [d for d in dirs if d not in DIRECTORIOS_IGNORADOS]
        
        for file in files:
            ruta_origen = os.path.join(root, file)
            
            # Verificar si el archivo coincide con algún patrón temporal
            if any(re.match(pattern, file) for pattern in PATRONES_ARCHIVOS_TEMPORALES):
                ruta_destino = os.path.join(temp_dir, file)
                
                # Si ya existe, agregar número secuencial
                if os.path.exists(ruta_destino):
                    base, ext = os.path.splitext(file)
                    counter = 1
                    while os.path.exists(os.path.join(temp_dir, f"{base}_{counter}{ext}")):
                        counter += 1
                    ruta_destino = os.path.join(temp_dir, f"{base}_{counter}{ext}")
                
                try:
                    shutil.move(ruta_origen, ruta_destino)
                    print(f"📋 Archivo temporal '{ruta_origen}' movido a '{ruta_destino}'")
                    archivos_movidos += 1
                except Exception as e:
                    print(f"❌ Error al mover '{ruta_origen}': {str(e)}")
    
    return archivos_movidos

def mover_archivos_prueba():
    """Mueve archivos de prueba a la carpeta dev/test si no están en la carpeta test"""
    archivos_movidos = 0
    test_dir = os.path.join('dev', 'test')
    
    # Crear carpeta de pruebas si no existe
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    # Buscar archivos de prueba fuera de la carpeta test
    for root, dirs, files in os.walk('.'):
        # Filtrar directorios ignorados
        dirs[:] = [d for d in dirs if d not in DIRECTORIOS_IGNORADOS]
        
        # Ignorar la carpeta test
        if root == './test':
            continue
        
        for file in files:
            # Verificar si es un archivo de prueba
            if (file.startswith('test_') and file.endswith('.py')) or \
               (file.startswith('run_test') and file.endswith('.py')):
                ruta_origen = os.path.join(root, file)
                ruta_destino = os.path.join(test_dir, file)
                
                # Si ya existe, agregar número secuencial
                if os.path.exists(ruta_destino):
                    base, ext = os.path.splitext(file)
                    counter = 1
                    while os.path.exists(os.path.join(test_dir, f"{base}_{counter}{ext}")):
                        counter += 1
                    ruta_destino = os.path.join(test_dir, f"{base}_{counter}{ext}")
                
                try:
                    shutil.move(ruta_origen, ruta_destino)
                    print(f"🧪 Archivo de prueba '{ruta_origen}' movido a '{ruta_destino}'")
                    archivos_movidos += 1
                except Exception as e:
                    print(f"❌ Error al mover '{ruta_origen}': {str(e)}")
    
    return archivos_movidos

if __name__ == "__main__":
    main() 