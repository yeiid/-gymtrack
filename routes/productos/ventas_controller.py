from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Producto, VentaProducto, Usuario
from models import datetime_colombia, date_colombia
from sqlalchemy import func, desc
from routes.auth.routes import admin_required
from datetime import datetime, timedelta
import csv
import io
import os
from routes.productos.routes import bp

@bp.route('/registrar_venta', methods=['GET', 'POST'])
def registrar_venta():
    try:
        if request.method == 'POST':
            producto_id = int(request.form['producto_id'])
            cantidad = int(request.form['cantidad'])
            usuario_id = request.form.get('usuario_id')  # Puede ser None si es venta sin usuario
            metodo_pago = request.form['metodo_pago']
            
            producto = Producto.query.get_or_404(producto_id)
            
            # Verificar stock
            if producto.stock < cantidad:
                flash(f"Stock insuficiente. Solo hay {producto.stock} unidades disponibles.", "danger")
                return redirect(url_for('main.registrar_venta_directo'))
            
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
            
            flash("Venta registrada correctamente", "success")
            return redirect(url_for('main.registrar_venta_directo'))
        
        productos = Producto.query.filter(Producto.stock > 0).all()
        usuarios = Usuario.query.all()
        return render_template('productos/registrar_venta.html', 
                               productos=productos, 
                               usuarios=usuarios, 
                               hoy=datetime.now().strftime('%Y-%m-%d'))
    except Exception as e:
        print(f"Error en registrar_venta: {str(e)}")
        flash(f"Error al procesar la venta: {str(e)}", "danger")
        return redirect(url_for('main.registrar_venta_directo'))

@bp.route('/ventas')
def ventas():
    try:
        # Obtener parámetros de filtro
        fecha_inicio_str = request.args.get('fecha_inicio')
        fecha_fin_str = request.args.get('fecha_fin')
        
        # Si no se proporcionan fechas, usar el último mes
        if not fecha_inicio_str:
            fecha_fin = date_colombia()
            fecha_inicio = fecha_fin - timedelta(days=30)
        else:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            if fecha_fin_str:
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            else:
                fecha_fin = date_colombia()
        
        # Consultar ventas
        ventas = VentaProducto.query.filter(
            func.date(VentaProducto.fecha) >= fecha_inicio,
            func.date(VentaProducto.fecha) <= fecha_fin
        ).order_by(VentaProducto.fecha.desc()).all()
        
        # Calcular totales
        total_ventas = sum(venta.total for venta in ventas)
        
        # Agrupar por método de pago
        ventas_por_metodo = {}
        for venta in ventas:
            if venta.metodo_pago not in ventas_por_metodo:
                ventas_por_metodo[venta.metodo_pago] = 0
            ventas_por_metodo[venta.metodo_pago] += venta.total
        
        return render_template('productos/ventas.html', 
                              ventas=ventas,
                              total_ventas=total_ventas,
                              ventas_por_metodo=ventas_por_metodo,
                              fecha_inicio=fecha_inicio,
                              fecha_fin=fecha_fin)
    except Exception as e:
        flash(f"Error al cargar ventas: {str(e)}", "danger")
        return redirect(url_for('main.index'))

@bp.route('/editar_venta/<int:venta_id>', methods=['GET', 'POST'])
@admin_required
def editar_venta(venta_id):
    try:
        venta = VentaProducto.query.get_or_404(venta_id)
        producto_original = venta.producto
        cantidad_original = venta.cantidad
        
        if request.method == 'POST':
            producto_id = int(request.form['producto_id'])
            cantidad = int(request.form['cantidad'])
            usuario_id = request.form.get('usuario_id')  # Puede ser None si es venta sin usuario
            metodo_pago = request.form['metodo_pago']
            
            # Verificar si cambió el producto o la cantidad
            cambio_producto = producto_id != venta.producto_id
            cambio_cantidad = cantidad != venta.cantidad
            
            if cambio_producto or cambio_cantidad:
                # Si cambió el producto, restablecer el stock del producto original
                if cambio_producto:
                    producto_original.stock += cantidad_original
                    nuevo_producto = Producto.query.get_or_404(producto_id)
                    
                    # Verificar stock del nuevo producto
                    if nuevo_producto.stock < cantidad:
                        flash(f"Stock insuficiente para {nuevo_producto.nombre}. Solo hay {nuevo_producto.stock} unidades disponibles.", "danger")
                        return redirect(url_for('main.productos.editar_venta', venta_id=venta_id))
                    
                    # Actualizar stock del nuevo producto
                    nuevo_producto.stock -= cantidad
                    venta.producto = nuevo_producto
                    venta.precio_unitario = nuevo_producto.precio
                elif cambio_cantidad:
                    # Si solo cambió la cantidad, ajustar el stock del producto actual
                    diferencia = cantidad - cantidad_original
                    if diferencia > 0 and producto_original.stock < diferencia:
                        flash(f"Stock insuficiente. Solo hay {producto_original.stock} unidades disponibles.", "danger")
                        return redirect(url_for('main.productos.editar_venta', venta_id=venta_id))
                    
                    producto_original.stock -= diferencia
            
            # Actualizar venta
            venta.usuario_id = usuario_id if usuario_id else None
            venta.cantidad = cantidad
            venta.metodo_pago = metodo_pago
            venta.total = venta.precio_unitario * cantidad
            
            db.session.commit()
            
            flash("Venta actualizada correctamente", "success")
            return redirect(url_for('main.productos.ventas'))
        
        # GET request
        productos = Producto.query.all()
        usuarios = Usuario.query.all()
        
        return render_template('productos/editar_venta.html', 
                              venta=venta, 
                              productos=productos, 
                              usuarios=usuarios)
    except Exception as e:
        db.session.rollback()
        flash(f"Error al editar venta: {str(e)}", "danger")
        return redirect(url_for('main.productos.ventas'))

