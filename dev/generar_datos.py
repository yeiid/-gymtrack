#!/usr/bin/env python
"""
Script para generar datos de prueba en la base de datos de GymTrack
Creado para facilitar la carga de datos de muestra en el sistema
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
from flask import Flask
from datetime import datetime, timedelta
import sqlite3

# Asegurar que se pueda importar desde el directorio raíz
sys.path.insert(0, os.path.abspath("."))

try:
    from models import db, Usuario, Admin, MedidasCorporales, ObjetivoPersonal, Asistencia, PagoMensualidad
    from app_launcher import create_app, crear_respaldo_automatico
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    print("Asegúrate de ejecutar este script desde el directorio raíz del proyecto")
    sys.exit(1)

def verificar_estructura_bd():
    """Verifica y actualiza la estructura de la base de datos si es necesario"""
    print("\n--- Verificando estructura de la base de datos ---")
    
    # Conectar a la base de datos directamente con sqlite3
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Verificar si la tabla objetivo_personal tiene la columna fecha_completado
    cursor.execute('PRAGMA table_info(objetivo_personal)')
    columnas = [x[1] for x in cursor.fetchall()]
    
    if 'fecha_completado' not in columnas:
        print("Añadiendo columna fecha_completado a la tabla objetivo_personal...")
        try:
            # Añadir la columna fecha_completado
            cursor.execute('ALTER TABLE objetivo_personal ADD COLUMN fecha_completado DATE')
            conn.commit()
            print("✅ Columna fecha_completado añadida correctamente")
        except sqlite3.Error as e:
            print(f"❌ Error al añadir columna: {e}")
    else:
        print("✅ La estructura de la base de datos es correcta")
    
    conn.close()

def generar_admin(app):
    """Crea un usuario administrador si no existe"""
    with app.app_context():
        admin_count = Admin.query.filter_by(usuario='admin').count()
        
        if admin_count == 0:
            print("\n--- Creando usuario administrador ---")
            admin = Admin(
                nombre="Administrador Principal",
                usuario="admin",
                rol="administrador"
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario admin creado con éxito.")
        else:
            print("\n--- Actualizando usuario administrador ---")
            admin = Admin.query.filter_by(usuario='admin').first()
            admin.rol = "administrador"
            db.session.commit()
            print("✅ Usuario admin actualizado a rol administrador.")
            
        print("\nCredenciales de administrador:")
        print("Usuario: admin")
        print("Contraseña: admin123")

def cargar_datos_dev(app):
    """Carga datos de desarrollo ejecutando los scripts existentes"""
    print("\n--- Intentando cargar datos mediante scripts de desarrollo ---")
    
    # Verificar existencia de scripts
    scripts_dev = [
        "dev/generar_100_usuarios.py",
        "dev/generar_asistencias.py",
        "dev/generar_medidas_objetivos.py"
    ]
    
    for script in scripts_dev:
        if not os.path.exists(script):
            print(f"❌ Script no encontrado: {script}")
            return False
    
    try:
        # Ejecutar los scripts en secuencia usando subprocess
        for script in scripts_dev:
            print(f"\nEjecutando: {script}")
            result = subprocess.run([sys.executable, script], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Error al ejecutar {script}:")
                print(result.stderr)
                return False
            print(result.stdout)
        
        return True
    except Exception as e:
        print(f"❌ Error al ejecutar scripts: {e}")
        return False

def generar_datos_manualmente(app, num_usuarios=20, meses_historial=3):
    """Genera datos de prueba directamente en este script"""
    print("\n--- Generando datos manualmente ---")
    
    # Crear respaldo antes de modificar
    crear_respaldo_automatico()
    
    # Verificar y corregir la estructura de la base de datos
    verificar_estructura_bd()
    
    with app.app_context():
        # 1. Generar usuarios aleatorios
        print(f"\nGenerando {num_usuarios} usuarios aleatorios...")
        usuarios_generados = generar_usuarios_aleatorios(num_usuarios)
        print(f"✅ {len(usuarios_generados)} usuarios creados correctamente")
        
        # 2. Generar asistencias para esos usuarios
        print(f"\nGenerando asistencias para los últimos {meses_historial} meses...")
        generar_asistencias_aleatorias(usuarios_generados, meses_historial)
        print("✅ Asistencias generadas correctamente")
        
        # 3. Generar medidas corporales y objetivos para usuarios con planes premium
        print("\nGenerando medidas corporales y objetivos para usuarios premium...")
        generar_medidas_y_objetivos(usuarios_generados, meses_historial)
        print("✅ Medidas y objetivos generados correctamente")
        
    print("\n✅ Todos los datos se han generado correctamente")

def generar_usuarios_aleatorios(cantidad):
    """Genera la cantidad especificada de usuarios aleatorios"""
    import random
    import string
    from datetime import datetime, timedelta
    
    # Datos para generación aleatoria
    NOMBRES = [
        "Juan", "Carlos", "Miguel", "David", "José", "Pedro", "Daniel", "Antonio", 
        "María", "Ana", "Laura", "Carmen", "Isabel", "Sofia", "Paula", "Lucía",
        "Alejandro", "Javier", "Fernando", "Roberto", "Diego", "Francisco", 
        "Patricia", "Claudia", "Mónica", "Elena", "Natalia", "Andrea", "Gabriela"
    ]

    APELLIDOS = [
        "García", "Rodríguez", "López", "Martínez", "González", "Pérez", "Sánchez", 
        "Romero", "Hernández", "Díaz", "Torres", "Ramírez", "Ruiz", "Vargas", 
        "Morales", "Ortiz", "Castro", "Jiménez", "Gutiérrez", "Álvarez", "Mendoza"
    ]

    PLANES = ["Diario", "Quincenal", "Mensual", "Estudiantil", "Dirigido", "Personalizado"]
    METODOS_PAGO = ["Efectivo", "Transferencia", "Tarjeta", "Nequi", "Daviplata"]
    
    usuarios_creados = []
    
    for i in range(cantidad):
        # Generar datos aleatorios
        nombre = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}"
        
        # Generar teléfono único
        while True:
            prefijo = random.choice(["300", "301", "302", "310", "311", "312", "313", "320", "321"])
            telefono = f"{prefijo}{''.join(random.choices(string.digits, k=7))}"
            if Usuario.query.filter_by(telefono=telefono).first() is None:
                break
        
        plan = random.choice(PLANES)
        metodo_pago = random.choice(METODOS_PAGO)
        
        # Fechas y precios
        fecha_ingreso = datetime.now() - timedelta(days=random.randint(1, 60))
        
        # Determinar precio según el plan
        if plan == "Diario":
            precio = Usuario.PRECIO_DIARIO
            dias_vigencia = 1
        elif plan == "Quincenal":
            precio = Usuario.PRECIO_QUINCENAL
            dias_vigencia = 15
        elif plan == "Mensual":
            precio = Usuario.PRECIO_MENSUAL
            dias_vigencia = 30
        elif plan == "Estudiantil":
            precio = Usuario.PRECIO_ESTUDIANTIL
            dias_vigencia = 30
        elif plan == "Dirigido":
            precio = Usuario.PRECIO_DIRIGIDO
            dias_vigencia = 30
        elif plan == "Personalizado":
            precio = Usuario.PRECIO_PERSONALIZADO
            dias_vigencia = 30
        
        fecha_vencimiento = fecha_ingreso + timedelta(days=dias_vigencia)
        
        # Crear usuario
        usuario = Usuario(
            nombre=nombre,
            telefono=telefono,
            plan=plan,
            metodo_pago=metodo_pago,
            fecha_ingreso=fecha_ingreso,
            fecha_vencimiento_plan=fecha_vencimiento,
            precio_plan=precio
        )
        db.session.add(usuario)
        
        # Crear pago asociado
        pago = PagoMensualidad(
            usuario=usuario,
            fecha_pago=fecha_ingreso,
            monto=precio,
            metodo_pago=metodo_pago,
            plan=plan,
            fecha_inicio=fecha_ingreso,
            fecha_fin=fecha_vencimiento
        )
        db.session.add(pago)
        
        usuarios_creados.append(usuario)
    
    # Commit los cambios
    db.session.commit()
    return usuarios_creados

def generar_asistencias_aleatorias(usuarios, meses=3):
    """Genera asistencias aleatorias para los usuarios en los últimos meses"""
    import random
    from datetime import datetime, timedelta
    
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=30 * meses)
    
    # Para cada usuario, generar asistencias aleatorias
    for usuario in usuarios:
        # Determinar cuántas veces por semana asiste según su plan
        if usuario.plan in ["Dirigido", "Personalizado"]:
            dias_por_semana = random.randint(4, 6)  # Planes premium asisten más
        elif usuario.plan in ["Mensual", "Estudiantil"]:
            dias_por_semana = random.randint(3, 5)  # Planes mensuales asistencia media
        else:
            dias_por_semana = random.randint(1, 3)  # Planes cortos asisten menos
        
        # Generar asistencias durante el período
        current_date = fecha_inicio
        while current_date <= fecha_fin:
            # Decidir aleatoriamente si asistió este día
            if random.randint(1, 7) <= dias_por_semana:
                # Generar una hora aleatoria entre 8:00 y 21:00
                hour = random.randint(8, 21)
                minute = random.randint(0, 59)
                fecha_asistencia = current_date.replace(hour=hour, minute=minute)
                
                # Crear registro de asistencia
                asistencia = Asistencia(
                    usuario_id=usuario.id,
                    fecha=fecha_asistencia
                )
                db.session.add(asistencia)
            
            # Avanzar al siguiente día
            current_date += timedelta(days=1)
    
    # Commit los cambios
    db.session.commit()

def generar_medidas_y_objetivos(usuarios, meses=3):
    """Genera medidas corporales y objetivos para usuarios con planes premium"""
    import random
    from datetime import datetime, timedelta
    
    fecha_fin = datetime.now()
    
    # Seleccionar solo usuarios con planes premium
    usuarios_premium = [u for u in usuarios if u.plan in ["Dirigido", "Personalizado"]]
    
    if not usuarios_premium:
        print("No hay usuarios premium para generar medidas y objetivos.")
        return
    
    print(f"Generando medidas para {len(usuarios_premium)} usuarios premium...")
    
    # Para cada usuario premium, generar medidas mensuales
    for usuario in usuarios_premium:
        # Generar medidas iniciales
        peso_inicial = random.uniform(60.0, 100.0)
        altura = random.uniform(1.60, 1.90)
        imc_inicial = peso_inicial / (altura * altura)
        
        pecho_inicial = random.uniform(80.0, 120.0)
        cintura_inicial = random.uniform(70.0, 110.0)
        cadera_inicial = random.uniform(80.0, 120.0)
        brazo_inicial = random.uniform(25.0, 45.0)
        pierna_inicial = random.uniform(40.0, 70.0)
        
        # Generar medidas progresivas para cada mes
        for mes in range(meses + 1):
            fecha_medida = fecha_fin - timedelta(days=30 * (meses - mes))
            
            # Calcular progreso (mejora gradual)
            factor_progreso = mes / (meses + 1)  # 0 al inicio, cerca de 1 al final
            
            # Para usuarios de plan personalizado, mejores resultados
            if usuario.plan == "Personalizado":
                factor_mejora = 0.95  # Reducción de medidas en plan personalizado
            else:
                factor_mejora = 0.97  # Reducción menor en plan dirigido
            
            # Calcular medidas con progreso
            peso_actual = peso_inicial * (1 - (0.05 * factor_progreso))
            imc_actual = peso_actual / (altura * altura)
            
            # Las medidas disminuyen gradualmente (excepto brazos/piernas que aumentan por músculo)
            pecho_actual = pecho_inicial * (1 - (0.03 * factor_progreso))
            cintura_actual = cintura_inicial * (1 - (0.08 * factor_progreso))
            cadera_actual = cadera_inicial * (1 - (0.04 * factor_progreso))
            brazo_actual = brazo_inicial * (1 + (0.05 * factor_progreso))
            pierna_actual = pierna_inicial * (1 + (0.03 * factor_progreso))
            
            # Crear registro de medidas
            medidas = MedidasCorporales(
                usuario_id=usuario.id,
                fecha=fecha_medida,
                peso=round(peso_actual, 1),
                altura=round(altura, 2),
                imc=round(imc_actual, 1),
                pecho=round(pecho_actual, 1),
                cintura=round(cintura_actual, 1),
                cadera=round(cadera_actual, 1),
                brazo_izquierdo=round(brazo_actual * random.uniform(0.98, 1.02), 1),
                brazo_derecho=round(brazo_actual, 1),
                pierna_izquierda=round(pierna_actual * random.uniform(0.98, 1.02), 1),
                pierna_derecha=round(pierna_actual, 1),
                notas="Medidas tomadas durante sesión regular."
            )
            db.session.add(medidas)
        
        # Generar objetivos personales (2-4 por usuario)
        num_objetivos = random.randint(2, 4)
        
        OBJETIVOS_TEMPLATES = [
            "Reducir peso a {peso_objetivo} kg",
            "Reducir medida de cintura a {cintura_objetivo} cm",
            "Aumentar masa muscular en brazos",
            "Mejorar resistencia cardiovascular",
            "Completar {num} sesiones de entrenamiento este mes",
            "Reducir porcentaje de grasa corporal",
            "Mejorar flexibilidad general",
            "Aumentar fuerza en press de banca"
        ]
        
        # Calcular objetivos personalizados
        peso_objetivo = round(peso_inicial * 0.9, 1)  # 10% menos que el inicial
        cintura_objetivo = round(cintura_inicial * 0.9, 1)  # 10% menos que la inicial
        
        for _ in range(num_objetivos):
            # Elegir un objetivo aleatorio
            plantilla = random.choice(OBJETIVOS_TEMPLATES)
            
            # Personalizar el objetivo
            if "{peso_objetivo}" in plantilla:
                descripcion = plantilla.format(peso_objetivo=peso_objetivo)
            elif "{cintura_objetivo}" in plantilla:
                descripcion = plantilla.format(cintura_objetivo=cintura_objetivo)
            elif "{num}" in plantilla:
                descripcion = plantilla.format(num=random.randint(12, 20))
            else:
                descripcion = plantilla
            
            # Fecha de creación aleatoria en los últimos meses
            dias_atras = random.randint(10, 30 * meses)
            fecha_creacion = fecha_fin - timedelta(days=dias_atras)
            
            # Fecha objetivo entre 1 y 3 meses después de la creación
            dias_objetivo = random.randint(30, 90)
            fecha_objetivo = fecha_creacion + timedelta(days=dias_objetivo)
            
            # Determinar si está completado
            completado = fecha_objetivo < fecha_fin and random.random() < 0.3
            fecha_completado = fecha_objetivo - timedelta(days=random.randint(0, 10)) if completado else None
            
            # Calcular progreso
            if completado:
                progreso = 100
            else:
                # Progreso basado en cuánto tiempo ha pasado hacia la fecha objetivo
                tiempo_total = (fecha_objetivo - fecha_creacion).days
                tiempo_transcurrido = (fecha_fin - fecha_creacion).days
                if tiempo_total > 0:
                    progreso = min(95, int(100 * tiempo_transcurrido / tiempo_total))
                else:
                    progreso = random.randint(10, 90)
            
            # Crear objetivo - Ahora con fecha_completado que fue añadida a la tabla
            objetivo = ObjetivoPersonal(
                usuario_id=usuario.id,
                descripcion=descripcion,
                fecha_creacion=fecha_creacion,
                fecha_objetivo=fecha_objetivo,
                fecha_completado=fecha_completado,
                completado=completado,
                progreso=progreso
            )
            db.session.add(objetivo)
    
    # Commit los cambios
    db.session.commit()

def menu_principal():
    """Muestra el menú principal y gestiona la interacción con el usuario"""
    print("\n" + "=" * 60)
    print(" HERRAMIENTA DE GENERACIÓN DE DATOS PARA GYMTRACK ")
    print("=" * 60)
    
    print("\nEsta herramienta te permite generar datos de prueba para el sistema GymTrack.")
    print("Por favor, selecciona una opción del menú:")
    
    print("\n1. Generar datos de prueba completos (usuarios, asistencias, medidas, objetivos)")
    print("2. Generar solo usuarios aleatorios")
    print("3. Crear/actualizar usuario administrador")
    print("4. Ejecutar scripts de desarrollo originales")
    print("5. Salir")
    
    while True:
        try:
            opcion = int(input("\nSelecciona una opción (1-5): "))
            if 1 <= opcion <= 5:
                return opcion
            else:
                print("Por favor, ingresa un número entre 1 y 5.")
        except ValueError:
            print("Por favor, ingresa un número válido.")

if __name__ == "__main__":
    # Crear la aplicación Flask
    app = create_app()
    
    # Procesar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Generador de datos para GymTrack')
    parser.add_argument('--opcion', type=int, choices=[1, 2, 3, 4, 5], 
                        help='Opción a ejecutar (1-5, igual que en el menú)')
    parser.add_argument('--usuarios', type=int, default=20,
                        help='Número de usuarios a generar (predeterminado: 20)')
    parser.add_argument('--meses', type=int, default=3,
                        help='Meses de historial a generar (predeterminado: 3)')
    
    args = parser.parse_args()
    
    if args.opcion:
        opcion = args.opcion
    else:
        opcion = menu_principal()
    
    try:
        if opcion == 1:
            print("\n--- Generando datos de prueba completos ---")
            generar_datos_manualmente(app, args.usuarios, args.meses)
            
        elif opcion == 2:
            print("\n--- Generando solo usuarios aleatorios ---")
            with app.app_context():
                usuarios = generar_usuarios_aleatorios(args.usuarios)
                print(f"✅ {len(usuarios)} usuarios creados correctamente")
            
        elif opcion == 3:
            print("\n--- Creando/actualizando usuario administrador ---")
            generar_admin(app)
            
        elif opcion == 4:
            print("\n--- Ejecutando scripts de desarrollo originales ---")
            if not cargar_datos_dev(app):
                print("\n❌ Error al ejecutar scripts de desarrollo.")
                print("Intenta ejecutar la opción 1 como alternativa.")
            
        elif opcion == 5:
            print("\nSaliendo del programa...")
            sys.exit(0)
    
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    print("\n✅ Operación completada. Puedes iniciar la aplicación para ver los cambios.") 