from . import db

class Clase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    dia = db.Column(db.String(20), nullable=False)
    hora = db.Column(db.String(10), nullable=False)
    duracion = db.Column(db.Integer, default=60)  # Duración en minutos
    capacidad = db.Column(db.Integer, default=20)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.id'), nullable=True) 