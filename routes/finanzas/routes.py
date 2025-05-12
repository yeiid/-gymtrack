"""
Módulo de Finanzas del Sistema GymTrack - Enrutamiento Central
==============================================================

Este archivo centraliza la importación de todos los controladores modulares
y mantiene el blueprint unificado para el módulo de finanzas.

Estructura modular:
- dashboard_controller.py: Dashboard principal y análisis financiero
- diarias_controller.py: Análisis de finanzas diarias
- reportes_controller.py: Exportación de informes y vista de pagos
- utils.py: Funciones utilitarias comunes y constantes financieras

Desarrollado por: YEIFRAN HERNANDEZ
NEURALJIRA_DEV - Visión inteligente para gestión de gimnasios
"""

# Importar el blueprint desde __init__
from routes.finanzas import bp

# Importar todos los controladores para registrar sus rutas en el blueprint
import routes.finanzas.dashboard_controller  # Ruta / (dashboard)
import routes.finanzas.diarias_controller    # Ruta /diarias
import routes.finanzas.reportes_controller   # Rutas /pagos y /exportar

# La funcionalidad completa ha sido modularizada en los controladores individuales
