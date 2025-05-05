#!/usr/bin/env python
"""
Pruebas unitarias para los modelos de GimnasioDB
"""
import os
import sys
import unittest
from datetime import datetime, timedelta

# Añadir directorio principal al path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Establecer modo de desarrollo
os.environ['APP_MODE'] = 'development'
os.environ['FLASK_ENV'] = 'development'
os.environ['TEST_MODE'] = 'True'

# Importar después de configurar variables de entorno
from flask import Flask
from models import db, Usuario, Admin, Producto, MedidasCorporales, PagoMensualidad, Asistencia

class TestModelos(unittest.TestCase):
    """Pruebas unitarias para los modelos de la base de datos"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todas las pruebas"""
        # Crear aplicación de prueba
        cls.app = Flask(__name__)
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Inicializar base de datos
        db.init_app(cls.app)
        
    def setUp(self):
        """Configuración para cada prueba"""
        # Crear contexto de aplicación
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Crear tablas para cada test
        db.create_all()
        
        # Crear datos de prueba básicos
        self.crear_datos_prueba()
        
    def tearDown(self):
        """Limpieza después de cada prueba"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def crear_datos_prueba(self):
        """Crea datos de prueba en la base de datos"""
        # Crear administrador
        admin = Admin(
            nombre="Admin Test",
            usuario="admin_test",
            rol="administrador"
        )
        admin.set_password("test123")
        
        # Crear usuario
        usuario = Usuario(
            nombre="Usuario Test",
            telefono="123456789",
            plan="Mensual",
            fecha_ingreso=datetime.now(),
            fecha_vencimiento_plan=datetime.now() + timedelta(days=30),
            precio_plan=Usuario.PRECIO_MENSUAL
        )
        
        # Crear producto
        producto = Producto(
            nombre="Producto Test",
            descripcion="Descripción de prueba",
            precio=10000,
            stock=10,
            categoria="Suplementos"
        )
        
        # Guardar en la base de datos
        db.session.add_all([admin, usuario, producto])
        db.session.commit()
    
    def test_usuario_creacion(self):
        """Prueba que se pueden crear usuarios correctamente"""
        usuario = Usuario.query.filter_by(telefono="123456789").first()
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.nombre, "Usuario Test")
        self.assertEqual(usuario.plan, "Mensual")
    
    def test_admin_autenticacion(self):
        """Prueba que la autenticación de administradores funciona"""
        admin = Admin.query.filter_by(usuario="admin_test").first()
        self.assertTrue(admin.check_password("test123"))
        self.assertFalse(admin.check_password("contraseña_incorrecta"))
    
    def test_producto_creacion(self):
        """Prueba que se pueden crear productos correctamente"""
        producto = Producto.query.filter_by(nombre="Producto Test").first()
        self.assertIsNotNone(producto)
        self.assertEqual(producto.precio, 10000)
        self.assertEqual(producto.stock, 10)
    
    def test_registro_medidas(self):
        """Prueba que se pueden registrar medidas corporales"""
        usuario = Usuario.query.filter_by(telefono="123456789").first()
        
        medidas = MedidasCorporales(
            usuario_id=usuario.id,
            peso=70.5,
            altura=175,
            imc=70.5 / (1.75 ** 2),
            pecho=95,
            cintura=80,
            cadera=98
        )
        
        db.session.add(medidas)
        db.session.commit()
        
        # Verificar que se guardó correctamente
        medidas_db = MedidasCorporales.query.filter_by(usuario_id=usuario.id).first()
        self.assertIsNotNone(medidas_db)
        self.assertAlmostEqual(medidas_db.peso, 70.5)
        self.assertAlmostEqual(medidas_db.imc, 70.5 / (1.75 ** 2), places=2)
    
    def test_registro_pago(self):
        """Prueba que se pueden registrar pagos de mensualidad"""
        usuario = Usuario.query.filter_by(telefono="123456789").first()
        
        fecha_inicio = datetime.now()
        fecha_fin = fecha_inicio + timedelta(days=30)
        
        pago = PagoMensualidad(
            usuario_id=usuario.id,
            monto=70000,
            metodo_pago="Efectivo",
            plan="Mensual",
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        db.session.add(pago)
        db.session.commit()
        
        # Verificar que se guardó correctamente
        pago_db = PagoMensualidad.query.filter_by(usuario_id=usuario.id).first()
        self.assertIsNotNone(pago_db)
        self.assertEqual(pago_db.monto, 70000)
        self.assertEqual(pago_db.plan, "Mensual")
    
    def test_registro_asistencia(self):
        """Prueba que se puede registrar asistencia"""
        usuario = Usuario.query.filter_by(telefono="123456789").first()
        
        # Registrar asistencia
        asistencia = Asistencia(usuario_id=usuario.id)
        db.session.add(asistencia)
        db.session.commit()
        
        # Verificar que se guardó correctamente
        asistencia_db = Asistencia.query.filter_by(usuario_id=usuario.id).first()
        self.assertIsNotNone(asistencia_db)
        self.assertEqual(asistencia_db.usuario_id, usuario.id)

if __name__ == "__main__":
    unittest.main() 