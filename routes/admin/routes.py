from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask import current_app
from models import db, Admin, Usuario, Asistencia, Producto, VentaProducto, PagoMensualidad, MedidasCorporales, ObjetivoPersonal
from models import datetime_colombia, date_colombia  # Importar las funciones de zona horaria
from datetime import datetime, timedelta
import os, shutil
from werkzeug.security import check_password_hash
from routes.auth.routes import admin_required
import glob
import json
import requests
from sqlalchemy import func

# Crear blueprint
bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/')
def index():
    return "Módulo de Administración"

@bp.route('/crear_admin', methods=['GET', 'POST'])
@admin_required
def crear_admin():
    # Verificar que sea administrador
    current_admin = Admin.query.get(session['admin_id'])
    if current_admin.rol != 'administrador':
        flash('No tienes permisos para crear administradores', 'danger')
        return redirect(url_for('main.admin.lista_admins'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario = request.form['usuario']
        password = request.form['password']
        rol = request.form['rol']
        
        # Verificar si el usuario ya existe
        admin_existente = Admin.query.filter_by(usuario=usuario).first()
        if admin_existente:
            flash(f'El usuario {usuario} ya existe', 'danger')
            return render_template('admin/crear_admin.html')
        
        # Crear el nuevo administrador
        nuevo_admin = Admin(
            nombre=nombre,
            usuario=usuario,
            rol=rol
        )
        nuevo_admin.set_password(password)
        
        db.session.add(nuevo_admin)
        db.session.commit()
        
        flash(f'Administrador {nombre} creado correctamente', 'success')
        return redirect(url_for('main.admin.lista_admins'))
    
    return render_template('admin/crear_admin.html')

@bp.route('/lista_admins')
def lista_admins():
    # Verificar que el usuario esté logueado
    if 'admin_id' not in session:
        flash('Debe iniciar sesión para acceder a esta sección', 'warning')
        return redirect(url_for('main.auth.login'))
    
    # Verificar el rol del usuario actual
    current_admin = Admin.query.get(session['admin_id'])
    if not current_admin:
        session.pop('admin_id', None)
        session.pop('admin_nombre', None)
        session.pop('admin_rol', None)
        flash('Su sesión ha expirado o ha sido eliminada. Por favor, inicie sesión nuevamente.', 'warning')
        return redirect(url_for('main.auth.login'))
    
    # Obtener todos los administradores
    admins = Admin.query.all()
    
    # Verificar si es administrador para mostrar controles de edición
    is_admin = current_admin.rol == 'administrador'
    return render_template('admin/lista_admins.html', admins=admins, is_admin=is_admin)

@bp.route('/reset_password/<int:admin_id>', methods=['POST'])
@admin_required
def reset_password(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    current_admin = Admin.query.get(session['admin_id'])
    
    # Solo permitir cambio si:
    # 1. El usuario actual es administrador, o
    # 2. El usuario está cambiando su propia contraseña
    if current_admin.rol != 'administrador' and current_admin.id != admin_id:
        flash('No tienes permisos para cambiar esta contraseña', 'danger')
        return redirect(url_for('main.admin.lista_admins'))
    
    new_password = request.form.get('new_password')
    if new_password:
        admin.set_password(new_password)
        db.session.commit()
        flash(f'Contraseña actualizada para {admin.nombre}', 'success')
    else:
        flash('No se proporcionó una nueva contraseña', 'danger')
    
    return redirect(url_for('main.admin.lista_admins'))

@bp.route('/config', methods=['GET', 'POST'])
@admin_required
def configuracion():
    # Verificación adicional de seguridad
    try:
        if 'admin_id' not in session:
            flash('Debe iniciar sesión como administrador', 'danger')
            return redirect(url_for('main.auth.login'))
        
        # Verificar si es POST para procesar acciones
        if request.method == 'POST':
            accion = request.form.get('accion')
            
            if accion == 'backup_db':
                try:
                    import os
                    import shutil
                    
                    # Crear copia de seguridad de la base de datos
                    fecha_actual = datetime_colombia().strftime('%Y%m%d_%H%M%S')
                    
                    # Crear carpeta de backups si no existe
                    backup_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
                    os.makedirs(backup_folder, exist_ok=True)
                    
                    # Nombre del archivo de backup con fecha y hora
                    backup_filename = f'backup_db_{fecha_actual}.db'
                    backup_path = os.path.join(backup_folder, backup_filename)
                    
                    # Verificar si existe el archivo de base de datos
                    if os.path.exists('database.db'):
                        # Copiar el archivo de base de datos
                        shutil.copy2('database.db', backup_path)
                        flash(f'Copia de seguridad creada exitosamente: {backup_filename}', 'success')
                    else:
                        flash('No se encontró el archivo database.db para crear copia de seguridad', 'warning')
                except Exception as e:
                    flash(f'Error al crear copia de seguridad: {str(e)}', 'danger')
            
            elif accion == 'restore_db':
                backup_file = request.files.get('backup_file')
                if backup_file:
                    try:
                        import os
                        import shutil
                        import sys
                        
                        # Determinar rutas según el modo de ejecución
                        if getattr(sys, 'frozen', False):
                            # Modo ejecutable
                            base_dir = os.path.expanduser('~')
                            app_data_dir = os.path.join(base_dir, 'GimnasioDB_Data')
                            db_path = os.path.join(app_data_dir, 'database.db')
                            temp_backup_path = os.path.join(app_data_dir, 'temp_backup.db')
                        else:
                            # Modo desarrollo
                            db_path = 'database.db'
                            temp_backup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp_backup.db')
                        
                        # Guardar el archivo subido
                        backup_file.save(temp_backup_path)
                        
                        # Verificar que sea un archivo SQLite válido
                        import sqlite3
                        try:
                            conn = sqlite3.connect(temp_backup_path)
                            conn.close()
                        except sqlite3.Error:
                            os.remove(temp_backup_path)
                            flash('El archivo subido no es una base de datos SQLite válida', 'danger')
                            return redirect(url_for('main.admin.configuracion'))
                        
                        # Restaurar el archivo
                        shutil.copy2(temp_backup_path, db_path)
                        os.remove(temp_backup_path)
                        
                        flash('Base de datos restaurada exitosamente', 'success')
                    except Exception as e:
                        flash(f'Error al restaurar base de datos: {str(e)}', 'danger')
                else:
                    flash('No se seleccionó ningún archivo para restaurar', 'warning')
            
            elif accion == 'optimize_db':
                try:
                    # Optimizar la base de datos con VACUUM
                    from sqlalchemy import text
                    
                    # Ejecutar VACUUM para optimizar la base de datos
                    db.session.execute(text('VACUUM;'))
                    db.session.commit()
                    
                    # Ejecutar ANALYZE para actualizar estadísticas
                    db.session.execute(text('ANALYZE;'))
                    db.session.commit()
                    
                    flash('Base de datos optimizada correctamente', 'success')
                except Exception as e:
                    flash(f'Error al optimizar la base de datos: {str(e)}', 'danger')
            
            elif accion == 'clean_data':
                try:
                    from datetime import datetime, timedelta
                    from sqlalchemy import text
                    
                    registros_eliminados = 0
                    
                    # Limpiar asistencias antiguas (mayores a 6 meses)
                    if request.form.get('clean_old_attendance'):
                        fecha_limite = datetime_colombia() - timedelta(days=180)
                        resultado = db.session.execute(
                            text("DELETE FROM asistencia WHERE fecha < :fecha_limite"),
                            {"fecha_limite": fecha_limite}
                        )
                        registros_eliminados += resultado.rowcount
                    
                    # Limpiar pagos antiguos (mayores a 1 año)
                    if request.form.get('clean_old_payments'):
                        fecha_limite = datetime_colombia() - timedelta(days=365)
                        resultado = db.session.execute(
                            text("DELETE FROM pago_mensualidad WHERE fecha_pago < :fecha_limite"),
                            {"fecha_limite": fecha_limite}
                        )
                        registros_eliminados += resultado.rowcount
                    
                    # Limpiar ventas antiguas (mayores a 1 año)
                    if request.form.get('clean_old_sales'):
                        fecha_limite = datetime_colombia() - timedelta(days=365)
                        resultado = db.session.execute(
                            text("DELETE FROM venta_producto WHERE fecha < :fecha_limite"),
                            {"fecha_limite": fecha_limite}
                        )
                        registros_eliminados += resultado.rowcount
                    
                    # Limpiar usuarios inactivos (sin asistencia por más de 1 año)
                    if request.form.get('clean_deleted_users'):
                        # Obtener usuarios sin asistencias en el último año
                        fecha_limite = datetime_colombia() - timedelta(days=365)
                        # Subconsulta para obtener usuarios con alguna asistencia reciente
                        usuarios_activos = db.session.query(Asistencia.usuario_id).filter(
                            Asistencia.fecha >= fecha_limite
                        ).distinct().subquery()
                        
                        # Conseguir usuarios que no estén en la subconsulta
                        usuarios_inactivos = Usuario.query.filter(
                            ~Usuario.id.in_(db.session.query(usuarios_activos))
                        ).all()
                        
                        # Eliminar usuarios inactivos (primero eliminamos referencias)
                        for usuario in usuarios_inactivos:
                            # Eliminar referencias en otras tablas
                            PagoMensualidad.query.filter_by(usuario_id=usuario.id).delete()
                            MedidasCorporales.query.filter_by(usuario_id=usuario.id).delete()
                            ObjetivoPersonal.query.filter_by(usuario_id=usuario.id).delete()
                            VentaProducto.query.filter_by(usuario_id=usuario.id).delete()
                            
                            # Finalmente eliminar el usuario
                            db.session.delete(usuario)
                            registros_eliminados += 1
                    
                    db.session.commit()
                    
                    # Optimizar la base de datos después de la limpieza
                    db.session.execute(text('VACUUM;'))
                    db.session.commit()
                    
                    flash(f'Limpieza completada. Se eliminaron {registros_eliminados} registros.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error al limpiar datos: {str(e)}', 'danger')
            
            elif accion == 'export_csv':
                try:
                    import csv
                    import os
                    
                    tabla = request.form.get('tabla_exportar')
                    export_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
                    os.makedirs(export_folder, exist_ok=True)
                    
                    fecha_actual = datetime_colombia().strftime('%Y%m%d_%H%M%S')
                    filename = f'export_{tabla}_{fecha_actual}.csv'
                    filepath = os.path.join(export_folder, filename)
                    
                    # Seleccionar los datos apropiados según la tabla elegida
                    if tabla == 'usuarios':
                        data = Usuario.query.all()
                        headers = ['ID', 'Nombre', 'Teléfono', 'Plan', 'Fecha Ingreso', 'Método Pago', 'Fecha Vencimiento']
                        rows = [[u.id, u.nombre, u.telefono, u.plan, u.fecha_ingreso, u.metodo_pago, u.fecha_vencimiento_plan] for u in data]
                    
                    elif tabla == 'asistencias':
                        # Consulta con JOIN para incluir nombre de usuario
                        data = db.session.query(Asistencia, Usuario).join(Usuario).all()
                        headers = ['ID', 'Usuario ID', 'Nombre Usuario', 'Fecha']
                        rows = [[a.id, a.usuario_id, u.nombre, a.fecha] for a, u in data]
                    
                    elif tabla == 'pagos':
                        # Consulta con JOIN para incluir nombre de usuario
                        data = db.session.query(PagoMensualidad, Usuario).join(Usuario).all()
                        headers = ['ID', 'Usuario', 'Fecha Pago', 'Monto', 'Método Pago', 'Plan', 'Fecha Inicio', 'Fecha Fin']
                        rows = [[p.id, u.nombre, p.fecha_pago, p.monto, p.metodo_pago, p.plan, p.fecha_inicio, p.fecha_fin] for p, u in data]
                    
                    elif tabla == 'productos':
                        data = Producto.query.all()
                        headers = ['ID', 'Nombre', 'Descripción', 'Precio', 'Stock', 'Categoría', 'Fecha Creación']
                        rows = [[p.id, p.nombre, p.descripcion, p.precio, p.stock, p.categoria, p.fecha_creacion] for p in data]
                    
                    elif tabla == 'ventas':
                        # Consulta con JOIN para incluir información de producto y usuario
                        data = db.session.query(VentaProducto, Producto, Usuario).\
                            join(Producto).\
                            outerjoin(Usuario).all()
                        headers = ['ID', 'Producto', 'Usuario', 'Cantidad', 'Precio Unitario', 'Total', 'Método Pago', 'Fecha']
                        rows = [[v.id, p.nombre, u.nombre if u else 'Sin usuario', v.cantidad, v.precio_unitario, v.total, v.metodo_pago, v.fecha] for v, p, u in data]
                    
                    # Escribir al archivo CSV
                    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(headers)
                        writer.writerows(rows)
                    
                    # Preparar para descarga
                    return send_file(filepath, as_attachment=True, download_name=filename)
                
                except Exception as e:
                    flash(f'Error al exportar datos: {str(e)}', 'danger')
            
            elif accion == 'run_sql':
                try:
                    from sqlalchemy import text
                    
                    sql_query = request.form.get('sql_query', '')
                    allow_write = request.form.get('allow_write') == 'on'
                    
                    # Verificar si es una operación de escritura
                    is_write_operation = any(keyword in sql_query.upper() for keyword in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE'])
                    
                    if is_write_operation and not allow_write:
                        flash('Para ejecutar operaciones de escritura debe marcar la casilla correspondiente', 'warning')
                        return redirect(url_for('main.admin.configuracion'))
                    
                    # Ejecutar la consulta
                    result = db.session.execute(text(sql_query))
                    
                    # Si es una operación de escritura, hacer commit
                    if is_write_operation:
                        db.session.commit()
                        flash(f'Consulta ejecutada correctamente. Filas afectadas: {result.rowcount}', 'success')
                    else:
                        # Si es SELECT, mostrar resultados
                        flash('Consulta ejecutada correctamente.', 'success')
                        session['sql_results'] = {
                            'columns': result.keys(),
                            'rows': [list(row) for row in result.fetchall()]
                        }
                
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error al ejecutar SQL: {str(e)}', 'danger')
                
            elif accion == 'reset_all_data':
                try:
                    # Verificar confirmación
                    confirmacion = request.form.get('confirmacion')
                    if confirmacion != 'BORRAR TODO':
                        flash('Confirmación incorrecta. Operación cancelada.', 'warning')
                        return redirect(url_for('main.admin.configuracion'))
                    
                    # Crear backup si se solicitó
                    if request.form.get('create_backup') == 'on':
                        import os
                        import shutil
                        
                        # Crear carpeta de backups si no existe
                        backup_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
                        os.makedirs(backup_folder, exist_ok=True)
                        
                        # Nombre del archivo de backup con fecha y hora
                        fecha_actual = datetime_colombia().strftime('%Y%m%d_%H%M%S')
                        backup_filename = f'backup_db_before_reset_{fecha_actual}.db'
                        backup_path = os.path.join(backup_folder, backup_filename)
                        
                        # Verificar si existe el archivo de base de datos
                        if os.path.exists('database.db'):
                            # Copiar el archivo de base de datos
                            shutil.copy2('database.db', backup_path)
                            flash(f'Copia de seguridad creada antes del borrado: {backup_filename}', 'info')
                        else:
                            flash('No se encontró el archivo database.db para crear copia de seguridad', 'warning')
                    
                    # Guardar información del administrador actual si se solicitó
                    keep_admin = request.form.get('keep_admin') == 'on'
                    admin_actual = None
                    if keep_admin and 'admin_id' in session:
                        admin_actual = Admin.query.get(session['admin_id'])
                        if admin_actual:
                            admin_info = {
                                'id': admin_actual.id,
                                'nombre': admin_actual.nombre,
                                'usuario': admin_actual.usuario,
                                'rol': admin_actual.rol,
                                'password_hash': admin_actual.password_hash  # Guardar el hash directamente
                            }
                    
                    # Borrar todos los datos de cada tabla
                    from sqlalchemy import text
                    
                    # Lista de todas las tablas en orden para evitar problemas de restricciones de clave foránea
                    tablas = [
                        'asistencia', 
                        'venta_producto', 
                        'pago_mensualidad', 
                        'medidas_corporales', 
                        'objetivo_personal', 
                        'usuario', 
                        'producto',
                        'admin'
                    ]
                    
                    # Desactivar restricciones de clave foránea temporalmente
                    db.session.execute(text('PRAGMA foreign_keys = OFF;'))
                    
                    # Borrar datos de cada tabla
                    registros_eliminados = 0
                    errores = []
                    for tabla in tablas:
                        try:
                            # Verificar primero si la tabla existe
                            result = db.session.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla}';"))
                            if result.scalar():
                                result = db.session.execute(text(f"DELETE FROM {tabla};"))
                                registros_eliminados += result.rowcount
                            else:
                                errores.append(f"La tabla '{tabla}' no existe en la base de datos")
                        except Exception as e:
                            errores.append(f"Error al limpiar tabla '{tabla}': {str(e)}")
                            continue
                    
                    # Reactivar restricciones de clave foránea
                    db.session.execute(text('PRAGMA foreign_keys = ON;'))
                    
                    # Mostrar errores si hubo alguno
                    if errores:
                        for error in errores:
                            flash(f'Advertencia: {error}', 'warning')
                    
                    # Resetear secuencias de autoincremento
                    try:
                        # Primero verificar si la tabla sqlite_sequence existe
                        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';"))
                        if result.scalar():
                            # La tabla existe, resetear cada secuencia
                            for tabla in tablas:
                                try:
                                    db.session.execute(text(f"DELETE FROM sqlite_sequence WHERE name='{tabla}';"))
                                except Exception as e:
                                    # Ignorar errores individuales al resetear secuencias
                                    flash(f'Advertencia: No se pudo resetear la secuencia para {tabla}: {str(e)}', 'warning')
                    except Exception as e:
                        # Si hay algún error al verificar o manipular sqlite_sequence, solo lo registramos y continuamos
                        flash(f'Advertencia: Error al manipular secuencias de autoincremento: {str(e)}', 'warning')
                    
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Error al confirmar los cambios: {str(e)}. Se realizó un rollback.', 'danger')
                        return redirect(url_for('main.admin.configuracion'))
                    
                    # Recrear el administrador si se solicitó
                    if keep_admin and admin_actual:
                        try:
                            # Crear un nuevo administrador con los mismos datos
                            nuevo_admin = Admin(
                                nombre=admin_info['nombre'],
                                usuario=admin_info['usuario'],
                                rol=admin_info['rol']
                            )
                            # Asignar el hash directamente para mantener la misma contraseña
                            nuevo_admin.password_hash = admin_info['password_hash']
                            db.session.add(nuevo_admin)
                            db.session.commit()
                            
                            # Actualizar la sesión con el nuevo ID
                            session['admin_id'] = nuevo_admin.id
                            session['admin_nombre'] = nuevo_admin.nombre
                            session['admin_rol'] = nuevo_admin.rol
                            
                            flash('Se ha recreado tu cuenta de administrador.', 'success')
                        except Exception as e:
                            db.session.rollback()
                            flash(f'Advertencia: No se pudo recrear la cuenta de administrador: {str(e)}', 'warning')
                    
                    # Optimizar la base de datos después de la limpieza
                    try:
                        db.session.execute(text('VACUUM;'))
                        db.session.commit()
                    except Exception as e:
                        flash(f'Advertencia: No se pudo optimizar la base de datos: {str(e)}', 'warning')
                    
                    # Mensaje de éxito
                    if errores:
                        flash(f'Base de datos borrada parcialmente. Se eliminaron {registros_eliminados} registros. Se encontraron {len(errores)} errores.', 'warning')
                    else:
                        flash(f'Base de datos completamente borrada. Se eliminaron {registros_eliminados} registros de todas las tablas.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error al borrar la base de datos: {str(e)}', 'danger')
            
            elif accion == 'configure_daily_report':
                # Procesar configuración del reporte diario
                success, message = process_daily_report_config(request.form)
                if success:
                    flash(message, 'success')
                else:
                    flash(message, 'danger')
                    
                return redirect(url_for('main.admin.configuracion'))
    except Exception as e:
        flash(f'Error en la configuración: {str(e)}', 'danger')
        return redirect(url_for('main.index'))
    
    # Obtener lista de archivos de backup
    import os
    backup_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
    backups = []
    if os.path.exists(backup_folder):
        backups = sorted([f for f in os.listdir(backup_folder) if f.startswith('backup_db_')], reverse=True)
    
    # Obtener resultados de SQL si existen
    sql_results = session.pop('sql_results', None)
    
    # Cargar configuración de reporte diario si existe
    daily_report_config = None
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'daily_report.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                daily_report_config = json.load(f)
        except Exception:
            daily_report_config = None
    
    return render_template('admin/configuracion.html', backups=backups, sql_results=sql_results, daily_report_config=daily_report_config)

@bp.route('/download_backup/<filename>')
@admin_required
def download_backup(filename):
    import os
    from flask import send_from_directory
    
    backup_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
    return send_from_directory(directory=backup_folder, path=filename, as_attachment=True)

@bp.route('/delete_backup/<filename>')
@admin_required
def delete_backup(filename):
    import os
    
    backup_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
    backup_path = os.path.join(backup_folder, filename)
    
    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
            flash(f'Backup {filename} eliminado correctamente', 'success')
        else:
            flash(f'El archivo {filename} no existe', 'warning')
    except Exception as e:
        flash(f'Error al eliminar backup: {str(e)}', 'danger')
    
    return redirect(url_for('main.admin.configuracion'))

@bp.route('/cambiar_rol/<int:admin_id>', methods=['POST'])
@admin_required
def cambiar_rol(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    
    # Verificar que el usuario actual sea administrador
    current_admin = Admin.query.get(session['admin_id'])
    
    if current_admin.rol != 'administrador':
        flash('No tienes permisos para cambiar roles', 'danger')
        return redirect(url_for('main.admin.lista_admins'))
    
    # Verificar que no sea el último administrador al cambiar su propio rol
    if admin.id == current_admin.id and admin.rol == 'administrador':
        # Contar cuántos administradores hay en total
        admin_count = Admin.query.filter_by(rol='administrador').count()
        if admin_count <= 1 and request.form.get('rol') != 'administrador':
            flash('No puedes cambiar tu rol. Debe existir al menos un administrador en el sistema.', 'danger')
            return redirect(url_for('main.admin.lista_admins'))
    
    # Cambiar el rol
    nuevo_rol = request.form.get('rol')
    if nuevo_rol in ['administrador', 'recepcionista']:
        admin.rol = nuevo_rol
        db.session.commit()
        flash(f'Rol de {admin.nombre} cambiado a {nuevo_rol} correctamente', 'success')
        
        # Si el usuario cambió su propio rol a recepcionista, actualizar la sesión
        if admin.id == current_admin.id:
            session['admin_rol'] = nuevo_rol
    else:
        flash('Rol inválido', 'danger')
    
    return redirect(url_for('main.admin.lista_admins'))

@bp.route('/export_data/<format>/<table>', methods=['POST'])
@admin_required
def export_data(format, table):
    """Exporta datos de la tabla especificada en el formato solicitado (pdf o excel)"""
    try:
        # Verificar formato válido
        if format not in ['pdf', 'excel']:
            flash('Formato de exportación no válido', 'danger')
            return redirect(url_for('main.admin.configuracion'))
        
        # Crear carpeta para exportaciones si no existe
        export_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
        os.makedirs(export_folder, exist_ok=True)
        
        # Fecha para el nombre del archivo
        fecha_actual = datetime_colombia().strftime('%Y%m%d_%H%M%S')
        
        # Obtener datos según la tabla seleccionada
        if table == 'usuarios':
            data = Usuario.query.all()
            headers = ['ID', 'Nombre', 'Teléfono', 'Plan', 'Fecha Ingreso', 'Método Pago', 'Fecha Vencimiento']
            rows = [[u.id, u.nombre, u.telefono, u.plan, u.fecha_ingreso, u.metodo_pago, u.fecha_vencimiento_plan] for u in data]
            title = "Usuarios Registrados"
        
        elif table == 'asistencias':
            data = db.session.query(Asistencia, Usuario).join(Usuario).all()
            headers = ['ID', 'Usuario ID', 'Nombre Usuario', 'Fecha']
            rows = [[a.id, a.usuario_id, u.nombre, a.fecha] for a, u in data]
            title = "Registro de Asistencias"
        
        elif table == 'pagos':
            data = db.session.query(PagoMensualidad, Usuario).join(Usuario).all()
            headers = ['ID', 'Usuario', 'Fecha Pago', 'Monto', 'Método Pago', 'Plan', 'Fecha Inicio', 'Fecha Fin']
            rows = [[p.id, u.nombre, p.fecha_pago, p.monto, p.metodo_pago, p.plan, p.fecha_inicio, p.fecha_fin] for p, u in data]
            title = "Registro de Pagos"
        
        elif table == 'productos':
            data = Producto.query.all()
            headers = ['ID', 'Nombre', 'Descripción', 'Precio', 'Stock', 'Categoría', 'Fecha Creación']
            rows = [[p.id, p.nombre, p.descripcion, p.precio, p.stock, p.categoria, p.fecha_creacion] for p in data]
            title = "Inventario de Productos"
        
        elif table == 'ventas':
            data = db.session.query(VentaProducto, Producto, Usuario).\
                join(Producto).\
                outerjoin(Usuario).all()
            headers = ['ID', 'Producto', 'Usuario', 'Cantidad', 'Precio Unitario', 'Total', 'Método Pago', 'Fecha']
            rows = [[v.id, p.nombre, u.nombre if u else 'Sin usuario', v.cantidad, v.precio_unitario, v.total, v.metodo_pago, v.fecha] for v, p, u in data]
            title = "Registro de Ventas"
        else:
            flash('Tabla no válida para exportación', 'danger')
            return redirect(url_for('main.admin.configuracion'))
        
        # Exportar según el formato
        if format == 'pdf':
            # Verificar si ReportLab está instalado
            try:
                import reportlab
            except ImportError:
                flash('Para exportar a PDF se requiere instalar la biblioteca ReportLab. Por favor, ejecute: pip install reportlab', 'warning')
                return redirect(url_for('main.admin.configuracion'))
                
            # Importar módulos necesarios para PDF
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            # Nombre del archivo
            filename = f'export_{table}_{fecha_actual}.pdf'
            filepath = os.path.join(export_folder, filename)
            
            # Crear documento PDF
            doc = SimpleDocTemplate(filepath, pagesize=landscape(letter))
            elements = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            
            # Añadir título
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 20))
            
            # Preparar datos para la tabla (incluyendo encabezados)
            data_with_headers = [headers] + rows
            
            # Crear tabla
            table = Table(data_with_headers)
            
            # Estilo de tabla
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ])
            table.setStyle(style)
            
            # Añadir tabla al documento
            elements.append(table)
            
            # Generar PDF
            doc.build(elements)
            
            return send_file(filepath, as_attachment=True, download_name=filename)
            
        elif format == 'excel':
            # Verificar si pandas y openpyxl están instalados
            try:
                import pandas as pd
                import xlsxwriter
            except ImportError:
                flash('Para exportar a Excel se requiere instalar las bibliotecas pandas, openpyxl y xlsxwriter. Por favor, ejecute: pip install pandas openpyxl xlsxwriter', 'warning')
                return redirect(url_for('main.admin.configuracion'))
            
            # Nombre del archivo
            filename = f'export_{table}_{fecha_actual}.xlsx'
            filepath = os.path.join(export_folder, filename)
            
            # Crear DataFrame y exportar a Excel
            df = pd.DataFrame(rows, columns=headers)
            
            # Crear Excel writer con XlsxWriter como motor
            writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
            df.to_excel(writer, sheet_name=title, index=False)
            
            # Obtener objeto workbook y worksheet
            workbook = writer.book
            worksheet = writer.sheets[title]
            
            # Añadir formato a los encabezados
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Formato para las celdas
            cell_format = workbook.add_format({'border': 1})
            
            # Aplicar formato a los encabezados
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Ajustar ancho de columnas
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
            
            # Guardar el archivo
            writer.close()
            
            return send_file(filepath, as_attachment=True, download_name=filename)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error al exportar datos: {str(e)}', 'danger')
        return redirect(url_for('main.admin.configuracion'))

