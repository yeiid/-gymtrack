from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Usuario, Asistencia, MedidasCorporales, ObjetivoPersonal, PagoMensualidad
from datetime import datetime, timedelta
from sqlalchemy import func

# Crear blueprint para usuarios
bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@bp.route('/')
def index():
    usuarios = Usuario.query.all()
    success = request.args.get('success')
    return render_template('usuarios/usuarios.html', 
                          users=usuarios, 
                          success=success,
                          now=datetime.now())

@bp.route('/registrar_usuario', methods=['POST'])
def registrar_usuario():
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
        return render_template('usuarios/usuarios.html', 
                             users=Usuario.query.all(),
                             error="¡Usuario con teléfono " + telefono + " ya existe en el sistema!")
    
    # Convertir fechas de string a objetos date
    fecha_pago = datetime.strptime(fecha_pago_str, '%Y-%m-%d').date() if fecha_pago_str else datetime.now().date()
    fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date() if fecha_vencimiento_str else None
    
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
        fecha_pago=datetime.now()  # La fecha de registro del pago es ahora
    )
    db.session.add(pago)
    
    db.session.commit()
    
    return redirect(url_for('main.usuarios.index', success="Usuario registrado correctamente"))

@bp.route('/ver_usuario/<int:usuario_id>')
def ver_usuario(usuario_id):
    try:
        print(f"Accediendo a ver_usuario con ID: {usuario_id}")  # Log para depuración
        usuario = Usuario.query.get_or_404(usuario_id)
        print(f"Usuario encontrado: {usuario.nombre}")  # Verificar que se encontró el usuario
        
        # Recuperar historial de asistencias
        asistencias = Asistencia.query.filter_by(usuario_id=usuario_id).order_by(Asistencia.fecha.desc()).all()
        print(f"Asistencias encontradas: {len(asistencias)}")  # Verificar asistencias
        
        # Recuperar historial de pagos
        pagos = PagoMensualidad.query.filter_by(usuario_id=usuario_id).order_by(PagoMensualidad.fecha_pago.desc()).limit(5).all()
        print(f"Pagos encontrados: {len(pagos)}")  # Verificar pagos
        
        # Recuperar última medida
        ultima_medida = MedidasCorporales.query.filter_by(usuario_id=usuario_id).order_by(MedidasCorporales.fecha.desc()).first()
        
        # Intentar obtener objetivos activos, con manejo de error para columna faltante
        try:
            objetivos_activos = ObjetivoPersonal.query.filter_by(usuario_id=usuario_id, completado=False).order_by(ObjetivoPersonal.fecha_creacion.desc()).all()
        except Exception as e:
            print(f"Error al recuperar objetivos: {str(e)}")
            # Si falla, asumir que no hay objetivos activos
            objetivos_activos = []
        
        print("Renderizando plantilla ver_usuario.html")  # Verificar que se llega a la renderización
        return render_template('usuarios/ver_usuario.html', 
                            usuario=usuario, 
                            asistencias=asistencias, 
                            pagos=pagos,
                            ultima_medida=ultima_medida,
                            objetivos_activos=objetivos_activos,
                            today=datetime.now())
    except Exception as e:
        print(f"Error en ver_usuario: {str(e)}")  # Log para depuración
        import traceback
        traceback.print_exc()  # Imprimir stack trace completo
        flash(f'Error al mostrar usuario: {str(e)}', 'danger')
        return redirect(url_for('main.usuarios.index'))

