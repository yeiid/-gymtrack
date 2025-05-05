#!/usr/bin/env python
"""
Script para generar medidas corporales y objetivos personales aleatorios
para usuarios con planes dirigidos y personalizados en GymTrack.
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
    from models import db, Usuario, MedidasCorporales, ObjetivoPersonal
except ImportError as e:
    print(f"ERROR: Error al importar módulos: {e}")
    print("Asegúrate de ejecutar el script desde el directorio raíz del proyecto")
    sys.exit(1)

# Lista de posibles objetivos personales
OBJETIVOS = [
    "Reducir peso corporal",
    "Aumentar masa muscular",
    "Mejorar resistencia cardiovascular",
    "Tonificar músculos",
    "Reducir porcentaje de grasa corporal",
    "Mejorar flexibilidad",
    "Aumentar fuerza en piernas",
    "Aumentar fuerza en brazos",
    "Definir abdominales",
    "Mejorar postura corporal",
    "Recuperación de lesión",
    "Preparación para competición",
    "Mantener peso actual",
    "Mejorar salud general",
    "Reducir estrés",
    "Mejorar calidad del sueño"
]

def crear_app():
    """Crea una instancia de la aplicación Flask para importar datos de prueba"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Usar la base de datos principal
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def generar_valor_aleatorio(min_val, max_val, precision=1):
    """Genera un valor aleatorio con la precisión especificada"""
    valor = random.uniform(min_val, max_val)
    return round(valor, precision)

