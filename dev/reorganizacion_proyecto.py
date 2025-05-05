#!/usr/bin/env python
"""
Script para reorganizar el proyecto GimnasioDB
- Mueve archivos de desarrollo a la carpeta dev
- Prepara el proyecto para empaquetado
- Elimina archivos innecesarios en la distribución

Autor: Asistente IA
Fecha: Generado automáticamente
"""
import os
import shutil
import glob
import sys
import subprocess
import platform

# Archivos y directorios principales que deben permanecer en la raíz para la distribución
ARCHIVOS_DISTRIBUCION = [
    'app_launcher.py',
    'models.py',
    'config.py',
    'requirements.txt',
    'README.md',
    'ejecutar_app.bat',
    'ejecutar_windows.bat',
    'INSTRUCCIONES_ANTIVIRUS.md',
    '.gitignore',
]

# Directorios que deben permanecer en la raíz
DIRECTORIOS_DISTRIBUCION = [
    'templates',
    'static',
    'routes',
]

# Archivos que deben moverse a dev/
ARCHIVOS_DESARROLLO = [
    'empaquetar_exe.py',
    'empaquetado_linux.py',
    'limpiar_codigo.py',
    'insertar_usuario.py',
    'actualizar_db.py',
    'reparar_base_datos.bat',
    'verificar_base_datos.bat',
    'empaquetar_seguro.bat',
    'backup_datos.bat',
    'file_version_info.txt',
]

# Directorios que deben moverse a dev/
DIRECTORIOS_DESARROLLO = [
    'test',
]

def crear_directorio_si_no_existe(directorio):
    """Crea un directorio si no existe"""
    if not os.path.exists(directorio):
        os.makedirs(directorio)
        print(f"Creado directorio: {directorio}")

def mover_archivo(origen, destino):
    """Mueve un archivo de origen a destino"""
    if os.path.exists(origen):
        # Asegurarse de que el directorio destino existe
        dir_destino = os.path.dirname(destino)
        if not os.path.exists(dir_destino):
            os.makedirs(dir_destino)
        
        # Si el archivo ya existe en el destino, hacer backup
        if os.path.exists(destino):
            backup_path = f"{destino}.bak"
            if os.path.exists(backup_path):
                os.remove(backup_path)
            shutil.move(destino, backup_path)
            print(f"Backup creado: {backup_path}")
        
        # Mover el archivo
        shutil.move(origen, destino)
        print(f"Movido: {origen} -> {destino}")
        return True
    else:
        print(f"No existe el archivo: {origen}")
        return False

def copiar_archivo(origen, destino):
    """Copia un archivo de origen a destino"""
    if os.path.exists(origen):
        # Asegurarse de que el directorio destino existe
        dir_destino = os.path.dirname(destino)
        if not os.path.exists(dir_destino):
            os.makedirs(dir_destino)
        
        # Copiar el archivo
        shutil.copy2(origen, destino)
        print(f"Copiado: {origen} -> {destino}")
        return True
    else:
        print(f"No existe el archivo: {origen}")
        return False

