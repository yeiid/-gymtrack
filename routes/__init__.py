from flask import Blueprint

# Crear el Blueprint principal
main = Blueprint('main', __name__)

# Importar rutas específicas
from routes.usuarios import routes as usuarios_routes
from routes.finanzas import routes as finanzas_routes
from routes.productos import routes as productos_routes
from routes.ventas import routes as ventas_routes
from routes.admin import routes as admin_routes
from routes.auth import routes as auth_routes

# Registrar todas las rutas en el Blueprint principal
main.register_blueprint(usuarios_routes.bp)
main.register_blueprint(finanzas_routes.bp)
main.register_blueprint(productos_routes.bp)
main.register_blueprint(ventas_routes.bp)
main.register_blueprint(admin_routes.bp)
main.register_blueprint(auth_routes.bp) 