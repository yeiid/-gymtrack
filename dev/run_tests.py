#!/usr/bin/env python
"""
Script para ejecutar pruebas en GimnasioDB
"""
import os
import sys
import unittest
import time
import requests
import threading
import subprocess
from urllib.error import URLError

# Añadir directorio principal al path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Establecer modo de desarrollo
os.environ['APP_MODE'] = 'development'
os.environ['FLASK_ENV'] = 'development'
os.environ['TEST_MODE'] = 'True'

# Importar después de configurar variables de entorno
import config_dev
from flask import Flask
from models import db, Usuario, Admin, Producto
from routes import main

class TestGimnasioDB(unittest.TestCase):
    """Clase base para pruebas de GimnasioDB"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial antes de todas las pruebas"""
        print("\n=== Iniciando pruebas de GimnasioDB ===")
        
        # Crear aplicación de prueba
        cls.app = Flask(__name__, 
                    template_folder=os.path.join(parent_dir, 'templates'),
                    static_folder=os.path.join(parent_dir, 'static'))
        
        # Configurar para pruebas
        cls.app.config.from_object('dev.config_dev')
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Usar base de datos en memoria
        
        # Inicializar base de datos
        db.init_app(cls.app)
        cls.app.register_blueprint(main)
        
        with cls.app.app_context():
            # Crear tablas
            db.create_all()
            
            # Añadir datos de prueba
            admin = Admin(
                nombre="Admin Prueba",
                usuario="admin_test",
                rol="administrador"
            )
            admin.set_password("test123")
            
            usuario = Usuario(
                nombre="Usuario Prueba",
                telefono="123456789",
                plan="Mensual"
            )
            
            producto = Producto(
                nombre="Producto Prueba",
                descripcion="Descripción de prueba",
                precio=10000,
                stock=10,
                categoria="Suplementos"
            )
            
            db.session.add_all([admin, usuario, producto])
            db.session.commit()
        
        # Iniciar el servidor en un proceso separado
        cls.server_thread = threading.Thread(target=cls._run_test_server, args=(cls.app,))
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Esperar a que el servidor esté listo
        cls._wait_for_server()
    
    @classmethod
    def _run_test_server(cls, app):
        """Ejecuta el servidor de prueba"""
        app.run(debug=False, use_reloader=False, port=5001)
    
    @classmethod
    def _wait_for_server(cls):
        """Espera a que el servidor esté disponible"""
        max_attempts = 10
        attempts = 0
        
        while attempts < max_attempts:
            try:
                response = requests.get('http://127.0.0.1:5001/')
                if response.status_code == 200:
                    print("Servidor de prueba iniciado correctamente")
                    return
            except requests.exceptions.ConnectionError:
                attempts += 1
                time.sleep(0.5)
        
        print("Error: No se pudo conectar al servidor de prueba")
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todas las pruebas"""
        print("\n=== Finalizando pruebas de GimnasioDB ===")
    
    def test_home_page(self):
        """Prueba que la página principal responde correctamente"""
        response = requests.get('http://127.0.0.1:5001/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('GimnasioDB', response.text)
    
    def test_login_page(self):
        """Prueba que la página de login responde correctamente"""
        response = requests.get('http://127.0.0.1:5001/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Iniciar sesión', response.text)
    
    def test_database_models(self):
        """Prueba que los modelos de base de datos funcionan correctamente"""
        with self.app.app_context():
            # Verificar que se crearon los datos de prueba
            admin = Admin.query.filter_by(usuario="admin_test").first()
            self.assertIsNotNone(admin)
            self.assertTrue(admin.check_password("test123"))
            
            usuario = Usuario.query.filter_by(telefono="123456789").first()
            self.assertIsNotNone(usuario)
            self.assertEqual(usuario.nombre, "Usuario Prueba")
            
            producto = Producto.query.filter_by(nombre="Producto Prueba").first()
            self.assertIsNotNone(producto)
            self.assertEqual(producto.precio, 10000)

def run_server_tests():
    """Ejecuta pruebas del servidor"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestGimnasioDB)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

def verify_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    try:
        import flask
        import flask_sqlalchemy
        import werkzeug
        import jinja2
        import sqlalchemy
        import requests
        print("✓ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"✗ Error: Falta la dependencia {e.name}")
        print("Ejecute 'pip install -r requirements.txt' para instalar todas las dependencias")
        return False

if __name__ == "__main__":
    print("=== Verificando entorno de pruebas ===")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists(os.path.join(parent_dir, "app_launcher.py")):
        print("Error: Este script debe ejecutarse desde el directorio dev/")
        sys.exit(1)
    
    # Verificar dependencias
    if not verify_dependencies():
        sys.exit(1)
    
    # Ejecutar pruebas
    print("\n=== Ejecutando pruebas de servidor ===")
    result = run_server_tests()
    
    # Devolver código de salida adecuado
    sys.exit(not result.wasSuccessful()) 