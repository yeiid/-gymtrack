from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from sqlalchemy import and_

from models import Usuario, Asistencia, PagoMensualidad, VentaProducto, Producto
from models import datetime_colombia, date_colombia
from .utils import sanitizar_valor_numerico

# Importar el blueprint directamente desde el paquete finanzas
from routes.finanzas import bp

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
                fecha = date_colombia()
        else:
            fecha = date_colombia()
        
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