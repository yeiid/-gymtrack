#!/usr/bin/env python
"""
Script maestro para generar datos de prueba en GymTrack
Permite generar usuarios, asistencias, medidas corporales y objetivos personales
"""
import os
import sys
import subprocess
from importlib.util import find_spec, module_from_spec
from pathlib import Path

# Lista de scripts requeridos
SCRIPTS_REQUERIDOS = [
    "generar_100_usuarios.py",
    "generar_asistencias.py",
    "generar_medidas_objetivos.py"
]

def verificar_scripts():
    """Verifica que todos los scripts necesarios existan"""
    scripts_faltantes = []
    for script in SCRIPTS_REQUERIDOS:
        if not os.path.exists(script):
            scripts_faltantes.append(script)
    
    if scripts_faltantes:
        print("\n❌ ERROR: Faltan los siguientes scripts:")
        for script in scripts_faltantes:
            print(f"  - {script}")
        print("\nAsegúrate de que todos los scripts requeridos estén en el mismo directorio.")
        return False
    
    return True

def ejecutar_script(script_path, *args):
    """Ejecuta un script Python con argumentos"""
    cmd = [sys.executable, script_path] + list(args)
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR al ejecutar {script_path}: {str(e)}")
        return False

def importar_script(script_path):
    """Importa un script como módulo para ejecutarlo directamente"""
    try:
        # Convertir ruta a Path para manipulación más sencilla
        script_path = Path(script_path)
        
        # Verificar que el script existe
        if not script_path.exists():
            print(f"\n❌ ERROR: El script {script_path} no existe")
            return None
        
        # Crear un nombre de módulo único basado en el nombre del archivo
        modulo_nombre = script_path.stem
        
        # Importar el módulo desde el archivo
        spec = find_spec(modulo_nombre, [str(script_path.parent)])
        if spec is None:
            # Si find_spec falla, intentamos crear el spec manualmente
            import importlib.machinery
            loader = importlib.machinery.SourceFileLoader(modulo_nombre, str(script_path))
            spec = importlib.util.spec_from_loader(modulo_nombre, loader)
        
        modulo = module_from_spec(spec)
        spec.loader.exec_module(modulo)
        
        return modulo
    except Exception as e:
        print(f"\n❌ ERROR al importar {script_path}: {str(e)}")
        return None

def generar_datos_prueba():
    """Función principal para generar todos los datos de prueba"""
    print("=" * 60)
    print(" GENERACIÓN DE DATOS DE PRUEBA PARA GYMTRACK ")
    print("=" * 60)
    
    # Verificar que todos los scripts requeridos existen
    if not verificar_scripts():
        return
    
    # Solicitar confirmación al usuario
    print("\n⚠️ ADVERTENCIA: Este proceso generará múltiples datos de prueba en la base de datos.")
    print("Los datos generados incluyen:")
    print("  - Usuarios con planes aleatorios")
    print("  - Registros de asistencia")
    print("  - Medidas corporales para usuarios con planes premium")
    print("  - Objetivos personales para usuarios con planes premium")
    
    confirmacion = input("\n¿Deseas continuar con la generación de datos? (s/n): ")
    if confirmacion.lower() != 's':
        print("Operación cancelada.")
        return
    
    # Configuración de parámetros
    print("\n--- Configuración de parámetros ---")
    try:
        num_usuarios = int(input("Número de usuarios a generar (predeterminado: 100): ") or "100")
        meses_historial = int(input("Meses de historial para asistencias y medidas (predeterminado: 6): ") or "6")
        objetivos_por_usuario = int(input("Objetivos por usuario premium (predeterminado: 3): ") or "3")
    except ValueError:
        print("\n❌ ERROR: Los valores deben ser números enteros.")
        print("Se usarán los valores predeterminados.")
        num_usuarios = 100
        meses_historial = 6
        objetivos_por_usuario = 3
    
    # Paso 1: Generar usuarios
    print("\n--- Paso 1: Generación de usuarios ---")
    modulo_usuarios = importar_script("generar_100_usuarios.py")
    if modulo_usuarios:
        # Buscar la función principal de generación de usuarios
        if hasattr(modulo_usuarios, "generar_usuarios"):
            modulo_usuarios.generar_usuarios(num_usuarios)
        else:
            print("\n❌ ERROR: No se encontró la función de generación de usuarios en el script")
            return
    else:
        print("\n❌ ERROR: No se pudo importar el script de generación de usuarios")
        return
    
    # Paso 2: Generar asistencias
    print("\n--- Paso 2: Generación de asistencias ---")
    modulo_asistencias = importar_script("generar_asistencias.py")
    if modulo_asistencias:
        # Buscar la función principal de generación de asistencias
        if hasattr(modulo_asistencias, "generar_asistencias_aleatorias"):
            # Crear la aplicación Flask primero
            app = modulo_asistencias.crear_app()
            modulo_asistencias.generar_asistencias_aleatorias(app, meses_historial)
        else:
            print("\n❌ ERROR: No se encontró la función de generación de asistencias en el script")
            return
    else:
        print("\n❌ ERROR: No se pudo importar el script de generación de asistencias")
        return
    
    # Paso 3: Generar medidas y objetivos
    print("\n--- Paso 3: Generación de medidas corporales y objetivos ---")
    modulo_medidas = importar_script("generar_medidas_objetivos.py")
    if modulo_medidas:
        # Buscar la función principal de generación de medidas y objetivos
        if hasattr(modulo_medidas, "generar_medidas_y_objetivos"):
            modulo_medidas.generar_medidas_y_objetivos(meses_historial, 1, objetivos_por_usuario)
        else:
            print("\n❌ ERROR: No se encontró la función de generación de medidas en el script")
            return
    else:
        print("\n❌ ERROR: No se pudo importar el script de generación de medidas")
        return
    
    print("\n" + "=" * 60)
    print(" GENERACIÓN DE DATOS DE PRUEBA COMPLETADA ")
    print("=" * 60)
    print("\n✅ Se han generado con éxito los siguientes datos:")
    print(f"  - {num_usuarios} usuarios con planes aleatorios")
    print(f"  - Asistencias aleatorias para los últimos {meses_historial} meses")
    print(f"  - Medidas corporales para usuarios premium (últimos {meses_historial} meses)")
    print(f"  - Aproximadamente {objetivos_por_usuario} objetivos personales por usuario premium")
    print("\n¡Los datos de prueba están listos para usar!")

if __name__ == "__main__":
    generar_datos_prueba() 