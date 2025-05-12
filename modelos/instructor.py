from . import db, date_colombia

class Instructor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(50), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    fecha_ingreso = db.Column(db.Date, default=date_colombia)
    
    clases = db.relationship('Clase', backref='instructor', lazy=True) 