from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from models import db

# Crear el Blueprint principal
main = Blueprint('main', __name__)

# Importar blueprints de cada módulo directamente
from routes.usuarios.routes import bp as usuarios_bp
from routes.finanzas.routes import bp as finanzas_bp
from routes.productos.routes import bp as productos_bp
from routes.ventas.routes import bp as ventas_bp
from routes.admin.routes import bp as admin_bp
from routes.auth.routes import bp as auth_bp

# Registrar todas las rutas en el Blueprint principal
main.register_blueprint(usuarios_bp)
main.register_blueprint(finanzas_bp)
main.register_blueprint(productos_bp)
main.register_blueprint(ventas_bp)
main.register_blueprint(admin_bp)
main.register_blueprint(auth_bp)

# Crear rutas con nombres específicos para solucionar problemas de navegación
@main.route('/usuarios/ver_usuario/<int:usuario_id>')
def ver_usuario_directo(usuario_id):
    from routes.usuarios.routes import ver_usuario
    return ver_usuario(usuario_id)

# Ruta adicional para manejar /usuarios/<id> directamente
@main.route('/usuarios/<int:usuario_id>')
def usuario_directo(usuario_id):
    print(f"Llamada a usuario_directo con ID: {usuario_id}")
    try:
        # Llamar directamente a la función ver_usuario en lugar de redireccionar
        from routes.usuarios.routes import ver_usuario
        return ver_usuario(usuario_id)
    except Exception as e:
        # Registrar el error y mostrar un mensaje de error amigable
        print(f"Error al mostrar usuario {usuario_id}: {str(e)}")
        flash(f"Error al mostrar información del usuario: {str(e)}", "danger")
        return redirect(url_for('main.usuarios.index'))

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/actualizar-bd')
def actualizar_bd():
    print("Actualizando estructura de la base de datos...")
    try:
        # Añadir la columna fecha_completado si no existe
        db.engine.execute('ALTER TABLE objetivo_personal ADD COLUMN fecha_completado DATE;')
        print("Columna fecha_completado añadida correctamente")
        
        # Añadir la columna estado si no existe
        try:
            db.engine.execute('ALTER TABLE objetivo_personal ADD COLUMN estado VARCHAR(20) DEFAULT "En progreso";')
            print("Columna estado añadida correctamente")
        except Exception as e:
            if 'duplicate column name' in str(e).lower():
                print("La columna estado ya existe")
            else:
                raise e
                
        return "Base de datos actualizada correctamente. <a href='/'>Volver al inicio</a>"
    except Exception as e:
        print(f"Error al actualizar la base de datos: {str(e)}")
        return f"Error al actualizar la base de datos: {str(e)}. <a href='/'>Volver al inicio</a>"

@main.route('/emergencia-admin', methods=['GET', 'POST'])
def emergencia_admin():
    # Esta ruta es solo para emergencias cuando no hay administradores
    import os
    from models import db, Admin
    from sqlalchemy import text
    
    # Verificar si ya existe un administrador
    admin_count = Admin.query.filter_by(rol='administrador').count()
    if admin_count > 0:
        # Si ya hay administradores, redirigir a la página de administradores
        return redirect(url_for('main.admin.lista_admins'))
    
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        if admin_id and admin_id.isdigit():
            try:
                # Cambiar el rol del usuario a administrador
                db.session.execute(text(f"UPDATE admin SET rol = 'administrador' WHERE id = {admin_id}"))
                db.session.commit()
                flash('¡Rol actualizado correctamente! Ahora tienes permisos de administrador.', 'success')
                
                # Actualizar la sesión si es el usuario actual
                if 'admin_id' in session and session['admin_id'] == int(admin_id):
                    session['admin_rol'] = 'administrador'
                
                return redirect(url_for('main.admin.lista_admins'))
            except Exception as e:
                flash(f'Error al actualizar rol: {str(e)}', 'danger')
    
    # Obtener todos los usuarios
    administradores = Admin.query.all()
    return render_template('admin/emergencia_admin.html', administradores=administradores)

@main.route('/actualizar-rol-admin')
def actualizar_rol_admin():
    """Ruta de emergencia para actualizar el rol a administrador"""
    try:
        from models import Admin
        from flask import session
        
        # Verificar si hay un usuario en sesión
        if 'admin_id' not in session:
            return "No hay sesión activa. Por favor inicia sesión primero. <a href='/'>Volver al inicio</a>"
        
        # Obtener el usuario actual
        admin_id = session['admin_id']
        admin = Admin.query.get(admin_id)
        
        if not admin:
            return "Usuario no encontrado. <a href='/'>Volver al inicio</a>"
        
        # Actualizar el rol a administrador
        old_rol = admin.rol
        admin.rol = 'administrador'
        db.session.commit()
        
        # Actualizar la sesión
        session['admin_rol'] = 'administrador'
        
        return f"""
        <h3>¡Rol actualizado correctamente!</h3>
        <p>Usuario: {admin.nombre} ({admin.usuario})</p>
        <p>Rol anterior: {old_rol}</p>
        <p>Rol actual: {admin.rol}</p>
        <p><a href='/admin/lista_admins'>Ir a la página de administradores</a></p>
        <p><a href='/'>Volver al inicio</a></p>
        """
    except Exception as e:
        return f"Error al actualizar rol: {str(e)} <a href='/'>Volver al inicio</a>"

@main.route('/login')
def login_directo():
    """Ruta directa para ir al login"""
    return redirect(url_for('main.auth.login'))

@main.route('/registrar_venta', methods=['GET', 'POST'])
def registrar_venta_directo():
    """Ruta directa para el registro de ventas"""
    success = request.args.get('success')
    error = request.args.get('error')
    
    # Convertir mensajes de URL a flash messages para asegurar consistencia
    if success:
        flash(success, "success")
    if error:
        flash(error, "danger")
        
    from routes.productos.routes import registrar_venta
    return registrar_venta() 