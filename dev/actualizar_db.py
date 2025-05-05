#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para actualizar la estructura de la base de datos y corregir 
problemas con relaciones y restricciones de integridad referencial.
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

# Ruta de la base de datos
DB_PATH = 'database.db'

def hacer_backup():
    """Crea una copia de seguridad de la base de datos antes de hacer cambios."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = 'backups'
    
    # Crear directorio de respaldos si no existe
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    backup_path = os.path.join(backup_dir, f'database_backup_{timestamp}.db')
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"Backup creado: {backup_path}")
        return True
    except Exception as e:
        print(f"Error al crear backup: {str(e)}")
        return False

def aplicar_actualizaciones():
    """Aplica las actualizaciones necesarias a la base de datos."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Activar soporte para claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Verificar si la activación de claves foráneas fue exitosa
        status = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        print(f"Estado de claves foráneas: {'Activadas' if status else 'Desactivadas'}")
        
        # Crear tablas temporales con la nueva estructura y transferir datos
        actualizar_tabla_medidas_corporales(conn, cursor)
        actualizar_tabla_objetivo_personal(conn, cursor)
        actualizar_tabla_asistencia(conn, cursor)
        actualizar_tabla_pago_mensualidad(conn, cursor)
        actualizar_tabla_venta_producto(conn, cursor)
        
        # Eliminar cualquier registro huérfano antes de activar restricciones
        limpiar_registros_huerfanos(conn, cursor)
        
        # Optimizar la base de datos
        conn.execute("VACUUM")
        
        conn.close()
        print("Actualización de la base de datos completada con éxito")
        return True
    except Exception as e:
        print(f"Error al actualizar la base de datos: {str(e)}")
        return False

def actualizar_tabla_medidas_corporales(conn, cursor):
    """Actualiza la tabla de medidas corporales para incluir restricciones de clave foránea."""
    try:
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='medidas_corporales'")
        if cursor.fetchone():
            print("Actualizando tabla medidas_corporales...")
            
            # Crear tabla temporal con la nueva estructura
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medidas_corporales_temp (
                    id INTEGER PRIMARY KEY,
                    usuario_id INTEGER,
                    fecha DATE,
                    peso FLOAT,
                    altura FLOAT, 
                    imc FLOAT,
                    pecho FLOAT,
                    cintura FLOAT,
                    cadera FLOAT,
                    brazo_izquierdo FLOAT,
                    brazo_derecho FLOAT,
                    pierna_izquierda FLOAT,
                    pierna_derecha FLOAT,
                    notas TEXT,
                    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
                )
            """)
            
            # Transferir datos
            cursor.execute("""
                INSERT INTO medidas_corporales_temp
                SELECT * FROM medidas_corporales
            """)
            
            # Eliminar registros huérfanos
            cursor.execute("""
                DELETE FROM medidas_corporales_temp 
                WHERE usuario_id NOT IN (SELECT id FROM usuario)
            """)
            
            # Reemplazar la tabla original
            cursor.execute("DROP TABLE medidas_corporales")
            cursor.execute("ALTER TABLE medidas_corporales_temp RENAME TO medidas_corporales")
            
            conn.commit()
            print("Tabla medidas_corporales actualizada")
    except Exception as e:
        conn.rollback()
        print(f"Error al actualizar medidas_corporales: {str(e)}")
        raise

def actualizar_tabla_objetivo_personal(conn, cursor):
    """Actualiza la tabla de objetivos personales para incluir restricciones de clave foránea."""
    try:
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='objetivo_personal'")
        if cursor.fetchone():
            print("Actualizando tabla objetivo_personal...")
            
            # Crear tabla temporal con la nueva estructura
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS objetivo_personal_temp (
                    id INTEGER PRIMARY KEY,
                    usuario_id INTEGER,
                    descripcion TEXT NOT NULL,
                    fecha_creacion DATE,
                    fecha_objetivo DATE,
                    fecha_completado DATE,
                    completado BOOLEAN DEFAULT 0,
                    progreso INTEGER DEFAULT 0,
                    estado VARCHAR(20) DEFAULT 'En progreso',
                    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
                )
            """)
            
            # Transferir datos
            cursor.execute("""
                INSERT INTO objetivo_personal_temp
                SELECT * FROM objetivo_personal
            """)
            
            # Eliminar registros huérfanos
            cursor.execute("""
                DELETE FROM objetivo_personal_temp 
                WHERE usuario_id NOT IN (SELECT id FROM usuario)
            """)
            
            # Reemplazar la tabla original
            cursor.execute("DROP TABLE objetivo_personal")
            cursor.execute("ALTER TABLE objetivo_personal_temp RENAME TO objetivo_personal")
            
            conn.commit()
            print("Tabla objetivo_personal actualizada")
    except Exception as e:
        conn.rollback()
        print(f"Error al actualizar objetivo_personal: {str(e)}")
        raise

