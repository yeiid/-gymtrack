#!/usr/bin/env python
"""
Archivo de despliegue para Render
Desarrollado por: YEIFRAN HERNANDEZ
NEURALJIRA_DEV - Visión inteligente para gestión de gimnasios
"""
from flask import Flask
from models import db

def create_app():
    """Crea y configura la aplicación Flask para entorno de producción"""
    app = Flask(__name__)
    
    # Configuración para entorno de producción
    app.config.from_mapping(
        SECRET_KEY='prod_key_secure_8e7a1b94c3d2',
        SQLALCHEMY_DATABASE_URI='sqlite:///database.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DEBUG=False
    )
    
    # Inicializar la base de datos
    db.init_app(app)
    
    # Registrar el blueprint principal
    from routes import main
    app.register_blueprint(main)
    
    # Añadir variables de contexto globales
    @app.context_processor
    def inject_debug():
        return dict(debug=False)
    
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
    
    return app

# Instancia de la aplicación para Gunicorn
app = create_app()

if __name__ == '__main__':
    # Este bloque solo se ejecuta cuando se corre directamente este archivo
    # No se usa en producción con Gunicorn
    app.run(host='0.0.0.0', port=8080) 