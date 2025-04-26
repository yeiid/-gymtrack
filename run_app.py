from app import app
import webbrowser
import os
import sys
import threading
import time
import signal
from flask import request, jsonify
import io
import logging

# Redirigir stdout y stderr a un objeto nulo para evitar errores de NoneType
class NullIO(io.IOBase):
    def write(self, *args, **kwargs):
        pass
    def read(self, *args, **kwargs):
        return ''
    def flush(self, *args, **kwargs):
        pass

# Solo redirigir en modo empaquetado (cuando se ejecuta como .exe)
if getattr(sys, 'frozen', False):
    sys.stdout = NullIO()
    sys.stderr = NullIO()

# Desactivar todos los logs de Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
log.disabled = True
app.logger.disabled = True

# Desactivar mensajes de Flask
import click
click.echo = lambda *args, **kwargs: None

# Variable para controlar el servidor
server_running = True

def open_browser():
    """
    Abre el navegador después de un breve retardo para asegurar que Flask esté en ejecución
    """
    time.sleep(1.5)
    try:
        webbrowser.open('http://127.0.0.1:5000')
        if not getattr(sys, 'frozen', False):  # Solo mostrar mensajes si no estamos en modo empaquetado
            print("Abriendo la aplicación en el navegador...")
    except Exception as e:
        if not getattr(sys, 'frozen', False):
            print(f"Error al abrir el navegador: {e}")
            print("Por favor, abra manualmente http://127.0.0.1:5000 en su navegador")

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
    
    # Ejecuta la aplicación Flask sin mensajes y sin recargador
    app.run(debug=False, use_reloader=False, host='127.0.0.1', port=5000) 