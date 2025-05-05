#!/usr/bin/env python
"""
Lanzador unificado de la aplicación GimnasioDB
Este script puede usarse tanto para desarrollo como para producción, 
y reemplaza a los scripts individuales app.py, run_app.py y standalone_app.py
"""
from flask import Flask, request, jsonify, url_for, send_from_directory
from models import db
from routes import main  # Importar el blueprint principal de la nueva estructura
import webbrowser
import os
import sys
import threading
import time
import signal
import logging
import io
import argparse
import datetime
import shutil
import platform
import pytz  # Importación de pytz para manejo de zonas horarias

# Configuración global de zona horaria Colombia
ZONA_HORARIA_COLOMBIA = pytz.timezone('America/Bogota')

# La configuración antigua se mantiene para sistemas que soportan tzset
os.environ['TZ'] = 'America/Bogota'
try:
    time.tzset()  # En Windows esta función no existe
except AttributeError:
    pass

# Clase para redirigir salida en modo empaquetado
class NullIO(io.IOBase):
    def write(self, *args, **kwargs):
        pass
    def read(self, *args, **kwargs):
        return ''
    def flush(self, *args, **kwargs):
        pass

def init_database(app, fresh=False):
    """
    Inicializa o actualiza la base de datos
    
    Args:
        app: Aplicación Flask
        fresh: Si es True, recreará la base de datos
    """
    # Crear respaldo antes de modificar la base de datos
    crear_respaldo_automatico()
    
    with app.app_context():
        print(f"Inicializando base de datos. Fresh: {fresh}")  # Depuración
        if fresh:
            # Recrear la base de datos desde cero
            print("ADVERTENCIA: Recreando la base de datos. ¡Todos los datos existentes se perderán!")  # Depuración
            db.drop_all()
            db.create_all()
            print("Base de datos recreada.")
            # Verificar y crear administrador por defecto después de recrear la BD
            verificar_admin_por_defecto()
        else:
            # Solo crear las tablas si no existen
            print("Inicializando la base de datos - Solo creando tablas si no existen")  # Depuración
            db.create_all()
            print("Base de datos inicializada.")
            # Verificar y crear administrador por defecto
            verificar_admin_por_defecto()

def crear_respaldo_automatico():
    """
    Crea un respaldo automático de la base de datos
    """
    # Importar la función para obtener la fecha con zona horaria de Colombia
    from models import datetime_colombia
    
    # Determinar la ruta de la base de datos según el modo de ejecución
    if getattr(sys, 'frozen', False):
        # Modo ejecutable
        base_dir = os.path.expanduser('~')
        app_data_dir = os.path.join(base_dir, 'GimnasioDB_Data')
        db_path = os.path.join(app_data_dir, 'database.db')
        backup_dir = os.path.join(app_data_dir, 'backups')
    else:
        # Modo desarrollo
        db_path = 'database.db'
        backup_dir = 'backups'
    
    # Si no existe el archivo de base de datos, no hay nada que respaldar
    if not os.path.exists(db_path):
        print(f"No se encontró la base de datos en {db_path}, no se creará respaldo.")
        return
        
    # Crear directorio de respaldos si no existe
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Generar nombre de archivo con fecha
    fecha = datetime_colombia().strftime('%Y%m%d_%H%M%S')
    archivo_respaldo = os.path.join(backup_dir, f'database_{fecha}.db')
    
    # Copiar la base de datos
    try:
        shutil.copy2(db_path, archivo_respaldo)
        print(f"Respaldo creado: {archivo_respaldo}")
        
        # Limpiar respaldos antiguos (mantener solo los últimos 7)
        respaldos = sorted([f for f in os.listdir(backup_dir) if f.startswith('database_')])
        if len(respaldos) > 7:
            for archivo in respaldos[:-7]:
                ruta_completa = os.path.join(backup_dir, archivo)
                os.remove(ruta_completa)
                print(f"Respaldo antiguo eliminado: {archivo}")
    except Exception as e:
        print(f"Error al crear respaldo: {str(e)}")

