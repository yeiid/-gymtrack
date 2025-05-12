"""
Pruebas para el servicio de autenticación
"""
import unittest
from app import create_app
from app.core.config import config
from app.database.models import db, Admin
from app.services.implementations.auth_service import AuthService
from flask import session

class TestAuthService(unittest.TestCase):
    """Pruebas para el servicio de autenticación"""
    
    def setUp(self):
        """Configurar el entorno de prueba"""
        self.app = create_app(config['testing'])
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Crear un administrador de prueba
        admin = Admin(
            nombre="Admin Prueba",
            usuario="testadmin",
            rol="administrador"
        )
        admin.set_password("testpassword")
        db.session.add(admin)
        db.session.commit()
        
        self.client = self.app.test_client()
        
    def tearDown(self):
        """Limpiar después de las pruebas"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_login_success(self):
        """Probar inicio de sesión exitoso"""
        with self.client:
            response = self.client.post('/api/auth/login', json={
                'username': 'testadmin',
                'password': 'testpassword'
            })
            data = response.get_json()
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('id', data)
            self.assertEqual(data['usuario'], 'testadmin')
            self.assertEqual(data['rol'], 'administrador')
            self.assertIn('user_id', session)
    
    def test_login_failure(self):
        """Probar inicio de sesión fallido"""
        with self.client:
            response = self.client.post('/api/auth/login', json={
                'username': 'testadmin',
                'password': 'wrongpassword'
            })
            data = response.get_json()
            
            self.assertEqual(response.status_code, 401)
            self.assertIn('error', data)
            self.assertNotIn('user_id', session)
    
    def test_get_current_user(self):
        """Probar obtener usuario actual"""
        with self.client as c:
            # Iniciar sesión
            c.post('/api/auth/login', json={
                'username': 'testadmin',
                'password': 'testpassword'
            })
            
            # Obtener usuario actual
            response = c.get('/api/auth/user')
            data = response.get_json()
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['usuario'], 'testadmin')
    
    def test_logout(self):
        """Probar cierre de sesión"""
        with self.client as c:
            # Iniciar sesión
            c.post('/api/auth/login', json={
                'username': 'testadmin',
                'password': 'testpassword'
            })
            
            # Verificar que la sesión existe
            self.assertIn('user_id', session)
            
            # Cerrar sesión
            response = c.post('/api/auth/logout')
            
            # Verificar respuesta y sesión
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('user_id', session)

if __name__ == '__main__':
    unittest.main() 