from flask import Blueprint

# Crear blueprint para productos
bp = Blueprint('productos', __name__, url_prefix='/productos')