def verificar_admin_por_defecto():
    """
    Verifica si existe al menos un administrador en el sistema.
    Si no existe ninguno, crea un administrador por defecto.
    """
    from models import Admin
    
    # Verificar si hay administradores
    admin_count = Admin.query.count()
    
    if admin_count == 0:
        # No hay administradores, crear uno por defecto
        print("No se encontraron administradores. Creando administrador por defecto...")
        admin = Admin(
            nombre="Administrador",
            usuario="admin",
            rol="administrador"
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Administrador por defecto creado: usuario='admin', contraseña='admin123'")
    else:
        print(f"Se encontraron {admin_count} administradores en el sistema.")

def migrar_datos_existentes(origen, destino):
    """
    Migra la base de datos desde la ubicación original a la nueva ubicación
    si es necesario
    """
    # Si el destino ya existe, no necesitamos migrar nada
    if os.path.exists(destino):
        return False
        
    # Si el origen no existe, no hay nada que migrar
    if not os.path.exists(origen):
        return False
    
    # Crear el directorio destino si no existe
    destino_dir = os.path.dirname(destino)
    if not os.path.exists(destino_dir):
        os.makedirs(destino_dir)
    
    try:
        # Copiar la base de datos
        shutil.copy2(origen, destino)
        print(f"Base de datos migrada de {origen} a {destino}")
        return True
    except Exception as e:
        print(f"Error al migrar la base de datos: {str(e)}")
        return False

def crear_acceso_directo_datos(ruta_datos):
    """
    Crea un acceso directo en el escritorio a la carpeta de datos
    para facilitar el acceso y las copias de seguridad
    """
    if not platform.system() == 'Windows':
        return False
        
    try:
        import winshell
        from win32com.client import Dispatch
        
        # Obtener ruta al escritorio
        desktop = winshell.desktop()
        
        # Crear acceso directo
        shortcut_path = os.path.join(desktop, "GimnasioDB - Datos.lnk")
        
        # No crear si ya existe
        if os.path.exists(shortcut_path):
            return True
            
        # Crear el acceso directo
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = ruta_datos
        shortcut.WorkingDirectory = ruta_datos
        shortcut.Description = "Carpeta de datos de GimnasioDB"
        shortcut.save()
        
        return True
    except ImportError:
        print("No se pudo crear acceso directo: winshell o pywin32 no instalados")
        return False
    except Exception as e:
        print(f"Error al crear acceso directo: {str(e)}")
        return False

def resource_path(relative_path):
    """
    Obtiene la ruta absoluta a un recurso, funciona tanto para desarrollo 
    como cuando la aplicación está empaquetada por PyInstaller
    """
    try:
        # PyInstaller crea un directorio temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class CustomStaticFlask(Flask):
    """Clase personalizada de Flask para manejar archivos estáticos en modo empaquetado"""
    def __init__(self, *args, **kwargs):
        super(CustomStaticFlask, self).__init__(*args, **kwargs)
        self._static_folder = None
        
    @property
    def static_folder(self):
        if self._static_folder:
            return self._static_folder
        return resource_path('static')
        
    @static_folder.setter
    def static_folder(self, value):
        self._static_folder = value
    
    def get_send_file_max_age(self, name):
        """Reduce el tiempo de caché para desarrollo y elimina para producción"""
        if getattr(sys, 'frozen', False):
            return 0  # No usar caché en modo empaquetado
        return super(CustomStaticFlask, self).get_send_file_max_age(name)

def create_app(test_config=None):
    """Crea y configura la aplicación Flask"""
    # Usar nuestra clase personalizada en lugar de Flask directamente
    app = CustomStaticFlask(__name__, instance_relative_config=True)
    
    # Determinar la ruta de la base de datos
    if getattr(sys, 'frozen', False):
        # Si estamos en un ejecutable empaquetado por PyInstaller
        # Usar la carpeta del usuario, que siempre es accesible
        base_dir = os.path.expanduser('~')
        app_data_dir = os.path.join(base_dir, 'GimnasioDB_Data')
        
        # Crear directorio si no existe
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)
            
        db_path = os.path.join(app_data_dir, 'database.db')
        
        # Verificar si necesitamos migrar datos desde la ubicación actual
        ruta_actual = os.path.join(os.getcwd(), 'database.db')
        migrar_datos_existentes(ruta_actual, db_path)
        
        # Intentar crear acceso directo
        try:
            crear_acceso_directo_datos(app_data_dir)
        except Exception as e:
            print(f"Nota: No se pudo crear acceso directo a los datos: {str(e)}")
        
        db_uri = f'sqlite:///{db_path}'
        print(f"Modo ejecutable: Guardando base de datos en: {db_path}")
    else:
        # Si estamos en desarrollo, usar la ubicación relativa normal
        db_uri = 'sqlite:///database.db'
        print(f"Modo desarrollo: Guardando base de datos en directorio actual")
    
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DEBUG=True,  # Configurar modo debug
        SEND_FILE_MAX_AGE_DEFAULT=0  # Evitar caché de archivos estáticos
    )
    
    print(f"Configurando conexión a la base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Inicializar la base de datos
    db.init_app(app)
    
    # Registrar el blueprint principal
    app.register_blueprint(main)
    
    # Añadir variables de contexto globales
    @app.context_processor
    def inject_debug():
        return dict(debug=app.debug)
    
    # Crear rutas especiales para acceder a recursos estáticos de forma más fiable
    @app.route('/static_secure/<path:filename>')
    def static_secure(filename):
        """Ruta alternativa para servir archivos estáticos en modo empaquetado"""
        if getattr(sys, 'frozen', False):
            # En modo empaquetado, usar resource_path para la ruta correcta
            static_dir = resource_path('static')
            return send_from_directory(static_dir, filename)
        return send_from_directory(app.static_folder, filename)
        
    # Añadir función para recursos estáticos accesible en plantillas
    @app.context_processor
    def inject_resource_functions():
        def static_resource(filename):
            """Función para acceder a recursos estáticos desde las plantillas"""
            if getattr(sys, 'frozen', False):
                return url_for('static_secure', filename=filename)
            return url_for('static', filename=filename)
        return dict(static_resource=static_resource)
    
    # Crear tabla si no existe
    with app.app_context():
        try:
            db.create_all()
            # Verificar la conexión a la base de datos
            resultado = db.session.execute('SELECT name FROM sqlite_master WHERE type="table";').fetchall()
            print(f"Tablas en la base de datos: {[r[0] for r in resultado]}")
        except Exception as e:
            print(f"ERROR al conectar con la base de datos: {str(e)}")
    
    # Ruta para cerrar la aplicación
    @app.route('/cerrar-aplicacion', methods=['POST'])
    def cerrar_aplicacion():
        threading.Thread(target=lambda: shutdown_app(app)).start()
        return jsonify({"status": "cerrando"})
    
    return app

def open_browser(quiet=False):
    """Abre el navegador después de un breve retardo"""
    # Verificar si ya se abrió el navegador en esta ejecución
    # para evitar duplicados durante recargas en modo debug
    if os.environ.get('BROWSER_OPENED') == '1':
        return
        
    time.sleep(2)
    try:
        webbrowser.open('http://127.0.0.1:5000')
        if not quiet:
            print("Abriendo la aplicación en el navegador...")
        # Marcar que ya se abrió el navegador
        os.environ['BROWSER_OPENED'] = '1'
    except Exception as e:
        if not quiet:
            print(f"Error al abrir el navegador: {e}")
            print("Por favor, abra manualmente http://127.0.0.1:5000 en su navegador")

def shutdown_app(app):
    """Función para apagar el servidor desde un endpoint"""
    print("Cerrando aplicación por solicitud del usuario...")
    time.sleep(1)  # Esperar para que la respuesta se envíe
    try:
        # En Windows, usar un método diferente para terminar el proceso
        if platform.system() == 'Windows':
            import subprocess
            current_pid = os.getpid()
            subprocess.call(['taskkill', '/F', '/PID', str(current_pid)])
        else:
            # En Linux/Mac, usar la señal SIGTERM
            os.kill(os.getpid(), signal.SIGTERM)
    except Exception as e:
        print(f"Error al cerrar la aplicación: {str(e)}")
        sys.exit(1)  # Forzar cierre con código de error

def configure_for_production(app):
    """Configura la app para modo producción"""
    # Desactivar logs y mensajes de consola
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    log.disabled = True
    app.logger.disabled = True
    
    # Desactivar mensajes de Flask
    import click
    click.echo = lambda *args, **kwargs: None
    
    # Configurar rutas estáticas correctamente para modo empaquetado
    # usando resource_path para obtener la ruta real de los directorios
    if getattr(sys, 'frozen', False):
        app.template_folder = resource_path('templates')
        app.static_folder = resource_path('static')
        
        # Configurar opciones para un mejor rendimiento en producción
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # No usar caché en producción
        app.config['TEMPLATES_AUTO_RELOAD'] = False
        app.config['EXPLAIN_TEMPLATE_LOADING'] = False

def verificar_tablas_medidas(app):
    """
    Verifica que las tablas esenciales existen en la base de datos
    y tienen la estructura correcta.
    """
    with app.app_context():
        try:
            # Verificar tabla medidas_corporales
            estructura = db.session.execute('PRAGMA table_info(medidas_corporales);').fetchall()
            print(f"Estructura de la tabla medidas_corporales:")
            for columna in estructura:
                print(f"  {columna[1]} ({columna[2]})")
            
            # Contar registros en la tabla
            count = db.session.execute('SELECT COUNT(*) FROM medidas_corporales;').scalar()
            print(f"Registros en la tabla medidas_corporales: {count}")
            
            # Si hay registros, mostrar uno de ejemplo
            if count > 0:
                ejemplo = db.session.execute('SELECT * FROM medidas_corporales LIMIT 1;').fetchone()
                print(f"Ejemplo de registro: {ejemplo}")
        except Exception as e:
            print(f"Error al verificar tablas: {str(e)}")

def verificar_base_datos():
    """
    Herramienta de diagnóstico para verificar la ubicación y estado de la base de datos.
    Útil para resolver problemas de persistencia de datos.
    """
    print("\n=== VERIFICACIÓN DE BASE DE DATOS GIMNASIO DB ===\n")
    
    # Determinar si estamos en modo ejecutable
    modo_ejecucion = "Ejecutable" if getattr(sys, 'frozen', False) else "Desarrollo"
    print(f"Modo de ejecución detectado: {modo_ejecucion}")
    
    # Mostrar mensaje importante sobre persistencia de datos
    print("\nIMPORTANTE:")
    print("- En modo EJECUTABLE, los datos se guardan permanentemente en la carpeta del usuario.")
    print("- En modo DESARROLLO, los datos se guardan en el directorio actual del proyecto.")
    print("- Si cambias de un modo a otro, deberás copiar manualmente la base de datos.")
    
    # Obtener rutas posibles
    rutas = []
    
    # 1. Ruta en modo desarrollo (carpeta actual)
    ruta_dev = os.path.join(os.getcwd(), 'database.db')
    if os.path.exists(ruta_dev):
        rutas.append({
            'tipo': 'Desarrollo',
            'ruta': ruta_dev,
            'existe': True,
            'tamaño': os.path.getsize(ruta_dev) / 1024,  # KB
        })
    else:
        rutas.append({
            'tipo': 'Desarrollo',
            'ruta': ruta_dev,
            'existe': False,
            'tamaño': 0,
        })
    
    # 2. Ruta en modo ejecutable (carpeta del usuario)
    base_dir = os.path.expanduser('~')
    app_data_dir = os.path.join(base_dir, 'GimnasioDB_Data')
    ruta_exe = os.path.join(app_data_dir, 'database.db')
    
    if os.path.exists(ruta_exe):
        rutas.append({
            'tipo': 'Ejecutable',
            'ruta': ruta_exe,
            'existe': True,
            'tamaño': os.path.getsize(ruta_exe) / 1024,  # KB
        })
    else:
        rutas.append({
            'tipo': 'Ejecutable',
            'ruta': ruta_exe,
            'existe': False,
            'tamaño': 0,
        })
    
    print("\nPOSIBLES UBICACIONES DE LA BASE DE DATOS:")
    for ruta in rutas:
        estado = "✓ EXISTE" if ruta['existe'] else "✗ NO EXISTE"
        print(f"  {ruta['tipo']}: {ruta['ruta']} - {estado}")
        if ruta['existe']:
            print(f"    Tamaño: {ruta['tamaño']:.2f} KB")
    
    # Analizar las bases de datos existentes
    print("\nANÁLISIS DE CONTENIDO:")
    
    for ruta in rutas:
        if ruta['existe']:
            print(f"\n> Base de datos en modo {ruta['tipo']}:")
            try:
                # Conectar a la base de datos
                import sqlite3
                conn = sqlite3.connect(ruta['ruta'])
                cursor = conn.cursor()
                
                # Obtener lista de tablas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tablas = [row[0] for row in cursor.fetchall()]
                
                # Obtener cantidad de registros por tabla
                estadisticas = {}
                for tabla in tablas:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla};")
                    estadisticas[tabla] = cursor.fetchone()[0]
                
                # Verificar específicamente medidas_corporales
                medidas_info = None
                if 'medidas_corporales' in tablas:
                    cursor.execute("SELECT id, usuario_id, fecha, peso FROM medidas_corporales ORDER BY fecha DESC LIMIT 5;")
                    ultimas_medidas = cursor.fetchall()
                    
                    medidas_info = {
                        'total': estadisticas.get('medidas_corporales', 0),
                        'ultimas': ultimas_medidas
                    }
                
                conn.close()
                
                print(f"  Tablas encontradas: {', '.join(tablas)}")
                print("\n  Registros por tabla:")
                for tabla, cantidad in estadisticas.items():
                    print(f"    {tabla}: {cantidad} registros")
                
                if medidas_info:
                    print("\n  Información de medidas corporales:")
                    print(f"    Total de medidas: {medidas_info['total']}")
                    print("    Últimas medidas registradas:")
                    for medida in medidas_info['ultimas']:
                        print(f"      ID: {medida[0]}, Usuario: {medida[1]}, Fecha: {medida[2]}, Peso: {medida[3]}")
            except Exception as e:
                print(f"  No se pudo analizar la base de datos: {str(e)}")
    
    print("\n=== VERIFICACIÓN COMPLETADA ===")

