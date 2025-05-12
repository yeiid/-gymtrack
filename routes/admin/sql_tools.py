"""
Herramientas SQL para administradores
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask import current_app as app
from models import db
import sqlite3
import pandas as pd
import datetime
import traceback

sql_tools = Blueprint('sql_tools', __name__)

@sql_tools.route('/sql_console', methods=['GET', 'POST'])
def sql_console():
    """
    Consola SQL para ejecutar consultas directamente
    """
    # Solo permitir acceso a administradores con rol "administrador"
    from flask import session
    if not session.get('admin_id') or session.get('admin_rol') != 'administrador':
        flash('No tienes permiso para acceder a esta función', 'danger')
        return redirect(url_for('main.index'))
        
    resultados = None
    columnas = []
    error = None
    codigo_sql = ""
    
    if request.method == 'POST':
        codigo_sql = request.form.get('codigo_sql', '')
        
        # Verificar que no sea una consulta peligrosa
        codigo_lower = codigo_sql.lower().strip()
        comandos_prohibidos = ['drop table', 'drop database', 'truncate', 'alter table']
        
        if any(cmd in codigo_lower for cmd in comandos_prohibidos):
            error = "Consulta no permitida. No se pueden ejecutar comandos que modifiquen la estructura de la base de datos."
        elif not codigo_sql:
            error = "Por favor, ingresa una consulta SQL."
        else:
            try:
                # Para consultas SELECT, usar pandas para mostrar los resultados de forma tabular
                if codigo_lower.startswith('select'):
                    resultados_df = pd.read_sql_query(codigo_sql, db.engine)
                    if resultados_df.empty:
                        resultados = []
                        columnas = []
                        flash('La consulta no devolvió resultados.', 'info')
                    else:
                        columnas = resultados_df.columns.tolist()
                        resultados = resultados_df.values.tolist()
                        flash(f'Consulta ejecutada con éxito. {len(resultados)} filas devueltas.', 'success')
                else:
                    # Para INSERT, UPDATE, DELETE, etc. ejecutar con session y commit
                    db.session.execute(codigo_sql)
                    db.session.commit()
                    flash('Consulta ejecutada con éxito. Base de datos actualizada.', 'success')
            except Exception as e:
                error = f"Error al ejecutar la consulta: {str(e)}"
                traceback.print_exc()
                db.session.rollback()
    
    # Obtener lista de tablas para referencia
    tablas = []
    try:
        result = db.session.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tablas = [row[0] for row in result]
    except:
        pass
        
    return render_template(
        'admin/sql_console.html', 
        resultados=resultados, 
        columnas=columnas, 
        error=error, 
        codigo_sql=codigo_sql,
        tablas=tablas
    )

@sql_tools.route('/ejemplo_sql/<tipo>', methods=['GET'])
def ejemplo_sql(tipo):
    """Devuelve ejemplos de consultas SQL"""
    ejemplos = {
        'select_usuarios': "SELECT * FROM usuario ORDER BY fecha_ingreso DESC LIMIT 10;",
        'select_pagos': "SELECT p.id, u.nombre, p.monto, p.fecha_pago, p.metodo_pago FROM pago_mensualidad p JOIN usuario u ON p.usuario_id = u.id ORDER BY p.fecha_pago DESC LIMIT 10;",
        'insert_usuario': """INSERT INTO usuario 
(nombre, telefono, plan, fecha_ingreso, metodo_pago, fecha_vencimiento_plan, precio_plan)
VALUES 
('Nuevo Usuario', '3001234567', 'mensual', '2024-05-01', 'efectivo', '2024-06-01', 70000);""",
        'update_usuario': "UPDATE usuario SET plan = 'mensual', precio_plan = 70000 WHERE id = 1;",
        'delete_registro': "DELETE FROM pago_mensualidad WHERE id = 999 AND usuario_id = 999;",
        'estadisticas': """SELECT plan, COUNT(*) as total_usuarios, AVG(precio_plan) as promedio_precio
FROM usuario
GROUP BY plan
ORDER BY total_usuarios DESC;"""
    }
    
    return jsonify({'sql': ejemplos.get(tipo, "SELECT * FROM usuario LIMIT 10;")})

@sql_tools.route('/info_tabla/<nombre_tabla>', methods=['GET'])
def info_tabla(nombre_tabla):
    """Devuelve información sobre la estructura de una tabla"""
    try:
        # Obtener estructura de la tabla
        result = db.session.execute(f"PRAGMA table_info({nombre_tabla});")
        columnas = [{'nombre': row[1], 'tipo': row[2], 'nullable': not row[3], 'pk': row[5]} for row in result]
        
        # Obtener conteo de registros
        result = db.session.execute(f"SELECT COUNT(*) FROM {nombre_tabla};")
        conteo = result.scalar()
        
        return jsonify({
            'tabla': nombre_tabla,
            'columnas': columnas,
            'total_registros': conteo
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400 