@bp.route('/export_to_external_db', methods=['POST'])
@admin_required
def export_to_external_db():
    """Exporta la base de datos SQLite a una base de datos externa (MySQL o PostgreSQL)"""
    try:
        db_type = request.form.get('db_type')
        db_host = request.form.get('db_host')
        db_port = request.form.get('db_port')
        db_name = request.form.get('db_name')
        db_user = request.form.get('db_user')
        db_password = request.form.get('db_password')
        
        # Validar parámetros
        if not all([db_type, db_host, db_port, db_name, db_user]):
            flash('Todos los campos son obligatorios excepto la contraseña', 'warning')
            return redirect(url_for('main.admin.configuracion'))
        
        # Importar SQLAlchemy para crear el motor según tipo de BD
        from sqlalchemy import create_engine, inspect, MetaData, Table, Column, Integer, String, Float, Date, DateTime, Text, ForeignKey
        
        # Verificar si pandas está instalado
        try:
            import pandas as pd
        except ImportError:
            flash('Para exportar a bases de datos externas se requiere la biblioteca pandas. Por favor, ejecute: pip install pandas', 'warning')
            return redirect(url_for('main.admin.configuracion'))
        
        # Crear conexión a la BD externa
        if db_type == 'mysql':
            try:
                import pymysql
                # Configurar pymysql para MySQL
                pymysql.install_as_MySQLdb()
            except ImportError:
                flash('Para exportar a MySQL se requiere la biblioteca PyMySQL. Por favor, ejecute: pip install pymysql', 'warning')
                return redirect(url_for('main.admin.configuracion'))
                
            engine_url = f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
        elif db_type == 'postgresql':
            try:
                import psycopg2
            except ImportError:
                flash('Para exportar a PostgreSQL se requiere la biblioteca psycopg2-binary. Por favor, ejecute: pip install psycopg2-binary', 'warning')
                return redirect(url_for('main.admin.configuracion'))
                
            engine_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            flash('Tipo de base de datos no soportado', 'danger')
            return redirect(url_for('main.admin.configuracion'))
        
        # Crear conexión
        try:
            engine = create_engine(engine_url)
            connection = engine.connect()
            connection.close()
        except Exception as e:
            flash(f'Error de conexión a la base de datos: {str(e)}', 'danger')
            return redirect(url_for('main.admin.configuracion'))
        
        # Obtener metadatos de SQLite
        sqlite_engine = db.engine
        sqlite_inspector = inspect(sqlite_engine)
        
        # Tablas a exportar
        tables = ['admin', 'usuario', 'producto', 'asistencia', 'pago_mensualidad', 'venta_producto']
        
        # Transferir cada tabla
        for table_name in tables:
            # Verificar si la tabla existe en SQLite
            if table_name not in sqlite_inspector.get_table_names():
                flash(f'Tabla {table_name} no encontrada en SQLite', 'warning')
                continue
            
            # Cargar datos de SQLite
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, sqlite_engine)
            
            # Exportar a la base de datos externa
            df.to_sql(table_name, engine, if_exists='replace', index=False)
        
        flash('Datos exportados correctamente a la base de datos externa', 'success')
        return redirect(url_for('main.admin.configuracion'))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error al exportar a base de datos externa: {str(e)}', 'danger')
        return redirect(url_for('main.admin.configuracion'))

