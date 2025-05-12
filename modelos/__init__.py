from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

# Función para obtener la fecha y hora actual en Colombia
def datetime_colombia():
    return datetime.now(pytz.timezone('America/Bogota')).replace(tzinfo=None)

# Función para obtener solo la fecha actual en Colombia
def date_colombia():
    return datetime_colombia().date()

# Importar todos los modelos para que estén disponibles cuando se importe el paquete modelos
from .usuario import Usuario
from .medidas import MedidasCorporales
from .objetivos import ObjetivoPersonal
from .asistencia import Asistencia
from .instructor import Instructor
from .clase import Clase
from .producto import Producto
from .ventas import VentaProducto
from .pagos import PagoMensualidad
from .admin import Admin 