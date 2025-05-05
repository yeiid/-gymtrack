#!/usr/bin/env python
"""
Script para ejecutar todas las pruebas de GimnasioDB
"""
import os
import sys
import unittest
import pytest
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tests')

# Añadir directorio principal al path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Establecer modo de desarrollo
os.environ['APP_MODE'] = 'development'
os.environ['FLASK_ENV'] = 'development'
os.environ['TEST_MODE'] = 'True'

def run_unittest_tests():
    """Ejecuta todas las pruebas unittest en el directorio dev/"""
    logger.info("=== Ejecutando pruebas unitarias ===")
    
    # Descubrir todas las pruebas en el directorio dev/
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(
        start_dir=os.path.dirname(os.path.abspath(__file__)),
        pattern='test_*.py'
    )
    
    # Ejecutar las pruebas
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return result.wasSuccessful()

def run_pytest_tests():
    """Ejecuta todas las pruebas pytest en el directorio dev/"""
    logger.info("=== Ejecutando pruebas con pytest ===")
    
    # Ejecutar pytest en el directorio dev/
    test_dir = os.path.dirname(os.path.abspath(__file__))
    result = pytest.main([
        test_dir,
        '-v',
        '--cov=../models',
        '--cov=../routes',
        '--cov-report=term'
    ])
    
    return result == 0

def check_test_environment():
    """Verifica que el entorno de pruebas esté configurado correctamente"""
    logger.info("Verificando entorno de pruebas...")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists(os.path.join(parent_dir, "app_launcher.py")):
        logger.error("Error: Este script debe ejecutarse desde el directorio dev/")
        return False
    
    # Verificar dependencias
    try:
        import flask
        import flask_sqlalchemy
        import werkzeug
        import pytest
        import requests
        logger.info("✓ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        logger.error(f"✗ Error: Falta la dependencia {e.name}")
        logger.info("Ejecute 'pip install -r dev/requirements-dev.txt' para instalar todas las dependencias")
        return False

def setup_test_database():
    """Configura una base de datos temporal para pruebas"""
    from flask import Flask
    from models import db
    
    # Crear aplicación de prueba
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar base de datos
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
    return True

def generate_test_report(unit_success, pytest_success):
    """Genera un reporte de las pruebas ejecutadas"""
    report = """
==================================
    REPORTE DE PRUEBAS GIMNASIO DB
==================================

Pruebas unitarias: {}
Pruebas pytest: {}

==================================
""".format(
        "PASARON" if unit_success else "FALLARON", 
        "PASARON" if pytest_success else "FALLARON"
    )
    
    logger.info(report)
    
    # Guardar reporte en un archivo
    report_path = os.path.join(parent_dir, 'dev', 'test_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Reporte guardado en {report_path}")
    
    return unit_success and pytest_success

if __name__ == "__main__":
    # Verificar entorno
    if not check_test_environment():
        sys.exit(1)
    
    # Configurar base de datos de prueba
    if not setup_test_database():
        logger.error("Error al configurar la base de datos de prueba")
        sys.exit(1)
    
    # Ejecutar pruebas unitarias
    unit_success = run_unittest_tests()
    
    # Ejecutar pruebas pytest
    pytest_success = run_pytest_tests()
    
    # Generar reporte
    all_tests_passed = generate_test_report(unit_success, pytest_success)
    
    # Devolver código de salida adecuado
    sys.exit(0 if all_tests_passed else 1) 