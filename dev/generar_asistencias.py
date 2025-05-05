#!/usr/bin/env python
"""
Script para generar asistencias aleatorias para los usuarios existentes en GymTrack.
Este script complementa la generación de usuarios de prueba con registros de asistencia.
"""
import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask

# Añadir el directorio raíz al path para que se puedan encontrar los módulos
sys.path.insert(0, str(Path(__file__).parent))

# Importar los módulos necesarios
try:
    from models import db, Usuario, Asistencia
except ImportError as e:
    print(f"ERROR: Error al importar módulos: {e}")
    print("Asegúrate de ejecutar el script desde el directorio raíz del proyecto")
    sys.exit(1)

def crear_app():
    """Crea una instancia de la aplicación Flask para importar datos de prueba"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Usar la base de datos principal
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def generar_asistencias_aleatorias(app, dias_historial=60, frecuencia_promedio=0.7):
    """
    Genera asistencias aleatorias para los usuarios existentes
    
    Args:
        app: Aplicación Flask
        dias_historial: Cantidad de días de historial a generar
        frecuencia_promedio: Probabilidad promedio de asistencia diaria (0-1)
    """
    print(f"\nGenerando asistencias aleatorias para los últimos {dias_historial} días...")
    
    with app.app_context():
        # Obtener todos los usuarios
        usuarios = Usuario.query.all()
        
        if not usuarios:
            print("❌ No hay usuarios en la base de datos. Ejecuta primero generar_100_usuarios.py")
            return
        
        print(f"Generando asistencias para {len(usuarios)} usuarios...")
        
        # Fecha inicial (hace X días)
        fecha_inicial = datetime.now().date() - timedelta(days=dias_historial)
        fecha_actual = datetime.now().date()
        
        # Contador de asistencias generadas
        asistencias_generadas = 0
        
        # Para cada usuario, generar un patrón de asistencia aleatorio
        for usuario in usuarios:
            # Determinar frecuencia de asistencia específica para este usuario
            # Algunos usuarios son más constantes que otros
            frecuencia_usuario = random.uniform(frecuencia_promedio - 0.3, min(frecuencia_promedio + 0.3, 0.9))
            
            # Determinar días preferidos (algunos usuarios prefieren ciertos días de la semana)
            dias_preferidos = random.sample(range(7), random.randint(3, 5))
            
            # Recorrer cada día del historial
            fecha_actual_iteracion = fecha_inicial
            while fecha_actual_iteracion <= fecha_actual:
                # Aumentar probabilidad en días preferidos
                dia_semana = fecha_actual_iteracion.weekday()
                probabilidad_asistencia = frecuencia_usuario
                
                if dia_semana in dias_preferidos:
                    probabilidad_asistencia += 0.2
                
                # Reducir probabilidad si el plan ha vencido
                if usuario.fecha_vencimiento_plan and fecha_actual_iteracion > usuario.fecha_vencimiento_plan:
                    probabilidad_asistencia -= 0.5
                
                # Decisión aleatoria de asistencia
                if random.random() < probabilidad_asistencia:
                    # Crear una asistencia para este día
                    asistencia = Asistencia(
                        usuario_id=usuario.id,
                        fecha=datetime.combine(fecha_actual_iteracion, 
                                              datetime.strptime(f"{random.randint(6, 21)}:{random.choice(['00', '15', '30', '45'])}", 
                                                                "%H:%M").time())
                    )
                    db.session.add(asistencia)
                    asistencias_generadas += 1
                
                # Pasar al siguiente día
                fecha_actual_iteracion += timedelta(days=1)
            
            # Commit por cada usuario para no saturar la memoria
            db.session.commit()
        
        print(f"✅ COMPLETADO: Se generaron {asistencias_generadas} asistencias para {len(usuarios)} usuarios.")

def generar_asistencias(dias=60, frecuencia=0.7):
    """Genera asistencias aleatorias para todos los usuarios en la base de datos"""
    # Crear la aplicación
    app = crear_app()
    
    print("=" * 60)
    print(f" GENERACIÓN DE ASISTENCIAS DE PRUEBA ")
    print("=" * 60)
    
    # Confirmar la operación
    print("\n⚠️ ADVERTENCIA: Este script agregará asistencias de prueba a la base de datos.")
    print("Los datos generados simularán patrones de asistencia reales de los usuarios.")
    confirmacion = input("\n¿Deseas continuar? (s/n): ")
    
    if confirmacion.lower() != 's':
        print("Operación cancelada.")
        return
    
    # Generar asistencias
    try:
        generar_asistencias_aleatorias(app, dias_historial=dias, frecuencia_promedio=frecuencia)
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ ERROR: Ocurrió un problema al generar las asistencias: {str(e)}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    # Determinar los parámetros
    dias = 60
    frecuencia = 0.7
    
    if len(sys.argv) > 1:
        try:
            dias = int(sys.argv[1])
        except ValueError:
            print(f"Error: El primer argumento debe ser un número entero. Usando valor por defecto: {dias}")
    
    if len(sys.argv) > 2:
        try:
            frecuencia = float(sys.argv[2])
            if not 0 <= frecuencia <= 1:
                raise ValueError("La frecuencia debe estar entre 0 y 1")
        except ValueError as e:
            print(f"Error: {str(e)}. Usando valor por defecto: {frecuencia}")
    
    # Ejecutar la generación de asistencias
    generar_asistencias(dias, frecuencia) 