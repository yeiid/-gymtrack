#!/usr/bin/env python
"""
Test de integridad para el sistema de gestión de clases y asistencias de GymTrack.
Este script verifica la correcta programación de clases, registro de asistencias,
y la relación entre usuarios, clases y asistencias.
"""
import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# Añadir el directorio raíz al path para que se puedan encontrar los módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar los módulos de la aplicación
try:
    from models import db, Usuario, Clase, Asistencia, Instructor
    import config
except ImportError as e:
    print(f"ERROR: Error al importar módulos: {e}")
    print("Asegúrate de ejecutar el script desde el directorio raíz del proyecto")
    sys.exit(1)

# Constantes para generación de datos de prueba
TIPOS_CLASE = ["Spinning", "Yoga", "Pilates", "Crossfit", "Zumba", "Funcional", "Boxeo"]
HORARIOS = ["06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "16:00", "17:00", "18:00", "19:00", "20:00"]
DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
NOMBRES_INSTRUCTOR = ["Juan", "Carlos", "María", "Ana", "Pedro", "Laura", "Diego", "Sofía"]
APELLIDOS_INSTRUCTOR = ["García", "Rodríguez", "López", "Martínez", "González", "Pérez", "Sánchez", "Ramírez"]

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

def generar_instructores_test(num_instructores=5):
    """Genera instructores de prueba en la base de datos"""
    instructores = []
    
    for i in range(num_instructores):
        nombre = random.choice(NOMBRES_INSTRUCTOR)
        apellido = random.choice(APELLIDOS_INSTRUCTOR)
        especialidad = random.choice(TIPOS_CLASE)
        
        instructor = Instructor(
            nombre=f"{nombre} {apellido}",
            especialidad=especialidad,
            telefono=f"3{random.randint(10, 99)}{random.randint(1000000, 9999999)}"
        )
        db.session.add(instructor)
        instructores.append(instructor)
    
    # Commit de los instructores
    db.session.commit()
    
    return instructores

def generar_clases_test(instructores, num_clases=20):
    """Genera clases de prueba en la base de datos"""
    clases = []
    
    for i in range(num_clases):
        tipo_clase = random.choice(TIPOS_CLASE)
        dia = random.choice(DIAS_SEMANA)
        hora = random.choice(HORARIOS)
        duracion = random.choice([45, 60, 90])
        capacidad = random.randint(10, 30)
        
        # Asignar un instructor preferentemente con la especialidad adecuada
        instructores_especialidad = [i for i in instructores if i.especialidad == tipo_clase]
        if instructores_especialidad:
            instructor = random.choice(instructores_especialidad)
        else:
            instructor = random.choice(instructores)
        
        clase = Clase(
            tipo=tipo_clase,
            dia=dia,
            hora=hora,
            duracion=duracion,
            capacidad=capacidad,
            instructor_id=instructor.id
        )
        db.session.add(clase)
        clases.append(clase)
    
    # Simular algunas clases con errores
    # 1. Clase sin instructor
    clase_error1 = Clase(
        tipo=random.choice(TIPOS_CLASE),
        dia=random.choice(DIAS_SEMANA),
        hora=random.choice(HORARIOS),
        duracion=60,
        capacidad=20,
        instructor_id=None  # Error: sin instructor
    )
    db.session.add(clase_error1)
    clases.append(clase_error1)
    
    # 2. Clase con capacidad inválida
    clase_error2 = Clase(
        tipo=random.choice(TIPOS_CLASE),
        dia=random.choice(DIAS_SEMANA),
        hora=random.choice(HORARIOS),
        duracion=60,
        capacidad=0,  # Error: capacidad inválida
        instructor_id=random.choice(instructores).id
    )
    db.session.add(clase_error2)
    clases.append(clase_error2)
    
    # Commit de las clases
    db.session.commit()
    
    return clases

def generar_usuarios_test(num_usuarios=30):
    """Genera usuarios de prueba en la base de datos"""
    usuarios = []
    
    for i in range(num_usuarios):
        nombre = f"Usuario Test {i+1}"
        telefono = f"3{random.randint(10, 99)}{random.randint(1000000, 9999999)}"
        
        usuario = Usuario(
            nombre=nombre,
            telefono=telefono,
            plan=random.choice(["Mensual", "Trimestral", "Semestral", "Anual"])
        )
        db.session.add(usuario)
        usuarios.append(usuario)
    
    # Commit de los usuarios
    db.session.commit()
    
    return usuarios

def generar_asistencias_test(usuarios, clases, num_semanas=4):
    """Genera asistencias de prueba en la base de datos"""
    asistencias = []
    
    # Calcular fecha base (primer día de la semana hace num_semanas)
    fecha_base = datetime.now() - timedelta(days=num_semanas * 7)
    
    # Generar asistencias durante las semanas pasadas
    for semana in range(num_semanas):
        fecha_semana = fecha_base + timedelta(days=semana * 7)
        
        # Por cada clase, registrar algunas asistencias
        for clase in clases:
            # Saltear clases con error (sin instructor o capacidad 0)
            if clase.instructor_id is None or clase.capacidad <= 0:
                continue
                
            # Determinar el día de la semana para esta clase
            dia_indice = DIAS_SEMANA.index(clase.dia) if clase.dia in DIAS_SEMANA else 0
            fecha_clase = fecha_semana + timedelta(days=dia_indice)
            
            # Determinar cuántos usuarios asistieron (entre 30% y 90% de la capacidad)
            porcentaje_asistencia = random.uniform(0.3, 0.9)
            num_asistentes = min(int(clase.capacidad * porcentaje_asistencia), len(usuarios))
            
            # Seleccionar usuarios al azar para esta clase
            asistentes = random.sample(usuarios, num_asistentes)
            
            # Registrar asistencias
            for usuario in asistentes:
                asistencia = Asistencia(
                    usuario_id=usuario.id,
                    clase_id=clase.id,
                    fecha=fecha_clase
                )
                db.session.add(asistencia)
                asistencias.append(asistencia)
            
            # Simular algunas asistencias con errores (fechas futuras)
            if random.random() < 0.05:  # 5% de probabilidad
                fecha_futura = datetime.now() + timedelta(days=random.randint(1, 30))
                usuario_aleatorio = random.choice(usuarios)
                
                asistencia_error = Asistencia(
                    usuario_id=usuario_aleatorio.id,
                    clase_id=clase.id,
                    fecha=fecha_futura  # Error: fecha futura
                )
                db.session.add(asistencia_error)
                asistencias.append(asistencia_error)
    
    # Commit de todas las asistencias
    db.session.commit()
    
    return asistencias

def validar_clases_asistencias():
    """Verifica la integridad y consistencia de las clases y asistencias"""
    print("\nValidando integridad de datos de clases y asistencias...")
    
    errores = []
    estadisticas = {
        "total_clases": 0,
        "clases_validas": 0,
        "clases_invalidas": 0,
        "total_asistencias": 0,
        "asistencias_validas": 0,
        "asistencias_invalidas": 0,
        "clases_sin_instructor": 0,
        "clases_capacidad_invalida": 0,
        "asistencias_fecha_futura": 0,
        "asistencias_clase_invalida": 0,
        "asistencias_usuario_invalido": 0,
        "conflictos_horario": 0
    }
    
    # 1. Validar clases
    clases = Clase.query.all()
    estadisticas["total_clases"] = len(clases)
    
    for clase in clases:
        es_valida = True
        
        # Verificar instructor asignado
        if clase.instructor_id is None:
            es_valida = False
            estadisticas["clases_sin_instructor"] += 1
            errores.append(f"ERROR: Clase {clase.id} ({clase.tipo}) no tiene instructor asignado")
        
        # Verificar capacidad válida
        if clase.capacidad <= 0:
            es_valida = False
            estadisticas["clases_capacidad_invalida"] += 1
            errores.append(f"ERROR: Clase {clase.id} ({clase.tipo}) tiene capacidad inválida: {clase.capacidad}")
        
        # Verificar conflictos de horario (mismo instructor, mismo día y hora)
        clases_mismo_horario = Clase.query.filter(
            Clase.id != clase.id,
            Clase.dia == clase.dia,
            Clase.hora == clase.hora,
            Clase.instructor_id == clase.instructor_id
        ).all()
        
        if clases_mismo_horario:
            es_valida = False
            estadisticas["conflictos_horario"] += 1
            errores.append(f"ERROR: Clase {clase.id} ({clase.tipo}) tiene conflicto de horario: el instructor ya tiene otra clase el {clase.dia} a las {clase.hora}")
        
        # Actualizar estadísticas
        if es_valida:
            estadisticas["clases_validas"] += 1
        else:
            estadisticas["clases_invalidas"] += 1
    
    # 2. Validar asistencias
    asistencias = Asistencia.query.all()
    estadisticas["total_asistencias"] = len(asistencias)
    
    for asistencia in asistencias:
        es_valida = True
        
        # Verificar que la clase existe
        clase = Clase.query.get(asistencia.clase_id)
        if not clase:
            es_valida = False
            estadisticas["asistencias_clase_invalida"] += 1
            errores.append(f"ERROR: Asistencia {asistencia.id} está asociada a una clase inexistente (ID {asistencia.clase_id})")
        
        # Verificar que el usuario existe
        usuario = Usuario.query.get(asistencia.usuario_id)
        if not usuario:
            es_valida = False
            estadisticas["asistencias_usuario_invalido"] += 1
            errores.append(f"ERROR: Asistencia {asistencia.id} está asociada a un usuario inexistente (ID {asistencia.usuario_id})")
        
        # Verificar que la fecha no es futura
        if asistencia.fecha > datetime.now():
            es_valida = False
            estadisticas["asistencias_fecha_futura"] += 1
            errores.append(f"ERROR: Asistencia {asistencia.id} tiene fecha futura: {asistencia.fecha}")
        
        # Actualizar estadísticas
        if es_valida:
            estadisticas["asistencias_validas"] += 1
        else:
            estadisticas["asistencias_invalidas"] += 1
    
    # Mostrar reporte de errores (limitado a los primeros 10)
    if errores:
        print("\nDetalles de errores encontrados:")
        for i, error in enumerate(errores[:10]):
            print(f"  {error}")
        if len(errores) > 10:
            print(f"  ... y {len(errores) - 10} errores más")
    
    # Mostrar estadísticas
    print("\nEstadísticas de validación:")
    print(f"  • Total de clases evaluadas: {estadisticas['total_clases']}")
    print(f"  • Clases válidas: {estadisticas['clases_validas']} ({100 * estadisticas['clases_validas'] / estadisticas['total_clases']:.1f}% del total)")
    print(f"  • Clases sin instructor: {estadisticas['clases_sin_instructor']}")
    print(f"  • Clases con capacidad inválida: {estadisticas['clases_capacidad_invalida']}")
    print(f"  • Conflictos de horario detectados: {estadisticas['conflictos_horario']}")
    print(f"\n  • Total de asistencias evaluadas: {estadisticas['total_asistencias']}")
    print(f"  • Asistencias válidas: {estadisticas['asistencias_validas']} ({100 * estadisticas['asistencias_validas'] / estadisticas['total_asistencias']:.1f}% del total)")
    print(f"  • Asistencias con fecha futura: {estadisticas['asistencias_fecha_futura']}")
    print(f"  • Asistencias con clase inválida: {estadisticas['asistencias_clase_invalida']}")
    print(f"  • Asistencias con usuario inválido: {estadisticas['asistencias_usuario_invalido']}")
    
    # Determinar si la prueba pasa
    porcentaje_clases_validas = 100 * estadisticas['clases_validas'] / estadisticas['total_clases'] if estadisticas['total_clases'] > 0 else 0
    porcentaje_asistencias_validas = 100 * estadisticas['asistencias_validas'] / estadisticas['total_asistencias'] if estadisticas['total_asistencias'] > 0 else 0
    
    # La prueba pasa si al menos 90% de clases y asistencias son válidas
    prueba_exitosa = porcentaje_clases_validas >= 90 and porcentaje_asistencias_validas >= 90
    
    if prueba_exitosa:
        print("\nCOMPLETADO: PRUEBA DE INTEGRIDAD DE CLASES Y ASISTENCIAS EXITOSA")
    else:
        print("\nERROR: PRUEBA DE INTEGRIDAD DE CLASES Y ASISTENCIAS FALLIDA")
    
    return prueba_exitosa

def realizar_pruebas_clases_asistencias(num_instructores=5, num_clases=20, num_usuarios=30, num_semanas=4):
    """Ejecuta pruebas completas sobre el sistema de clases y asistencias"""
    print("=" * 70)
    print(f" PRUEBAS DE INTEGRIDAD DEL SISTEMA DE CLASES Y ASISTENCIAS - GYMTRACK ")
    print("=" * 70)
    
    # Crear aplicación de prueba
    app = crear_app_test()
    
    # Generar datos de prueba
    print("\nGenerando datos de prueba...")
    print(f"  • Instructores: {num_instructores}")
    print(f"  • Clases: {num_clases}")
    print(f"  • Usuarios: {num_usuarios}")
    print(f"  • Período de asistencias: {num_semanas} semanas")
    
    with app.app_context():
        # Generar instructores, clases, usuarios y asistencias dentro del mismo contexto
        instructores = generar_instructores_test(num_instructores)
        clases = generar_clases_test(instructores, num_clases)
        usuarios = generar_usuarios_test(num_usuarios)
        asistencias = generar_asistencias_test(usuarios, clases, num_semanas)
    
        print(f"COMPLETADO: Generados {len(instructores)} instructores, {len(clases)} clases, {len(usuarios)} usuarios y {len(asistencias)} asistencias de prueba")
    
        # Validar integridad de clases y asistencias
        resultado = validar_clases_asistencias()
    
    print("\n" + "=" * 70)
    if resultado:
        print("COMPLETADO: El sistema de clases y asistencias es SÓLIDO (más del 90% de datos válidos)")
    else:
        print("ERROR: El sistema de clases y asistencias necesita MEJORAS (menos del 90% de datos válidos)")
    print("=" * 70)
    
    return resultado

if __name__ == "__main__":
    # Determinar los parámetros para las pruebas
    num_instructores = 5
    num_clases = 20
    num_usuarios = 30
    num_semanas = 4
    
    # Leer argumentos de la línea de comandos
    if len(sys.argv) > 1:
        try:
            num_instructores = int(sys.argv[1])
        except ValueError:
            print(f"Error: El primer argumento debe ser un número entero. Usando valor por defecto: {num_instructores}")
    
    if len(sys.argv) > 2:
        try:
            num_clases = int(sys.argv[2])
        except ValueError:
            print(f"Error: El segundo argumento debe ser un número entero. Usando valor por defecto: {num_clases}")
    
    if len(sys.argv) > 3:
        try:
            num_usuarios = int(sys.argv[3])
        except ValueError:
            print(f"Error: El tercer argumento debe ser un número entero. Usando valor por defecto: {num_usuarios}")
    
    if len(sys.argv) > 4:
        try:
            num_semanas = int(sys.argv[4])
        except ValueError:
            print(f"Error: El cuarto argumento debe ser un número entero. Usando valor por defecto: {num_semanas}")
    
    # Ejecutar pruebas
    resultado = realizar_pruebas_clases_asistencias(num_instructores, num_clases, num_usuarios, num_semanas)
    
    # Salir con código apropiado
    sys.exit(0 if resultado else 1) 