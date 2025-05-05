#!/usr/bin/env python
"""
Script para crear un ejecutable autónomo del Gimnasio.
Modificado para reducir falsos positivos en antivirus y optimizar el rendimiento.

Desarrollado por: YEIFRAN HERNANDEZ
NEURALJIRA_DEV - Visión inteligente para gestión de gimnasios
"""
import os
import sys
import shutil
import subprocess
import datetime
import platform
from colorama import init, Fore, Style

# Inicializar colorama para soporte de colores en consola
init()

def print_color(message, color=Fore.WHITE, style=Style.NORMAL):
    """Imprime un mensaje con color"""
    print(f"{style}{color}{message}{Style.RESET_ALL}")

def crear_respaldo_automatico():
    """Crea un respaldo de la base de datos antes de empaquetar"""
    # Si no existe database.db, no hay nada que respaldar
    if not os.path.exists('database.db'):
        print_color("[INFO] No se encontró base de datos para respaldar.", Fore.YELLOW)
        return
        
    # Crear directorio de respaldos si no existe
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    # Generar nombre de archivo con fecha
    fecha = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    archivo_respaldo = f'backups/database_{fecha}_pre_build.db'
    
    # Copiar la base de datos
    try:
        shutil.copy2('database.db', archivo_respaldo)
        print_color(f"[INFO] Respaldo creado: {archivo_respaldo}", Fore.GREEN)
    except Exception as e:
        print_color(f"[ERROR] Error al crear respaldo: {str(e)}", Fore.RED, Style.BRIGHT)

def limpiar_archivos_temporales():
    """Limpia archivos temporales y caches que pueden causar problemas"""
    # Eliminar archivos __pycache__
    directorios = ['.', 'routes', 'routes/usuarios', 'routes/finanzas', 'routes/productos', 'routes/ventas', 'routes/admin', 'routes/auth']
    
    for directorio in directorios:
        if os.path.exists(directorio):
            pycache_dir = os.path.join(directorio, '__pycache__')
            if os.path.exists(pycache_dir):
                try:
                    shutil.rmtree(pycache_dir)
                    print_color(f"[INFO] Eliminado directorio {pycache_dir}", Fore.GREEN)
                except Exception as e:
                    print_color(f"[ERROR] No se pudo eliminar {pycache_dir}: {e}", Fore.RED)
    
    # Eliminar archivos .pyc
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                    print_color(f"[INFO] Eliminado archivo {os.path.join(root, file)}", Fore.GREEN)
                except Exception as e:
                    print_color(f"[ERROR] No se pudo eliminar {os.path.join(root, file)}: {e}", Fore.RED)

    # Limpiar archivos de construcción anteriores
    build_dirs = ['build', 'dist']
    for build_dir in build_dirs:
        if os.path.exists(build_dir):
            try:
                shutil.rmtree(build_dir)
                print_color(f"[INFO] Eliminado directorio de construcción anterior: {build_dir}", Fore.GREEN)
            except Exception as e:
                print_color(f"[ERROR] No se pudo eliminar {build_dir}: {e}", Fore.RED)
                
    # Eliminar archivo de información de versión si existe
    if os.path.exists('file_version_info.txt'):
        try:
            os.remove('file_version_info.txt')
            print_color("[INFO] Eliminado archivo de información de versión anterior", Fore.GREEN)
        except Exception as e:
            print_color(f"[ERROR] No se pudo eliminar file_version_info.txt: {e}", Fore.RED)

def generar_informacion_version():
    """Genera información de versión para incluir en el ejecutable"""
    version_info = {
        'version': '1.0.0',
        'company_name': 'NEURALJIRA_DEV',
        'product_name': 'GimnasioDB',
        'description': 'Sistema de gestión para gimnasios',
        'copyright': f'© {datetime.datetime.now().year} YEIFRAN HERNANDEZ',
        'trademark': 'NEURALJIRA_DEV',
    }
    
    return version_info

