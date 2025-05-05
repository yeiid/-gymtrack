from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Usuario, Asistencia, MedidasCorporales, ObjetivoPersonal, PagoMensualidad, VentaProducto, Admin
from models import datetime_colombia, date_colombia  # Importar las funciones de zona horaria
from datetime import datetime, timedelta, date
from sqlalchemy import func
from routes.auth.routes import admin_required
import calendar

# Crear blueprint para usuarios
bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

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
            except Exception:
                objetivos_activos = []
        
        # Obtener historial de pagos con manejo de errores
        try:
            pagos = PagoMensualidad.query.filter_by(usuario_id=usuario_id).order_by(PagoMensualidad.fecha_pago.desc()).all()
        except Exception as e:
            print(f"Error al obtener pagos: {str(e)}")
            pagos = []
        
        return render_template('usuarios/ver_usuario.html', 
                              usuario=usuario, 
                              asistencias=asistencias,
                              ultima_medida=ultima_medida,
                              objetivos_activos=objetivos_activos,
                              pagos=pagos,
                              dias_restantes=dias_restantes,
                              estado_plan=estado_plan,
                              today=datetime_colombia())
    except Exception as e:
        print(f"Error general en vista de usuario: {str(e)}")
        flash(f"Error al mostrar información del usuario: {str(e)}", "danger")
        return redirect(url_for('main.usuarios.index'))

