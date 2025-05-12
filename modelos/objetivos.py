from . import db, date_colombia

class ObjetivoPersonal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'))
    descripcion = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.Date, default=date_colombia)
    fecha_objetivo = db.Column(db.Date, nullable=True)
    fecha_completado = db.Column(db.Date, nullable=True)
    completado = db.Column(db.Boolean, default=False)
    progreso = db.Column(db.Integer, default=0)
    estado = db.Column(db.String(20), default='En progreso')  # En progreso, Completado, Cancelado 