@bp.route('/asistencia')
def asistencia():
    try:
        # Obtener todos los usuarios
        usuarios = Usuario.query.all()
        
        # Obtener todas las asistencias con información de usuario
        asistencias = db.session.query(Asistencia, Usuario).\
            join(Usuario, Asistencia.usuario_id == Usuario.id).\
            order_by(Asistencia.fecha.desc()).all()
        
        # Convertir a formato adecuado para la plantilla
        asistencias_con_usuario = []
        for asistencia, usuario in asistencias:
            asistencia.usuario = usuario
            asistencias_con_usuario.append(asistencia)
        
        # Obtener estadísticas de asistencia
        hoy = datetime.now().date()
        asistencias_hoy = db.session.query(func.count(Asistencia.id)).\
            filter(func.date(Asistencia.fecha) == hoy).scalar() or 0
            
        mes_actual = hoy.replace(day=1)
        asistencias_mes = db.session.query(func.count(Asistencia.id)).\
            filter(func.date(Asistencia.fecha) >= mes_actual).scalar() or 0
        
        return render_template('asistencia/asistencia.html', 
                              usuarios=usuarios, 
                              asistencias=asistencias_con_usuario,
                              asistencias_hoy=asistencias_hoy,
                              asistencias_mes=asistencias_mes,
                              fecha_hoy=hoy)
    except Exception as e:
        flash(f'Error al cargar asistencias: {str(e)}', 'danger')
        return render_template('asistencia/asistencia.html', 
                              usuarios=[], 
                              asistencias=[])

