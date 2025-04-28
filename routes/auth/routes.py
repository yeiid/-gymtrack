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
            
        if admin.rol != 'administrador':
            flash('No tiene permisos para acceder a esta sección', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        
        admin = Admin.query.filter_by(usuario=usuario).first()
        
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_nombre'] = admin.nombre
            session['admin_rol'] = admin.rol
            
            # Actualizar fecha de último acceso
            admin.ultimo_acceso = datetime.now()
            db.session.commit()
            
            flash(f'¡Bienvenido, {admin.nombre}!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.pop('admin_id', None)
    session.pop('admin_nombre', None)
    session.pop('admin_rol', None)
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('main.index')) 