def generar_medidas_corporales(app, historial_meses=6, frecuencia_mensual=1):
    """
    Genera medidas corporales para usuarios con planes dirigidos y personalizados
    
    Args:
        app: Aplicación Flask
        historial_meses: Cantidad de meses de historial a generar
        frecuencia_mensual: Cantidad promedio de mediciones por mes
    """
    print(f"\nGenerando medidas corporales para los últimos {historial_meses} meses...")
    
    with app.app_context():
        # Obtener usuarios con planes dirigidos o personalizados
        usuarios = Usuario.query.filter(Usuario.plan.in_(['Dirigido', 'Personalizado'])).all()
        
        if not usuarios:
            print("❌ No hay usuarios con planes Dirigido o Personalizado en la base de datos.")
            return
        
        print(f"Generando medidas para {len(usuarios)} usuarios con planes premium...")
        
        # Contador de medidas generadas
        medidas_generadas = 0
        
        # Para cada usuario, generar un historial de medidas
        for usuario in usuarios:
            # Configuración inicial de las medidas del usuario
            # Los valores iniciales dependen de la complexión
            complexion = random.choice(['delgada', 'media', 'robusta'])
            
            # Valores iniciales basados en complexión
            if complexion == 'delgada':
                peso_base = generar_valor_aleatorio(55, 65) if random.random() < 0.5 else generar_valor_aleatorio(45, 55)
                altura = generar_valor_aleatorio(160, 180) if random.random() < 0.5 else generar_valor_aleatorio(150, 165)
                factor_medidas = 0.8
            elif complexion == 'media':
                peso_base = generar_valor_aleatorio(65, 80) if random.random() < 0.5 else generar_valor_aleatorio(55, 70)
                altura = generar_valor_aleatorio(165, 185) if random.random() < 0.5 else generar_valor_aleatorio(155, 170)
                factor_medidas = 1.0
            else:  # robusta
                peso_base = generar_valor_aleatorio(80, 100) if random.random() < 0.5 else generar_valor_aleatorio(70, 90)
                altura = generar_valor_aleatorio(170, 190) if random.random() < 0.5 else generar_valor_aleatorio(160, 175)
                factor_medidas = 1.2
            
            # Determinar si el usuario está en proceso de reducción o aumento de peso
            tendencia = random.choice(['reduccion', 'aumento', 'mantenimiento'])
            
            # Tendencia de cambio por mes en kg
            if tendencia == 'reduccion':
                cambio_mensual = -generar_valor_aleatorio(0.5, 2.0)
            elif tendencia == 'aumento':
                cambio_mensual = generar_valor_aleatorio(0.3, 1.5)
            else:
                cambio_mensual = generar_valor_aleatorio(-0.5, 0.5)
            
            # Generar medidas para cada mes
            fecha_actual = datetime.now().date()
            fecha_inicial = fecha_actual - timedelta(days=30 * historial_meses)
            
            # Mes actual de iteración
            mes_actual = fecha_inicial.month
            año_actual = fecha_inicial.year
            
            # Para cada mes en el historial
            for mes in range(historial_meses):
                # Determinar la fecha de las medidas (un día aleatorio del mes)
                if mes == historial_meses - 1:  # último mes (actual)
                    dia_medida = random.randint(1, min(fecha_actual.day, 28))
                    fecha_medida = datetime(fecha_actual.year, fecha_actual.month, dia_medida).date()
                else:
                    dia_medida = random.randint(1, 28)
                    fecha_medida = datetime(año_actual, mes_actual, dia_medida).date()
                
                # Actualizar mes_actual para la siguiente iteración
                mes_actual += 1
                if mes_actual > 12:
                    mes_actual = 1
                    año_actual += 1
                
                # Cálculo del peso con tendencia y variación aleatoria
                peso_mes = peso_base + (cambio_mensual * mes) + generar_valor_aleatorio(-0.5, 0.5)
                if peso_mes < 40:  # establecer un mínimo razonable
                    peso_mes = 40
                
                # Calcular otras medidas basadas en el peso y factor de complexión
                pecho = generar_valor_aleatorio(85, 110, 1) * factor_medidas * (peso_mes / peso_base)
                cintura = generar_valor_aleatorio(65, 90, 1) * factor_medidas * (peso_mes / peso_base)
                cadera = generar_valor_aleatorio(85, 115, 1) * factor_medidas * (peso_mes / peso_base)
                
                # Medidas adicionales con ligeras variaciones para dar realismo
                brazo_derecho = generar_valor_aleatorio(25, 38, 1) * factor_medidas * (peso_mes / peso_base)
                brazo_izquierdo = brazo_derecho * generar_valor_aleatorio(0.95, 1.03, 2)  # ligera asimetría
                
                pierna_derecha = generar_valor_aleatorio(45, 65, 1) * factor_medidas * (peso_mes / peso_base)
                pierna_izquierda = pierna_derecha * generar_valor_aleatorio(0.97, 1.02, 2)  # ligera asimetría
                
                # Calcular IMC
                altura_metros = altura / 100
                imc = peso_mes / (altura_metros * altura_metros)
                
                # Generar notas opcionales (70% de probabilidad de tener notas)
                if random.random() < 0.7:
                    notas_opciones = [
                        f"Progreso {'positivo' if cambio_mensual * mes >= 0 else 'negativo'} este mes.",
                        f"{'Aumento' if peso_mes > peso_base else 'Reducción'} de medidas según lo esperado.",
                        f"IMC actual: {imc:.1f} - {'Bueno' if 18.5 <= imc <= 24.9 else 'Necesita mejorar'}",
                        f"Se recomienda {'aumentar' if imc < 18.5 else 'reducir' if imc > 24.9 else 'mantener'} el peso actual.",
                        "Continuar con el plan de entrenamiento actual.",
                        "Ajustar plan de alimentación.",
                        f"Enfocarse en {'aumentar masa muscular' if tendencia == 'aumento' else 'reducir grasa corporal' if tendencia == 'reduccion' else 'mantener composición corporal'}.",
                        "Las medidas muestran progreso consistente.",
                        "Se observa mejoría en la proporción cintura-cadera."
                    ]
                    notas = random.choice(notas_opciones)
                else:
                    notas = None
                
                # Crear registro de medidas
                medida = MedidasCorporales(
                    usuario_id=usuario.id,
                    fecha=fecha_medida,
                    peso=peso_mes,
                    altura=altura,
                    imc=imc,
                    pecho=pecho,
                    cintura=cintura,
                    cadera=cadera,
                    brazo_izquierdo=brazo_izquierdo,
                    brazo_derecho=brazo_derecho,
                    pierna_izquierda=pierna_izquierda,
                    pierna_derecha=pierna_derecha,
                    notas=notas
                )
                
                db.session.add(medida)
                medidas_generadas += 1
            
            # Commit por cada usuario para no saturar la memoria
            db.session.commit()
        
        print(f"✅ COMPLETADO: Se generaron {medidas_generadas} registros de medidas corporales para {len(usuarios)} usuarios.")

