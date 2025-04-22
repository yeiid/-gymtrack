from app import app
import webbrowser
import os
import sys
import threading
import time
import signal
from flask import request, jsonify

# Variable para controlar el servidor
server_running = True

def open_browser():
    """
    Abre el navegador después de un breve retardo para asegurar que Flask esté en ejecución
    """
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')

def resource_path(relative_path):
    """
    Obtiene la ruta absoluta a un recurso, funciona tanto para desarrollo 
    como cuando la aplicación está empaquetada por PyInstaller
    """
    try:
        # PyInstaller crea un directorio temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Ruta para cerrar la aplicación
@app.route('/cerrar-aplicacion', methods=['POST'])
def cerrar_aplicacion():
    global server_running
    # Detenemos el servidor en un hilo separado para que pueda responder antes de cerrarse
    threading.Thread(target=shutdown_server).start()
    return jsonify({"status": "cerrando"})

def shutdown_server():
    """Función para apagar el servidor desde un endpoint"""
    global server_running
    time.sleep(1)  # Esperar para que la respuesta se envíe
    os.kill(os.getpid(), signal.SIGTERM)
    server_running = False

if __name__ == '__main__':
    # Inicia un hilo para abrir el navegador
    threading.Thread(target=open_browser).start()
    
    # Asegura que las rutas a los directorios estáticos sean correctas
    app.template_folder = resource_path('templates')
    app.static_folder = resource_path('static')
    
    # Ejecuta la aplicación Flask
    app.run(debug=False) 