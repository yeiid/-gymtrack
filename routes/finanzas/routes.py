from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, Usuario, Asistencia, PagoMensualidad, VentaProducto, Producto
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json

"""
Módulo de Finanzas del Sistema GymTrack
Desarrollado por: YEIFRAN HERNANDEZ
NEURALJIRA_DEV - Visión inteligente para gestión de gimnasios
"""

# Crear blueprint para finanzas
bp = Blueprint('finanzas', __name__, url_prefix='/finanzas')

@bp.route('/')
def index():
    """
    Vista principal de finanzas que muestra un dashboard con indicadores clave
    y gráficos de rendimiento financiero.
    
    Implementado por: YEIFRAN HERNANDEZ (NEURALJIRA_DEV)
    """
    try:
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
        costo_porcentaje = 0.60
        
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
            try:
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
            except Exception as e:
                flash(f'Error en cálculo para mes {i}: {str(e)}', 'warning')
                # Agregar valores por defecto
                if len(meses) < i + 1:
                    meses.append(f"Mes {i}")
                if len(datos_ingresos_membresias) < i + 1:
                    datos_ingresos_membresias.append(0)
                if len(datos_ingresos_productos) < i + 1:
                    datos_ingresos_productos.append(0)
                if len(datos_margenes) < i + 1:
                    datos_margenes.append(0)
        
        # Verificar que tenemos datos para los gráficos
        if not meses:
            meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
            datos_ingresos_membresias = [0, 0, 0, 0, 0, 0]
            datos_ingresos_productos = [0, 0, 0, 0, 0, 0]
            datos_margenes = [0, 0, 0, 0, 0, 0]
        
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
        
        # Verificar y preparar datos para productos
        if productos_vendidos:
            # Asegurar que los datos sean del tipo correcto para evitar errores en JSON
            productos_nombres = [str(p[0]) for p in productos_vendidos]
            productos_cantidades = [int(p[1]) if p[1] is not None else 0 for p in productos_vendidos]
            productos_ingresos = [float(p[2]) if p[2] is not None else 0.0 for p in productos_vendidos]
        else:
            productos_nombres = ["Sin ventas"]
            productos_cantidades = [0]
            productos_ingresos = [0.0]
        
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
        
        return render_template('finanzas/finanzas.html',
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
    except Exception as e:
        flash(f'Error al cargar finanzas: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/pagos')
def pagos():
    pagos = PagoMensualidad.query.order_by(PagoMensualidad.fecha_pago.desc()).all()
    return render_template('pagos/pagos.html', pagos=pagos)

@bp.route('/diarias')
def finanzas_diarias():
    """
    Análisis financiero diario con desglose detallado de ingresos,
    ventas y métricas de rendimiento.
    
    Implementado por: YEIFRAN HERNANDEZ (NEURALJIRA_DEV)
    """
    try:
        # Obtener la fecha para el análisis (hoy por defecto)
        fecha_str = request.args.get('fecha')
        
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                fecha = datetime.now().date()
        else:
            fecha = datetime.now().date()
        
        # Inicio y fin del día
        inicio_dia = datetime.combine(fecha, datetime.min.time())
        fin_dia = datetime.combine(fecha, datetime.max.time())
        
        # 1. Obtener ingresos por membresías del día
        pagos_membresia = PagoMensualidad.query.filter(
            PagoMensualidad.fecha_pago >= inicio_dia,
            PagoMensualidad.fecha_pago <= fin_dia
        ).all()
        
        total_membresias = sum(pago.monto for pago in pagos_membresia)
        
        # Agrupar por tipo de plan
        ingresos_por_plan = {}
        for pago in pagos_membresia:
            if pago.plan in ingresos_por_plan:
                ingresos_por_plan[pago.plan] += pago.monto
            else:
                ingresos_por_plan[pago.plan] = pago.monto
        
        # 2. Obtener ingresos por ventas de productos del día
        ventas_productos = VentaProducto.query.filter(
            VentaProducto.fecha >= inicio_dia,
            VentaProducto.fecha <= fin_dia
        ).all()
        
        total_productos = sum(venta.total for venta in ventas_productos)
        
        # Agrupar por categoría
        productos_por_categoria = {}
        for venta in ventas_productos:
            producto = venta.producto
            if producto.categoria in productos_por_categoria:
                productos_por_categoria[producto.categoria] += venta.total
            else:
                productos_por_categoria[producto.categoria] = venta.total
        
        # Detalle de productos vendidos
        detalle_productos = {}
        for venta in ventas_productos:
            nombre_producto = venta.producto.nombre
            if nombre_producto in detalle_productos:
                detalle_productos[nombre_producto]['cantidad'] += venta.cantidad
                detalle_productos[nombre_producto]['total'] += venta.total
            else:
                detalle_productos[nombre_producto] = {
                    'cantidad': venta.cantidad,
                    'precio_unitario': venta.precio_unitario,
                    'total': venta.total
                }
        
        # 3. Calcular totales
        total_ingresos = total_membresias + total_productos
        
        # 4. Método de pago
        ingresos_por_metodo = {}
        
        # Métodos de pago de membresías
        for pago in pagos_membresia:
            if pago.metodo_pago in ingresos_por_metodo:
                ingresos_por_metodo[pago.metodo_pago] += pago.monto
            else:
                ingresos_por_metodo[pago.metodo_pago] = pago.monto
        
        # Métodos de pago de productos
        for venta in ventas_productos:
            if venta.metodo_pago in ingresos_por_metodo:
                ingresos_por_metodo[venta.metodo_pago] += venta.total
            else:
                ingresos_por_metodo[venta.metodo_pago] = venta.total
        
        # 5. Obtener asistencias del día
        asistencias = Asistencia.query.filter(
            Asistencia.fecha >= inicio_dia,
            Asistencia.fecha <= fin_dia
        ).count()
        
        return render_template('finanzas/finanzas_diarias.html',
                              fecha=fecha,
                              pagos_membresia=pagos_membresia,
                              ventas_productos=ventas_productos,
                              total_membresias=total_membresias,
                              total_productos=total_productos,
                              total_ingresos=total_ingresos,
                              ingresos_por_plan=ingresos_por_plan,
                              productos_por_categoria=productos_por_categoria,
                              detalle_productos=detalle_productos,
                              ingresos_por_metodo=ingresos_por_metodo,
                              asistencias=asistencias)
    except Exception as e:
        flash(f'Error al cargar finanzas diarias: {str(e)}', 'danger')
        return redirect(url_for('main.finanzas.index'))

"""
Sistema de análisis financiero para GymTrack
Copyright © NEURALJIRA_DEV - YEIFRAN HERNANDEZ
Todos los derechos reservados.
""" 