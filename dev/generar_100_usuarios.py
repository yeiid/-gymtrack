#!/usr/bin/env python
"""
Script para generar 100 usuarios de prueba en el sistema GymTrack.
Este script facilita la carga de datos de muestra para pruebas y demos.
"""
import sys
import os
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask

# Añadir el directorio raíz al path para que se puedan encontrar los módulos
sys.path.insert(0, str(Path(__file__).parent))

# Importar los módulos necesarios
try:
    from models import db, Usuario, PagoMensualidad
except ImportError as e:
    print(f"ERROR: Error al importar módulos: {e}")
    print("Asegúrate de ejecutar el script desde el directorio raíz del proyecto")
    sys.exit(1)

# Constantes para la generación de datos aleatorios
NOMBRES = [
    "Juan", "Carlos", "Miguel", "David", "José", "Pedro", "Daniel", "Antonio", 
    "María", "Ana", "Laura", "Carmen", "Isabel", "Sofia", "Paula", "Lucía",
    "Alejandro", "Javier", "Fernando", "Roberto", "Diego", "Francisco", 
    "Patricia", "Claudia", "Mónica", "Elena", "Natalia", "Andrea", "Gabriela"
]

APELLIDOS = [
    "García", "Rodríguez", "López", "Martínez", "González", "Pérez", "Sánchez", 
    "Romero", "Hernández", "Díaz", "Torres", "Ramírez", "Ruiz", "Vargas", 
    "Morales", "Ortiz", "Castro", "Jiménez", "Gutiérrez", "Álvarez", "Mendoza",
    "Navarro", "Rojas", "Moreno", "Silva", "Ramos", "Flores", "Rivera", "Cruz"
]

PLANES = ["Diario", "Quincenal", "Mensual", "Estudiantil", "Dirigido", "Personalizado"]
METODOS_PAGO = ["Efectivo", "Transferencia", "Tarjeta", "Nequi", "Daviplata"]

def generar_telefono():
    """Genera un número de teléfono colombiano aleatorio"""
    prefijos = ["300", "301", "302", "303", "304", "305", "310", "311", "312", "313", "314", "315", "316", "317", "318", "319", "320", "321", "322", "323", "324", "350", "351"]
    prefijo = random.choice(prefijos)
    resto = ''.join(random.choices(string.digits, k=7))
    return f"{prefijo}{resto}"

def generar_usuario_aleatorio():
    """Genera datos aleatorios para un usuario"""
    nombre = random.choice(NOMBRES)
    apellido = random.choice(APELLIDOS)
    telefono = generar_telefono()
    plan = random.choice(PLANES)
    metodo_pago = random.choice(METODOS_PAGO)
    
    # Generar fechas de pago y vencimiento lógicas
    fecha_pago = datetime.now() - timedelta(days=random.randint(0, 30))
    
    # Determinar la fecha de vencimiento según el plan
    if plan == "Diario":
        dias_vigencia = 1
    elif plan == "Quincenal":
        dias_vigencia = 15
    elif plan == "Mensual" or plan == "Estudiantil" or plan == "Dirigido" or plan == "Personalizado":
        dias_vigencia = 30
    else:
        dias_vigencia = 30  # Por defecto
    
    fecha_vencimiento = fecha_pago + timedelta(days=dias_vigencia)
    
    # Obtener precio del plan
    if plan == "Diario":
        precio = Usuario.PRECIO_DIARIO
    elif plan == "Quincenal":
        precio = Usuario.PRECIO_QUINCENAL
    elif plan == "Mensual":
        precio = Usuario.PRECIO_MENSUAL
    elif plan == "Estudiantil":
        precio = Usuario.PRECIO_ESTUDIANTIL
    elif plan == "Dirigido":
        precio = Usuario.PRECIO_DIRIGIDO
    elif plan == "Personalizado":
        precio = Usuario.PRECIO_PERSONALIZADO
    else:
        precio = 0
    
    return {
        "nombre": f"{nombre} {apellido}",
        "telefono": telefono,
        "plan": plan,
        "metodo_pago": metodo_pago,
        "fecha_pago": fecha_pago,
        "fecha_vencimiento": fecha_vencimiento,
        "precio": precio
    }

def crear_app():
    """Crea una instancia de la aplicación Flask para importar datos de prueba"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Usar la base de datos principal
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def registrar_usuarios_test(app, cantidad=100):
    """Registra una cantidad de usuarios aleatorios para pruebas"""
    print(f"\nRegistrando {cantidad} usuarios aleatorios para pruebas...")
    
    usuarios_creados = []
    with app.app_context():
        for i in range(cantidad):
            datos = generar_usuario_aleatorio()
            
            # Crear usuario
            usuario = Usuario(
                nombre=datos["nombre"],
                telefono=datos["telefono"],
                plan=datos["plan"],
                metodo_pago=datos["metodo_pago"],
                fecha_vencimiento_plan=datos["fecha_vencimiento"],
                precio_plan=datos["precio"],
                fecha_ingreso=datos["fecha_pago"]  # Usar la fecha de pago como fecha de ingreso
            )
            db.session.add(usuario)
            
            # Crear pago asociado
            pago = PagoMensualidad(
                usuario=usuario,
                fecha_pago=datos["fecha_pago"],
                fecha_inicio=datos["fecha_pago"],
                fecha_fin=datos["fecha_vencimiento"],
                metodo_pago=datos["metodo_pago"],
                plan=datos["plan"],
                monto=datos["precio"]
            )
            db.session.add(pago)
            
            usuarios_creados.append(usuario)
            
            # Hacer commit cada 10 usuarios para no saturar la memoria
            if (i + 1) % 10 == 0:
                db.session.commit()
                print(f"  + {i + 1} usuarios registrados")
        
        # Commit final
        db.session.commit()
    
    print(f"COMPLETADO: {cantidad} usuarios registrados exitosamente")
    return usuarios_creados

def generar_usuarios(cantidad=100):
    """Genera la cantidad especificada de usuarios de prueba en la base de datos"""
    # Crear la aplicación
    app = crear_app()
    
    print("=" * 60)
    print(f" GENERACIÓN DE {cantidad} USUARIOS DE PRUEBA ")
    print("=" * 60)
    
    # Confirmar la operación
    print("\n⚠️ ADVERTENCIA: Este script agregará usuarios de prueba a la base de datos.")
    print("Los datos generados simularán usuarios reales con planes y pagos.")
    confirmacion = input("\n¿Deseas continuar? (s/n): ")
    
    if confirmacion.lower() != 's':
        print("Operación cancelada.")
        return
    
    # Registrar usuarios
    try:
        usuarios = registrar_usuarios_test(app, cantidad)
        print(f"\n✅ COMPLETADO: Se han generado {len(usuarios)} usuarios de prueba exitosamente.")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ ERROR: Ocurrió un problema al generar los usuarios: {str(e)}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    # Determinar la cantidad de usuarios a generar
    cantidad = 100
    if len(sys.argv) > 1:
        try:
            cantidad = int(sys.argv[1])
        except ValueError:
            print(f"Error: El argumento debe ser un número entero. Usando valor por defecto: {cantidad}")
    
    # Ejecutar la generación de usuarios
    generar_usuarios(cantidad) 