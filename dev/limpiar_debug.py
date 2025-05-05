#!/usr/bin/env python
"""
Script para limpiar características de depuración del proyecto
Este script eliminará elementos de depuración para preparar la aplicación para producción.
"""
import os
import re
import shutil

def backup_file(file_path):
    """Crea una copia de seguridad del archivo"""
    backup_path = file_path + '.bak'
    shutil.copy2(file_path, backup_path)
    print(f"Copia de seguridad creada: {backup_path}")

def remove_debug_menu(file_path):
    """Elimina el menú de depuración del archivo layout.html"""
    backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Buscar y eliminar el bloque del menú de depuración
    pattern = r'\s*<!-- Menú de debug.*?{% endif %}'
    cleaned_content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(cleaned_content)
    
    print(f"Menú de depuración eliminado de {file_path}")

def remove_debug_endpoints(file_path):
    """Elimina los endpoints de depuración de routes/__init__.py"""
    backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Buscar y eliminar las rutas de depuración
    patterns = [
        r'@main\.route\(\'/actualizar-bd\'.*?return f.*?\)',
        r'@main\.route\(\'/emergencia-admin\'.*?return render_template.*?\)',
        r'@main\.route\(\'/actualizar_rol_admin\'.*?return f.*?\)'
    ]
    
    for pattern in patterns:
        cleaned_content = re.sub(pattern, '', content, flags=re.DOTALL)
        content = cleaned_content
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(cleaned_content)
    
    print(f"Endpoints de depuración eliminados de {file_path}")

def remove_debug_auth_functions(file_path):
    """Elimina funciones de depuración de auth/routes.py"""
    backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Buscar y eliminar las funciones de depuración
    pattern = r'@bp\.route\(\'/debug-session\'.*?"""\)'
    cleaned_content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(cleaned_content)
    
    print(f"Funciones de depuración eliminadas de {file_path}")

def main():
    # Verificar que estamos en la carpeta correcta
    if not os.path.exists('templates/layouts/layout.html'):
        print("Error: Este script debe ejecutarse desde la carpeta raíz del proyecto")
        return
    
    # Eliminar menú de depuración
    remove_debug_menu('templates/layouts/layout.html')
    
    # Eliminar endpoints de depuración
    if os.path.exists('routes/__init__.py'):
        remove_debug_endpoints('routes/__init__.py')
    
    # Eliminar funciones de depuración de auth
    if os.path.exists('routes/auth/routes.py'):
        remove_debug_auth_functions('routes/auth/routes.py')
    
    print("\n¡Limpieza completa! La aplicación está lista para producción.")
    print("Si necesitas restaurar algún archivo, usa las copias de seguridad (.bak).")

if __name__ == "__main__":
    confirmation = input("¿Estás seguro de que deseas eliminar todas las características de depuración? (s/n): ")
    if confirmation.lower() == 's':
        main()
    else:
        print("Operación cancelada.") 