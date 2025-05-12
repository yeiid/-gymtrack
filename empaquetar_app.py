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
    if not os.path.exists('database.db'):
        print_color("[INFO] No se encontró base de datos para respaldar.", Fore.YELLOW)
        return
        
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    fecha = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    archivo_respaldo = f'backups/database_{fecha}_pre_build.db'
    
    try:
        shutil.copy2('database.db', archivo_respaldo)
        print_color(f"[INFO] Respaldo creado: {archivo_respaldo}", Fore.GREEN)
    except Exception as e:
        print_color(f"[ERROR] Error al crear respaldo: {str(e)}", Fore.RED, Style.BRIGHT)

def limpiar_archivos_temporales():
    """Limpia archivos temporales y caches"""
    directorios = ['.', 'routes', 'services']
    
    for directorio in directorios:
        if os.path.exists(directorio):
            pycache_dir = os.path.join(directorio, '__pycache__')
            if os.path.exists(pycache_dir):
                try:
                    shutil.rmtree(pycache_dir)
                    print_color(f"[INFO] Eliminado directorio {pycache_dir}", Fore.GREEN)
                except Exception as e:
                    print_color(f"[ERROR] No se pudo eliminar {pycache_dir}: {e}", Fore.RED)
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                    print_color(f"[INFO] Eliminado archivo {os.path.join(root, file)}", Fore.GREEN)
                except Exception as e:
                    print_color(f"[ERROR] No se pudo eliminar {os.path.join(root, file)}: {e}", Fore.RED)

    build_dirs = ['build', 'dist']
    for build_dir in build_dirs:
        if os.path.exists(build_dir):
            try:
                shutil.rmtree(build_dir)
                print_color(f"[INFO] Eliminado directorio de construcción anterior: {build_dir}", Fore.GREEN)
            except Exception as e:
                print_color(f"[ERROR] No se pudo eliminar {build_dir}: {e}", Fore.RED)

def generar_informacion_version():
    """Genera información de versión para incluir en el ejecutable"""
    version_info = {
        'version': '1.0.0',
        'company_name': 'NEURALJIRA_DEV',
        'product_name': 'GimnasioDB',
        'description': 'Sistema de gestión para gimnasios',
        'copyright': f'© {datetime.datetime.now().year} NEURALJIRA_DEV',
        'trademark': 'NEURALJIRA_DEV',
    }
    return version_info