def reorganizar_proyecto():
    """Reorganiza el proyecto según las reglas definidas"""
    # Crear directorio dev si no existe
    crear_directorio_si_no_existe('dev')
    
    # Mover archivos de desarrollo a dev/
    for archivo in ARCHIVOS_DESARROLLO:
        if os.path.exists(archivo):
            mover_archivo(archivo, os.path.join('dev', archivo))
    
    # Mover directorios de desarrollo a dev/
    for directorio in DIRECTORIOS_DESARROLLO:
        if os.path.exists(directorio) and directorio != 'dev':
            # Verificar si el directorio destino ya existe en dev/
            dir_destino = os.path.join('dev', directorio)
            if os.path.exists(dir_destino):
                # Si existe, copiar solo el contenido
                for item in os.listdir(directorio):
                    item_path = os.path.join(directorio, item)
                    dest_path = os.path.join(dir_destino, item)
                    if os.path.isdir(item_path):
                        if not os.path.exists(dest_path):
                            shutil.copytree(item_path, dest_path)
                            print(f"Copiado directorio: {item_path} -> {dest_path}")
                    else:
                        copiar_archivo(item_path, dest_path)
                # Eliminar el directorio original
                shutil.rmtree(directorio)
                print(f"Eliminado directorio original: {directorio}")
            else:
                # Si no existe, simplemente mover el directorio completo
                shutil.move(directorio, dir_destino)
                print(f"Movido directorio: {directorio} -> {dir_destino}")
    
    # Identificar y mover archivos adicionales que no están en la lista de distribución
    for archivo in os.listdir('.'):
        if (os.path.isfile(archivo) and 
            archivo not in ARCHIVOS_DISTRIBUCION and 
            not any(archivo.endswith(ext) for ext in ['.db', '.git', '.md']) and
            not archivo.startswith('.')):
            
            # Verificar si no es un archivo ya procesado o que debe ignorarse
            if archivo not in ARCHIVOS_DESARROLLO and not archivo.startswith('__pycache__'):
                dest_path = os.path.join('dev', archivo)
                if not os.path.exists(dest_path):
                    mover_archivo(archivo, dest_path)
    
    # Mover directorios adicionales que no están en la lista de distribución
    for directorio in os.listdir('.'):
        if (os.path.isdir(directorio) and 
            directorio not in DIRECTORIOS_DISTRIBUCION and
            directorio != 'dev' and
            directorio != '.git' and
            directorio != 'backups' and
            directorio != '__pycache__' and
            directorio != 'venv' and
            directorio != 'build' and
            directorio != 'dist'):
            
            # Verificar si no es un directorio ya procesado
            if directorio not in DIRECTORIOS_DESARROLLO:
                dest_path = os.path.join('dev', directorio)
                if not os.path.exists(dest_path):
                    shutil.move(directorio, dest_path)
                    print(f"Movido directorio adicional: {directorio} -> {dest_path}")
                else:
                    # Si el directorio destino ya existe, mover solo el contenido
                    for item in os.listdir(directorio):
                        item_path = os.path.join(directorio, item)
                        item_dest = os.path.join(dest_path, item)
                        if os.path.isdir(item_path):
                            if not os.path.exists(item_dest):
                                shutil.copytree(item_path, item_dest)
                                print(f"Copiado directorio: {item_path} -> {item_dest}")
                        else:
                            if not os.path.exists(item_dest):
                                shutil.copy2(item_path, item_dest)
                                print(f"Copiado archivo: {item_path} -> {item_dest}")
                    # Eliminar el directorio original
                    shutil.rmtree(directorio)
                    print(f"Eliminado directorio original después de copiar contenido: {directorio}")

def actualizar_spec_file():
    """Actualiza el archivo .spec para reflejar la nueva estructura"""
    spec_path = "GimnasioDB.spec"
    if os.path.exists(spec_path):
        # Hacer backup del archivo spec
        backup_path = os.path.join("dev", "GimnasioDB.spec.bak")
        shutil.copy2(spec_path, backup_path)
        print(f"Backup de spec creado: {backup_path}")
        
        # Mover el archivo spec a dev/
        dev_spec_path = os.path.join("dev", "GimnasioDB.spec")
        shutil.move(spec_path, dev_spec_path)
        print(f"Archivo spec movido a: {dev_spec_path}")