@bp.route('/marcar_asistencia/<int:usuario_id>')
def marcar_asistencia(usuario_id):
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        
        # Verificar si ya existe una asistencia para este usuario en el día de hoy
        hoy = datetime.now().date()
        asistencia_hoy = Asistencia.query.filter(
            Asistencia.usuario_id == usuario_id,
            func.date(Asistencia.fecha) == hoy
        ).first()
        
        if asistencia_hoy:
            flash(f'El usuario {usuario.nombre} ya tiene registrada su asistencia hoy.', 'info')
            return redirect(url_for('main.usuarios.asistencia'))
        
        # Verificar si el plan ha vencido
        if usuario.fecha_vencimiento_plan and usuario.fecha_vencimiento_plan < hoy:
            if usuario.plan == 'Diario':
                # Para plan diario, se debe pagar al entrar
                return redirect(url_for('main.usuarios.renovar_plan', usuario_id=usuario_id))
            else:
                # Para otros planes, mostrar advertencia
                flash(f'¡Atención! El plan {usuario.plan} del usuario {usuario.nombre} ha vencido el {usuario.fecha_vencimiento_plan.strftime("%d/%m/%Y")}', 'warning')
        
        # Si todo está bien, registrar asistencia
        asistencia = Asistencia(usuario_id=usuario_id)
        db.session.add(asistencia)
        db.session.commit()
        
        flash(f'Asistencia registrada para {usuario.nombre}', 'success')
        return redirect(url_for('main.usuarios.asistencia'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar asistencia: {str(e)}', 'danger')
        return redirect(url_for('main.usuarios.asistencia'))

@bp.route('/renovar_plan/<int:usuario_id>', methods=['GET', 'POST'])
def renovar_plan(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if request.method == 'POST':
        metodo_pago = request.form['metodo_pago']
        
        # Renovar el plan según su tipo
        if usuario.plan == 'Diario':
            usuario.fecha_vencimiento_plan = datetime.now().date() + timedelta(days=1)
        elif usuario.plan == 'Quincenal':
            usuario.fecha_vencimiento_plan = datetime.now().date() + timedelta(days=15)
        else:  # Mensual, Dirigido o Personalizado
            usuario.fecha_vencimiento_plan = datetime.now().date() + timedelta(days=30)
        
        # Registrar el pago
        pago = PagoMensualidad(
            usuario_id=usuario_id,
            monto=usuario.precio_plan,
            metodo_pago=metodo_pago,
            plan=usuario.plan,
            fecha_inicio=datetime.now().date(),
            fecha_fin=usuario.fecha_vencimiento_plan
        )
        db.session.add(pago)
        db.session.commit()
        
        # Registrar asistencia automáticamente para planes diarios
        if usuario.plan == 'Diario':
            asistencia = Asistencia(usuario_id=usuario_id)
            db.session.add(asistencia)
            db.session.commit()
            return redirect(url_for('main.usuarios.asistencia'))
        
        return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
    
    return render_template('pagos/renovar_plan.html', usuario=usuario, now=datetime.now())

@bp.route('/editar_usuario/<int:usuario_id>', methods=['GET', 'POST'])
def editar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if request.method == 'POST':
        # Verificar si el teléfono ya existe y no es el de este usuario
        if request.form['telefono'] != usuario.telefono:
            usuario_existente = Usuario.query.filter_by(telefono=request.form['telefono']).first()
            if usuario_existente:
                return render_template('usuarios/editar_usuario.html', 
                                      usuario=usuario, 
                                      today=datetime.now(),
                                      error="El teléfono ya está registrado para otro usuario")
        
        # Guardar el plan anterior para comprobar si cambió
        plan_anterior = usuario.plan
        
        # Actualizar datos básicos
        usuario.nombre = request.form['nombre']
        usuario.telefono = request.form['telefono']
        usuario.plan = request.form['plan']
        usuario.metodo_pago = request.form['metodo_pago']
        
        # Verificar si se está renovando el plan
        renovar_plan = 'renovar_plan' in request.form
        
        if renovar_plan:
            # Procesar fecha de pago
            fecha_pago_str = request.form.get('fecha_pago')
            fecha_pago = datetime.strptime(fecha_pago_str, '%Y-%m-%d').date() if fecha_pago_str else datetime.now().date()
            
            # Procesar fecha de vencimiento
            fecha_vencimiento_str = request.form.get('fecha_vencimiento_plan')
            fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date() if fecha_vencimiento_str else None
            
            # Actualizar fecha de vencimiento
            usuario.fecha_vencimiento_plan = fecha_vencimiento
            
            # Actualizar el precio del plan
            if usuario.plan == 'Diario':
                usuario.precio_plan = Usuario.PRECIO_DIARIO
            elif usuario.plan == 'Quincenal':
                usuario.precio_plan = Usuario.PRECIO_QUINCENAL
            elif usuario.plan == 'Mensual':
                usuario.precio_plan = Usuario.PRECIO_MENSUAL
            elif usuario.plan == 'Estudiantil':
                usuario.precio_plan = Usuario.PRECIO_ESTUDIANTIL
            elif usuario.plan == 'Dirigido':
                usuario.precio_plan = Usuario.PRECIO_DIRIGIDO
            elif usuario.plan == 'Personalizado':
                usuario.precio_plan = Usuario.PRECIO_PERSONALIZADO
            
            # Registrar un nuevo pago
            pago = PagoMensualidad(
                usuario=usuario,
                monto=usuario.precio_plan,
                metodo_pago=usuario.metodo_pago,
                plan=usuario.plan,
                fecha_inicio=fecha_pago,
                fecha_fin=fecha_vencimiento,
                fecha_pago=datetime.now()
            )
            db.session.add(pago)
        else:
            # Si no se renueva el plan, solo actualizar fecha de vencimiento si se proporciona
            fecha_vencimiento_str = request.form.get('fecha_vencimiento_plan')
            if fecha_vencimiento_str:
                usuario.fecha_vencimiento_plan = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
        
        db.session.commit()
        return redirect(url_for('main.usuarios.index', success="Usuario actualizado correctamente"))
    
    return render_template('usuarios/editar_usuario.html', usuario=usuario, today=datetime.now())

@bp.route('/medidas/<int:usuario_id>', methods=['GET', 'POST'])
def medidas(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Verificar si el usuario tiene un plan dirigido o personalizado
    if usuario.plan not in ['Dirigido', 'Personalizado']:
        flash('Solo los usuarios con plan Dirigido o Personalizado pueden acceder a esta función', 'warning')
        return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
    
    if request.method == 'POST':
        # Registrar nuevas medidas
        medida = MedidasCorporales(
            usuario_id=usuario_id,
            peso=request.form.get('peso', type=float),
            altura=request.form.get('altura', type=float),
            pecho=request.form.get('pecho', type=float),
            cintura=request.form.get('cintura', type=float),
            cadera=request.form.get('cadera', type=float),
            brazo_izquierdo=request.form.get('brazo_izquierdo', type=float),
            brazo_derecho=request.form.get('brazo_derecho', type=float),
            pierna_izquierda=request.form.get('pierna_izquierda', type=float),
            pierna_derecha=request.form.get('pierna_derecha', type=float),
            notas=request.form.get('notas')
        )
        
        # Calcular IMC si hay peso y altura
        if medida.peso and medida.altura:
            altura_metros = medida.altura / 100  # convertir cm a metros
            medida.imc = medida.peso / (altura_metros * altura_metros)
        
        db.session.add(medida)
        db.session.commit()
        
        flash('Medidas registradas correctamente', 'success')
        return redirect(url_for('main.usuarios.medidas', usuario_id=usuario_id))
    
    # Obtener historial de medidas
    historial_medidas = MedidasCorporales.query.filter_by(usuario_id=usuario_id).order_by(MedidasCorporales.fecha.desc()).all()
    
    return render_template('usuarios/medidas.html', 
                          usuario=usuario, 
                          historial=historial_medidas,
                          ultima_medida=historial_medidas[0] if historial_medidas else None)

@bp.route('/objetivos/<int:usuario_id>', methods=['GET', 'POST'])
def objetivos(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Verificar si el usuario tiene un plan dirigido o personalizado
    if usuario.plan not in ['Dirigido', 'Personalizado']:
        flash('Solo los usuarios con plan Dirigido o Personalizado pueden acceder a esta función', 'warning')
        return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
    
    if request.method == 'POST':
        # Registrar nuevo objetivo
        objetivo = ObjetivoPersonal(
            usuario_id=usuario_id,
            descripcion=request.form.get('descripcion'),
            fecha_objetivo=datetime.strptime(request.form.get('fecha_objetivo'), '%Y-%m-%d').date() if request.form.get('fecha_objetivo') else None,
            progreso=request.form.get('progreso', type=int, default=0)
        )
        
        db.session.add(objetivo)
        db.session.commit()
        
        flash('Objetivo registrado correctamente', 'success')
        return redirect(url_for('main.usuarios.objetivos', usuario_id=usuario_id))
    
    # Obtener objetivos actuales
    try:
        objetivos_activos = ObjetivoPersonal.query.filter_by(usuario_id=usuario_id, completado=False).order_by(ObjetivoPersonal.fecha_creacion.desc()).all()
        objetivos_completados = ObjetivoPersonal.query.filter_by(usuario_id=usuario_id, completado=True).order_by(ObjetivoPersonal.fecha_creacion.desc()).all()
    except Exception as e:
        print(f"Error al recuperar objetivos: {str(e)}")
        # Si hay un error, suponer listas vacías
        objetivos_activos = []
        objetivos_completados = []
        flash('Error al recuperar objetivos. Por favor actualice la base de datos.', 'warning')
    
    return render_template('usuarios/objetivos.html', 
                          usuario=usuario, 
                          objetivos_activos=objetivos_activos,
                          objetivos_completados=objetivos_completados)

@bp.route('/actualizar_objetivo/<int:objetivo_id>', methods=['POST'])
def actualizar_objetivo(objetivo_id):
    try:
        objetivo = ObjetivoPersonal.query.get_or_404(objetivo_id)
        
        progreso = request.form.get('progreso', type=int)
        completado = request.form.get('completado') == 'on'
        
        objetivo.progreso = progreso
        objetivo.completado = completado
        
        # Si el objetivo se marca como completado, registrar la fecha actual
        if completado and hasattr(objetivo, 'fecha_completado'):
            objetivo.fecha_completado = datetime.now().date()
        
        db.session.commit()
        
        flash('Objetivo actualizado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar objetivo: {str(e)}', 'danger')
        print(f"Error en actualizar_objetivo: {str(e)}")
    
    return redirect(url_for('main.usuarios.objetivos', usuario_id=objetivo.usuario_id)) 