def crear_ejecutable(plataforma_objetivo=None):
    """Crea el ejecutable con PyInstaller usando opciones optimizadas para la plataforma especificada"""
    print_color(f"\n[INFO] Iniciando proceso de empaquetado para {plataforma_objetivo or 'plataforma actual'}...", Fore.CYAN, Style.BRIGHT)
    
    if "--no-backup" not in sys.argv:
        crear_respaldo_automatico()
    else:
        print_color("[INFO] Respaldo automático desactivado por parámetro --no-backup", Fore.YELLOW)
    
    limpiar_archivos_temporales()
    version_info = generar_informacion_version()
    
    # Verificar icono
    icon_path = 'static/img/favicon.ico'
    if not os.path.exists(icon_path):
        print_color(f"[ADVERTENCIA] No se encontró el archivo de icono en {icon_path}. Se utilizará un icono predeterminado.", Fore.YELLOW)
        icon_arg = []
    else:
        icon_arg = [f'--icon={icon_path}']
    
    # Determinar configuración según plataforma objetivo
    if plataforma_objetivo:
        is_windows = plataforma_objetivo == 'windows'
        target_os = f"--target-architecture={plataforma_objetivo}"
    else:
        is_windows = platform.system() == 'Windows'
        target_os = ""
    
    # Nombre del ejecutable según plataforma
    nombre_ejecutable = 'GimnasioDB_' + (plataforma_objetivo or platform.system().lower())
    
    pyinstaller_args = [
        'pyinstaller',
        '--noconfirm',
        '--clean',
        '--log-level=INFO',
        f'--name={nombre_ejecutable}',
    ]
    
    if icon_arg:
        pyinstaller_args.extend(icon_arg)
    
    # Añadir datos necesarios
    data_args = []
    
    # En Linux, PyInstaller requiere el formato SOURCE:DEST
    # En Windows, PyInstaller requiere el formato SOURCE;DEST
    # Ahora usaremos el formato correcto para cada argumento
    for dir_name in ['templates', 'static']:
        if os.path.exists(dir_name):
            # Formatear el argumento de forma que PyInstaller lo entienda directamente
            if is_windows:
                data_args.append(f'--add-data={dir_name};{dir_name}')
            else:
                data_args.append(f'--add-data={dir_name}:{dir_name}')
        else:
            print_color(f"[ADVERTENCIA] No se encontró la carpeta {dir_name}.", Fore.YELLOW)
    
    # Añadir archivos adicionales
    for file_name in ['INSTRUCCIONES_ANTIVIRUS.md', 'README.md']:
        if os.path.exists(file_name):
            if is_windows:
                data_args.append(f'--add-data={file_name};.')
            else:
                data_args.append(f'--add-data={file_name}:.')
        else:
            print_color(f"[INFO] No se encontró {file_name} para incluir.", Fore.YELLOW)
    
    if os.path.exists('database.db') and "--include-db" in sys.argv:
        if is_windows:
            data_args.append('--add-data=database.db;.')
        else:
            data_args.append('--add-data=database.db:.')
        print_color("[INFO] Se incluirá la base de datos actual en la distribución.", Fore.GREEN)
    
    pyinstaller_args.extend(data_args)
    
    # Añadir imports necesarios
    hidden_imports = [
        '--hidden-import=flask',
        '--hidden-import=flask_sqlalchemy',
        '--hidden-import=sqlite3',
        '--hidden-import=webbrowser',
        '--hidden-import=sqlalchemy.sql.default_comparator',
        '--hidden-import=jinja2.ext',
        '--hidden-import=routes',
        '--hidden-import=services'
    ]
    
    pyinstaller_args.extend(hidden_imports)
    
    # Opciones de optimización
    pyinstaller_args.extend([
        '--upx-exclude=vcruntime140.dll',
        '--upx-exclude=python*.dll',
        '--upx-exclude=VCRUNTIME140.dll',
        '--upx-exclude=msvcp140.dll',
        '--noupx',
        '--strip',
    ])
    
    # Información de versión solo para Windows
    if is_windows:
        pyinstaller_args.extend([
            f'--version-file={crear_archivo_version(version_info)}',
        ])
    
    pyinstaller_args.extend([
        '--onefile',
        '--windowed',
    ])
    
    if not os.path.exists('app_launcher.py'):
        print_color("[ERROR] No se encontró el archivo app_launcher.py. No se puede continuar.", Fore.RED, Style.BRIGHT)
        return False
    
    pyinstaller_args.append('app_launcher.py')
    
    print_color(f"[INFO] Ejecutando PyInstaller con argumentos:", Fore.CYAN)
    for arg in pyinstaller_args:
        print_color(f"  {arg}", Fore.CYAN)
        
    try:
        subprocess.run(pyinstaller_args, check=True)
        
        ejecutable = f'dist/{nombre_ejecutable}.exe' if is_windows else f'dist/{nombre_ejecutable}'
        if not os.path.exists(ejecutable):
            print_color(f"\n[ERROR] No se encontró el ejecutable en {ejecutable} después de la compilación.", Fore.RED, Style.BRIGHT)
            return False
            
        print_color("\n[ÉXITO] ¡Compilación completada correctamente!", Fore.GREEN, Style.BRIGHT)
        print_color(f"[INFO] El ejecutable se encuentra en: {os.path.abspath(ejecutable)}", Fore.GREEN)
    except subprocess.CalledProcessError as e:
        print_color(f"\n[ERROR] Error al empaquetar la aplicación: {e}", Fore.RED, Style.BRIGHT)
        return False
    
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
        f.write('    filevers=(1, 0, 0, 0),\n')
        f.write('    prodvers=(1, 0, 0, 0),\n')
        f.write('    mask=0x3f,\n')
        f.write('    flags=0x0,\n')
        f.write('    OS=0x40004,\n')
        f.write('    fileType=0x1,\n')
        f.write('    subtype=0x0,\n')
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

