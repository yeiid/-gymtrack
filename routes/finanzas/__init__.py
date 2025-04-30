# Inicializar paquete para rutas de finanzas
# Importando directamente el blueprint en lugar de todo el módulo
from routes.finanzas.routes import bp

# Para facilitar la importación desde otros módulos
__all__ = ['bp'] 