def actualizar_estructura_db(app):
    """
    Verificar y actualizar la estructura de la base de datos si es necesario
    """
    print("Verificando estructura de la base de datos...")
    with app.app_context():
        try:
            # Verificar si la tabla objetivo_personal tiene la columna estado
            has_estado = False
            try:
                # Verificar existencia de la columna estado
                result = db.session.execute('PRAGMA table_info(objetivo_personal);').fetchall()
                for column in result:
                    if column[1] == 'estado':
                        has_estado = True
                        break
                
                if not has_estado:
                    print("Añadiendo columna 'estado' a tabla objetivo_personal...")
                    db.session.execute('ALTER TABLE objetivo_personal ADD COLUMN estado VARCHAR(20) DEFAULT "En progreso";')
                    db.session.commit()
                    print("Columna 'estado' añadida correctamente")
            except Exception as e:
                print(f"Error al verificar/añadir columna 'estado': {str(e)}")
                
            # Verificar si la tabla objetivo_personal tiene la columna fecha_completado
            has_fecha_completado = False
            try:
                # Verificar existencia de la columna fecha_completado
                result = db.session.execute('PRAGMA table_info(objetivo_personal);').fetchall()
                for column in result:
                    if column[1] == 'fecha_completado':
                        has_fecha_completado = True
                        break
                
                if not has_fecha_completado:
                    print("Añadiendo columna 'fecha_completado' a tabla objetivo_personal...")
                    db.session.execute('ALTER TABLE objetivo_personal ADD COLUMN fecha_completado DATE;')
                    db.session.commit()
                    print("Columna 'fecha_completado' añadida correctamente")
            except Exception as e:
                print(f"Error al verificar/añadir columna 'fecha_completado': {str(e)}")
                
        except Exception as e:
            print(f"Error al actualizar estructura de la base de datos: {str(e)}")

