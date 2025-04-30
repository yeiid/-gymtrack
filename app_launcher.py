#!/usr/bin/env python
"""
Lanzador unificado de la aplicación GimnasioDB
Este script puede usarse tanto para desarrollo como para producción, 
y reemplaza a los scripts individuales app.py, run_app.py y standalone_app.py
"""
from flask import Flask, request, jsonify
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

# Establecer la zona horaria local
os.environ['TZ'] = 'America/Bogota'
# Asegurar que datetime.now() use la zona horaria local
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
        if fresh:
            # Recrear la base de datos desde cero
            db.drop_all()
            db.create_all()
            print("Base de datos recreada.")
            # Verificar y crear administrador por defecto después de recrear la BD
            verificar_admin_por_defecto()
        else:
            # Solo crear las tablas si no existen
            db.create_all()
            print("Base de datos inicializada.")
            # Verificar y crear administrador por defecto
            verificar_admin_por_defecto()

def crear_respaldo_automatico():
    """
    Crea un respaldo automático de la base de datos
    """
    # Si no existe database.db, no hay nada que respaldar
    if not os.path.exists('database.db'):
        return
        
    # Crear directorio de respaldos si no existe
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    # Generar nombre de archivo con fecha
    fecha = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    archivo_respaldo = f'backups/database_{fecha}.db'
    
    # Copiar la base de datos
    try:
        shutil.copy2('database.db', archivo_respaldo)
        print(f"Respaldo creado: {archivo_respaldo}")
        
        # Limpiar respaldos antiguos (mantener solo los últimos 7)
        respaldos = sorted([f for f in os.listdir('backups') if f.startswith('database_')])
        if len(respaldos) > 7:
            for archivo in respaldos[:-7]:
                ruta_completa = os.path.join('backups', archivo)
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

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///database.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DEBUG=True  # Configurar modo debug
    )
    
    # Inicializar la base de datos
    db.init_app(app)
    
    # Registrar el blueprint principal
    from routes import main
    app.register_blueprint(main)
    
    # Añadir variables de contexto globales
    @app.context_processor
    def inject_debug():
        return dict(debug=app.debug)
    
    # Crear tabla si no existe
    with app.app_context():
        db.create_all()
    
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

def shutdown_app(app):
    """Función para apagar el servidor desde un endpoint"""
    time.sleep(1)  # Esperar para que la respuesta se envíe
    os.kill(os.getpid(), signal.SIGTERM)

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
    
    # Configurar rutas estáticas
    app.template_folder = resource_path('templates')
    app.static_folder = resource_path('static')

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
    
    args = parser.parse_args()
    
    # En modo empaquetado, siempre usar producción
    if getattr(sys, 'frozen', False):
        args.mode = 'production'
        
        # Redirigir salida en modo empaquetado
        sys.stdout = NullIO()
        sys.stderr = NullIO()
    
    # Crear app
    app = create_app(args.mode)
    
    # Si se solicita, recrear la base de datos
    if args.fresh_db:
        init_database(app, fresh=True)
    
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