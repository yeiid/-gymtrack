#!/usr/bin/env python
"""
Script principal para ejecutar todas las pruebas del sistema GymTrack
"""
import os
import sys
import time
import importlib.util
import subprocess
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

def ejecutar_test(script_path, cantidad_usuarios=20):
    """Ejecuta un script de prueba y retorna si fue exitoso"""
    print("\n" + "=" * 60)
    print(f" EJECUTANDO TEST: {script_path}")
    print("=" * 60)
    
    # Construir comando
    comando = [sys.executable, script_path, str(cantidad_usuarios)]
    
    # Ejecutar como subproceso
    try:
        resultado = subprocess.run(
            comando,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Mostrar salida
        if resultado.stdout:
            print(resultado.stdout)
        if resultado.stderr:
            print("ERRORES:")
            print(resultado.stderr)
        
        # Verificar si fue exitoso
        return resultado.returncode == 0
    except Exception as e:
        print(f"❌ Error al ejecutar {script_path}: {e}")
        return False

def ejecutar_todos_tests(cantidad_usuarios=20):
    """Ejecuta todos los scripts de prueba y genera un reporte"""
    print("\n" + "=" * 60)
    print(" INICIO DE PRUEBAS COMPLETAS DEL SISTEMA ")
    print("=" * 60)
    print(f"Fecha y hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Pruebas con {cantidad_usuarios} usuarios")
    
    # Lista de pruebas a ejecutar
    tests = [
        {"nombre": "Integridad de datos de usuarios", "script": "test_usuarios.py", "peso": 0.25},
        {"nombre": "Integridad de pagos", "script": "test_pagos.py", "peso": 0.25},
        {"nombre": "Integridad de clases y asistencias", "script": "test_clases.py", "peso": 0.25},
        {"nombre": "Rendimiento", "script": "test_rendimiento.py", "peso": 0.25}
    ]
    
    # Ejecutar cada prueba
    resultados = {}
    for test in tests:
        test_path = Path(__file__).parent / test["script"]
        exito = ejecutar_test(test_path, cantidad_usuarios)
        resultados[test["nombre"]] = {
            "exito": exito,
            "peso": test["peso"]
        }
    
    # Generar reporte final
    print("\n" + "=" * 60)
    print(" REPORTE FINAL DE PRUEBAS ")
    print("=" * 60)
    
    exito_total = True
    puntaje_total = 0
    for nombre, resultado in resultados.items():
        exito = resultado["exito"]
        peso = resultado["peso"]
        
        estado = "✅ PASÓ" if exito else "❌ FALLÓ"
        puntaje = peso if exito else 0
        puntaje_total += puntaje
        
        print(f"{nombre}: {estado} - Puntaje: {puntaje:.2f}/{peso:.2f}")
        
        if not exito:
            exito_total = False
    
    # Calcular porcentaje de solidez
    porcentaje_solidez = (puntaje_total / sum(test["peso"] for test in tests)) * 100
    
    print("\n" + "-" * 60)
    print(f"Puntaje total: {puntaje_total:.2f}/{sum(test['peso'] for test in tests):.2f}")
    print(f"Solidez del sistema: {porcentaje_solidez:.1f}%")
    
    # Clasificar solidez
    if porcentaje_solidez >= 90:
        calificacion = "EXCELENTE"
    elif porcentaje_solidez >= 70:
        calificacion = "BUENO"
    elif porcentaje_solidez >= 50:
        calificacion = "REGULAR"
    else:
        calificacion = "DEFICIENTE"
    
    print(f"Calificación: {calificacion}")
    print("=" * 60)
    
    # Generar recomendaciones
    if not exito_total:
        print("\nRecomendaciones:")
        
        if not resultados.get("Integridad de datos de usuarios", {}).get("exito", False):
            print("- Revisar la estructura de datos de usuarios")
            print("- Verificar la validación de teléfonos y planes")
            print("- Asegurar que todos los usuarios tengan los datos requeridos")
        
        if not resultados.get("Integridad de pagos", {}).get("exito", False):
            print("- Revisar el sistema de pagos y su relación con los usuarios")
            print("- Verificar que los montos correspondan a los planes correctos")
            print("- Corregir posibles problemas con fechas de pago y vencimiento")
        
        if not resultados.get("Integridad de clases y asistencias", {}).get("exito", False):
            print("- Revisar la estructura de clases y asistencias")
            print("- Asegurar que todas las clases tengan instructor asignado")
            print("- Verificar que no haya conflictos de horarios o capacidades inválidas")
            print("- Corregir problemas con registros de asistencias futuras")
        
        if not resultados.get("Rendimiento", {}).get("exito", False):
            print("- Optimizar consultas SQL y agregar índices a campos frecuentemente consultados")
            print("- Revisar el manejo de caché y sesiones")
            print("- Considerar implementar paginación para grandes conjuntos de datos")
    
    return exito_total

if __name__ == "__main__":
    # Determinar la cantidad de usuarios para las pruebas
    cantidad = 20
    if len(sys.argv) > 1:
        try:
            cantidad = int(sys.argv[1])
        except ValueError:
            print(f"Error: El argumento debe ser un número entero. Usando valor por defecto: {cantidad}")
    
    # Ejecutar todas las pruebas
    exito = ejecutar_todos_tests(cantidad)
    
    # Salir con código apropiado
    sys.exit(0 if exito else 1) 