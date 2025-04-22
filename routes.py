from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from models import db, Usuario, Asistencia, Producto, VentaProducto, PagoMensualidad
from datetime import datetime, timedelta
from sqlalchemy import func, extract, desc
import json
import random

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/usuarios')
def usuarios():
    usuarios = Usuario.query.all()
    success = request.args.get('success')
    return render_template('usuarios.html', users=usuarios, success=success)

@main.route('/registrar_usuario', methods=['POST'])
def registrar_usuario():
    nombre = request.form['nombre']
    cedula = request.form['cedula']
    plan = request.form['plan']
    metodo_pago = request.form['metodo_pago']
    
    # Verificar si ya existe un usuario con la misma cédula
    usuario_existente = Usuario.query.filter_by(cedula=cedula).first()
    
    if usuario_existente:
        # Usuario ya existe, mostrar mensaje
        return render_template('usuarios.html', 
                             users=Usuario.query.all(),
                             error="¡Usuario con cédula " + cedula + " ya existe en el sistema!")
    
    # Calcular fecha de vencimiento y precio según el plan
    fecha_vencimiento = None
    precio_plan = None
    
    if plan == 'Diario':
        precio_plan = Usuario.PRECIO_DIARIO
        fecha_vencimiento = datetime.now().date() + timedelta(days=1)
    elif plan == 'Quincenal':
        precio_plan = Usuario.PRECIO_QUINCENAL
        fecha_vencimiento = datetime.now().date() + timedelta(days=15)
    elif plan == 'Mensual':
        precio_plan = Usuario.PRECIO_MENSUAL
        fecha_vencimiento = datetime.now().date() + timedelta(days=30)
    elif plan == 'Dirigido':
        precio_plan = Usuario.PRECIO_DIRIGIDO
        fecha_vencimiento = datetime.now().date() + timedelta(days=30)
    elif plan == 'Personalizado':
        precio_plan = Usuario.PRECIO_PERSONALIZADO
        fecha_vencimiento = datetime.now().date() + timedelta(days=30)
    
    # Si no existe, crear nuevo usuario
    usuario = Usuario(
        nombre=nombre, 
        cedula=cedula, 
        plan=plan, 
        metodo_pago=metodo_pago,
        fecha_vencimiento_plan=fecha_vencimiento,
        precio_plan=precio_plan
    )
    db.session.add(usuario)
    
    # Registrar el pago de mensualidad
    pago = PagoMensualidad(
        usuario=usuario,
        monto=precio_plan,
        metodo_pago=metodo_pago,
        plan=plan,
        fecha_inicio=datetime.now().date(),
        fecha_fin=fecha_vencimiento
    )
    db.session.add(pago)
    
    db.session.commit()
    
    return redirect(url_for('main.usuarios', success="Usuario registrado correctamente"))

@main.route('/ver_usuario/<int:usuario_id>')
def ver_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    asistencias = Asistencia.query.filter_by(usuario_id=usuario_id).order_by(Asistencia.fecha.desc()).all()
    
    # Recuperar historial de pagos
    pagos = PagoMensualidad.query.filter_by(usuario_id=usuario_id).order_by(PagoMensualidad.fecha_pago.desc()).limit(5).all()
    
    return render_template('ver_usuario.html', 
                           usuario=usuario, 
                           asistencias=asistencias, 
                           pagos=pagos,
                           today=datetime.now())

@main.route('/asistencia')
def asistencia():
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
    
    return render_template('asistencia.html', usuarios=usuarios, asistencias=asistencias_con_usuario)