def crear_ejecutable():
    """Crea el ejecutable con PyInstaller usando opciones optimizadas"""
    print_color("\n[INFO] Iniciando proceso de empaquetado...", Fore.CYAN, Style.BRIGHT)
    
    # Verificar si "--no-backup" no está en los argumentos
    if "--no-backup" not in sys.argv:
        # Crear respaldo automático
        crear_respaldo_automatico()
    else:
        print_color("[INFO] Respaldo automático desactivado por parámetro --no-backup", Fore.YELLOW)
    
    # Limpiar archivos temporales
    limpiar_archivos_temporales()
    
    # Generar información de versión
    version_info = generar_informacion_version()
    
    # Verificar si el icono existe
    icon_path = 'static/img/icon.ico'
    if not os.path.exists(icon_path):
        print_color(f"[ADVERTENCIA] No se encontró el archivo de icono en {icon_path}. Se utilizará un icono predeterminado.", Fore.YELLOW)
        icon_arg = []
    else:
        icon_arg = [f'--icon={icon_path}']
    
    # Definir argumentos base para PyInstaller
    pyinstaller_args = [
        'pyinstaller',
        '--noconfirm',
        '--clean',
        '--log-level=INFO',
        '--name=GimnasioDB',
    ]
    
    # Añadir icono si existe
    if icon_arg:
        pyinstaller_args.extend(icon_arg)
    
    # Añadir datos según el sistema operativo
    path_separator = ';' if platform.system() == 'Windows' else ':'
    
    # Verificar si las carpetas de recursos existen
    data_args = []
    
    if os.path.exists('templates'):
        data_args.append(f'--add-data=templates{path_separator}templates')
    else:
        print_color("[ADVERTENCIA] No se encontró la carpeta templates.", Fore.YELLOW)
    
    if os.path.exists('static'):
        data_args.append(f'--add-data=static{path_separator}static')
    else:
        print_color("[ADVERTENCIA] No se encontró la carpeta static.", Fore.YELLOW)
    
    pyinstaller_args.extend(data_args)
    
    # Verificar rutas antes de añadir hidden-imports
    routes_dirs = ['routes', 'routes/usuarios', 'routes/finanzas', 'routes/productos', 
                  'routes/ventas', 'routes/admin', 'routes/auth']
    
    hidden_imports = ['--hidden-import=routes']
    
    for route_dir in routes_dirs[1:]:  # Saltar el primero que ya está incluido
        if os.path.exists(route_dir):
            module_name = route_dir.replace('/', '.')
            hidden_imports.append(f'--hidden-import={module_name}')
    
    pyinstaller_args.extend(hidden_imports)
    
    # Opciones específicas para reducir falsos positivos
    pyinstaller_args.extend([
        '--upx-exclude=vcruntime140.dll',  # Evitar comprimir DLLs del sistema
        '--upx-exclude=python*.dll',
        '--upx-exclude=VCRUNTIME140.dll',
        '--upx-exclude=msvcp140.dll',
    ])
    
    # Añadir opciones de optimización
    pyinstaller_args.extend([
        '--noupx',  # Evitar problemas con antivirus
        '--strip',  # Eliminar símbolos de depuración
    ])
    
    # Añadir información de versión para Windows
    if platform.system() == 'Windows':
        pyinstaller_args.extend([
            f'--version-file={crear_archivo_version(version_info)}',
        ])
    
    # Configurar el tipo de compilación
    pyinstaller_args.extend([
        '--onefile',  # Crear un solo archivo ejecutable
        '--windowed',  # Aplicación sin consola
    ])
    
    # Verificar si app_launcher.py existe
    if not os.path.exists('app_launcher.py'):
        print_color("[ERROR] No se encontró el archivo app_launcher.py. No se puede continuar.", Fore.RED, Style.BRIGHT)
        return False
    
    pyinstaller_args.append('app_launcher.py')  # Script principal a empaquetar
    
    # Ejecutar PyInstaller
    print_color(f"[INFO] Ejecutando PyInstaller con argumentos:", Fore.CYAN)
    for arg in pyinstaller_args:
        print_color(f"  {arg}", Fore.CYAN)
        
    try:
        subprocess.run(pyinstaller_args, check=True)
        
        # Verificar si la compilación fue exitosa
        ejecutable = 'dist/GimnasioDB.exe' if platform.system() == 'Windows' else 'dist/GimnasioDB'
        if not os.path.exists(ejecutable):
            print_color(f"\n[ERROR] No se encontró el ejecutable en {ejecutable} después de la compilación.", Fore.RED, Style.BRIGHT)
            return False
            
        print_color("\n[ÉXITO] ¡Compilación completada correctamente!", Fore.GREEN, Style.BRIGHT)
        print_color(f"[INFO] El ejecutable se encuentra en: {os.path.abspath(ejecutable)}", Fore.GREEN)
    except subprocess.CalledProcessError as e:
        print_color(f"\n[ERROR] Error al empaquetar la aplicación: {e}", Fore.RED, Style.BRIGHT)
        return False
    
    # Generar un archivo README para incluir con el ejecutable
    try:
        generar_readme_distribucion()
    except Exception as e:
        print_color(f"[ERROR] Error al generar el archivo README: {e}", Fore.RED)
    
    # Comprimir la carpeta dist
    try:
        compresion_exitosa = comprimir_distribucion()
        if not compresion_exitosa:
            print_color("[ADVERTENCIA] No se pudo comprimir la distribución, pero el ejecutable está disponible.", Fore.YELLOW)
    except Exception as e:
        print_color(f"[ERROR] Error al comprimir la distribución: {e}", Fore.RED)
    
    # Si se especificó, intentar firmar el ejecutable
    if "--sign" in sys.argv:
        try:
            firma_exitosa = firmar_ejecutable()
            if not firma_exitosa:
                print_color("[ADVERTENCIA] No se pudo firmar el ejecutable.", Fore.YELLOW)
        except Exception as e:
            print_color(f"[ERROR] Error al firmar el ejecutable: {e}", Fore.RED)
    
    return True

