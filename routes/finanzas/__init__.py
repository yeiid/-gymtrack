# Inicializar paquete para rutas de finanzas
from flask import Blueprint

# Crear blueprint para finanzas
bp = Blueprint('finanzas', __name__, url_prefix='/finanzas')

# Importamos los controladores después de definir el blueprint
# para evitar importaciones circulares
import routes.finanzas.dashboard_controller
import routes.finanzas.diarias_controller
import routes.finanzas.reportes_controller

# Para facilitar la importación desde otros módulos
__all__ = ['bp'] 