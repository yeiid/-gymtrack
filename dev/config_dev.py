import os
import sys

# Añadir directorio principal al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar configuración base
from config import *

# Sobrescribir configuraciones para desarrollo
DEBUG = True
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'dev_database.db')
SQLALCHEMY_ECHO = True  # Muestra consultas SQL en consola
SESSION_COOKIE_SECURE = False

# Variables específicas para entorno de desarrollo
DEVELOPMENT_MODE = True
TESTING = True
TEMPLATES_AUTO_RELOAD = True

# Configuración de logs para desarrollo
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

print("Cargando configuración de DESARROLLO") 