if __name__ == '__main__':
    # Asegurarnos de que la variable de entorno no exista al inicio
    if 'BROWSER_OPENED' in os.environ:
        del os.environ['BROWSER_OPENED']
        
    parser = argparse.ArgumentParser(description='Ejecuta la aplicación GimnasioDB')
    parser.add_argument('--mode', choices=['development', 'production'], default='production',
                        help='Modo de ejecución: development o production')
    parser.add_argument('--no-browser', action='store_true', 
                        help='No abrir automáticamente el navegador')
    parser.add_argument('--host', default='127.0.0.1',
                        help='Host en el que se ejecutará el servidor')
    parser.add_argument('--port', type=int, default=5000,
                        help='Puerto en el que se ejecutará el servidor')
    parser.add_argument('--debug', action='store_true',
                        help='Habilitar modo de depuración')
    parser.add_argument('--fresh-db', action='store_true',
                        help='Recrear la base de datos desde cero')
    parser.add_argument('--verify-db', action='store_true',
                        help='Verificar estado de la base de datos')
    
    args = parser.parse_args()
    
    # Verificar la base de datos si se solicita
    if args.verify_db:
        verificar_base_datos()
        sys.exit(0)
    
    # En modo empaquetado, siempre usar producción
    if getattr(sys, 'frozen', False):
        args.mode = 'production'
        
        # Redirigir salida en modo empaquetado para evitar errores
        # pero no en modo desarrollo para mantener la depuración
        if args.mode == 'production' and not args.debug:
            sys.stdout = NullIO()
            sys.stderr = NullIO()
    
    # Crear app
    app = create_app(args.mode)
    
    # Si se solicita, recrear la base de datos
    if args.fresh_db:
        print("\n¡ADVERTENCIA! Se recreará toda la base de datos y se perderán TODOS los datos existentes.")
        confirmacion = input("¿Está seguro que desea continuar? (s/n): ")
        if confirmacion.lower() == "s":
            init_database(app, fresh=True)
            print("Base de datos recreada correctamente.")
        else:
            print("Operación de recreación de base de datos cancelada.")
            args.fresh_db = False
    
    # Verificar tablas de medidas
    verificar_tablas_medidas(app)
    
    # Verificar y actualizar estructura de la base de datos
    actualizar_estructura_db(app)
    
    # Configuración para producción
    if args.mode == 'production' or getattr(sys, 'frozen', False):
        configure_for_production(app)
    
    # Abrir navegador
    if not args.no_browser:
        threading.Thread(target=lambda: open_browser(quiet=args.mode == 'production')).start()
    
    # Ejecutar aplicación
    app.run(
        debug=args.debug and args.mode == 'development',
        use_reloader=args.debug and args.mode == 'development',
        host=args.host,
        port=args.port
    ) 