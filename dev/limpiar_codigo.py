#!/usr/bin/env python
"""
Script principal para limpiar el código de archivos innecesarios
Este script ejecuta el limpiador ubicado en dev/limpiar_archivos.py

Desarrollado por: NEURALJIRA_DEV
"""

import os
import sys
import subprocess

def main():
    """Función principal"""
    print("======================================================")
    print(" LIMPIEZA DE CÓDIGO PARA CONSTRUCCIÓN DEL EJECUTABLE ")
    print("======================================================")
    print()
    
    # Verificar si existe la carpeta dev
    if not os.path.exists('dev'):
        os.makedirs('dev')
        print("Carpeta 'dev' creada.")
    
    # Verificar si existe el script de limpieza
    limpiador_path = os.path.join('dev', 'limpiar_archivos.py')
    if not os.path.exists(limpiador_path):
        print("⚠️ No se encontró el script de limpieza.")
        print("Primero debe crear el script de limpieza en dev/limpiar_archivos.py")
        return
    
    # Verificar permisos de ejecución
    try:
        # Hacer ejecutable el script si es necesario
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            subprocess.run(['chmod', '+x', limpiador_path], check=True)
    except subprocess.SubprocessError:
        print("⚠️ No se pudieron establecer permisos de ejecución, pero continuaremos.")
    
    # Ejecutar el script de limpieza
    try:
        print("Ejecutando limpiador de código...")
        # Usar sys.executable para asegurar que se use el mismo intérprete de Python
        subprocess.run([sys.executable, limpiador_path], check=True)
        print("\n✅ Limpieza completada exitosamente!")
        print("\nAhora puede proceder con la construcción del ejecutable con:")
        print("  python empaquetar_exe.py")
    except subprocess.SubprocessError as e:
        print(f"❌ Error durante la limpieza: {e}")
        return
    
if __name__ == "__main__":
    main() 