@bp.route('/asistencia')
def asistencia():
    try:
        # Límite de asistencias recientes a mostrar (para reducir la carga)
        limite_asistencias = 100
        
        # Obtener usuarios con plan activo o próximo a vencer para optimizar la consulta
        hoy = date_colombia()
        
        # Consulta optimizada de usuarios (solo los necesarios en vez de todos)
        usuarios = Usuario.query.all()
        
        # Optimizar agregando información de días restantes con procesamiento más eficiente
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
        
        # Optimizar: Obtener solo las asistencias recientes con JOIN más eficiente
        # Evitar el producto cartesiano usando una sola consulta directa
        asistencias = db.session.query(Asistencia, Usuario).\
            join(Usuario, Asistencia.usuario_id == Usuario.id).\
            order_by(Asistencia.fecha.desc()).\
            limit(limite_asistencias).all()
        
        # Optimizar la transformación del resultado
        asistencias_con_usuario = []
        for asistencia, usuario in asistencias:
            asistencia.usuario = usuario
            asistencias_con_usuario.append(asistencia)
        
        # Optimizar: Estadísticas de asistencia con consultas más eficientes
        inicio_dia = datetime.combine(hoy, datetime.min.time())
        fin_dia = datetime.combine(hoy, datetime.max.time())
        
        # Consultas optimizadas con índices apropiados
        asistencias_hoy = db.session.query(func.count(Asistencia.id)).\
            filter(Asistencia.fecha >= inicio_dia, 
                   Asistencia.fecha <= fin_dia).scalar() or 0
            
        # Calcular inicio del mes de manera optimizada
        mes_actual = hoy.replace(day=1)
        inicio_mes = datetime.combine(mes_actual, datetime.min.time())
        
        # Optimizar consulta mensual
        asistencias_mes = db.session.query(func.count(Asistencia.id)).\
            filter(Asistencia.fecha >= inicio_mes).scalar() or 0
        
        # Optimizar: Calcular vencimientos próximos filtrando primero la lista en memoria
        proximos_vencimientos = []
        for info_usuario in [u for u in usuarios_con_info if u['estado'] == 'proximo']:
            proximos_vencimientos.append({
                'nombre': info_usuario['usuario'].nombre,
                'plan': info_usuario['usuario'].plan,
                'dias': info_usuario['dias_restantes'],
                'fecha_vencimiento': info_usuario['usuario'].fecha_vencimiento_plan.strftime('%d/%m/%Y')
            })
        
        return render_template('asistencia/asistencia.html', 
                              usuarios=usuarios_con_info,
                              asistencias=asistencias_con_usuario,
                              asistencias_hoy=asistencias_hoy,
                              asistencias_mes=asistencias_mes,
                              fecha_hoy=hoy,
                              proximos_vencimientos=proximos_vencimientos,
                              limite_asistencias=limite_asistencias)
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
        # Usamos date_colombia para mantener consistencia con la zona horaria configurada
        hoy = date_colombia()
        
        # Obtener el inicio y fin del día actual para un filtrado más preciso
        inicio_dia = datetime.combine(hoy, datetime.min.time())
        fin_dia = datetime.combine(hoy, datetime.max.time())
        
        # Verificar asistencias entre inicio y fin del día
        asistencia_hoy = Asistencia.query.filter(
            Asistencia.usuario_id == usuario_id,
            Asistencia.fecha >= inicio_dia,
            Asistencia.fecha <= fin_dia
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
        
        # Obtener la fecha de inicio (hoy por defecto)
        fecha_inicio = date_colombia()
        
        # Renovar el plan según su tipo usando la nueva función
        usuario.fecha_vencimiento_plan = calcular_fecha_vencimiento(fecha_inicio, usuario.plan)
        
        # Registrar el pago
        pago = PagoMensualidad(
            usuario_id=usuario_id,
            monto=usuario.precio_plan,
            metodo_pago=metodo_pago,
            plan=usuario.plan,
            fecha_inicio=fecha_inicio,
            fecha_fin=usuario.fecha_vencimiento_plan
        )
        db.session.add(pago)
        db.session.commit()
        
        # Registrar asistencia automáticamente para planes diarios
        if usuario.plan == 'Diario':
            # Verificar si ya existe una asistencia para este usuario en el día de hoy
            hoy = date_colombia()
            inicio_dia = datetime.combine(hoy, datetime.min.time())
            fin_dia = datetime.combine(hoy, datetime.max.time())
            
            asistencia_hoy = Asistencia.query.filter(
                Asistencia.usuario_id == usuario_id,
                Asistencia.fecha >= inicio_dia,
                Asistencia.fecha <= fin_dia
            ).first()
            
            # Solo registramos si no hay asistencia previa hoy
            if not asistencia_hoy:
                asistencia = Asistencia(usuario_id=usuario_id)
                db.session.add(asistencia)
                db.session.commit()
            
            return redirect(url_for('main.usuarios.asistencia'))
        
        return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
    
    return render_template('pagos/renovar_plan.html', usuario=usuario, now=datetime_colombia())

@bp.route('/editar_usuario/<int:usuario_id>', methods=['GET', 'POST'])
def editar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if request.method == 'POST':
        # Verificar si el teléfono ya existe para otro usuario
        telefono = request.form['telefono']
        usuario_existente = Usuario.query.filter(Usuario.telefono == telefono, Usuario.id != usuario_id).first()
        if usuario_existente:
            return render_template('usuarios/editar_usuario.html', 
                                  usuario=usuario, 
                                  today=datetime_colombia(),
                                  error="El teléfono ya está registrado para otro usuario")
        
        # Obtener datos del formulario
        usuario.nombre = request.form['nombre']
        usuario.telefono = telefono
        usuario.plan = request.form['plan']
        usuario.metodo_pago = request.form['metodo_pago']
        
        renovar_plan = 'renovar_plan' in request.form
        
        if renovar_plan:
            # Procesar fecha de pago
            fecha_pago_str = request.form.get('fecha_pago')
            fecha_pago = datetime.strptime(fecha_pago_str, '%Y-%m-%d').date() if fecha_pago_str else date_colombia()
            
            # Procesar fecha de vencimiento
            fecha_vencimiento_str = request.form.get('fecha_vencimiento_plan')
            if fecha_vencimiento_str:
                fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
            else:
                # Calcular automáticamente según el nuevo sistema
                fecha_vencimiento = calcular_fecha_vencimiento(fecha_pago, usuario.plan)
            
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
                fecha_pago=datetime_colombia()
            )
            db.session.add(pago)
        else:
            # Si no se renueva el plan, solo actualizar fecha de vencimiento si se proporciona
            fecha_vencimiento_str = request.form.get('fecha_vencimiento_plan')
            if fecha_vencimiento_str:
                usuario.fecha_vencimiento_plan = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
        
        db.session.commit()
        return redirect(url_for('main.usuarios.index', success="Usuario actualizado correctamente"))
    
    return render_template('usuarios/editar_usuario.html', usuario=usuario, today=datetime_colombia())

