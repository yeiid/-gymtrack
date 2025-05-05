from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Admin, db
from datetime import datetime
from functools import wraps

# Crear blueprint
bp = Blueprint('auth', __name__, url_prefix='/auth')

# Decorador para verificar autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Debe iniciar sesión para acceder a esta sección', 'warning')
            return redirect(url_for('main.auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para verificar si es administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
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
        
        # Solo verificar que sea administrador, no redireccionar
        # Esto permite que la función maneje el caso del recepcionista
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/inicializar')
def inicializar_admin():
    try:
        # Verificar si ya existe un admin
        admin_count = Admin.query.count()
        
        if admin_count > 0:
            flash('Ya existen administradores en el sistema.', 'info')
            return redirect(url_for('main.auth.login'))
            
        # Crear admin por defecto
        admin_default = Admin(
            nombre="Administrador Principal",
            usuario="admin",
            rol="administrador"
        )
        # Crear password explícitamente
        password = "admin123"
        admin_default.set_password(password)
        
        # Guardar en la base de datos
        db.session.add(admin_default)
        db.session.commit()
        
        # Confirmar que se creó correctamente
        nuevo_admin = Admin.query.filter_by(usuario="admin").first()
        if nuevo_admin and nuevo_admin.check_password("admin123"):
            flash(f'Administrador creado correctamente. Usuario: admin, Contraseña: admin123', 'success')
        else:
            flash('Se creó el administrador pero hay problemas con la autenticación.', 'warning')
            
        return redirect(url_for('main.auth.login'))
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error al crear administrador: {str(e)}', 'danger')
        return render_template('auth/login.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Intentar verificar si existen administradores
    try:
        admin_count = Admin.query.count()
        if admin_count == 0:
            flash('No existen administradores. Redirigiendo a la página de inicialización...', 'warning')
            return redirect(url_for('main.auth.inicializar_admin'))
    except Exception as e:
        flash(f'Error al verificar administradores: {str(e)}', 'danger')
    
    if request.method == 'POST':
        try:
            usuario = request.form['usuario']
            password = request.form['password']
            
            print(f"Intento de login: Usuario={usuario}")
            
            admin = Admin.query.filter_by(usuario=usuario).first()
            
            if admin:
                print(f"Usuario encontrado: ID={admin.id}, Nombre={admin.nombre}, Rol={admin.rol}")
                print(f"Hash de contraseña almacenado: {admin.password_hash if hasattr(admin, 'password_hash') else 'No tiene hash'}")
                
                # Verificar si el hash de contraseña está vacío o corrupto
                if not admin.password_hash or len(admin.password_hash) < 20:
                    print(f"Hash de contraseña inválido o vacío. Resetear contraseña.")
                    admin.set_password("admin123")
                    db.session.commit()
                    flash('Tu contraseña ha sido restablecida a "admin123". Por favor, inténtalo de nuevo.', 'warning')
                    return render_template('auth/login.html')
                
                try:
                    if admin.check_password(password):
                        print(f"Contraseña correcta, iniciando sesión")
                        session['admin_id'] = admin.id
                        session['admin_nombre'] = admin.nombre
                        session['admin_rol'] = admin.rol
                        
                        print(f"Sesión creada: admin_id={session.get('admin_id')}, admin_nombre={session.get('admin_nombre')}, admin_rol={session.get('admin_rol')}")
                        
                        # Actualizar fecha de último acceso
                        admin.ultimo_acceso = datetime.now()
                        db.session.commit()
                        
                        flash(f'¡Bienvenido, {admin.nombre}!', 'success')
                        return redirect(url_for('main.index'))
                    else:
                        print(f"Contraseña incorrecta para usuario {usuario}")
                        flash('Usuario o contraseña incorrectos', 'danger')
                except Exception as pwd_err:
                    print(f"Error en verificación de contraseña: {str(pwd_err)}")
                    flash(f'Error en autenticación: {str(pwd_err)}', 'danger')
            else:
                print(f"Usuario {usuario} no encontrado")
                flash('Usuario o contraseña incorrectos', 'danger')
        except Exception as e:
            print(f"Error en login: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Error al procesar el login: {str(e)}', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.pop('admin_id', None)
    session.pop('admin_nombre', None)
    session.pop('admin_rol', None)
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('main.index'))

@bp.route('/cambiar_contrasena', methods=['GET', 'POST'])
@login_required
def cambiar_contrasena():
    admin = Admin.query.get(session['admin_id'])
    
    if request.method == 'POST':
        contrasena_actual = request.form.get('contrasena_actual')
        nueva_contrasena = request.form.get('nueva_contrasena')
        confirmar_contrasena = request.form.get('confirmar_contrasena')
        
        if not admin.check_password(contrasena_actual):
            flash('La contraseña actual es incorrecta', 'danger')
            return render_template('auth/cambiar_contrasena.html')
        
        if nueva_contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('auth/cambiar_contrasena.html')
        
        admin.set_password(nueva_contrasena)
        db.session.commit()
        
        flash('Contraseña actualizada correctamente', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('auth/cambiar_contrasena.html')

@bp.route('/debug-session')
def debug_session():
    from flask import jsonify
    
    # Muestra información de la sesión para depuración
    session_info = {
        'admin_id': session.get('admin_id'),
        'admin_nombre': session.get('admin_nombre'),
        'admin_rol': session.get('admin_rol'),
        'is_authenticated': 'admin_id' in session
    }
    
    return f"""
    <h3>Información de sesión</h3>
    <pre>{session_info}</pre>
    <p><a href="{url_for('main.index')}">Volver al inicio</a></p>
    """

# Añadir una nueva ruta para resetear la contraseña de emergencia
@bp.route('/reset_admin')
def reset_admin_password():
    try:
        # Buscar usuario admin
        admin = Admin.query.filter_by(usuario="admin").first()
        
        if admin:
            # Resetear contraseña
            admin.set_password("admin123")
            db.session.commit()
            flash('Contraseña del administrador restablecida a "admin123"', 'success')
        else:
            # Si no existe, crear uno nuevo
            nuevo_admin = Admin(
                nombre="Administrador Principal",
                usuario="admin",
                rol="administrador"
            )
            nuevo_admin.set_password("admin123")
            db.session.add(nuevo_admin)
            db.session.commit()
            flash('Administrador creado con usuario "admin" y contraseña "admin123"', 'success')
        
        return redirect(url_for('main.auth.login'))
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error al resetear administrador: {str(e)}', 'danger')
        return render_template('auth/login.html') 