@bp.route('/eliminar_venta/<int:venta_id>', methods=['POST'])
@admin_required
def eliminar_venta(venta_id):
    try:
        venta = VentaProducto.query.get_or_404(venta_id)
        
        # Restaurar stock
        producto = venta.producto
        if producto:
            producto.stock += venta.cantidad
        
        db.session.delete(venta)
        db.session.commit()
        
        flash("Venta eliminada correctamente", "success")
        return redirect(url_for('main.productos.ventas'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar venta: {str(e)}", "danger")
        return redirect(url_for('main.productos.ventas'))

@bp.route('/generar_reporte_ventas', methods=['POST'])
@admin_required
def generar_reporte_ventas():
    try:
        # Obtener datos del formulario
        fecha_inicio_str = request.form.get('fecha_inicio')
        fecha_fin_str = request.form.get('fecha_fin')
        tipo_reporte = request.form.get('tipo_reporte', 'detallado')
        
        # Si no se proporcionan fechas, usar el último mes
        if not fecha_inicio_str:
            fecha_fin = date_colombia()
            fecha_inicio = fecha_fin - timedelta(days=30)
        else:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            if fecha_fin_str:
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            else:
                fecha_fin = date_colombia()
        
        # Consultar ventas
        ventas = VentaProducto.query.filter(
            func.date(VentaProducto.fecha) >= fecha_inicio,
            func.date(VentaProducto.fecha) <= fecha_fin
        ).order_by(VentaProducto.fecha.desc()).all()
        
        # Crear directorio para reportes si no existe
        reportes_dir = os.path.join('routes', 'exports')
        if not os.path.exists(reportes_dir):
            os.makedirs(reportes_dir)
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"reporte_ventas_{tipo_reporte}_{timestamp}.csv"
        ruta_archivo = os.path.join(reportes_dir, nombre_archivo)
        
        # Crear archivo CSV
        with open(ruta_archivo, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            
            if tipo_reporte == 'detallado':
                # Reporte detallado
                csvwriter.writerow(['ID', 'Fecha', 'Producto', 'Cantidad', 'Precio Unitario', 'Total', 'Método de Pago', 'Cliente'])
                
                for venta in ventas:
                    nombre_cliente = venta.usuario.nombre if venta.usuario else 'Sin cliente'
                    csvwriter.writerow([
                        venta.id,
                        venta.fecha.strftime('%Y-%m-%d %H:%M'),
                        venta.producto.nombre if venta.producto else 'Producto eliminado',
                        venta.cantidad,
                        venta.precio_unitario,
                        venta.total,
                        venta.metodo_pago,
                        nombre_cliente
                    ])
            elif tipo_reporte == 'resumen_diario':
                # Resumen diario
                ventas_por_dia = {}
                for venta in ventas:
                    fecha = venta.fecha.strftime('%Y-%m-%d')
                    if fecha not in ventas_por_dia:
                        ventas_por_dia[fecha] = {
                            'cantidad': 0,
                            'total': 0,
                            'metodos': {}
                        }
                    
                    ventas_por_dia[fecha]['cantidad'] += 1
                    ventas_por_dia[fecha]['total'] += venta.total
                    
                    # Contabilizar por método de pago
                    if venta.metodo_pago not in ventas_por_dia[fecha]['metodos']:
                        ventas_por_dia[fecha]['metodos'][venta.metodo_pago] = 0
                    ventas_por_dia[fecha]['metodos'][venta.metodo_pago] += venta.total
                
                # Escribir encabezados
                csvwriter.writerow(['Fecha', 'Cantidad de Ventas', 'Total', 'Métodos de Pago'])
                
                # Escribir datos por día
                for fecha, datos in sorted(ventas_por_dia.items(), reverse=True):
                    metodos_texto = ', '.join([f"{metodo}: ${total:.2f}" for metodo, total in datos['metodos'].items()])
                    csvwriter.writerow([
                        fecha, 
                        datos['cantidad'], 
                        f"${datos['total']:.2f}", 
                        metodos_texto
                    ])
        
        # Devolver nombre del archivo para descarga
        flash(f"Reporte generado correctamente: {nombre_archivo}", "success")
        return redirect(url_for('main.productos.descargar_reporte', nombre_archivo=nombre_archivo))
    except Exception as e:
        flash(f"Error al generar reporte: {str(e)}", "danger")
        return redirect(url_for('main.productos.ventas'))

@bp.route('/descargar_reporte/<nombre_archivo>')
@admin_required
def descargar_reporte(nombre_archivo):
    try:
        reportes_dir = os.path.join('routes', 'exports')
        return send_file(os.path.join(reportes_dir, nombre_archivo),
                         as_attachment=True,
                         download_name=nombre_archivo,
                         mimetype='text/csv')
    except Exception as e:
        flash(f"Error al descargar reporte: {str(e)}", "danger")
        return redirect(url_for('main.productos.ventas')) 