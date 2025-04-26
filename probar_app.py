"""
Script para probar la aplicación antes de empaquetar
"""
import sys
import subprocess
import time
import os
import webbrowser
import threading

def abrir_navegador():
    """Abre el navegador después de un breve retraso"""
    print("Esperando a que inicie el servidor...")
    time.sleep(2)
    try:
        webbrowser.open('http://127.0.0.1:5000')
        print("Abriendo GimnasioDB en el navegador...")
    except Exception as e:
        print(f"Error al abrir el navegador: {e}")
        print("Por favor, abre manualmente http://127.0.0.1:5000 en tu navegador")
    
    print("\nPara cerrar la aplicación:")
    print("1. Usa el botón 'Cerrar' en la barra de navegación de la aplicación, o")
    print("2. Presiona Ctrl+C en esta ventana")

if __name__ == "__main__":
    try:
        print("=== Probando GimnasioDB ===")
        
        # Verificar que estamos en el directorio correcto
        if not os.path.exists("app.py"):
            print("Error: Este script debe ejecutarse desde el directorio principal del proyecto")
            sys.exit(1)
        
        # Iniciar navegador en un hilo separado
        threading.Thread(target=abrir_navegador).start()
        
        # Ejecutar la aplicación
        print("Iniciando servidor GimnasioDB...")
        subprocess.call([sys.executable, "run_app.py"])
    except KeyboardInterrupt:
        print("\nAplicación cerrada manualmente.")
    except Exception as e:
        print(f"\nError al ejecutar la aplicación: {e}")
    
    print("\nPrueba finalizada.") 