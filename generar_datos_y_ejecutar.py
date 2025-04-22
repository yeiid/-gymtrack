import os
import sys
import generar_datos

print("Generando datos de prueba...")
generar_datos.generar_datos_prueba(50, 20)  # 50 usuarios, 20 productos
print("Datos generados correctamente.")

print("Iniciando la aplicación...")
os.system("python app.py") 