def generar_objetivos_personales(app, objetivos_por_usuario=3):
    """
    Genera objetivos personales para usuarios con planes dirigidos y personalizados
    
    Args:
        app: Aplicación Flask
        objetivos_por_usuario: Cantidad promedio de objetivos por usuario
    """
    print(f"\nGenerando objetivos personales...")
    
    with app.app_context():
        # Obtener usuarios con planes dirigidos o personalizados
        usuarios = Usuario.query.filter(Usuario.plan.in_(['Dirigido', 'Personalizado'])).all()
        
        if not usuarios:
            print("❌ No hay usuarios con planes Dirigido o Personalizado en la base de datos.")
            return
        
        print(f"Generando objetivos para {len(usuarios)} usuarios con planes premium...")
        
        # Contador de objetivos generados
        objetivos_generados = 0
        objetivos_completados = 0
        
        # Para cada usuario, generar objetivos
        for usuario in usuarios:
            # Determinar cuántos objetivos crear (variación aleatoria)
            num_objetivos = max(1, int(objetivos_por_usuario + random.uniform(-1.5, 1.5)))
            
            # Generar objetivos
            for i in range(num_objetivos):
                # Seleccionar un objetivo aleatorio
                descripcion = random.choice(OBJETIVOS)
                
                # Determinar si es un objetivo reciente o más antiguo
                es_reciente = random.random() < 0.6  # 60% de objetivos recientes
                
                # Determinar fecha de creación
                if es_reciente:
                    # Objetivo reciente (últimos 2 meses)
                    dias_atras = random.randint(1, 60)
                else:
                    # Objetivo más antiguo (entre 2 y 6 meses)
                    dias_atras = random.randint(61, 180)
                
                fecha_creacion = datetime.now().date() - timedelta(days=dias_atras)
                
                # Determinar fecha objetivo (entre 1 y 3 meses después de la creación)
                if random.random() < 0.8:  # 80% de probabilidad de tener fecha objetivo
                    dias_objetivo = random.randint(30, 90)
                    fecha_objetivo = fecha_creacion + timedelta(days=dias_objetivo)
                else:
                    fecha_objetivo = None
                
                # Determinar si está completado (más probable si es antiguo)
                if not es_reciente and random.random() < 0.7:  # 70% de objetivos antiguos completados
                    completado = True
                    progreso = 100
                    # Fecha de completado (entre la fecha de creación y hoy o la fecha objetivo)
                    if fecha_objetivo and fecha_objetivo < datetime.now().date():
                        max_dias = (min(fecha_objetivo, datetime.now().date()) - fecha_creacion).days
                    else:
                        max_dias = (datetime.now().date() - fecha_creacion).days
                    
                    dias_hasta_completado = random.randint(1, max(1, max_dias))
                    fecha_completado = fecha_creacion + timedelta(days=dias_hasta_completado)
                    objetivos_completados += 1
                elif es_reciente and random.random() < 0.2:  # 20% de objetivos recientes completados
                    completado = True
                    progreso = 100
                    dias_hasta_completado = random.randint(1, dias_atras)
                    fecha_completado = fecha_creacion + timedelta(days=dias_hasta_completado)
                    objetivos_completados += 1
                else:
                    completado = False
                    # Para objetivos no completados, el progreso varía según antigüedad
                    if es_reciente:
                        progreso = random.randint(0, 70)  # Objetivos recientes tienen menos progreso
                    else:
                        progreso = random.randint(50, 95)  # Objetivos antiguos tienen más progreso
                    fecha_completado = None
                
                # Crear objetivo
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
                objetivos_generados += 1
            
            # Commit por cada usuario
            db.session.commit()
        
        print(f"✅ COMPLETADO: Se generaron {objetivos_generados} objetivos ({objetivos_completados} completados)")

def generar_medidas_y_objetivos(meses_historial=6, frecuencia_medidas=1, objetivos_por_usuario=3):
    """Genera medidas corporales y objetivos personales para usuarios premium"""
    # Crear la aplicación
    app = crear_app()
    
    print("=" * 60)
    print(" GENERACIÓN DE MEDIDAS Y OBJETIVOS DE PRUEBA ")
    print("=" * 60)
    
    # Confirmar la operación
    print("\n⚠️ ADVERTENCIA: Este script agregará datos de medidas corporales y objetivos personales")
    print("a usuarios con planes Dirigido o Personalizado.")
    confirmacion = input("\n¿Deseas continuar? (s/n): ")
    
    if confirmacion.lower() != 's':
        print("Operación cancelada.")
        return
    
    # Generar medidas corporales
    try:
        generar_medidas_corporales(app, meses_historial, frecuencia_medidas)
    except Exception as e:
        print(f"\n❌ ERROR: Ocurrió un problema al generar medidas corporales: {str(e)}")
        return False
    
    # Generar objetivos personales
    try:
        generar_objetivos_personales(app, objetivos_por_usuario)
    except Exception as e:
        print(f"\n❌ ERROR: Ocurrió un problema al generar objetivos personales: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print(" GENERACIÓN COMPLETADA ")
    print("=" * 60)

if __name__ == "__main__":
    # Determinar parámetros
    meses_historial = 6
    frecuencia_medidas = 1
    objetivos_por_usuario = 3
    
    if len(sys.argv) > 1:
        try:
            meses_historial = int(sys.argv[1])
        except ValueError:
            print(f"Error: El primer argumento debe ser un número entero. Usando valor por defecto: {meses_historial}")
    
    if len(sys.argv) > 2:
        try:
            objetivos_por_usuario = int(sys.argv[2])
        except ValueError:
            print(f"Error: El segundo argumento debe ser un número entero. Usando valor por defecto: {objetivos_por_usuario}")
    
    # Ejecutar generador
    generar_medidas_y_objetivos(meses_historial, frecuencia_medidas, objetivos_por_usuario) 