@main.route('/marcar_asistencia/<int:usuario_id>')
def marcar_asistencia(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Verificar si el plan ha vencido
    if usuario.fecha_vencimiento_plan and usuario.fecha_vencimiento_plan < datetime.now().date():
        if usuario.plan == 'Diario':
            # Para plan diario, se debe pagar al entrar
            return redirect(url_for('main.renovar_plan', usuario_id=usuario_id))
        else:
            # Para otros planes, mostrar advertencia
            flash(f'¡Atención! El plan {usuario.plan} del usuario {usuario.nombre} ha vencido el {usuario.fecha_vencimiento_plan.strftime("%d/%m/%Y")}', 'warning')
    
    # Si todo está bien, registrar asistencia
    asistencia = Asistencia(usuario_id=usuario_id)
    db.session.add(asistencia)
    db.session.commit()
    return redirect(url_for('main.asistencia'))

@main.route('/renovar_plan/<int:usuario_id>', methods=['GET', 'POST'])
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
            usuario=usuario,
            monto=usuario.precio_plan,
            metodo_pago=metodo_pago,
            plan=usuario.plan,
            fecha_inicio=datetime.now().date(),
            fecha_fin=usuario.fecha_vencimiento_plan
        )
        db.session.add(pago)
        db.session.commit()
        
        # Registrar asistencia
        asistencia = Asistencia(usuario_id=usuario_id)
        db.session.add(asistencia)
        db.session.commit()
        
        flash(f'Plan {usuario.plan} renovado correctamente hasta el {usuario.fecha_vencimiento_plan.strftime("%d/%m/%Y")}', 'success')
        return redirect(url_for('main.asistencia'))
    
    return render_template('renovar_plan.html', usuario=usuario, now=datetime.now())

@main.route('/pagos')
def pagos():
    pagos = PagoMensualidad.query.order_by(PagoMensualidad.fecha_pago.desc()).all()
    return render_template('pagos.html', pagos=pagos, now=datetime.now())

@main.route('/productos')
def productos():
    productos = Producto.query.all()
    success = request.args.get('success')
    error = request.args.get('error')
    return render_template('productos.html', productos=productos, success=success, error=error)

@main.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = float(request.form['precio'])
    stock = int(request.form['stock'])
    categoria = request.form['categoria']
    
    # Verificar si ya existe un producto con el mismo nombre
    producto_existente = Producto.query.filter_by(nombre=nombre).first()
    
    if producto_existente:
        return redirect(url_for('main.productos', error=f"Ya existe un producto con el nombre {nombre}"))
    
    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock,
        categoria=categoria
    )
    
    db.session.add(nuevo_producto)
    db.session.commit()
    
    return redirect(url_for('main.productos', success="Producto agregado correctamente"))

@main.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    
    if request.method == 'POST':
        # Verificar si el nombre ya existe y no es el de este producto
        if request.form['nombre'] != producto.nombre:
            producto_existente = Producto.query.filter_by(nombre=request.form['nombre']).first()
            if producto_existente:
                return render_template('editar_producto.html', producto=producto, 
                                     error="Ya existe un producto con este nombre")
        
        # Actualizar datos
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.precio = float(request.form['precio'])
        producto.stock = int(request.form['stock'])
        producto.categoria = request.form['categoria']
        
        db.session.commit()
        return redirect(url_for('main.productos', success="Producto actualizado correctamente"))
    
    return render_template('editar_producto.html', producto=producto)

@main.route('/eliminar_producto/<int:producto_id>')
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    
    # Verificar si hay ventas asociadas
    ventas = VentaProducto.query.filter_by(producto_id=producto_id).first()
    
    if ventas:
        return redirect(url_for('main.productos', 
                              error="No se puede eliminar el producto porque tiene ventas asociadas"))
    
    db.session.delete(producto)
    db.session.commit()
    
    return redirect(url_for('main.productos', success="Producto eliminado correctamente"))

