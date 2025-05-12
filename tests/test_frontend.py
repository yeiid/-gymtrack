"""
Pruebas para verificar la correcta presentación y funcionalidad del frontend
"""
import unittest
from app import create_app
from app.core.config import config
from flask import url_for
import re
from bs4 import BeautifulSoup

class TestFrontend(unittest.TestCase):
    """Pruebas para el frontend de la aplicación"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.app = create_app(config['testing'])
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SERVER_NAME'] = 'localhost.localdomain'
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()
    
    def tearDown(self):
        """Limpieza después de las pruebas"""
        self.ctx.pop()
    
    def test_home_page_renders_correctly(self):
        """Verifica que la página principal se renderiza correctamente"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.content_type)
        
        # Verificar que contiene elementos estructurales clave
        soup = BeautifulSoup(response.data, 'html.parser')
        self.assertIsNotNone(soup.find('nav'), "La página debe contener una barra de navegación")
        self.assertIsNotNone(soup.find('footer'), "La página debe contener un pie de página")
    
    def test_css_resources_are_loaded(self):
        """Verifica que los recursos CSS se cargan correctamente"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        soup = BeautifulSoup(response.data, 'html.parser')
        css_links = soup.find_all('link', rel='stylesheet')
        
        # Verificar que hay enlaces a CSS
        self.assertTrue(len(css_links) > 0, "La página debe cargar hojas de estilo CSS")
        
        # Verificar que se carga custom.css
        custom_css_loaded = any('custom.css' in link.get('href', '') for link in css_links)
        self.assertTrue(custom_css_loaded, "La hoja de estilo custom.css debe estar cargada")
        
        # Verificar que los recursos CSS existen y son accesibles
        for link in css_links:
            if link.get('href').startswith('/static'):
                css_url = link.get('href')
                response = self.client.get(css_url)
                self.assertEqual(response.status_code, 200, f"El recurso CSS {css_url} debe ser accesible")
    
    def test_responsive_design(self):
        """Verifica que la página incluye configuración responsive"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Verificar que tiene viewport meta tag para diseño responsive
        self.assertIn(b'<meta name="viewport"', response.data, 
                      "La página debe incluir meta tag viewport para diseño responsive")
        
        soup = BeautifulSoup(response.data, 'html.parser')
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        self.assertIsNotNone(viewport, "Debe existir una etiqueta meta viewport")
        self.assertIn('width=device-width', viewport.get('content', ''), 
                      "La configuración viewport debe incluir width=device-width")
    
    def test_login_form_elements(self):
        """Verifica que el formulario de login contiene todos los elementos necesarios"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        
        soup = BeautifulSoup(response.data, 'html.parser')
        form = soup.find('form')
        
        self.assertIsNotNone(form, "Debe existir un formulario en la página de login")
        
        if form:
            # Verificar campos de usuario y contraseña
            usuario_field = form.find('input', {'name': 'usuario'})
            password_field = form.find('input', {'name': 'password', 'type': 'password'})
            submit_button = form.find('button', {'type': 'submit'})
            
            self.assertIsNotNone(usuario_field, "El formulario debe contener un campo de usuario")
            self.assertIsNotNone(password_field, "El formulario debe contener un campo de contraseña")
            self.assertIsNotNone(submit_button, "El formulario debe contener un botón de envío")

if __name__ == '__main__':
    unittest.main() 