@bp.route('/medidas/<int:usuario_id>', methods=['GET', 'POST'])
def medidas(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Verificar si el usuario tiene un plan dirigido o personalizado
    if usuario.plan not in ['Dirigido', 'Personalizado']:
        flash('Solo los usuarios con plan Dirigido o Personalizado pueden acceder a esta función', 'warning')
        return redirect(url_for('main.usuarios.ver_usuario', usuario_id=usuario_id))
    
    if request.method == 'POST':
        try:
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
            
            print(f"Guardando nueva medida para usuario {usuario.nombre} (ID: {usuario_id})")
            
            # Asegurarnos de que la sesión está limpia antes de añadir
            db.session.rollback()
            
            # Añadir y guardar la medida
            db.session.add(medida)
            db.session.commit()
            
            # Verificar que se guardó correctamente
            medida_guardada = MedidasCorporales.query.get(medida.id)
            if medida_guardada:
                print(f"Medida guardada correctamente con ID: {medida.id}")
            else:
                print(f"ERROR: No se pudo verificar que la medida se guardó correctamente")
            
            flash('Medidas registradas correctamente', 'success')
            
            # Forzar al usuario a ver la página actualizada
            return redirect(url_for('main.usuarios.medidas', usuario_id=usuario_id, _fresh=True))
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error al guardar medidas: {str(e)}"
            print(error_msg)
            flash(error_msg, 'danger')
            return redirect(url_for('main.usuarios.medidas', usuario_id=usuario_id))
    
    # Obtener historial de medidas
    try:
        print(f"Recuperando historial de medidas para usuario {usuario.nombre} (ID: {usuario_id})")
        # Hacer una consulta directa a la base de datos para verificar
        consulta_sql = f"SELECT * FROM medidas_corporales WHERE usuario_id = {usuario_id} ORDER BY fecha DESC"
        resultados_sql = db.session.execute(consulta_sql).fetchall()
        print(f"Resultado SQL directo: {len(resultados_sql)} registros encontrados")
        
        # Ahora hacer la consulta con SQLAlchemy
        historial_medidas = MedidasCorporales.query.filter_by(usuario_id=usuario_id).order_by(MedidasCorporales.fecha.desc()).all()
        print(f"Medidas recuperadas con SQLAlchemy: {len(historial_medidas)}")
        
        if historial_medidas:
            for i, medida in enumerate(historial_medidas[:3]):  # Mostrar las 3 primeras medidas para depuración
                print(f"Medida {i+1}: ID={medida.id}, Fecha={medida.fecha}, Peso={medida.peso}")
        else:
            print("No se encontraron medidas para este usuario")
    except Exception as e:
        print(f"Error al recuperar historial de medidas: {str(e)}")
        historial_medidas = []
        flash(f"Error al recuperar historial de medidas: {str(e)}", 'warning')
    
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
        
        # Comentamos esta parte porque la columna fecha_completado no existe
        # Si el objetivo se marca como completado, registrar la fecha actual
        # if completado and hasattr(objetivo, 'fecha_completado'):
        #     objetivo.fecha_completado = datetime.now().date()
        
        db.session.commit()
        
        flash('Objetivo actualizado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar objetivo: {str(e)}', 'danger')
        print(f"Error en actualizar_objetivo: {str(e)}")
    
    return redirect(url_for('main.usuarios.objetivos', usuario_id=objetivo.usuario_id))

@bp.route('/eliminar_usuario/<int:usuario_id>', methods=['POST'])
@admin_required
def eliminar_usuario(usuario_id):
    try:
        # Verificar que el usuario sea administrador
        if 'admin_id' not in session:
            flash('Debe iniciar sesión como administrador para realizar esta acción', 'danger')
            return redirect(url_for('main.usuarios.index'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin or admin.rol != 'administrador':
            flash('Solo los administradores pueden eliminar usuarios', 'danger')
            return redirect(url_for('main.usuarios.index'))
        
        # Buscar usuario
        usuario = Usuario.query.get_or_404(usuario_id)
        
        # Recopilar información para el reporte
        nombre_usuario = usuario.nombre
        telefono_usuario = usuario.telefono
        
        # Ahora solo necesitamos eliminar el usuario y las relaciones se eliminarán en cascada
        # Las ventas se desasociarán automáticamente (SET NULL)
        try:
            # Eliminar el usuario (las eliminaciones en cascada ocurrirán automáticamente)
            db.session.delete(usuario)
            db.session.commit()
            
            # Registrar en el log de actividades
            fecha_eliminacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('eliminaciones_usuarios.log', 'a', encoding='utf-8') as f:
                f.write(f"{fecha_eliminacion},ELIMINACIÓN,USUARIO,{usuario_id},{nombre_usuario},{telefono_usuario},{admin.nombre}\n")
            
            flash(f'Usuario {nombre_usuario} eliminado correctamente', 'success')
            return redirect(url_for('main.usuarios.index'))
        except Exception as e:
            # Si hay un error durante el proceso de eliminación
            db.session.rollback()
            raise Exception(f"Error durante el proceso de eliminación: {str(e)}")
    
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        print(f"Error al eliminar usuario: {error_msg}")
        
        # Mensajes más específicos según el tipo de error
        if "foreign key constraint fails" in error_msg.lower():
            flash(f'Error al eliminar usuario: Existen registros dependientes que no se pueden eliminar. Es posible que necesite actualizar la base de datos.', 'danger')
        else:
            flash(f'Error al eliminar usuario: {error_msg}', 'danger')
        
        return redirect(url_for('main.usuarios.index')) 