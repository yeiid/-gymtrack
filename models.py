from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import pytz

db = SQLAlchemy()

# Función para obtener la fecha y hora actual en Colombia
def datetime_colombia():
    return datetime.now(pytz.timezone('America/Bogota')).replace(tzinfo=None)

# Función para obtener solo la fecha actual en Colombia
def date_colombia():
    return datetime_colombia().date()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    telefono = db.Column(db.String(20), unique=True)
    plan = db.Column(db.String(50))
    fecha_ingreso = db.Column(db.Date, default=date_colombia)
    metodo_pago = db.Column(db.String(50))
    fecha_vencimiento_plan = db.Column(db.Date, nullable=True)
    precio_plan = db.Column(db.Float, nullable=True)
    
    # Relaciones con cascade delete
    medidas = db.relationship('MedidasCorporales', backref='usuario', cascade='all, delete-orphan')
    objetivos = db.relationship('ObjetivoPersonal', backref='usuario', cascade='all, delete-orphan')
    asistencias = db.relationship('Asistencia', backref='usuario', cascade='all, delete-orphan')
    pagos_mensualidad = db.relationship('PagoMensualidad', backref='usuario', cascade='all, delete-orphan')
    compras = db.relationship('VentaProducto', backref='usuario', cascade='save-update, merge', overlaps="usuario")
    
    # Define constantes para los precios de los planes
    PRECIO_DIARIO = 5000
    PRECIO_QUINCENAL = 35000
    PRECIO_MENSUAL = 70000
    PRECIO_ESTUDIANTIL = 50000
    PRECIO_DIRIGIDO = 130000
    PRECIO_PERSONALIZADO = 250000

class MedidasCorporales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'))
    fecha = db.Column(db.Date, default=date_colombia)
    peso = db.Column(db.Float, nullable=True)
    altura = db.Column(db.Float, nullable=True)
    imc = db.Column(db.Float, nullable=True)
    pecho = db.Column(db.Float, nullable=True)
    cintura = db.Column(db.Float, nullable=True)
    cadera = db.Column(db.Float, nullable=True)
    brazo_izquierdo = db.Column(db.Float, nullable=True)
    brazo_derecho = db.Column(db.Float, nullable=True)
    pierna_izquierda = db.Column(db.Float, nullable=True)
    pierna_derecha = db.Column(db.Float, nullable=True)
    notas = db.Column(db.Text, nullable=True)

class ObjetivoPersonal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'))
    descripcion = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.Date, default=date_colombia)
    fecha_objetivo = db.Column(db.Date, nullable=True)
    fecha_completado = db.Column(db.Date, nullable=True)
    completado = db.Column(db.Boolean, default=False)
    progreso = db.Column(db.Integer, default=0)
    estado = db.Column(db.String(20), default='En progreso')  # Nueva columna: En progreso, Completado, Cancelado

class Asistencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'))
    fecha = db.Column(db.DateTime, default=datetime_colombia)

class Instructor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(50), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    fecha_ingreso = db.Column(db.Date, default=date_colombia)
    
    clases = db.relationship('Clase', backref='instructor', lazy=True)

class Clase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    dia = db.Column(db.String(20), nullable=False)
    hora = db.Column(db.String(10), nullable=False)
    duracion = db.Column(db.Integer, default=60)  # Duración en minutos
    capacidad = db.Column(db.Integer, default=20)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.id'), nullable=True)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(50))
    fecha_creacion = db.Column(db.DateTime, default=datetime_colombia)

class VentaProducto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='SET NULL'), nullable=True)
    cantidad = db.Column(db.Integer, default=1)
    precio_unitario = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=datetime_colombia)
    
    producto = db.relationship('Producto', backref='ventas')

class PagoMensualidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'))
    fecha_pago = db.Column(db.DateTime, default=datetime_colombia)
    monto = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(50))
    plan = db.Column(db.String(50))
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='recepcionista')  # 'administrador' o 'recepcionista'
    fecha_creacion = db.Column(db.DateTime, default=datetime_colombia)
    ultimo_acceso = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
