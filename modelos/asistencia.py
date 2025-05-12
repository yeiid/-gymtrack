from . import db, datetime_colombia

class Asistencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'))
    fecha = db.Column(db.DateTime, default=datetime_colombia) 