def crear_archivo_version(info):
    """Crea un archivo de información de versión para Windows"""
    version_file = 'file_version_info.txt'
    
    with open(version_file, 'w') as f:
        f.write('# UTF-8\n')
        f.write('#\n')
        f.write('# For more details about fixed file info \'ffi\' see:\n')
        f.write('# http://msdn.microsoft.com/en-us/library/ms646997.aspx\n')
        f.write('VSVersionInfo(\n')
        f.write('  ffi=FixedFileInfo(\n')
        f.write('    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)\n')
        f.write('    # Set not needed items to zero 0.\n')
        f.write('    filevers=(1, 0, 0, 0),\n')
        f.write('    prodvers=(1, 0, 0, 0),\n')
        f.write('    # Contains a bitmask that specifies the valid bits \'flags\'\r\n')
        f.write('    mask=0x3f,\n')
        f.write('    # Contains a bitmask that specifies the Boolean attributes of the file.\n')
        f.write('    flags=0x0,\n')
        f.write('    # The operating system for which this file was designed.\n')
        f.write('    # 0x4 - NT and there is no need to change it.\n')
        f.write('    OS=0x40004,\n')
        f.write('    # The general type of file.\n')
        f.write('    # 0x1 - the file is an application.\n')
        f.write('    fileType=0x1,\n')
        f.write('    # The function of the file.\n')
        f.write('    # 0x0 - the function is not defined for this fileType\n')
        f.write('    subtype=0x0,\n')
        f.write('    # Creation date and time stamp.\n')
        f.write('    date=(0, 0)\n')
        f.write('    ),\n')
        f.write('  kids=[\n')
        f.write('    StringFileInfo(\n')
        f.write('      [\n')
        f.write('      StringTable(\n')
        f.write('        u\'040904B0\',\n')
        f.write(f'        [StringStruct(u\'CompanyName\', u\'{info["company_name"]}\'),\n')
        f.write(f'        StringStruct(u\'FileDescription\', u\'{info["description"]}\'),\n')
        f.write(f'        StringStruct(u\'FileVersion\', u\'{info["version"]}\'),\n')
        f.write(f'        StringStruct(u\'InternalName\', u\'GimnasioDB\'),\n')
        f.write(f'        StringStruct(u\'LegalCopyright\', u\'{info["copyright"]}\'),\n')
        f.write(f'        StringStruct(u\'OriginalFilename\', u\'GimnasioDB.exe\'),\n')
        f.write(f'        StringStruct(u\'ProductName\', u\'{info["product_name"]}\'),\n')
        f.write(f'        StringStruct(u\'ProductVersion\', u\'{info["version"]}\'),\n')
        f.write(f'        StringStruct(u\'Comments\', u\'Sistema de gestión para gimnasios\')])\n')
        f.write('      ]), \n')
        f.write('    VarFileInfo([VarStruct(u\'Translation\', [1033, 1200])])\n')
        f.write('  ]\n')
        f.write(')\n')
    
    return version_file

