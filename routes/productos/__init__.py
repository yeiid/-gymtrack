# Inicializar paquete para rutas de productos
from . import routes
from . import producto_controller
from . import ventas_controller

# Para facilitar la importación desde otros módulos
__all__ = ['bp'] 