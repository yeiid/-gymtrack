#!/usr/bin/env python
"""
Test de integridad para el sistema de gestión de pagos de GymTrack.
Este script verifica la correcta relación entre usuarios y pagos, y
la consistencia de los datos financieros.
"""
import sys
import os
import random
import decimal
from datetime import datetime, timedelta
from pathlib import Path

# Añadir el directorio raíz al path para que se puedan encontrar los módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar los módulos de la aplicación
try:
    from app.database.models import db, Usuario, PagoMensualidad
    from app.core.config import config
except ImportError as e:
    print(f"ERROR: Error al importar módulos: {e}")
    print("Asegúrate de ejecutar el script desde el directorio raíz del proyecto")
    sys.exit(1)

# Constantes para generación de datos de prueba
PLANES = ["Mensual", "Trimestral", "Semestral", "Anual"]
METODOS_PAGO = ["Efectivo", "Transferencia", "Tarjeta"]

# Precios por plan (en pesos colombianos)
PRECIOS = {
    "Mensual": 50000,
    "Trimestral": 120000,
    "Semestral": 200000,
    "Anual": 350000
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

def generar_pagos_test(app, num_usuarios=10, pagos_por_usuario=3):
    """Genera usuarios y pagos de prueba en la base de datos"""
    print(f"\nGenerando {num_usuarios} usuarios con {pagos_por_usuario} pagos cada uno...")
    
    usuarios_creados = []
    pagos_creados = []
    
    with app.app_context():
        # Crear usuarios de prueba
        for i in range(num_usuarios):
            nombre = f"Usuario Test {i+1}"
            telefono = f"3{random.randint(10, 99)}{random.randint(1000000, 9999999)}"
            
            usuario = Usuario(
                nombre=nombre,
                telefono=telefono,
                plan=random.choice(PLANES)
            )
            db.session.add(usuario)
            db.session.flush()  # Para obtener el ID asignado
            usuarios_creados.append(usuario)
            
            # Crear pagos históricos para cada usuario
            fecha_base = datetime.now() - timedelta(days=pagos_por_usuario * 30)
            
            for j in range(pagos_por_usuario):
                plan = random.choice(PLANES)
                fecha_pago = fecha_base + timedelta(days=j * 30)
                
                # Determinar fecha de vencimiento según el plan
                if plan == "Mensual":
                    fecha_vencimiento = fecha_pago + timedelta(days=30)
                elif plan == "Trimestral":
                    fecha_vencimiento = fecha_pago + timedelta(days=90)
                elif plan == "Semestral":
                    fecha_vencimiento = fecha_pago + timedelta(days=180)
                else:  # Anual
                    fecha_vencimiento = fecha_pago + timedelta(days=365)
                
                pago = PagoMensualidad(
                    usuario_id=usuario.id,
                    fecha_pago=fecha_pago,
                    fecha_inicio=fecha_pago,
                    fecha_fin=fecha_vencimiento,
                    metodo_pago=random.choice(METODOS_PAGO),
                    monto=PRECIOS[plan],
                    plan=plan
                )
                db.session.add(pago)
                pagos_creados.append(pago)
            
            # Simular algunos pagos con errores (aproximadamente 10%)
            if random.random() < 0.1:
                # Pago con fecha de vencimiento anterior a fecha de pago
                fecha_erronea = datetime.now() - timedelta(days=random.randint(1, 10))
                pago_error = PagoMensualidad(
                    usuario_id=usuario.id,
                    fecha_pago=fecha_erronea,
                    fecha_inicio=fecha_erronea,
                    fecha_fin=fecha_erronea - timedelta(days=1),  # Error: fin antes del inicio
                    metodo_pago=random.choice(METODOS_PAGO),
                    monto=PRECIOS[random.choice(PLANES)],
                    plan=random.choice(PLANES)
                )
                db.session.add(pago_error)
                pagos_creados.append(pago_error)
        
        # Commit de todos los cambios
        db.session.commit()
        print(f"COMPLETADO: Creados {len(usuarios_creados)} usuarios y {len(pagos_creados)} pagos de prueba")
    
    return usuarios_creados, pagos_creados

def validar_pagos(app):
    """Verifica la integridad y consistencia de los pagos en el sistema"""
    print("\nValidando integridad de datos de pagos...")
    
    errores = []
    estadisticas = {
        "total_pagos": 0,
        "pagos_validos": 0,
        "pagos_invalidos": 0,
        "usuarios_sin_pagos": 0,
        "pagos_sin_usuario": 0,
        "pagos_monto_incorrecto": 0,
        "pagos_fecha_invalida": 0,
        "pagos_metodo_invalido": 0
    }
    
    with app.app_context():
        # Verificar que cada usuario tiene al menos un pago
        usuarios = Usuario.query.all()
        pagos = PagoMensualidad.query.all()
        
        estadisticas["total_pagos"] = len(pagos)
        
        # Verificar usuarios sin pagos
        for usuario in usuarios:
            pagos_usuario = PagoMensualidad.query.filter_by(usuario_id=usuario.id).all()
            if not pagos_usuario:
                estadisticas["usuarios_sin_pagos"] += 1
                errores.append(f"ERROR: Usuario {usuario.id} ({usuario.nombre}) no tiene pagos registrados")
        
        # Verificar la validez de cada pago
        for pago in pagos:
            es_valido = True
            
            # 1. Verificar que el pago pertenece a un usuario existente
            usuario = Usuario.query.get(pago.usuario_id)
            if not usuario:
                es_valido = False
                estadisticas["pagos_sin_usuario"] += 1
                errores.append(f"ERROR: Pago {pago.id} está asociado a un usuario inexistente (ID {pago.usuario_id})")
            
            # 2. Verificar fechas
            if pago.fecha_pago is None or pago.fecha_inicio is None or pago.fecha_fin is None:
                es_valido = False
                estadisticas["pagos_fecha_invalida"] += 1
                errores.append(f"ERROR: Pago {pago.id} tiene fechas nulas")
            elif pago.fecha_fin <= pago.fecha_inicio:
                es_valido = False
                estadisticas["pagos_fecha_invalida"] += 1
                errores.append(f"ERROR: Pago {pago.id} tiene fechas ilógicas: fin ({pago.fecha_fin}) anterior o igual a inicio ({pago.fecha_inicio})")
            
            # 3. Verificar métodos de pago
            if pago.metodo_pago not in METODOS_PAGO:
                es_valido = False
                estadisticas["pagos_metodo_invalido"] += 1
                errores.append(f"ERROR: Pago {pago.id} tiene un método de pago inválido: {pago.metodo_pago}")
            
            # 4. Verificar montos según el plan
            if hasattr(pago, 'plan') and pago.plan in PRECIOS:
                precio_esperado = PRECIOS[pago.plan]
                if pago.monto != precio_esperado:
                    es_valido = False
                    estadisticas["pagos_monto_incorrecto"] += 1
                    errores.append(f"ERROR: Pago {pago.id} tiene un monto incorrecto: {pago.monto} (esperado: {precio_esperado} para plan {pago.plan})")
            
            # Actualizar estadísticas
            if es_valido:
                estadisticas["pagos_validos"] += 1
            else:
                estadisticas["pagos_invalidos"] += 1
    
    # Mostrar reporte de errores (limitado a los primeros 10)
    if errores:
        print("\nDetalles de errores encontrados:")
        for i, error in enumerate(errores[:10]):
            print(f"  {error}")
        if len(errores) > 10:
            print(f"  ... y {len(errores) - 10} errores más")
    
    # Mostrar estadísticas
    print("\nEstadísticas de validación:")
    print(f"  • Total de pagos evaluados: {estadisticas['total_pagos']}")
    print(f"  • Pagos válidos: {estadisticas['pagos_validos']} ({100 * estadisticas['pagos_validos'] / estadisticas['total_pagos']:.1f}% del total)")
    print(f"  • Pagos inválidos: {estadisticas['pagos_invalidos']}")
    print(f"  • Usuarios sin pagos: {estadisticas['usuarios_sin_pagos']}")
    print(f"  • Pagos sin usuario válido: {estadisticas['pagos_sin_usuario']}")
    print(f"  • Pagos con monto incorrecto: {estadisticas['pagos_monto_incorrecto']}")
    print(f"  • Pagos con fechas inválidas: {estadisticas['pagos_fecha_invalida']}")
    print(f"  • Pagos con método de pago inválido: {estadisticas['pagos_metodo_invalido']}")
    
    # Determinar si la prueba pasa
    porcentaje_validos = 100 * estadisticas['pagos_validos'] / estadisticas['total_pagos'] if estadisticas['total_pagos'] > 0 else 0
    prueba_exitosa = porcentaje_validos >= 90  # Al menos 90% de pagos válidos para considerar exitosa la prueba
    
    if prueba_exitosa:
        print("\nCOMPLETADO: PRUEBA DE INTEGRIDAD DE PAGOS EXITOSA")
    else:
        print("\nERROR: PRUEBA DE INTEGRIDAD DE PAGOS FALLIDA")
    
    return prueba_exitosa

def realizar_pruebas_pagos(num_usuarios=10, pagos_por_usuario=3):
    """Ejecuta pruebas completas sobre el sistema de pagos"""
    print("=" * 60)
    print(f" PRUEBAS DE INTEGRIDAD DEL SISTEMA DE PAGOS - GYMTRACK ")
    print("=" * 60)
    
    # Crear aplicación de prueba
    app = crear_app_test()
    
    # Generar datos de prueba
    usuarios, pagos = generar_pagos_test(app, num_usuarios, pagos_por_usuario)
    
    # Validar integridad de pagos
    resultado = validar_pagos(app)
    
    print("\n" + "=" * 60)
    if resultado:
        print("COMPLETADO: El sistema de pagos es SÓLIDO (más del 90% de pagos válidos)")
    else:
        print("ERROR: El sistema de pagos necesita MEJORAS (menos del 90% de pagos válidos)")
    print("=" * 60)
    
    return resultado

if __name__ == "__main__":
    # Determinar el número de usuarios y pagos para las pruebas
    num_usuarios = 10
    pagos_por_usuario = 3
    
    # Leer argumentos de la línea de comandos
    if len(sys.argv) > 1:
        try:
            num_usuarios = int(sys.argv[1])
        except ValueError:
            print(f"Error: El primer argumento debe ser un número entero. Usando valor por defecto: {num_usuarios}")
    
    if len(sys.argv) > 2:
        try:
            pagos_por_usuario = int(sys.argv[2])
        except ValueError:
            print(f"Error: El segundo argumento debe ser un número entero. Usando valor por defecto: {pagos_por_usuario}")
    
    # Ejecutar pruebas
    resultado = realizar_pruebas_pagos(num_usuarios, pagos_por_usuario)
    
    # Salir con código apropiado
    sys.exit(0 if resultado else 1) 