from app import app
import webbrowser
import os
import sys
import threading
import time

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

if __name__ == '__main__':
    # Inicia un hilo para abrir el navegador
    threading.Thread(target=open_browser).start()
    
    # Asegura que las rutas a los directorios estáticos sean correctas
    app.template_folder = resource_path('templates')
    app.static_folder = resource_path('static')
    
    # Ejecuta la aplicación Flask
    app.run(debug=False) 