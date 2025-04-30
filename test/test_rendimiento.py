#!/usr/bin/env python
"""
Script de prueba para evaluar el rendimiento de la aplicación GymTrack
"""
import sys
import os
import time
import datetime
import statistics
from pathlib import Path

# Añadir el directorio raíz al path para poder importar las dependencias del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from models import db, Usuario, PagoMensualidad, Asistencia

def crear_app_test():
    """Crea una instancia de la aplicación Flask para pruebas de rendimiento"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = False  # Desactivar logs de SQL para pruebas de rendimiento
    db.init_app(app)
    return app

def medir_tiempo(func):
    """Decorador para medir el tiempo de ejecución de una función"""
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fin = time.time()
        tiempo_ms = (fin - inicio) * 1000
        return resultado, tiempo_ms
    return wrapper

def formatear_tiempo(tiempo_ms):
    """Formatea el tiempo en milisegundos a una cadena legible"""
    if tiempo_ms < 1:
        return f"{tiempo_ms * 1000:.2f} µs"
    elif tiempo_ms < 1000:
        return f"{tiempo_ms:.2f} ms"
    else:
        return f"{tiempo_ms/1000:.2f} s"

@medir_tiempo
def consultar_todos_usuarios(app):
    """Consulta todos los usuarios"""
    with app.app_context():
        return Usuario.query.all()

@medir_tiempo
def consultar_usuario_por_id(app, usuario_id):
    """Consulta un usuario por su ID"""
    with app.app_context():
        return Usuario.query.get(usuario_id)

@medir_tiempo
def consultar_usuario_por_telefono(app, telefono):
    """Consulta un usuario por su teléfono"""
    with app.app_context():
        return Usuario.query.filter_by(telefono=telefono).first()

@medir_tiempo
def consultar_pagos_usuario(app, usuario_id):
    """Consulta los pagos de un usuario"""
    with app.app_context():
        return PagoMensualidad.query.filter_by(usuario_id=usuario_id).all()

@medir_tiempo
def consultar_asistencias_usuario(app, usuario_id):
    """Consulta las asistencias de un usuario"""
    with app.app_context():
        return Asistencia.query.filter_by(usuario_id=usuario_id).all()

@medir_tiempo
def consultar_usuarios_plan(app, plan):
    """Consulta usuarios por plan"""
    with app.app_context():
        return Usuario.query.filter_by(plan=plan).all()

@medir_tiempo
def consultar_usuarios_vencidos(app):
    """Consulta usuarios con planes vencidos"""
    with app.app_context():
        hoy = datetime.date.today()
        return Usuario.query.filter(Usuario.fecha_vencimiento_plan < hoy).all()

@medir_tiempo
def consultar_pagos_periodo(app, inicio, fin):
    """Consulta pagos en un periodo de tiempo"""
    with app.app_context():
        return PagoMensualidad.query.filter(
            PagoMensualidad.fecha_pago >= inicio,
            PagoMensualidad.fecha_pago <= fin
        ).all()

def prueba_rendimiento_consultas(app, repeticiones=10):
    """Realiza pruebas de rendimiento en consultas comunes"""
    print("=" * 50)
    print(" PRUEBAS DE RENDIMIENTO - CONSULTAS ")
    print("=" * 50)
    
    # Preparar datos para pruebas
    with app.app_context():
        # Verificar que haya datos
        count_usuarios = Usuario.query.count()
        if count_usuarios == 0:
            print("❌ No hay usuarios en la base de datos para pruebas.")
            print("   Ejecute primero test_usuarios.py para generar datos.")
            return False
        
        print(f"Base de datos con {count_usuarios} usuarios para pruebas.")
        
        # Obtener algunos IDs y teléfonos para pruebas
        primer_usuario = Usuario.query.first()
        ultimo_usuario = Usuario.query.order_by(Usuario.id.desc()).first()
        usuario_aleatorio = Usuario.query.offset(count_usuarios // 2).first()
        
        # Planes para pruebas
        planes = ['Diario', 'Mensual', 'Quincenal', 'Personalizado']
        
        # Fechas para pruebas
        hoy = datetime.datetime.now()
        inicio_mes = datetime.datetime(hoy.year, hoy.month, 1)
        fin_mes = datetime.datetime(hoy.year, hoy.month + 1, 1) - datetime.timedelta(days=1)
    
    resultados = {}
    
    # Prueba 1: Consultar todos los usuarios
    tiempos = []
    for _ in range(repeticiones):
        _, tiempo = consultar_todos_usuarios(app)
        tiempos.append(tiempo)
    resultados["Consultar todos los usuarios"] = tiempos
    
    # Prueba 2: Consultar usuario por ID
    tiempos = []
    for _ in range(repeticiones):
        _, tiempo = consultar_usuario_por_id(app, primer_usuario.id)
        tiempos.append(tiempo)
    resultados["Consultar usuario por ID (primero)"] = tiempos
    
    tiempos = []
    for _ in range(repeticiones):
        _, tiempo = consultar_usuario_por_id(app, ultimo_usuario.id)
        tiempos.append(tiempo)
    resultados["Consultar usuario por ID (último)"] = tiempos
    
    # Prueba 3: Consultar usuario por teléfono
    tiempos = []
    for _ in range(repeticiones):
        _, tiempo = consultar_usuario_por_telefono(app, usuario_aleatorio.telefono)
        tiempos.append(tiempo)
    resultados["Consultar usuario por teléfono"] = tiempos
    
    # Prueba 4: Consultar pagos de usuario
    tiempos = []
    for _ in range(repeticiones):
        _, tiempo = consultar_pagos_usuario(app, usuario_aleatorio.id)
        tiempos.append(tiempo)
    resultados["Consultar pagos de usuario"] = tiempos
    
    # Prueba 5: Consultar asistencias de usuario
    tiempos = []
    for _ in range(repeticiones):
        _, tiempo = consultar_asistencias_usuario(app, usuario_aleatorio.id)
        tiempos.append(tiempo)
    resultados["Consultar asistencias de usuario"] = tiempos
    
    # Prueba 6: Consultar usuarios por plan
    for plan in planes:
        tiempos = []
        for _ in range(repeticiones):
            _, tiempo = consultar_usuarios_plan(app, plan)
            tiempos.append(tiempo)
        resultados[f"Consultar usuarios con plan {plan}"] = tiempos
    
    # Prueba 7: Consultar usuarios con planes vencidos
    tiempos = []
    for _ in range(repeticiones):
        _, tiempo = consultar_usuarios_vencidos(app)
        tiempos.append(tiempo)
    resultados["Consultar usuarios con planes vencidos"] = tiempos
    
    # Prueba 8: Consultar pagos del mes actual
    tiempos = []
    for _ in range(repeticiones):
        _, tiempo = consultar_pagos_periodo(app, inicio_mes, fin_mes)
        tiempos.append(tiempo)
    resultados["Consultar pagos del mes actual"] = tiempos
    
    # Mostrar resultados
    print("\n" + "=" * 50)
    print(" RESULTADOS DE PRUEBAS DE RENDIMIENTO ")
    print("=" * 50)
    
    rendimiento_general = []
    
    for prueba, tiempos in resultados.items():
        media = statistics.mean(tiempos)
        mediana = statistics.median(tiempos)
        desviacion = statistics.stdev(tiempos) if len(tiempos) > 1 else 0
        minimo = min(tiempos)
        maximo = max(tiempos)
        
        rendimiento_general.append(media)
        
        print(f"\n{prueba}:")
        print(f"  Media: {formatear_tiempo(media)}")
        print(f"  Mediana: {formatear_tiempo(mediana)}")
        print(f"  Desviación estándar: {formatear_tiempo(desviacion)}")
        print(f"  Mínimo: {formatear_tiempo(minimo)}")
        print(f"  Máximo: {formatear_tiempo(maximo)}")
    
    # Calcular rendimiento general
    rendimiento_medio = statistics.mean(rendimiento_general)
    
    print("\n" + "=" * 50)
    print(" RENDIMIENTO GENERAL ")
    print("=" * 50)
    print(f"Tiempo medio por consulta: {formatear_tiempo(rendimiento_medio)}")
    
    # Evaluar rendimiento
    if rendimiento_medio < 50:  # Menos de 50ms por consulta se considera bueno
        print("✅ Rendimiento EXCELENTE")
        return True
    elif rendimiento_medio < 100:  # Menos de 100ms por consulta se considera aceptable
        print("✅ Rendimiento BUENO")
        return True
    elif rendimiento_medio < 500:  # Menos de 500ms por consulta se considera regular
        print("⚠️ Rendimiento REGULAR")
        return True
    else:  # Más de 500ms por consulta se considera deficiente
        print("❌ Rendimiento DEFICIENTE")
        return False

if __name__ == "__main__":
    # Determinar la cantidad de repeticiones para las pruebas
    repeticiones = 10
    if len(sys.argv) > 1:
        try:
            repeticiones = int(sys.argv[1])
        except ValueError:
            print(f"Error: El argumento debe ser un número entero. Usando valor por defecto: {repeticiones}")
    
    # Crear aplicación de prueba
    app = crear_app_test()
    
    # Ejecutar pruebas de rendimiento
    exito = prueba_rendimiento_consultas(app, repeticiones)
    
    # Reportar resultado
    if exito:
        sys.exit(0)
    else:
        sys.exit(1) 