def verificar_dependencias():
    """Verifica que todas las dependencias necesarias estén instaladas"""
    print_color("[INFO] Verificando dependencias necesarias...", Fore.CYAN)
    
    # Dependencias básicas necesarias para el empaquetado
    dependencias_basicas = [
        'flask',
        'werkzeug',
        'jinja2',
        'sqlalchemy',
        'flask-sqlalchemy',
        'colorama',
        'pyinstaller'
    ]
    
    # Dependencias opcionales que pueden causar problemas
    dependencias_opcionales = [
        'pandas',
        'openpyxl',
        'reportlab',
        'XlsxWriter'
    ]
    
    # Dependencias específicas de Windows
    dependencias_windows = []
    if platform.system() == 'Windows':
        dependencias_windows = [
            'pywin32',
            'winshell'
        ]
    
    faltantes = []
    
    # Verificar dependencias básicas
    for dep in dependencias_basicas:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            faltantes.append(dep)
    
    # Instalar dependencias faltantes
    if faltantes:
        print_color(f"[ADVERTENCIA] Faltan las siguientes dependencias básicas: {', '.join(faltantes)}", Fore.YELLOW)
        print_color("[INFO] Instalando dependencias básicas faltantes...", Fore.CYAN)
        
        for dep in faltantes:
            try:
                print_color(f"[INFO] Instalando {dep}...", Fore.CYAN)
                subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)
                print_color(f"[INFO] {dep} instalado correctamente", Fore.GREEN)
            except subprocess.CalledProcessError as e:
                print_color(f"[ERROR] Error al instalar {dep}: {e}", Fore.RED)
                return False
    else:
        print_color("[INFO] Todas las dependencias básicas están instaladas", Fore.GREEN)
    
    # Verificar e instalar dependencias de Windows si es necesario
    if dependencias_windows:
        print_color("[INFO] Verificando dependencias específicas de Windows...", Fore.CYAN)
        for dep in dependencias_windows:
            try:
                __import__(dep.replace('-', '_'))
            except ImportError:
                try:
                    print_color(f"[INFO] Instalando {dep}...", Fore.CYAN)
                    subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)
                    print_color(f"[INFO] {dep} instalado correctamente", Fore.GREEN)
                except subprocess.CalledProcessError as e:
                    print_color(f"[ADVERTENCIA] No se pudo instalar {dep}: {e}", Fore.YELLOW)
                    print_color("[INFO] Continuando sin esta dependencia...", Fore.YELLOW)
    
    # Verificar dependencias opcionales
    print_color("[INFO] Verificando dependencias opcionales...", Fore.CYAN)
    for dep in dependencias_opcionales:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            print_color(f"[ADVERTENCIA] No se encontró {dep}. Algunas funcionalidades podrían no estar disponibles.", Fore.YELLOW)
    
    return True

def instalar_dependencias_windows():
    """Instala dependencias específicas de Windows"""
    if platform.system() != 'Windows':
        return True
        
    print_color("[INFO] Instalando dependencias específicas de Windows...", Fore.CYAN)
    
    try:
        # Intentar instalar pywin32
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pywin32'], check=True)
        print_color("[INFO] pywin32 instalado correctamente", Fore.GREEN)
    except subprocess.CalledProcessError as e:
        print_color(f"[ADVERTENCIA] No se pudo instalar pywin32: {e}", Fore.YELLOW)
        print_color("[INFO] Algunas funcionalidades de Windows podrían no estar disponibles", Fore.YELLOW)
    
    try:
        # Intentar instalar winshell
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'winshell'], check=True)
        print_color("[INFO] winshell instalado correctamente", Fore.GREEN)
    except subprocess.CalledProcessError as e:
        print_color(f"[ADVERTENCIA] No se pudo instalar winshell: {e}", Fore.YELLOW)
        print_color("[INFO] Algunas funcionalidades de Windows podrían no estar disponibles", Fore.YELLOW)
    
    return True