@main.route('/registrar_venta', methods=['GET', 'POST'])
def registrar_venta():
    if request.method == 'POST':
        producto_id = int(request.form['producto_id'])
        cantidad = int(request.form['cantidad'])
        usuario_id = request.form.get('usuario_id')  # Puede ser None si es venta sin usuario
        metodo_pago = request.form['metodo_pago']
        
        producto = Producto.query.get_or_404(producto_id)
        
        # Verificar stock
        if producto.stock < cantidad:
            return render_template('registrar_venta.html', 
                                productos=Producto.query.all(),
                                usuarios=Usuario.query.all(),
                                error=f"Stock insuficiente. Solo hay {producto.stock} unidades disponibles.")
        
        # Calcular total
        precio_unitario = producto.precio
        total = precio_unitario * cantidad
        
        # Registrar venta
        venta = VentaProducto(
            producto_id=producto_id,
            usuario_id=usuario_id if usuario_id else None,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            total=total,
            metodo_pago=metodo_pago
        )
        
        # Actualizar stock
        producto.stock -= cantidad
        
        db.session.add(venta)
        db.session.commit()
        
        return redirect(url_for('main.ventas', success="Venta registrada correctamente"))
    
    productos = Producto.query.filter(Producto.stock > 0).all()
    usuarios = Usuario.query.all()
    return render_template('registrar_venta.html', productos=productos, usuarios=usuarios)

@main.route('/ventas')
def ventas():
    # Obtener todas las ventas con información de producto y usuario
    ventas = db.session.query(VentaProducto, Producto, Usuario).\
        join(Producto, VentaProducto.producto_id == Producto.id).\
        outerjoin(Usuario, VentaProducto.usuario_id == Usuario.id).\
        order_by(VentaProducto.fecha.desc()).all()
    
    success = request.args.get('success')
    
    return render_template('ventas.html', ventas=ventas, success=success)