def actualizar_tabla_asistencia(conn, cursor):
    """Actualiza la tabla de asistencia para incluir restricciones de clave foránea."""
    try:
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='asistencia'")
        if cursor.fetchone():
            print("Actualizando tabla asistencia...")
            
            # Crear tabla temporal con la nueva estructura
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asistencia_temp (
                    id INTEGER PRIMARY KEY,
                    usuario_id INTEGER,
                    fecha DATETIME,
                    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
                )
            """)
            
            # Transferir datos
            cursor.execute("""
                INSERT INTO asistencia_temp
                SELECT * FROM asistencia
            """)
            
            # Eliminar registros huérfanos
            cursor.execute("""
                DELETE FROM asistencia_temp 
                WHERE usuario_id NOT IN (SELECT id FROM usuario)
            """)
            
            # Reemplazar la tabla original
            cursor.execute("DROP TABLE asistencia")
            cursor.execute("ALTER TABLE asistencia_temp RENAME TO asistencia")
            
            conn.commit()
            print("Tabla asistencia actualizada")
    except Exception as e:
        conn.rollback()
        print(f"Error al actualizar asistencia: {str(e)}")
        raise

def actualizar_tabla_pago_mensualidad(conn, cursor):
    """Actualiza la tabla de pagos para incluir restricciones de clave foránea."""
    try:
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pago_mensualidad'")
        if cursor.fetchone():
            print("Actualizando tabla pago_mensualidad...")
            
            # Crear tabla temporal con la nueva estructura
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pago_mensualidad_temp (
                    id INTEGER PRIMARY KEY,
                    usuario_id INTEGER,
                    fecha_pago DATETIME,
                    monto FLOAT NOT NULL,
                    metodo_pago VARCHAR(50),
                    plan VARCHAR(50),
                    fecha_inicio DATE NOT NULL,
                    fecha_fin DATE NOT NULL,
                    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
                )
            """)
            
            # Transferir datos
            cursor.execute("""
                INSERT INTO pago_mensualidad_temp
                SELECT * FROM pago_mensualidad
            """)
            
            # Eliminar registros huérfanos
            cursor.execute("""
                DELETE FROM pago_mensualidad_temp 
                WHERE usuario_id NOT IN (SELECT id FROM usuario)
            """)
            
            # Reemplazar la tabla original
            cursor.execute("DROP TABLE pago_mensualidad")
            cursor.execute("ALTER TABLE pago_mensualidad_temp RENAME TO pago_mensualidad")
            
            conn.commit()
            print("Tabla pago_mensualidad actualizada")
    except Exception as e:
        conn.rollback()
        print(f"Error al actualizar pago_mensualidad: {str(e)}")
        raise

def actualizar_tabla_venta_producto(conn, cursor):
    """Actualiza la tabla de ventas para incluir restricciones de clave foránea con SET NULL."""
    try:
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='venta_producto'")
        if cursor.fetchone():
            print("Actualizando tabla venta_producto...")
            
            # Crear tabla temporal con la nueva estructura
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS venta_producto_temp (
                    id INTEGER PRIMARY KEY,
                    producto_id INTEGER,
                    usuario_id INTEGER,
                    cantidad INTEGER DEFAULT 1,
                    precio_unitario FLOAT NOT NULL,
                    total FLOAT NOT NULL,
                    metodo_pago VARCHAR(50),
                    fecha DATETIME,
                    FOREIGN KEY (producto_id) REFERENCES producto(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE SET NULL
                )
            """)
            
            # Transferir datos
            cursor.execute("""
                INSERT INTO venta_producto_temp
                SELECT * FROM venta_producto
            """)
            
            # Actualizar referencias a usuarios que ya no existen
            cursor.execute("""
                UPDATE venta_producto_temp 
                SET usuario_id = NULL
                WHERE usuario_id NOT IN (SELECT id FROM usuario) AND usuario_id IS NOT NULL
            """)
            
            # Reemplazar la tabla original
            cursor.execute("DROP TABLE venta_producto")
            cursor.execute("ALTER TABLE venta_producto_temp RENAME TO venta_producto")
            
            conn.commit()
            print("Tabla venta_producto actualizada")
    except Exception as e:
        conn.rollback()
        print(f"Error al actualizar venta_producto: {str(e)}")
        raise

def limpiar_registros_huerfanos(conn, cursor):
    """Limpia cualquier registro huérfano que pueda causar problemas de integridad referencial."""
    try:
        print("Limpiando registros huérfanos...")
        
        cursor.execute("DELETE FROM medidas_corporales WHERE usuario_id NOT IN (SELECT id FROM usuario)")
        cursor.execute("DELETE FROM objetivo_personal WHERE usuario_id NOT IN (SELECT id FROM usuario)")
        cursor.execute("DELETE FROM asistencia WHERE usuario_id NOT IN (SELECT id FROM usuario)")
        cursor.execute("DELETE FROM pago_mensualidad WHERE usuario_id NOT IN (SELECT id FROM usuario)")
        cursor.execute("UPDATE venta_producto SET usuario_id = NULL WHERE usuario_id NOT IN (SELECT id FROM usuario) AND usuario_id IS NOT NULL")
        
        conn.commit()
        print("Limpieza de registros huérfanos completada")
    except Exception as e:
        conn.rollback()
        print(f"Error al limpiar registros huérfanos: {str(e)}")
        raise

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
    
    print("Este script actualizará la estructura de la base de datos.")
    print("Se creará un respaldo antes de realizar cambios.")
    
    respuesta = input("¿Desea continuar? (s/n): ").lower()
    if respuesta != 's':
        print("Operación cancelada")
        sys.exit(0)
    
    if hacer_backup():
        if aplicar_actualizaciones():
            print("\n¡Actualización completada con éxito!")
            print("Ahora debería poder eliminar usuarios sin problemas.")
        else:
            print("\nOcurrió un error durante la actualización.")
            print("Se recomienda restaurar el respaldo si la aplicación no funciona correctamente.")
    else:
        print("No se pudo crear un respaldo. Operación cancelada.") 