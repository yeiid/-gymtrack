from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from models import db, Admin, Usuario, Asistencia, Producto, VentaProducto, PagoMensualidad, MedidasCorporales, ObjetivoPersonal
from datetime import datetime, timedelta
import os, shutil
from routes.auth.routes import admin_required

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
            flash('Debe iniciar sesión para acceder a esta sección', 'warning')
            return redirect(url_for('main.auth.login'))
            
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            # Si el admin no existe en la base de datos, cerrar sesión
            session.pop('admin_id', None)
            session.pop('admin_nombre', None)
            session.pop('admin_rol', None)
            flash('Su sesión ha expirado o ha sido eliminada. Por favor, inicie sesión nuevamente.', 'warning')
            return redirect(url_for('main.auth.login'))
            
        if admin.rol != 'administrador':
            flash('No tiene permisos para acceder a esta sección', 'danger')
            return redirect(url_for('main.index'))
    except Exception as e:
        flash(f'Error de autenticación: {str(e)}', 'danger')
        return redirect(url_for('main.auth.login'))
            
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        if accion == 'backup_db':
            try:
                # Crear copia de seguridad de la base de datos
                from datetime import datetime
                import os
                import shutil
                
                # Crear carpeta de backups si no existe
                backup_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
                os.makedirs(backup_folder, exist_ok=True)
                
                # Nombre del archivo de backup con fecha y hora
                fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f'backup_db_{fecha_actual}.db'
                backup_path = os.path.join(backup_folder, backup_filename)
                
                # Copiar el archivo de base de datos
                shutil.copy2('database.db', backup_path)
                
                flash(f'Copia de seguridad creada exitosamente: {backup_filename}', 'success')
            except Exception as e:
                flash(f'Error al crear copia de seguridad: {str(e)}', 'danger')
        
        elif accion == 'restore_db':
            # Implementar la restauración de la base de datos
            backup_file = request.files.get('backup_file')
            if backup_file:
                try:
                    import os
                    backup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp_backup.db')
                    backup_file.save(backup_path)
                    
                    # Cerrar la conexión con la base de datos actual
                    db.session.close()
                    
                    # Reemplazar la base de datos
                    import shutil
                    shutil.copy2(backup_path, 'database.db')
                    os.remove(backup_path)
                    
                    flash('Base de datos restaurada exitosamente. Por favor, reinicie la aplicación.', 'success')
                except Exception as e:
                    flash(f'Error al restaurar la base de datos: {str(e)}', 'danger')
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
                    fecha_limite = datetime.now() - timedelta(days=180)
                    resultado = db.session.execute(
                        text("DELETE FROM asistencia WHERE fecha < :fecha_limite"),
                        {"fecha_limite": fecha_limite}
                    )
                    registros_eliminados += resultado.rowcount
                
                # Limpiar pagos antiguos (mayores a 1 año)
                if request.form.get('clean_old_payments'):
                    fecha_limite = datetime.now() - timedelta(days=365)
                    resultado = db.session.execute(
                        text("DELETE FROM pago_mensualidad WHERE fecha_pago < :fecha_limite"),
                        {"fecha_limite": fecha_limite}
                    )
                    registros_eliminados += resultado.rowcount
                
                # Limpiar ventas antiguas (mayores a 1 año)
                if request.form.get('clean_old_sales'):
                    fecha_limite = datetime.now() - timedelta(days=365)
                    resultado = db.session.execute(
                        text("DELETE FROM venta_producto WHERE fecha < :fecha_limite"),
                        {"fecha_limite": fecha_limite}
                    )
                    registros_eliminados += resultado.rowcount
                
                # Limpiar usuarios inactivos (sin asistencia por más de 1 año)
                if request.form.get('clean_deleted_users'):
                    # Obtener usuarios sin asistencias en el último año
                    fecha_limite = datetime.now() - timedelta(days=365)
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
                from datetime import datetime
                
                tabla = request.form.get('tabla_exportar')
                export_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
                os.makedirs(export_folder, exist_ok=True)
                
                fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
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
                    from datetime import datetime
                    import os
                    import shutil
                    
                    # Crear carpeta de backups si no existe
                    backup_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
                    os.makedirs(backup_folder, exist_ok=True)
                    
                    # Nombre del archivo de backup con fecha y hora
                    fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_filename = f'backup_db_before_reset_{fecha_actual}.db'
                    backup_path = os.path.join(backup_folder, backup_filename)
                    
                    # Copiar el archivo de base de datos
                    shutil.copy2('database.db', backup_path)
                    flash(f'Copia de seguridad creada antes del borrado: {backup_filename}', 'info')
                
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
                    else:
                        flash('Aviso: La tabla sqlite_sequence no existe, se omitirá el reseteo de secuencias.', 'info')
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
    
    # Obtener lista de archivos de backup
    import os
    backup_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
    backups = []
    if os.path.exists(backup_folder):
        backups = sorted([f for f in os.listdir(backup_folder) if f.startswith('backup_db_')], reverse=True)
    
    # Obtener resultados de SQL si existen
    sql_results = session.pop('sql_results', None)
    
    return render_template('admin/configuracion.html', backups=backups, sql_results=sql_results)

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