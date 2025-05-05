#!/usr/bin/env python
"""
Lanzador de desarrollo para GimnasioDB
Este script permite ejecutar la aplicación en modo desarrollo con configuración específica
"""
import os
import sys
import threading
import time
import webbrowser

# Añadir directorio principal al path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Establecer variables de entorno para desarrollo
os.environ['APP_MODE'] = 'development'
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Importar después de configurar variables de entorno
import config_dev  # Importa configuración específica de desarrollo
from flask import Flask
from models import db
from routes import main

def create_dev_app():
    """Crea la aplicación Flask en modo desarrollo"""
    app = Flask(__name__, 
                template_folder=os.path.join(parent_dir, 'templates'),
                static_folder=os.path.join(parent_dir, 'static'))
    
    # Usar configuración de desarrollo
    app.config.from_object('dev.config_dev')
    
    # Inicializar base de datos
    db.init_app(app)
    
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
        
    # Registrar rutas
    app.register_blueprint(main)
    
    @app.route('/debug-info')
    def debug_info():
        """Ruta adicional solo para desarrollo que muestra información de depuración"""
        from flask import jsonify
        import platform
        
        debug_data = {
            'app_config': {k: str(v) for k, v in app.config.items() if k not in ['SECRET_KEY']},
            'environment': dict(os.environ),
            'platform': platform.platform(),
            'python_version': sys.version,
            'sys_path': sys.path
        }
        
        return jsonify(debug_data)
    
    return app

def open_browser():
    """Abre el navegador después de un breve retardo"""
    time.sleep(2)
    try:
        webbrowser.open('http://127.0.0.1:5000')
        print("Abriendo la aplicación en el navegador...")
    except Exception as e:
        print(f"Error al abrir el navegador: {e}")
        print("Por favor, abra manualmente http://127.0.0.1:5000 en su navegador")

if __name__ == "__main__":
    print("=== Iniciando GimnasioDB en modo DESARROLLO ===")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists(os.path.join(parent_dir, "app_launcher.py")):
        print("Error: Este script debe ejecutarse desde el directorio dev/")
        sys.exit(1)
    
    # Crear aplicación
    app = create_dev_app()
    
    # Iniciar navegador en un hilo separado
    threading.Thread(target=open_browser).start()
    
    # Ejecutar la aplicación con reloader habilitado
    app.run(debug=True, use_reloader=True, host='127.0.0.1', port=5000) 