@bp.route('/test_daily_report', methods=['POST'])
@admin_required
def test_daily_report():
    """Prueba la conexión al servicio de reporte diario"""
    try:
        # Obtener datos del request
        data = request.get_json()
        url = data.get('url')
        apikey = data.get('apikey')
        
        if not url:
            return jsonify({'success': False, 'message': 'URL no especificada'})
        
        # Probar la conexión enviando una solicitud de prueba
        from datetime import datetime
        
        # Datos de prueba
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'Reto Fit - Carlenis Ortiz',
            'type': 'connection_test',
            'apikey': apikey
        }
        
        # Intentar realizar la solicitud
        response = requests.post(url, json=test_data, timeout=5)
        
        # Verificar respuesta
        if response.status_code == 200:
            response_data = response.json()
            return jsonify({
                'success': True, 
                'message': f'Conexión exitosa (código {response.status_code})'
            })
        else:
            return jsonify({
                'success': False, 
                'message': f'Error: Código de respuesta {response.status_code}'
            })
            
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'Error de conexión: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

def process_daily_report_config(form_data):
    """Procesa la configuración del reporte diario desde el formulario"""
    try:
        config = {
            'url': form_data.get('daily_report_url', '').strip(),
            'apikey': form_data.get('daily_report_apikey', '').strip(),
            'include_users': 'include_users' in form_data,
            'include_attendance': 'include_attendance' in form_data,
            'include_payments': 'include_payments' in form_data,
            'include_sales': 'include_sales' in form_data,
        }
        
        # Guardar la configuración
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
        os.makedirs(config_path, exist_ok=True)
        
        with open(os.path.join(config_path, 'daily_report.json'), 'w') as f:
            json.dump(config, f, indent=4)
            
        return True, "Configuración guardada correctamente"
    except Exception as e:
        return False, f"Error al guardar configuración: {str(e)}"

