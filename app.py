from flask import Flask
from models import db, Usuario, Asistencia
from routes import main

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)

app.register_blueprint(main)

# Asegurarse de que la base de datos esté creada
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
