"""
Versión simplificada de run_app.py específicamente optimizada para el empaquetado
"""
from app import app
import webbrowser
import os
import sys
import threading
import time
import signal
from flask import request, jsonify

# Desactivar todos los mensajes de consola al ejecutar como .exe
if getattr(sys, 'frozen', False):
    # Estamos ejecutando como .exe
    os.environ['FLASK_ENV'] = 'production'
    # Redirigir stdout/stderr a un archivo o nulo
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

def open_browser():
    """Abre el navegador después de un breve retardo"""
    time.sleep(2)
    try:
        webbrowser.open('http://127.0.0.1:5000')
    except:
        pass  # Silenciar errores

def resource_path(relative_path):
    """Obtiene la ruta absoluta a un recurso"""
    try:
        # PyInstaller crea un directorio temporal
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Ruta para cerrar la aplicación
@app.route('/cerrar-aplicacion', methods=['POST'])
def cerrar_aplicacion():
    """Endpoint para cerrar la aplicación"""
    def shutdown():
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=shutdown).start()
    return jsonify({"status": "cerrando"})

if __name__ == '__main__':
    # Configurar rutas estáticas
    app.template_folder = resource_path('templates')
    app.static_folder = resource_path('static')
    
    # Abrir navegador
    threading.Thread(target=open_browser).start()
    
    # Ejecutar Flask sin opciones de desarrollo
    app.run(debug=False, use_reloader=False, host='127.0.0.1', port=5000) 