def mostrar_ayuda():
    """Muestra la ayuda del script"""
    print_color("\nOpciones disponibles:", Fore.CYAN, Style.BRIGHT)
    print_color("  --help       : Muestra esta ayuda", Fore.WHITE)
    print_color("  --no-backup  : No crea respaldo de la base de datos", Fore.WHITE)
    print_color("  --include-db : Incluye la base de datos actual en la distribución", Fore.WHITE)
    print_color("  --windows    : Crea un ejecutable para Windows", Fore.WHITE)
    print_color("  --linux      : Crea un ejecutable para Linux", Fore.WHITE)
    print_color("  --macos      : Crea un ejecutable para macOS", Fore.WHITE)
    print_color("  --all        : Crea ejecutables para todas las plataformas soportadas", Fore.WHITE)
    print_color("\nEjemplos de uso:", Fore.CYAN)
    print_color("  python empaquetar_app.py --include-db", Fore.WHITE)
    print_color("  python empaquetar_app.py --windows --include-db", Fore.WHITE)
    print_color("  python empaquetar_app.py --all", Fore.WHITE)
    sys.exit(0)

if __name__ == '__main__':
    print_color("="*60, Fore.BLUE, Style.BRIGHT)
    print_color("COMPILADOR DE GIMNASIO DB - NEURALJIRA_DEV", Fore.BLUE, Style.BRIGHT)
    print_color("="*60, Fore.BLUE, Style.BRIGHT)
    
    if "--help" in sys.argv or "-h" in sys.argv:
        mostrar_ayuda()
    
    print_color("Iniciando proceso de compilación...", Fore.WHITE, Style.BRIGHT)
    
    # Verificar dependencias primero
    if not verificar_dependencias():
        print_color("[ERROR] No se pudieron instalar todas las dependencias necesarias", Fore.RED, Style.BRIGHT)
        sys.exit(1)
    
    try:
        subprocess.run(['pyinstaller', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_color("[ERROR] PyInstaller no está instalado. Instalando...", Fore.YELLOW)
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        except subprocess.CalledProcessError as e:
            print_color(f"[ERROR] No se pudo instalar PyInstaller: {e}", Fore.RED, Style.BRIGHT)
            sys.exit(1)
    
    # Determinar plataformas objetivo
    plataformas = []
    
    if "--windows" in sys.argv:
        plataformas.append("windows")
    if "--linux" in sys.argv:
        plataformas.append("linux")
    if "--macos" in sys.argv:
        plataformas.append("macos")
    if "--all" in sys.argv:
        plataformas = ["windows", "linux", "macos"]
    
    # Si no se especificó ninguna plataforma, usar la actual
    if not plataformas:
        plataformas.append(None)  # None significa plataforma actual
    
    # Crear ejecutables para cada plataforma
    exitos = 0
    fallos = 0
    
    for plataforma in plataformas:
        if crear_ejecutable(plataforma):
            exitos += 1
        else:
            fallos += 1
    
    # Resumen final
    print_color("\n" + "="*60, Fore.BLUE, Style.BRIGHT)
    print_color("RESUMEN DE EMPAQUETADO", Fore.BLUE, Style.BRIGHT)
    print_color("="*60, Fore.BLUE, Style.BRIGHT)
    
    if exitos > 0:
        print_color(f"Se crearon {exitos} ejecutables correctamente.", Fore.GREEN, Style.BRIGHT)
    if fallos > 0:
        print_color(f"Fallaron {fallos} creaciones de ejecutables.", Fore.RED, Style.BRIGHT)
    
    if exitos > 0 and fallos == 0:
        print_color("\n¡Proceso de empaquetado completado con éxito total!", Fore.GREEN, Style.BRIGHT)
        print_color("Todos los ejecutables se encuentran en la carpeta 'dist/'", Fore.WHITE)
    elif exitos > 0:
        print_color("\nEl proceso de empaquetado completó parcialmente con éxito.", Fore.YELLOW, Style.BRIGHT)
        print_color("Los ejecutables generados con éxito se encuentran en la carpeta 'dist/'", Fore.WHITE)
    else:
        print_color("\nEl proceso de empaquetado falló completamente. Revise los mensajes de error anteriores.", Fore.RED, Style.BRIGHT)
        sys.exit(1) 