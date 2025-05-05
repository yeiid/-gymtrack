#!/usr/bin/env python
"""
Script para insertar usuarios en la base de datos
"""
import sqlite3
import sys
import os
import datetime
import pytz

def fecha_colombia():
    """
    Retorna la fecha actual en zona horaria de Colombia
    """
    tz_colombia = pytz.timezone('America/Bogota')
    return datetime.datetime.now(tz_colombia).date()

def insertar_usuario_sql(nombre, telefono, plan, metodo_pago, precio_plan=None):
    """
    Inserta un usuario en la base de datos usando SQL directo
    """
    # Determinar la ruta de la base de datos
    if getattr(sys, 'frozen', False):
        # Si estamos en un ejecutable empaquetado
        base_dir = os.path.expanduser('~')
        app_data_dir = os.path.join(base_dir, 'GimnasioDB_Data')
        db_path = os.path.join(app_data_dir, 'database.db')
    else:
        # En modo desarrollo
        db_path = 'database.db'
    
    # Verificar que la base de datos existe
    if not os.path.exists(db_path):
        print(f"Error: Base de datos no encontrada en {db_path}")
        return False
    
    # Calcular fechas
    fecha_ingreso = fecha_colombia()
    fecha_vencimiento = None
    
    # Establecer fecha de vencimiento según el plan
    if plan.lower() == 'diario':
        fecha_vencimiento = fecha_ingreso + datetime.timedelta(days=1)
        if not precio_plan:
            precio_plan = 5000
    elif plan.lower() == 'quincenal':
        fecha_vencimiento = fecha_ingreso + datetime.timedelta(days=15)
        if not precio_plan:
            precio_plan = 35000
    elif plan.lower() == 'mensual':
        fecha_vencimiento = fecha_ingreso + datetime.timedelta(days=30)
        if not precio_plan:
            precio_plan = 70000
    elif plan.lower() == 'estudiantil':
        fecha_vencimiento = fecha_ingreso + datetime.timedelta(days=30)
        if not precio_plan:
            precio_plan = 50000
    elif plan.lower() == 'dirigido':
        fecha_vencimiento = fecha_ingreso + datetime.timedelta(days=30)
        if not precio_plan:
            precio_plan = 130000
    elif plan.lower() == 'personalizado':
        fecha_vencimiento = fecha_ingreso + datetime.timedelta(days=30)
        if not precio_plan:
            precio_plan = 250000
    
    # Realizar la conexión e inserción
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si el usuario ya existe (por teléfono)
        cursor.execute("SELECT id FROM usuario WHERE telefono = ?", (telefono,))
        resultado = cursor.fetchone()
        if resultado:
            print(f"Ya existe un usuario con el teléfono {telefono}")
            conn.close()
            return False
        
        # Insertar el usuario
        sql = """
        INSERT INTO usuario 
        (nombre, telefono, plan, fecha_ingreso, metodo_pago, fecha_vencimiento_plan, precio_plan)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (
            nombre, 
            telefono, 
            plan, 
            fecha_ingreso.strftime('%Y-%m-%d'), 
            metodo_pago, 
            fecha_vencimiento.strftime('%Y-%m-%d') if fecha_vencimiento else None, 
            precio_plan
        ))
        
        # Obtener el ID del usuario insertado
        usuario_id = cursor.lastrowid
        
        # Registrar también el pago de la mensualidad
        sql_pago = """
        INSERT INTO pago_mensualidad
        (usuario_id, fecha_pago, monto, metodo_pago, plan, fecha_inicio, fecha_fin)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql_pago, (
            usuario_id,
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            precio_plan,
            metodo_pago,
            plan,
            fecha_ingreso.strftime('%Y-%m-%d'),
            fecha_vencimiento.strftime('%Y-%m-%d') if fecha_vencimiento else None
        ))
        
        # Guardar los cambios
        conn.commit()
        
        print(f"Usuario insertado correctamente con ID: {usuario_id}")
        conn.close()
        return True
    
    except Exception as e:
        print(f"Error al insertar usuario: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def main():
    """Función principal para ejecutar el script desde la línea de comandos"""
    if len(sys.argv) < 5:
        print("Uso: python insertar_usuario.py NOMBRE TELEFONO PLAN METODO_PAGO [PRECIO]")
        print("Ejemplo: python insertar_usuario.py 'Juan Pérez' 3001234567 mensual efectivo 70000")
        print("\nPlanes disponibles:")
        print("  - diario (5000)")
        print("  - quincenal (35000)")
        print("  - mensual (70000)")
        print("  - estudiantil (50000)")
        print("  - dirigido (130000)")
        print("  - personalizado (250000)")
        sys.exit(1)
    
    nombre = sys.argv[1]
    telefono = sys.argv[2]
    plan = sys.argv[3]
    metodo_pago = sys.argv[4]
    precio_plan = float(sys.argv[5]) if len(sys.argv) > 5 else None
    
    insertar_usuario_sql(nombre, telefono, plan, metodo_pago, precio_plan)

if __name__ == "__main__":
    main() 