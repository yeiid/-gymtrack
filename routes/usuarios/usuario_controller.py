from flask import render_template, request, redirect, url_for, flash
from models import db, Usuario, Asistencia, MedidasCorporales, ObjetivoPersonal, PagoMensualidad, VentaProducto
from models import datetime_colombia, date_colombia
from datetime import datetime, timedelta
from routes.auth.routes import admin_required
from routes.usuarios.routes import bp

# Función para calcular días restantes de un plan
def calcular_dias_restantes(usuario):
    if not usuario.fecha_vencimiento_plan:
        return None
    
    hoy = date_colombia()
    dias = (usuario.fecha_vencimiento_plan - hoy).days
    return dias

# Función para calcular fecha de vencimiento sumando exactamente los días del plan
def calcular_fecha_vencimiento(fecha_inicio, tipo_plan):
    """
    Calcula la fecha de vencimiento sumando exactamente los días según el tipo de plan.
    
    Args:
        fecha_inicio: Fecha de inicio (date)
        tipo_plan: Tipo de plan ('Diario', 'Quincenal', 'Mensual', etc.)
        
    Returns:
        Fecha de vencimiento (date)
    """
    if tipo_plan == 'Diario':
        return fecha_inicio + timedelta(days=1)
    elif tipo_plan == 'Quincenal':
        return fecha_inicio + timedelta(days=15)
    elif tipo_plan == 'Mensual':
        return fecha_inicio + timedelta(days=30)
    elif tipo_plan == 'Estudiantil':
        return fecha_inicio + timedelta(days=30)
    elif tipo_plan == 'Dirigido':
        return fecha_inicio + timedelta(days=30)
    elif tipo_plan == 'Personalizado':
        return fecha_inicio + timedelta(days=30)
    else:
        # Por defecto, 30 días
        return fecha_inicio + timedelta(days=30)

@bp.route('/')
def index():
    usuarios = Usuario.query.all()
    success = request.args.get('success')
    error = request.args.get('error')
    
    # Si hay mensajes en la URL, convertirlos a flash messages para asegurar consistencia
    if success:
        flash(success, "success")
    if error:
        flash(error, "danger")
    
    # Calcular días restantes para cada usuario
    usuarios_con_info = []
    for usuario in usuarios:
        dias_restantes = calcular_dias_restantes(usuario)
        usuarios_con_info.append({
            'usuario': usuario,
            'dias_restantes': dias_restantes,
            'estado': 'vencido' if dias_restantes is not None and dias_restantes < 0 else
                     'proximo' if dias_restantes is not None and dias_restantes <= 3 else
                     'activo' if dias_restantes is not None else 'sin_fecha'
        })
    
    return render_template('usuarios/usuarios.html', 
                          users=usuarios_con_info,
                          now=datetime_colombia())

@bp.route('/registrar_usuario', methods=['POST'])
def registrar_usuario():
    try:
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        plan = request.form['plan']
        metodo_pago = request.form['metodo_pago']
        fecha_pago_str = request.form.get('fecha_pago')
        fecha_vencimiento_str = request.form.get('fecha_vencimiento')
        
        # Verificar si ya existe un usuario con el mismo teléfono
        usuario_existente = Usuario.query.filter_by(telefono=telefono).first()
        
        if usuario_existente:
            # Usuario ya existe, mostrar mensaje
            flash(f"¡Usuario con teléfono {telefono} ya existe en el sistema!", "danger")
            return redirect(url_for('main.usuarios.index'))
        
        # Convertir fechas de string a objetos date
        fecha_pago = datetime.strptime(fecha_pago_str, '%Y-%m-%d').date() if fecha_pago_str else date_colombia()
        
        # Si se proporciona una fecha de vencimiento, usarla; de lo contrario, calcularla
        if fecha_vencimiento_str:
            fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
        else:
            fecha_vencimiento = calcular_fecha_vencimiento(fecha_pago, plan)
        
        # Calcular precio según el plan seleccionado
        if plan == 'Diario':
            precio_plan = Usuario.PRECIO_DIARIO
        elif plan == 'Quincenal':
            precio_plan = Usuario.PRECIO_QUINCENAL
        elif plan == 'Mensual':
            precio_plan = Usuario.PRECIO_MENSUAL
        elif plan == 'Estudiantil':
            precio_plan = Usuario.PRECIO_ESTUDIANTIL
        elif plan == 'Dirigido':
            precio_plan = Usuario.PRECIO_DIRIGIDO
        elif plan == 'Personalizado':
            precio_plan = Usuario.PRECIO_PERSONALIZADO
        else:
            precio_plan = 0
        
        # Crear el nuevo usuario
        nuevo_usuario = Usuario(
            nombre=nombre,
            telefono=telefono,
            plan=plan,
            metodo_pago=metodo_pago,
            fecha_vencimiento_plan=fecha_vencimiento,
            precio_plan=precio_plan,
            fecha_ingreso=fecha_pago  # Usar la fecha de pago como fecha de ingreso
        )
        
        db.session.add(nuevo_usuario)
        
        # Registrar el pago de mensualidad
        pago = PagoMensualidad(
            usuario=nuevo_usuario,
            monto=precio_plan,
            metodo_pago=metodo_pago,
            plan=plan,
            fecha_inicio=fecha_pago,
            fecha_fin=fecha_vencimiento,
            fecha_pago=datetime_colombia()  # La fecha de registro del pago es ahora
        )
        db.session.add(pago)
        
        db.session.commit()
        
        flash("Usuario registrado correctamente", "success")
        return redirect(url_for('main.usuarios.index'))
    except Exception as e:
        db.session.rollback()
        print(f"Error al registrar usuario: {str(e)}")
        
        # Verificar si el error está relacionado con la estructura de la base de datos
        if "no such column" in str(e).lower() or "unknown column" in str(e).lower():
            flash(f"Error en la estructura de la base de datos. Por favor, actualiza la base de datos visitando /actualizar-bd y luego intenta nuevamente.", "danger")
        else:
            flash(f"Error al registrar usuario: {str(e)}", "danger")
            
        return redirect(url_for('main.usuarios.index'))