@bp.route('/send_daily_report', methods=['POST'])
@admin_required
def send_daily_report():
    """Envía el reporte diario al servidor configurado"""
    try:
        # Cargar configuración
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'daily_report.json')
        
        if not os.path.exists(config_path):
            flash("No hay configuración de reporte diario", "warning")
            return redirect(url_for('main.admin.configuracion'))
            
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        url = config.get('url')
        apikey = config.get('apikey')
        
        if not url:
            flash("URL del servicio no configurada", "warning")
            return redirect(url_for('main.admin.configuracion'))
            
        # Fecha actual para filtrar registros
        from datetime import datetime, timedelta
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Preparar datos del reporte
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'date': today.isoformat(),
            'source': 'Reto Fit - Carlenis Ortiz',
            'apikey': apikey,
            'data': {}
        }
        
        # Recopilar datos según la configuración
        if config.get('include_users'):
            # Nuevos usuarios registrados hoy
            nuevos_usuarios = Usuario.query.filter(
                func.date(Usuario.fecha_ingreso) == today
            ).all()
            
            report_data['data']['new_users'] = [{
                'id': u.id,
                'nombre': u.nombre,
                'telefono': u.telefono,
                'plan': u.plan,
                'fecha_ingreso': u.fecha_ingreso.isoformat() if u.fecha_ingreso else None
            } for u in nuevos_usuarios]
        
        if config.get('include_attendance'):
            # Asistencias de hoy
            asistencias = db.session.query(
                Asistencia, Usuario.nombre.label('usuario_nombre')
            ).join(Usuario).filter(
                func.date(Asistencia.fecha) == today
            ).all()
            
            report_data['data']['attendance'] = [{
                'id': a.id,
                'usuario_id': a.usuario_id,
                'usuario_nombre': usuario_nombre,
                'fecha': a.fecha.isoformat() if a.fecha else None
            } for a, usuario_nombre in asistencias]
        
        if config.get('include_payments'):
            # Pagos registrados hoy
            pagos = db.session.query(
                PagoMensualidad, Usuario.nombre.label('usuario_nombre')
            ).join(Usuario).filter(
                func.date(PagoMensualidad.fecha_pago) == today
            ).all()
            
            report_data['data']['payments'] = [{
                'id': p.id,
                'usuario_id': p.usuario_id,
                'usuario_nombre': usuario_nombre,
                'fecha_pago': p.fecha_pago.isoformat() if p.fecha_pago else None,
                'monto': float(p.monto) if p.monto else 0,
                'plan': p.plan,
                'metodo_pago': p.metodo_pago
            } for p, usuario_nombre in pagos]
        
        if config.get('include_sales'):
            # Ventas realizadas hoy
            ventas = db.session.query(
                VentaProducto, 
                Producto.nombre.label('producto_nombre'),
                Usuario.nombre.label('usuario_nombre')
            ).join(Producto).outerjoin(Usuario).filter(
                func.date(VentaProducto.fecha) == today
            ).all()
            
            report_data['data']['sales'] = [{
                'id': v.id,
                'producto_id': v.producto_id,
                'producto_nombre': producto_nombre,
                'usuario_id': v.usuario_id,
                'usuario_nombre': usuario_nombre if v.usuario_id else None,
                'cantidad': v.cantidad,
                'precio_unitario': float(v.precio_unitario) if v.precio_unitario else 0,
                'total': float(v.total) if v.total else 0,
                'fecha': v.fecha.isoformat() if v.fecha else None,
                'metodo_pago': v.metodo_pago
            } for v, producto_nombre, usuario_nombre in ventas]
        
        # Agregar resumen
        report_data['summary'] = {
            'total_nuevos_usuarios': len(report_data['data'].get('new_users', [])),
            'total_asistencias': len(report_data['data'].get('attendance', [])),
            'total_pagos': len(report_data['data'].get('payments', [])),
            'total_ventas': len(report_data['data'].get('sales', [])),
            'total_ingresos_pagos': sum(p.get('monto', 0) for p in report_data['data'].get('payments', [])),
            'total_ingresos_ventas': sum(v.get('total', 0) for v in report_data['data'].get('sales', []))
        }
        
        # Enviar datos al servidor
        import requests
        response = requests.post(url, json=report_data, timeout=10)
        
        # Verificar respuesta
        if response.status_code == 200:
            # Guardar registro del envío
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
            os.makedirs(log_path, exist_ok=True)
            
            with open(os.path.join(log_path, f'daily_report_{today.strftime("%Y%m%d")}.json'), 'w') as f:
                json.dump(report_data, f, indent=4)
                
            flash("Reporte diario enviado correctamente", "success")
        else:
            flash(f"Error al enviar reporte: Código {response.status_code}", "danger")
            
        return redirect(url_for('main.admin.configuracion'))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"Error al enviar reporte diario: {str(e)}", "danger")
        return redirect(url_for('main.admin.configuracion')) 