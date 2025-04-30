#!/usr/bin/env python
"""
Test de integridad para el sistema de gestión de usuarios de GymTrack.
Este script genera usuarios aleatorios y valida la integridad de los datos.
"""
import sys
import os
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

# Añadir el directorio raíz al path para que se puedan encontrar los módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar los módulos de la aplicación
try:
    from models import db, Usuario, PagoMensualidad
    import config
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

PLANES = ["Mensual", "Trimestral", "Semestral", "Anual"]
METODOS_PAGO = ["Efectivo", "Transferencia", "Tarjeta"]

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
    if plan == "Mensual":
        fecha_vencimiento = fecha_pago + timedelta(days=30)
    elif plan == "Trimestral":
        fecha_vencimiento = fecha_pago + timedelta(days=90)
    elif plan == "Semestral":
        fecha_vencimiento = fecha_pago + timedelta(days=180)
    else:  # Anual
        fecha_vencimiento = fecha_pago + timedelta(days=365)
    
    return {
        "nombre": f"{nombre} {apellido}",
        "telefono": telefono,
        "plan": plan,
        "metodo_pago": metodo_pago,
        "fecha_pago": fecha_pago,
        "fecha_vencimiento": fecha_vencimiento
    }

def crear_app_test():
    """Crea una instancia de la aplicación para pruebas con una BD temporal"""
    from flask import Flask
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    
    # Inicializar la BD con la app de prueba
    db.init_app(app)
    
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
    
    return app

def registrar_usuarios_test(app, cantidad=50):
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
                plan=datos["plan"]
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
                monto=random.choice([50000, 120000, 200000, 350000])  # Montos aproximados según plan
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

def validar_integridad_datos(app):
    """Valida la integridad de los datos de usuarios y pagos"""
    print("\nValidando integridad de datos...")
    
    errores = []
    with app.app_context():
        # Obtener todos los usuarios y pagos
        usuarios = Usuario.query.all()
        pagos = PagoMensualidad.query.all()
        
        # Verificar que hay usuarios
        if not usuarios:
            errores.append("ERROR: No se encontraron usuarios en la base de datos")
        else:
            print(f"  + {len(usuarios)} usuarios encontrados")
        
        # Verificar que hay pagos
        if not pagos:
            errores.append("ERROR: No se encontraron pagos en la base de datos")
        else:
            print(f"  + {len(pagos)} pagos encontrados")
        
        # Verificar integridad de datos
        for usuario in usuarios:
            # Verificar que cada usuario tiene al menos un pago
            pagos_usuario = PagoMensualidad.query.filter_by(usuario_id=usuario.id).all()
            if not pagos_usuario:
                errores.append(f"ERROR: Usuario {usuario.id} ({usuario.nombre}) no tiene pagos asociados")
            
            # Verificar que el teléfono cumple con el formato esperado
            if not usuario.telefono or len(usuario.telefono) != 10 or not usuario.telefono.isdigit():
                errores.append(f"ERROR: Usuario {usuario.id} ({usuario.nombre}) tiene un teléfono inválido: {usuario.telefono}")
            
            # Verificar que el plan es válido
            if usuario.plan not in PLANES:
                errores.append(f"ERROR: Usuario {usuario.id} ({usuario.nombre}) tiene un plan inválido: {usuario.plan}")
        
        # Verificar integridad de pagos
        for pago in pagos:
            # Verificar que cada pago está asociado a un usuario existente
            usuario = Usuario.query.get(pago.usuario_id)
            if not usuario:
                errores.append(f"ERROR: Pago {pago.id} está asociado a un usuario inexistente (ID {pago.usuario_id})")
            
            # Verificar que el método de pago es válido
            if pago.metodo_pago not in METODOS_PAGO:
                errores.append(f"ERROR: Pago {pago.id} tiene un método de pago inválido: {pago.metodo_pago}")
            
            # Verificar lógica de fechas
            if pago.fecha_fin <= pago.fecha_inicio:
                errores.append(f"ERROR: Pago {pago.id} tiene fechas ilógicas: fin ({pago.fecha_fin}) <= inicio ({pago.fecha_inicio})")
    
    # Mostrar resultados
    if errores:
        for error in errores:
            print(error)
        print(f"ERROR: Se encontraron {len(errores)} errores de integridad")
        return False
    else:
        print("COMPLETADO: Todos los datos pasaron las pruebas de integridad")
        return True

def realizar_pruebas(cantidad_usuarios=50):
    """Realiza todas las pruebas de integridad"""
    print("=" * 60)
    print(f" PRUEBAS DE INTEGRIDAD DE DATOS - {cantidad_usuarios} USUARIOS ")
    print("=" * 60)
    
    # Crear la aplicación de prueba
    app = crear_app_test()
    
    # Registrar usuarios
    usuarios = registrar_usuarios_test(app, cantidad_usuarios)
    
    # Validar integridad
    resultado = validar_integridad_datos(app)
    
    print("\n" + "=" * 60)
    if resultado:
        print("COMPLETADO: TODAS LAS PRUEBAS DE INTEGRIDAD PASARON EXITOSAMENTE")
    else:
        print("ERROR: ALGUNAS PRUEBAS DE INTEGRIDAD FALLARON")
    print("=" * 60)
    
    return resultado

if __name__ == "__main__":
    # Determinar la cantidad de usuarios para las pruebas
    cantidad = 50
    if len(sys.argv) > 1:
        try:
            cantidad = int(sys.argv[1])
        except ValueError:
            print(f"Error: El argumento debe ser un número entero. Usando valor por defecto: {cantidad}")
    
    # Ejecutar pruebas
    resultado = realizar_pruebas(cantidad)
    
    # Salir con código apropiado
    sys.exit(0 if resultado else 1) 