from . import db, date_colombia

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