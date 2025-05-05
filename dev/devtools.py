#!/usr/bin/env python
"""
Herramientas de desarrollo para GimnasioDB

Este módulo centraliza todas las utilidades necesarias para el desarrollo,
pruebas y mantenimiento del sistema GimnasioDB.
"""
import os
import sys
import shutil
import threading
import time
import webbrowser
import logging
import subprocess
import argparse
from datetime import datetime

# Añadir directorio principal al path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Configuración de logging para desarrollo
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(parent_dir, 'dev', 'dev.log'))
    ]
)
logger = logging.getLogger('dev')

def setup_dev_environment():
    """Configura el entorno de desarrollo"""
    # Establecer variables de entorno
    os.environ['APP_MODE'] = 'development'
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Importar configuración de desarrollo
    sys.path.append(os.path.join(parent_dir, 'dev'))
    
    logger.info("Entorno de desarrollo configurado")
    
    # Verificar dependencias
    verify_dependencies()

def verify_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    try:
        # Dependencias principales
        import flask
        import flask_sqlalchemy
        import werkzeug
        import jinja2
        import sqlalchemy
        
        # Dependencias de desarrollo
        import pytest
        import requests
        
        logger.info("✓ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        logger.error(f"✗ Error: Falta la dependencia {e.name}")
        logger.info("Ejecute 'pip install -r requirements-dev.txt' para instalar todas las dependencias")
        return False

def create_dev_database():
    """Crea una nueva base de datos de desarrollo"""
    # Importamos aquí para evitar problemas de importación circular
    from models import db
    
    # Establecer variables de entorno
    os.environ['APP_MODE'] = 'development'
    
    # Importar app_launcher con configuración de desarrollo
    sys.path.insert(0, parent_dir)
    from app_launcher import create_app
    
    dev_app = create_app('development')
    dev_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(parent_dir, 'dev_database.db')
    
    with dev_app.app_context():
        logger.info("Creando base de datos de desarrollo...")
        db.drop_all()
        db.create_all()
        
        # Añadir datos de ejemplo
        from models import Admin, Usuario, Producto
        
        admin = Admin(
            nombre="Administrador Desarrollo",
            usuario="admin",
            rol="administrador"
        )
        admin.set_password("desarrollo")
        
        usuario_test = Usuario(
            nombre="Usuario de Prueba",
            telefono="123456789",
            plan="Mensual",
            fecha_ingreso=datetime.now()
        )
        
        producto_test = Producto(
            nombre="Producto de Prueba",
            descripcion="Producto para entorno de desarrollo",
            precio=10000,
            stock=100,
            categoria="Suplementos"
        )
        
        db.session.add_all([admin, usuario_test, producto_test])
        db.session.commit()
        
        logger.info("Base de datos de desarrollo creada con datos de ejemplo")
        
def backup_production_db():
    """Crea una copia de seguridad de la base de datos de producción"""
    db_path = os.path.join(parent_dir, 'database.db')
    backup_dir = os.path.join(parent_dir, 'backups')
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f'database_backup_{timestamp}.db')
    
    # Verificar que la base de datos existe
    if not os.path.exists(db_path):
        logger.error("Error: No se encontró la base de datos de producción")
        return False
    
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Copia de seguridad creada en: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error al crear copia de seguridad: {e}")
        return False

def clean_build_dirs():
    """Limpia los directorios de construcción"""
    dirs_to_clean = [
        os.path.join(parent_dir, 'build'),
        os.path.join(parent_dir, 'dist'),
        os.path.join(parent_dir, '__pycache__')
    ]
    
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                logger.info(f"Directorio limpiado: {dir_path}")
            except Exception as e:
                logger.error(f"Error al limpiar directorio {dir_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Herramientas de desarrollo para GimnasioDB')
    parser.add_argument('--setup', action='store_true',
                      help='Configurar entorno de desarrollo')
    parser.add_argument('--create-db', action='store_true',
                      help='Crear base de datos de desarrollo')
    parser.add_argument('--backup', action='store_true',
                      help='Crear copia de seguridad de la base de datos de producción')
    parser.add_argument('--clean', action='store_true',
                      help='Limpiar directorios de construcción')
    
    args = parser.parse_args()
    
    # Si no se proporcionan argumentos, mostrar ayuda
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    
    # Ejecutar acciones según argumentos
    if args.setup:
        setup_dev_environment()
    
    if args.create_db:
        create_dev_database()
    
    if args.backup:
        backup_production_db()
    
    if args.clean:
        clean_build_dirs() 