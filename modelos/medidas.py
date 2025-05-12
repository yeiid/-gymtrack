from . import db, date_colombia

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