def limpiar_directorios_build():
    """Limpia directorios de build anteriores"""
    build_dirs = ['build', 'dist', '__pycache__']
    for build_dir in build_dirs:
        if os.path.exists(build_dir):
            try:
                shutil.rmtree(build_dir)
                print(f"Eliminado directorio de build: {build_dir}")
            except PermissionError as e:
                print(f"Error de permisos al eliminar {build_dir}: {e}")
                print(f"Intentando eliminar con comandos del sistema...")
                
                # En Windows, intentar con comandos del sistema
                if platform.system() == 'Windows':
                    try:
                        os.system(f'rd /s /q "{build_dir}"')
                        if not os.path.exists(build_dir):
                            print(f"Eliminado directorio {build_dir} con comando del sistema")
                        else:
                            print(f"No se pudo eliminar completamente {build_dir}")
                    except Exception as e2:
                        print(f"Error al eliminar {build_dir} con comando del sistema: {e2}")
                elif platform.system() == 'Linux' or platform.system() == 'Darwin':
                    try:
                        os.system(f'rm -rf "{build_dir}"')
                        if not os.path.exists(build_dir):
                            print(f"Eliminado directorio {build_dir} con comando del sistema")
                        else:
                            print(f"No se pudo eliminar completamente {build_dir}")
                    except Exception as e2:
                        print(f"Error al eliminar {build_dir} con comando del sistema: {e2}")
    
    # Eliminar todos los __pycache__ en el proyecto
    for pycache_dir in glob.glob('**/__pycache__', recursive=True):
        if os.path.exists(pycache_dir):
            try:
                shutil.rmtree(pycache_dir)
                print(f"Eliminado directorio: {pycache_dir}")
            except PermissionError as e:
                print(f"Error de permisos al eliminar {pycache_dir}: {e}")
                print(f"Omitiendo este directorio...")

def crear_script_lanzamiento():
    """Crea un script para facilitar el empaquetado desde la carpeta dev"""
    script_path = os.path.join("dev", "empaquetar.bat")
    with open(script_path, 'w') as f:
        f.write('@echo off\n')
        f.write('echo Empaquetando aplicacion GimnasioDB...\n')
        f.write('cd ..\n')
        f.write('python -m PyInstaller --noconfirm dev\\GimnasioDB.spec\n')
        f.write('echo Empaquetado completado.\n')
        f.write('pause\n')
    print(f"Creado script de empaquetado: {script_path}")

def actualizar_gitignore():
    """Actualiza el archivo .gitignore para la nueva estructura"""
    gitignore_path = ".gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            content = f.read()
            
        # Asegurarse de que los directorios de desarrollo estén ignorados
        updates = []
        if "dev/database.db" not in content:
            updates.append("dev/database.db")
        if "dev/*.spec" not in content:
            updates.append("dev/*.spec")
        if "dev/*.bat" not in content:
            updates.append("dev/*.bat")
        
        if updates:
            with open(gitignore_path, 'a') as f:
                f.write("\n# Archivos de desarrollo adicionales\n")
                for update in updates:
                    f.write(f"{update}\n")
            print("Actualizado .gitignore con nuevas exclusiones")

def main():
    """Función principal"""
    print("=== Reorganización del proyecto GimnasioDB ===")
    print("Este script reorganizará el proyecto para separar")
    print("archivos de desarrollo y preparar para distribución.")
    
    # Pedir confirmación
    respuesta = input("¿Desea continuar? (s/n): ")
    if respuesta.lower() != 's':
        print("Operación cancelada.")
        sys.exit(0)
    
    # Ejecutar pasos de reorganización
    reorganizar_proyecto()
    actualizar_spec_file()
    limpiar_directorios_build()
    crear_script_lanzamiento()
    actualizar_gitignore()
    
    print("\n=== Reorganización completada ===")
    print("1. Archivos de desarrollo movidos a carpeta 'dev/'")
    print("2. Archivos de distribución mantenidos en la raíz")
    print("3. Configuración de empaquetado actualizada")
    print("4. Script de empaquetado creado en 'dev/empaquetar.bat'")
    
    # Preguntar si realizar commit de los cambios
    respuesta = input("\n¿Desea realizar un commit de los cambios? (s/n): ")
    if respuesta.lower() == 's':
        try:
            mensaje = "Reorganización del proyecto: separación de archivos de desarrollo"
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", mensaje])
            print("\nCommit realizado con éxito.")
            
            # Preguntar si hacer push
            respuesta = input("¿Desea hacer push de los cambios? (s/n): ")
            if respuesta.lower() == 's':
                subprocess.run(["git", "push"])
                print("Push realizado con éxito.")
        except Exception as e:
            print(f"Error al realizar operaciones de git: {str(e)}")

if __name__ == "__main__":
    main() 