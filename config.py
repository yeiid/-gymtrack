import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Función para determinar el modo (development/production)
def get_config_mode():
    """
    Determina el modo de configuración basado en la variable de entorno
    o, por defecto, modo de desarrollo
    """
    return os.environ.get('APP_MODE', 'production')

# Configuración común para ambos modos
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'mi_clave_supersecreta')

# Configuraciones específicas según el modo
mode = get_config_mode()

if mode == 'development':
    # Configuración de desarrollo
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    SQLALCHEMY_ECHO = True  # Muestra consultas SQL en consola
    SESSION_COOKIE_SECURE = False
elif mode == 'production':
    # Configuración de producción
    DEBUG = False
    if os.environ.get('DATABASE_URL'):
        # En Render, usa PostgreSQL
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    else:
        # En producción local, usa SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    SESSION_COOKIE_SECURE = True
else:
    # En caso de modo no reconocido, usar configuración de producción por defecto
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    SESSION_COOKIE_SECURE = True

# Silenciar advertencias de incompatibilidad con SQLAlchemy 2.0
SQLALCHEMY_SILENCE_UBER_WARNING = os.environ.get("SQLALCHEMY_SILENCE_UBER_WARNING", "1") == "1"
# Si deseamos ver todas las advertencias de deprecación para compatibilidad futura
SQLALCHEMY_WARN_20 = os.environ.get("SQLALCHEMY_WARN_20", "0") == "1"
