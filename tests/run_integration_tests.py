#!/usr/bin/env python
"""
Script para ejecutar pruebas de integración de la aplicación GimnasioDB
"""
import os
import sys
import time
import unittest
import pytest
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('integration_tests')

# Añadir directorio principal al path
parent_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(parent_dir)
sys.path.append(root_dir)

# Establecer modo de prueba
os.environ['FLASK_ENV'] = 'testing'

def run_unittest_tests():
    """Ejecuta todas las pruebas unittest en el directorio tests/"""
    logger.info("=== Ejecutando pruebas unitarias de integración ===")
    
    # Descubrir todas las pruebas en el directorio tests/
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(
        start_dir=parent_dir,
        pattern='test_*.py'
    )
    
    # Ejecutar las pruebas
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Mostrar resumen
    logger.info(f"Pruebas ejecutadas: {result.testsRun}")
    logger.info(f"Pruebas fallidas: {len(result.failures)}")
    logger.info(f"Pruebas con error: {len(result.errors)}")
    
    return result.wasSuccessful()

def check_test_environment():
    """Verifica que el entorno de pruebas esté configurado correctamente"""
    logger.info("Verificando entorno de pruebas...")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists(os.path.join(root_dir, "app_launcher.py")):
        logger.error("Error: Este script debe ejecutarse desde el directorio de pruebas")
        return False
    
    # Verificar que existe la nueva estructura de directorios
    required_dirs = [
        os.path.join(root_dir, "app"),
        os.path.join(root_dir, "app", "core"),
        os.path.join(root_dir, "app", "database"),
        os.path.join(root_dir, "app", "services"),
        os.path.join(root_dir, "app", "routes")
    ]
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            logger.error(f"Error: No se encontró el directorio {directory}")
            return False
    
    # Verificar dependencias
    try:
        import flask
        import flask_sqlalchemy
        import werkzeug
        logger.info("✓ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        logger.error(f"✗ Error: Falta la dependencia {e.name}")
        logger.info("Ejecute 'pip install -r requirements.txt' para instalar todas las dependencias")
        return False

def generate_test_report(success):
    """Genera un reporte de las pruebas ejecutadas"""
    report = """
==================================
   REPORTE DE PRUEBAS INTEGRACIÓN
==================================

Estado general: {}

==================================
""".format("PASARON" if success else "FALLARON")
    
    logger.info(report)
    
    # Guardar reporte en un archivo
    report_path = os.path.join(parent_dir, 'integration_test_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Reporte guardado en {report_path}")
    
    return success

if __name__ == "__main__":
    # Verificar entorno
    if not check_test_environment():
        logger.error("El entorno de pruebas no está configurado correctamente")
        sys.exit(1)
    
    # Ejecutar pruebas unitarias
    unit_success = run_unittest_tests()
    
    # Generar reporte
    success = generate_test_report(unit_success)
    
    # Devolver código de salida adecuado
    sys.exit(0 if success else 1) 