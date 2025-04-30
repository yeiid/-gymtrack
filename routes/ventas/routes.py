from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Usuario, Producto, VentaProducto
from datetime import datetime

# Crear blueprint para ventas
bp = Blueprint('ventas', __name__, url_prefix='/ventas')

@bp.route('/')
def index():
    # Redireccionar a la ruta de productos/ventas para mantener compatibilidad
    return redirect(url_for('main.productos.ventas')) 