@main.route('/finanzas')
def finanzas():
    # Obtener estadísticas de usuarios
    usuarios_activos = Usuario.query.count()
    
    # Fechas clave para los cálculos
    hoy = datetime.now().date()
    inicio_dia = datetime.combine(hoy, datetime.min.time())
    inicio_semana = inicio_dia - timedelta(days=hoy.weekday())
    inicio_mes = datetime(hoy.year, hoy.month, 1)
    
    # Calcular asistencias del mes actual (datos reales)
    asistencias_mes = Asistencia.query.filter(Asistencia.fecha >= inicio_mes).count()
    
    # Cálculo de ingresos por membresías (datos reales)
    pagos_mes = db.session.query(func.sum(PagoMensualidad.monto)).\
        filter(PagoMensualidad.fecha_pago >= inicio_mes).scalar() or 0
    ingresos_mensual_membresias = float(pagos_mes)
    
    # Cálculo de ingresos por ventas de productos (datos reales)
    ventas_mes = db.session.query(func.sum(VentaProducto.total)).\
        filter(VentaProducto.fecha >= inicio_mes).scalar() or 0
    ingresos_mensual_productos = float(ventas_mes)
    
    # Ingresos totales mensuales
    ingresos_mensual_total = ingresos_mensual_membresias + ingresos_mensual_productos
    
    # Cálculo de ingresos diarios (hoy)
    pagos_dia = db.session.query(func.sum(PagoMensualidad.monto)).\
        filter(PagoMensualidad.fecha_pago >= inicio_dia).scalar() or 0
    ventas_dia = db.session.query(func.sum(VentaProducto.total)).\
        filter(VentaProducto.fecha >= inicio_dia).scalar() or 0
    ingresos_diarios_total = float(pagos_dia) + float(ventas_dia)
    
    # Cálculo de ingresos semanales
    pagos_semana = db.session.query(func.sum(PagoMensualidad.monto)).\
        filter(PagoMensualidad.fecha_pago >= inicio_semana).scalar() or 0
    ventas_semana = db.session.query(func.sum(VentaProducto.total)).\
        filter(VentaProducto.fecha >= inicio_semana).scalar() or 0
    ingresos_semanales_total = float(pagos_semana) + float(ventas_semana)
    
    # Costos estimados (ejemplo: supongamos un 40% de margen bruto)
    costo_porcentaje = 0.60  # 60% del ingreso va a costos
    
    # Cálculo de márgenes de ganancia
    margen_diario = ingresos_diarios_total * (1 - costo_porcentaje)
    margen_semanal = ingresos_semanales_total * (1 - costo_porcentaje)
    margen_mensual = ingresos_mensual_total * (1 - costo_porcentaje)
    
    # Datos para el gráfico de ingresos mensuales (últimos 6 meses)
    meses = []
    datos_ingresos_membresias = []
    datos_ingresos_productos = []
    datos_margenes = []
    
    for i in range(5, -1, -1):
        # Calcular mes
        mes_actual = datetime.today().replace(day=1) - timedelta(days=i*30)
        mes_siguiente = (mes_actual.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        # Nombre del mes
        nombre_mes = mes_actual.strftime('%b')
        meses.append(nombre_mes)
        
        # Ingresos por membresías (datos reales)
        pagos_mes_i = db.session.query(func.sum(PagoMensualidad.monto)).\
            filter(PagoMensualidad.fecha_pago >= mes_actual).\
            filter(PagoMensualidad.fecha_pago < mes_siguiente).scalar() or 0
        ingresos_membresias = float(pagos_mes_i)
        datos_ingresos_membresias.append(ingresos_membresias)
        
        # Ingresos por productos
        ventas_mes_i = db.session.query(func.sum(VentaProducto.total)).\
            filter(VentaProducto.fecha >= mes_actual).\
            filter(VentaProducto.fecha < mes_siguiente).scalar() or 0
        ingresos_productos = float(ventas_mes_i)
        datos_ingresos_productos.append(ingresos_productos)
        
        # Cálculo del margen para el mes
        margen_mes = (ingresos_membresias + ingresos_productos) * (1 - costo_porcentaje)
        datos_margenes.append(margen_mes)
    
    # Datos para el gráfico de distribución de planes
    planes_count = db.session.query(
        Usuario.plan, func.count(Usuario.id)
    ).group_by(Usuario.plan).all()
    
    # Inicializar con ceros para todos los planes posibles
    planes_nombres = ['Diario', 'Quincenal', 'Mensual', 'Dirigido', 'Personalizado']
    datos_planes = [0] * len(planes_nombres)
    
    # Llenar con datos reales
    for plan, count in planes_count:
        if plan in planes_nombres:
            index = planes_nombres.index(plan)
            datos_planes[index] = count
    
    # Datos para productos más vendidos
    productos_vendidos = db.session.query(
        Producto.nombre,
        func.sum(VentaProducto.cantidad).label('cantidad_vendida'),
        func.sum(VentaProducto.total).label('total_vendido')
    ).join(VentaProducto).group_by(Producto.id).order_by(desc('cantidad_vendida')).limit(5).all()
    
    productos_nombres = [p[0] for p in productos_vendidos] if productos_vendidos else []
    productos_cantidades = [p[1] for p in productos_vendidos] if productos_vendidos else []
    productos_ingresos = [float(p[2]) for p in productos_vendidos] if productos_vendidos else []
    
    # Obtener los últimos pagos de membresías (reales, no simulados)
    pagos_membresias = PagoMensualidad.query.order_by(PagoMensualidad.fecha_pago.desc()).limit(10).all()
    
    # Obtener las últimas ventas de productos
    ultimas_ventas = db.session.query(VentaProducto, Producto, Usuario).\
        join(Producto).\
        outerjoin(Usuario).\
        order_by(VentaProducto.fecha.desc()).limit(10).all()
    
    # Convertir ventas a formato para mostrar
    pagos_productos = []
    for venta, producto, usuario in ultimas_ventas:
        pago = type('Pago', (), {
            'usuario': usuario,
            'monto': venta.total,
            'fecha': venta.fecha,
            'tipo': 'Producto',
            'metodo_pago': venta.metodo_pago
        })
        pagos_productos.append(pago)
    
    # Convertir pagos de membresías a formato similar
    pagos_memb_formateados = []
    for pago in pagos_membresias:
        pago_obj = type('Pago', (), {
            'usuario': pago.usuario,
            'monto': pago.monto,
            'fecha': pago.fecha_pago,
            'tipo': 'Membresía',
            'metodo_pago': pago.metodo_pago
        })
        pagos_memb_formateados.append(pago_obj)
    
    # Combinar todos los pagos
    pagos = pagos_memb_formateados + pagos_productos
    pagos.sort(key=lambda x: x.fecha, reverse=True)
    
    return render_template('finanzas.html',
                          usuarios_activos=usuarios_activos,
                          asistencias_mes=asistencias_mes,
                          ingresos_mensual_membresias=ingresos_mensual_membresias,
                          ingresos_mensual_productos=ingresos_mensual_productos,
                          ingresos_mensual_total=ingresos_mensual_total,
                          ingresos_diarios_total=ingresos_diarios_total,
                          ingresos_semanales_total=ingresos_semanales_total,
                          margen_diario=margen_diario,
                          margen_semanal=margen_semanal,
                          margen_mensual=margen_mensual,
                          meses=json.dumps(meses),
                          datos_ingresos_membresias=json.dumps(datos_ingresos_membresias),
                          datos_ingresos_productos=json.dumps(datos_ingresos_productos),
                          datos_planes=json.dumps(datos_planes),
                          planes_nombres=json.dumps(planes_nombres),
                          productos_nombres=json.dumps(productos_nombres),
                          productos_cantidades=json.dumps(productos_cantidades),
                          productos_ingresos=json.dumps(productos_ingresos),
                          datos_margenes=json.dumps(datos_margenes),
                          pagos=pagos)

@main.route('/editar_usuario/<int:usuario_id>', methods=['GET', 'POST'])
def editar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if request.method == 'POST':
        # Verificar si la cédula ya existe y no es la de este usuario
        if request.form['cedula'] != usuario.cedula:
            usuario_existente = Usuario.query.filter_by(cedula=request.form['cedula']).first()
            if usuario_existente:
                return render_template('editar_usuario.html', usuario=usuario, 
                                     error="La cédula ya está registrada para otro usuario")
        
        # Guardar el plan anterior para comprobar si cambió
        plan_anterior = usuario.plan
        
        # Actualizar datos
        usuario.nombre = request.form['nombre']
        usuario.cedula = request.form['cedula']
        usuario.plan = request.form['plan']
        usuario.metodo_pago = request.form['metodo_pago']
        
        # Procesar fecha de vencimiento del plan
        fecha_vencimiento_str = request.form.get('fecha_vencimiento_plan')
        if fecha_vencimiento_str:
            usuario.fecha_vencimiento_plan = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
        else:
            # Si el plan es diario y no se especificó fecha, establecer vencimiento a mañana
            if usuario.plan == 'Diario':
                usuario.fecha_vencimiento_plan = datetime.now().date() + timedelta(days=1)
            # Para otros planes sin fecha específica, establecer según el plan
            elif plan_anterior != usuario.plan:  # Si cambió el plan
                if usuario.plan == 'Quincenal':
                    usuario.fecha_vencimiento_plan = datetime.now().date() + timedelta(days=15)
                else:  # Mensual, Dirigido o Personalizado
                    usuario.fecha_vencimiento_plan = datetime.now().date() + timedelta(days=30)
        
        # Actualizar el precio del plan
        if usuario.plan == 'Diario':
            usuario.precio_plan = Usuario.PRECIO_DIARIO
        elif usuario.plan == 'Quincenal':
            usuario.precio_plan = Usuario.PRECIO_QUINCENAL
        elif usuario.plan == 'Mensual':
            usuario.precio_plan = Usuario.PRECIO_MENSUAL
        elif usuario.plan == 'Dirigido':
            usuario.precio_plan = Usuario.PRECIO_DIRIGIDO
        elif usuario.plan == 'Personalizado':
            usuario.precio_plan = Usuario.PRECIO_PERSONALIZADO
        
        # Si cambió el plan, registrar un nuevo pago
        if plan_anterior != usuario.plan:
            pago = PagoMensualidad(
                usuario=usuario,
                monto=usuario.precio_plan,
                metodo_pago=usuario.metodo_pago,
                plan=usuario.plan,
                fecha_inicio=datetime.now().date(),
                fecha_fin=usuario.fecha_vencimiento_plan
            )
            db.session.add(pago)
        
        db.session.commit()
        return redirect(url_for('main.usuarios', success="Usuario actualizado correctamente"))
    
    return render_template('editar_usuario.html', usuario=usuario)
