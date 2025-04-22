from flask import Flask
from models import db, Usuario, Asistencia
from routes import main

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)

app.register_blueprint(main)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