def generar_readme_distribucion():
    """Genera un archivo README para incluir con la distribución"""
    # Asegurarse de que el directorio dist existe
    if not os.path.exists('dist'):
        os.makedirs('dist')
        
    readme_path = 'dist/LEEME.txt'
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write('GimnasioDB - Sistema de gestión para gimnasios\n')
        f.write('===============================================\n\n')
        f.write(f'Versión: 1.0.0\n')
        f.write(f'Desarrollado por: YEIFRAN HERNANDEZ (NEURALJIRA_DEV)\n')
        f.write(f'Fecha: {datetime.datetime.now().strftime("%d/%m/%Y")}\n\n')
        f.write('INSTRUCCIONES DE USO\n')
        f.write('-------------------\n\n')
        f.write('1. Ejecute el archivo GimnasioDB.exe para iniciar la aplicación.\n')
        f.write('2. El sistema abrirá automáticamente su navegador predeterminado.\n')
        f.write('3. Si el navegador no se abre, acceda a http://127.0.0.1:5000 manualmente.\n\n')
        f.write('NOTAS IMPORTANTES\n')
        f.write('----------------\n\n')
        f.write('- Este software es legítimo y no contiene malware.\n')
        f.write('- Su antivirus podría mostrar una alerta debido a que es un ejecutable empaquetado.\n')
        f.write('- Si esto ocurre, por favor configure una excepción en su antivirus para este archivo.\n')
        f.write('- Todos los datos se almacenan localmente en su computadora.\n\n')
        f.write('REQUISITOS DEL SISTEMA\n')
        f.write('--------------------\n\n')
        f.write('- Windows 10 o superior\n')
        f.write('- 4GB de RAM mínimo\n')
        f.write('- 100MB de espacio en disco\n')
        f.write('- Navegador web moderno (Chrome, Firefox, Edge)\n\n')
        f.write('SOPORTE\n')
        f.write('-------\n\n')
        f.write('Para soporte técnico, contacte a: neuraljiradev@example.com\n\n')
        f.write('Copyright © NEURALJIRA_DEV - Todos los derechos reservados.\n')
    
    print_color(f"[INFO] Archivo README generado en: {os.path.abspath(readme_path)}", Fore.GREEN)

def comprimir_distribucion():
    """Comprime la carpeta dist en un archivo ZIP"""
    try:
        import zipfile
        from datetime import datetime
        
        dist_dir = 'dist'
        if not os.path.exists(dist_dir):
            print_color("[ERROR] No se encontró el directorio dist para comprimir", Fore.RED)
            return False
            
        # Generar nombre de archivo con fecha
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'GimnasioDB_{fecha}.zip'
        
        print_color(f"[INFO] Comprimiendo distribución en {zip_filename}...", Fore.CYAN)
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dist_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dist_dir)
                    zipf.write(file_path, arcname)
        
        print_color(f"[ÉXITO] Distribución comprimida en: {os.path.abspath(zip_filename)}", Fore.GREEN)
        return True
    except Exception as e:
        print_color(f"[ERROR] Error al comprimir la distribución: {str(e)}", Fore.RED)
        return False

def firmar_ejecutable():
    """Intenta firmar el ejecutable si existe el script sign_exe.py"""
    try:
        if os.path.exists('sign_exe.py'):
            print_color("[INFO] Intentando firmar el ejecutable...", Fore.CYAN)
            ejecutable = 'dist/GimnasioDB.exe' if platform.system() == 'Windows' else 'dist/GimnasioDB'
            resultado = subprocess.run([sys.executable, 'sign_exe.py', ejecutable], 
                                     check=True, capture_output=True, text=True)
            print_color("[ÉXITO] Ejecutable firmado correctamente", Fore.GREEN)
            return True
        else:
            print_color("[INFO] No se encontró el script sign_exe.py. El ejecutable no será firmado", Fore.YELLOW)
            return False
    except subprocess.CalledProcessError as e:
        print_color(f"[ERROR] Error al firmar el ejecutable: {e.stderr}", Fore.RED)
        return False