@bp.route('/ver_usuario/<int:usuario_id>')
def ver_usuario(usuario_id):
    try:
        # Obtener el usuario con manejo de errores
        usuario = Usuario.query.get_or_404(usuario_id)
        
        # Obtener asistencias con manejo de errores
        try:
            asistencias = Asistencia.query.filter_by(usuario_id=usuario_id).order_by(Asistencia.fecha.desc()).all()
        except Exception as e:
            print(f"Error al obtener asistencias: {str(e)}")
            asistencias = []
        
        # Calcular días restantes y estado del plan
        try:
            dias_restantes = calcular_dias_restantes(usuario)
            estado_plan = 'vencido' if dias_restantes is not None and dias_restantes < 0 else \
                         'proximo' if dias_restantes is not None and dias_restantes <= 3 else \
                         'activo' if dias_restantes is not None else 'sin_fecha'
        except Exception as e:
            print(f"Error al calcular días restantes: {str(e)}")
            dias_restantes = None
            estado_plan = 'sin_fecha'
        
        # Obtener medidas corporales con manejo de errores
        try:
            ultima_medida = MedidasCorporales.query.filter_by(usuario_id=usuario_id).order_by(MedidasCorporales.fecha.desc()).first()
        except Exception as e:
            print(f"Error al obtener medidas: {str(e)}")
            ultima_medida = None
        
        # Obtener objetivos activos con manejo de errores
        try:
            objetivos_activos = ObjetivoPersonal.query.filter_by(
                usuario_id=usuario_id, 
                estado='En progreso'
            ).all()
        except Exception as e:
            print(f"Error al obtener objetivos: {str(e)}")
            # Verificar si la columna 'estado' existe, caso contrario usar filtro por completado
            try:
                objetivos_activos = ObjetivoPersonal.query.filter_by(
                    usuario_id=usuario_id, 
                    completado=False
                ).all()
            except:
                objetivos_activos = []
        
        # Obtener pagos de mensualidad con manejo de errores
        try:
            pagos = PagoMensualidad.query.filter_by(usuario_id=usuario_id).order_by(PagoMensualidad.fecha_pago.desc()).all()
        except Exception as e:
            print(f"Error al obtener pagos: {str(e)}")
            pagos = []
            
        # Obtener las ventas asociadas al usuario con manejo de errores
        try:
            ventas = VentaProducto.query.filter_by(usuario_id=usuario_id).order_by(VentaProducto.fecha.desc()).all()
        except Exception as e:
            print(f"Error al obtener ventas: {str(e)}")
            ventas = []
        
        # Añadir la fecha actual para las comparaciones en la plantilla
        today = datetime.now()
        
        return render_template('usuarios/ver_usuario.html', 
                              usuario=usuario, 
                              asistencias=asistencias,
                              dias_restantes=dias_restantes,
                              estado_plan=estado_plan,
                              ultima_medida=ultima_medida,
                              objetivos=objetivos_activos,
                              pagos=pagos,
                              ventas=ventas,
                              today=today)
    except Exception as e:
        print(f"Error al ver usuario: {str(e)}")
        flash(f"Error al cargar datos del usuario: {str(e)}", "danger")
        return redirect(url_for('main.usuarios.index'))

@bp.route('/editar_usuario/<int:usuario_id>', methods=['GET', 'POST'])
def editar_usuario(usuario_id):
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        
        if request.method == 'POST':
            nombre = request.form['nombre']
            telefono = request.form['telefono']
            plan = request.form['plan']
            metodo_pago = request.form['metodo_pago']
            
            # Verificar si el nuevo teléfono ya existe para otro usuario
            usuario_existente = Usuario.query.filter(
                Usuario.telefono == telefono,
                Usuario.id != usuario_id
            ).first()
            
            if usuario_existente:
                flash(f"¡Ya existe otro usuario con el teléfono {telefono}!", "danger")
                return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
            
            # Actualizar usuario
            usuario.nombre = nombre
            usuario.telefono = telefono
            usuario.plan = plan
            usuario.metodo_pago = metodo_pago
            
            # Actualizar fecha de vencimiento si se proporciona
            fecha_vencimiento_str = request.form.get('fecha_vencimiento')
            if fecha_vencimiento_str:
                usuario.fecha_vencimiento_plan = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
            
            db.session.commit()
            flash("Usuario actualizado correctamente", "success")
            return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
        
        # Añadir la fecha actual para las comparaciones en la plantilla
        today = datetime.now()
        
        return render_template('usuarios/editar_usuario.html', usuario=usuario, today=today)
    except Exception as e:
        db.session.rollback()
        flash(f"Error al editar usuario: {str(e)}", "danger")
        return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))

@bp.route('/eliminar_usuario/<int:usuario_id>', methods=['POST'])
@admin_required
def eliminar_usuario(usuario_id):
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        
        # Eliminar usuario y todas sus relaciones
        db.session.delete(usuario)
        db.session.commit()
        
        flash("Usuario eliminado correctamente", "success")
        return redirect(url_for('main.usuarios.index'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar usuario: {str(e)}", "danger")
        return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id)) 