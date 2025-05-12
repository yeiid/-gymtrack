from flask import Blueprint

# Crear blueprint para usuarios
bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')