def verificar_dependencias():
    """Verifica que todas las dependencias necesarias estén instaladas"""
    print_color("[INFO] Verificando dependencias necesarias...", Fore.CYAN)
    
    # Lista de paquetes necesarios
    dependencias = [
        'flask',
        'werkzeug',
        'jinja2',
        'sqlalchemy',
        'flask-sqlalchemy',
        'colorama',
        'pyinstaller'
    ]
    
    faltantes = []
    
    for dep in dependencias:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            faltantes.append(dep)
    
    if faltantes:
        print_color(f"[ADVERTENCIA] Faltan las siguientes dependencias: {', '.join(faltantes)}", Fore.YELLOW)
        print_color("[INFO] Instalando dependencias faltantes...", Fore.CYAN)
        
        for dep in faltantes:
            try:
                print_color(f"[INFO] Instalando {dep}...", Fore.CYAN)
                subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)
                print_color(f"[INFO] {dep} instalado correctamente", Fore.GREEN)
            except subprocess.CalledProcessError as e:
                print_color(f"[ERROR] Error al instalar {dep}: {e}", Fore.RED)
                return False
    else:
        print_color("[INFO] Todas las dependencias están instaladas", Fore.GREEN)
    
    return True

def mostrar_ayuda():
    """Muestra la ayuda del script"""
    print_color("\nOpciones disponibles:", Fore.CYAN, Style.BRIGHT)
    print_color("  --help     : Muestra esta ayuda", Fore.WHITE)
    print_color("  --sign     : Firma el ejecutable después de crearlo", Fore.WHITE)
    print_color("  --no-backup: No crea respaldo de la base de datos", Fore.WHITE)
    print_color("\nEjemplo de uso:", Fore.CYAN)
    print_color("  python empaquetar_exe.py --sign", Fore.WHITE)
    sys.exit(0)

if __name__ == '__main__':
    print_color("="*60, Fore.BLUE, Style.BRIGHT)
    print_color("COMPILADOR DE GIMNASIO DB - NEURALJIRA_DEV", Fore.BLUE, Style.BRIGHT)
    print_color("="*60, Fore.BLUE, Style.BRIGHT)
    
    # Procesar argumentos
    if "--help" in sys.argv or "-h" in sys.argv:
        mostrar_ayuda()
    
    print_color("Iniciando proceso de compilación...", Fore.WHITE, Style.BRIGHT)
    
    # Verificar dependencias antes de continuar
    if not verificar_dependencias():
        print_color("[ERROR] No se pudieron instalar todas las dependencias necesarias", Fore.RED, Style.BRIGHT)
        sys.exit(1)
    
    # Verificar que PyInstaller está instalado
    try:
        subprocess.run(['pyinstaller', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_color("[ERROR] PyInstaller no está instalado. Instalando...", Fore.YELLOW)
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        except subprocess.CalledProcessError as e:
            print_color(f"[ERROR] No se pudo instalar PyInstaller: {e}", Fore.RED, Style.BRIGHT)
            sys.exit(1)
    
    # Verificar si UPX está instalado (opcional, para mejor compresión)
    upx_installed = False
    try:
        subprocess.run(['upx', '--version'], check=True, capture_output=True)
        upx_installed = True
        print_color("[INFO] UPX encontrado, se usará para compresión adicional.", Fore.GREEN)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_color("[INFO] UPX no encontrado. La compilación continuará sin compresión adicional.", Fore.YELLOW)
    
    if crear_ejecutable():
        print_color("\n¡Proceso de empaquetado completado con éxito!", Fore.GREEN, Style.BRIGHT)
        ejecutable = 'dist/GimnasioDB.exe' if platform.system() == 'Windows' else 'dist/GimnasioDB'
        print_color(f"El ejecutable se encuentra en la carpeta: {os.path.abspath(ejecutable)}", Fore.WHITE)
    else:
        print_color("\nEl proceso de empaquetado falló. Revise los mensajes de error anteriores.", Fore.RED, Style.BRIGHT)
        sys.exit(1)