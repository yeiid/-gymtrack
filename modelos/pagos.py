from . import db, datetime_colombia

class PagoMensualidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'))
    fecha_pago = db.Column(db.DateTime, default=datetime_colombia)
    monto = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(50))
    plan = db.Column(db.String(50))
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False) 