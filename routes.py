from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import db, Usuario, Asistencia, Producto, VentaProducto
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
    
    # Si no existe, crear nuevo usuario
    usuario = Usuario(nombre=nombre, cedula=cedula, plan=plan, metodo_pago=metodo_pago)
    db.session.add(usuario)
    db.session.commit()
    
    return redirect(url_for('main.usuarios', success="Usuario registrado correctamente"))

@main.route('/ver_usuario/<int:usuario_id>')
def ver_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    asistencias = Asistencia.query.filter_by(usuario_id=usuario_id).order_by(Asistencia.fecha.desc()).all()
    return render_template('ver_usuario.html', usuario=usuario, asistencias=asistencias, today=datetime.now())

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
    asistencia = Asistencia(usuario_id=usuario_id)
    db.session.add(asistencia)
    db.session.commit()
    return redirect(url_for('main.asistencia'))

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
    
    # Calcular asistencias del mes actual
    inicio_mes = datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    asistencias_mes = Asistencia.query.filter(Asistencia.fecha >= inicio_mes).count()
    
    # Obtener ingresos por membresías (simulados)
    ingresos_mensual_membresias = usuarios_activos * 50000  # Asumiendo un promedio de 50000 COP por usuario
    
    # Obtener ingresos por ventas de productos
    ventas_mes = db.session.query(func.sum(VentaProducto.total)).\
        filter(VentaProducto.fecha >= inicio_mes).scalar() or 0
        
    ingresos_mensual_productos = float(ventas_mes)
    
    # Ingresos totales
    ingresos_mensual_total = ingresos_mensual_membresias + ingresos_mensual_productos
    
    # Datos para el gráfico de ingresos mensuales (últimos 6 meses)
    meses = []
    datos_ingresos_membresias = []
    datos_ingresos_productos = []
    
    for i in range(5, -1, -1):
        # Calcular mes
        mes_actual = datetime.today().replace(day=1) - timedelta(days=i*30)
        mes_siguiente = (mes_actual.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        # Nombre del mes
        nombre_mes = mes_actual.strftime('%b')
        meses.append(nombre_mes)
        
        # Ingresos por membresías (simulados)
        if i == 0:
            # Mes actual
            ingresos_membresias = ingresos_mensual_membresias
        else:
            # Meses anteriores (simulados)
            ingresos_membresias = random.randint(int(ingresos_mensual_membresias * 0.8), 
                                               int(ingresos_mensual_membresias * 1.2))
        
        datos_ingresos_membresias.append(ingresos_membresias)
        
        # Ingresos por productos
        ventas_mes_i = db.session.query(func.sum(VentaProducto.total)).\
            filter(VentaProducto.fecha >= mes_actual).\
            filter(VentaProducto.fecha < mes_siguiente).scalar() or 0
            
        if i == 0:
            # Mes actual
            ingresos_productos = ingresos_mensual_productos
        else:
            # Si no hay datos, simular
            if ventas_mes_i == 0:
                ingresos_productos = random.randint(200000, 500000)
            else:
                ingresos_productos = float(ventas_mes_i)
        
        datos_ingresos_productos.append(ingresos_productos)
    
    # Datos para el gráfico de distribución de planes
    planes_count = db.session.query(
        Usuario.plan, func.count(Usuario.id)
    ).group_by(Usuario.plan).all()
    
    datos_planes = [0, 0, 0]  # [Diario, Mensual, Personalizado]
    for plan, count in planes_count:
        if plan == 'Diario':
            datos_planes[0] = count
        elif plan == 'Mensual':
            datos_planes[1] = count
        elif plan == 'Personalizado':
            datos_planes[2] = count
    
    # Datos para productos más vendidos
    productos_vendidos = db.session.query(
        Producto.nombre,
        func.sum(VentaProducto.cantidad).label('cantidad_vendida'),
        func.sum(VentaProducto.total).label('total_vendido')
    ).join(VentaProducto).group_by(Producto.id).order_by(desc('cantidad_vendida')).limit(5).all()
    
    productos_nombres = [p[0] for p in productos_vendidos] if productos_vendidos else []
    productos_cantidades = [p[1] for p in productos_vendidos] if productos_vendidos else []
    productos_ingresos = [float(p[2]) for p in productos_vendidos] if productos_vendidos else []
    
    # Últimas ventas para mostrar en finanzas
    ultimas_ventas = db.session.query(VentaProducto, Producto, Usuario).\
        join(Producto).\
        outerjoin(Usuario).\
        order_by(VentaProducto.fecha.desc()).limit(10).all()
    
    # Simular pagos de membresías
    pagos_membresias = []
    for i in range(5):
        usuario = Usuario.query.get(random.randint(1, max(1, usuarios_activos)))
        if usuario:
            # Este objeto simulado debería tener la misma estructura que un modelo real de Pago
            pago = type('Pago', (), {
                'usuario': usuario,
                'monto': 50000 if usuario.plan == 'Mensual' else 10000,
                'fecha': datetime.now() - timedelta(days=random.randint(0, 30)),
                'tipo': 'Membresía'
            })
            pagos_membresias.append(pago)
    
    # Convertir ventas a formato para mostrar
    pagos_productos = []
    for venta, producto, usuario in ultimas_ventas:
        pago = type('Pago', (), {
            'usuario': usuario,
            'monto': venta.total,
            'fecha': venta.fecha,
            'tipo': f'Producto: {producto.nombre}',
            'metodo_pago': venta.metodo_pago
        })
        pagos_productos.append(pago)
    
    # Combinar todos los pagos
    pagos = pagos_membresias + pagos_productos
    pagos.sort(key=lambda x: x.fecha, reverse=True)
    
    return render_template('finanzas.html',
                          usuarios_activos=usuarios_activos,
                          asistencias_mes=asistencias_mes,
                          ingresos_mensual_membresias=ingresos_mensual_membresias,
                          ingresos_mensual_productos=ingresos_mensual_productos,
                          ingresos_mensual_total=ingresos_mensual_total,
                          meses=json.dumps(meses),
                          datos_ingresos_membresias=json.dumps(datos_ingresos_membresias),
                          datos_ingresos_productos=json.dumps(datos_ingresos_productos),
                          datos_planes=json.dumps(datos_planes),
                          productos_nombres=json.dumps(productos_nombres),
                          productos_cantidades=json.dumps(productos_cantidades),
                          productos_ingresos=json.dumps(productos_ingresos),
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
                
        # Actualizar datos
        usuario.nombre = request.form['nombre']
        usuario.cedula = request.form['cedula']
        usuario.plan = request.form['plan']
        usuario.metodo_pago = request.form['metodo_pago']
        
        db.session.commit()
        return redirect(url_for('main.usuarios', success="Usuario actualizado correctamente"))
    
    return render_template('editar_usuario.html', usuario=usuario)
