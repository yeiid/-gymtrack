import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Configuración para entorno de producción o desarrollo
if os.environ.get('DATABASE_URL'):
    # En Render, usa PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
else:
    # En desarrollo local, usa SQLite
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')

SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'mi_clave_supersecreta')
