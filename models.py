from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True)
    plan = db.Column(db.String(50))
    fecha_ingreso = db.Column(db.Date, default=datetime.utcnow)
    metodo_pago = db.Column(db.String(50))
    fecha_vencimiento_plan = db.Column(db.Date, nullable=True)
    precio_plan = db.Column(db.Float, nullable=True)
    
    # Define constantes para los precios de los planes
    PRECIO_DIARIO = 5000
    PRECIO_QUINCENAL = 35000
    PRECIO_MENSUAL = 70000
    PRECIO_DIRIGIDO = 130000
    PRECIO_PERSONALIZADO = 250000

class Asistencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    fecha = db.Column(db.Date, default=datetime.utcnow)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(50))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

class VentaProducto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    cantidad = db.Column(db.Integer, default=1)
    precio_unitario = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    
    producto = db.relationship('Producto', backref='ventas')
    usuario = db.relationship('Usuario', backref='compras')

class PagoMensualidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    monto = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(50))
    plan = db.Column(db.String(50))
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    
    usuario = db.relationship('Usuario', backref='pagos_mensualidad')
