from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, send_from_directory
from models import db, Usuario, Producto, VentaProducto, Admin
from models import datetime_colombia, date_colombia  # Importar las funciones de zona horaria
from sqlalchemy import func, desc
from routes.auth.routes import admin_required
from datetime import datetime, timedelta
import csv
import io
import os

# Crear blueprint para productos
bp = Blueprint('productos', __name__, url_prefix='/productos')

@bp.route('/')
def index():
    productos = Producto.query.all()
    return render_template('productos/productos.html', productos=productos)

@bp.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    try:
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        
        # Validar campos obligatorios
        if not nombre:
            flash("El nombre del producto es obligatorio", "danger")
            return redirect(url_for('main.productos.index'))
            
        try:
            precio = float(request.form.get('precio', 0))
            if precio < 0:
                raise ValueError("El precio no puede ser negativo")
        except ValueError:
            flash("El precio debe ser un número válido", "danger")
            return redirect(url_for('main.productos.index'))
            
        try:
            stock = int(request.form.get('stock', 0))
            if stock < 0:
                raise ValueError("El stock no puede ser negativo")
        except ValueError:
            flash("El stock debe ser un número entero válido", "danger")
            return redirect(url_for('main.productos.index'))
            
        categoria = request.form.get('categoria', 'Otro')
        
        # Verificar si ya existe un producto con el mismo nombre
        producto_existente = Producto.query.filter_by(nombre=nombre).first()
        
        if producto_existente:
            flash(f"Ya existe un producto con el nombre {nombre}", "danger")
            return redirect(url_for('main.productos.index'))
        
        nuevo_producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            categoria=categoria
        )
        
        db.session.add(nuevo_producto)
        db.session.commit()
        
        flash("Producto agregado correctamente", "success")
        return redirect(url_for('main.productos.index'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al agregar producto: {str(e)}", "danger")
        return redirect(url_for('main.productos.index'))

@bp.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
def editar_producto(producto_id):
    try:
        producto = Producto.query.get_or_404(producto_id)
        
        if request.method == 'POST':
            # Validar campos
            try:
                nombre = request.form.get('nombre', '').strip()
                if not nombre:
                    flash("El nombre del producto es obligatorio", "danger")
                    return render_template('productos/editar_producto.html', producto=producto)
                
                # Validar que el nombre no exista en otro producto
                producto_existente = Producto.query.filter(
                    Producto.nombre == nombre, 
                    Producto.id != producto_id
                ).first()
                
                if producto_existente:
                    flash(f"Ya existe otro producto con el nombre {nombre}", "danger")
                    return render_template('productos/editar_producto.html', producto=producto)
                
                # Validar precio
                try:
                    precio = float(request.form.get('precio', 0))
                    if precio < 0:
                        raise ValueError("El precio no puede ser negativo")
                except ValueError:
                    flash("El precio debe ser un número válido", "danger")
                    return render_template('productos/editar_producto.html', producto=producto)
                
                # Validar stock
                try:
                    stock = int(request.form.get('stock', 0))
                    if stock < 0:
                        raise ValueError("El stock no puede ser negativo")
                except ValueError:
                    flash("El stock debe ser un número entero válido", "danger")
                    return render_template('productos/editar_producto.html', producto=producto)
                
                # Actualizar producto
                producto.nombre = nombre
                producto.descripcion = request.form.get('descripcion', '').strip()
                producto.precio = precio
                producto.stock = stock
                producto.categoria = request.form.get('categoria', 'Otro')
                
                db.session.commit()
                flash("Producto actualizado correctamente", "success")
                return redirect(url_for('main.productos.index'))
            except Exception as e:
                db.session.rollback()
                flash(f"Error al actualizar producto: {str(e)}", "danger")
                return render_template('productos/editar_producto.html', producto=producto)
        
        # GET request
        return render_template('productos/editar_producto.html', producto=producto)
    except Exception as e:
        flash(f"Error al cargar producto: {str(e)}", "danger")
        return redirect(url_for('main.productos.index'))

@bp.route('/eliminar_producto/<int:producto_id>')
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    
    # Verificar si hay ventas asociadas
    ventas = VentaProducto.query.filter_by(producto_id=producto_id).first()
    
    if ventas:
        flash("No se puede eliminar el producto porque tiene ventas asociadas", "danger")
        return redirect(url_for('main.productos.index'))
    
    db.session.delete(producto)
    db.session.commit()
    
    flash("Producto eliminado correctamente", "success")
    return redirect(url_for('main.productos.index'))

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
        # Obtener todas las ventas con información de producto y usuario
        ventas = db.session.query(
            VentaProducto,
            Producto.nombre.label('producto_nombre'),
            Usuario.nombre.label('usuario_nombre')
        ).join(
            Producto, VentaProducto.producto_id == Producto.id
        ).outerjoin(
            Usuario, VentaProducto.usuario_id == Usuario.id
        ).order_by(
            VentaProducto.fecha.desc()
        ).all()
        
        # Determinar si el usuario es admin
        is_admin = False
        is_admin_role = False
        if 'admin_id' in session:
            is_admin = True
            admin = Admin.query.get(session['admin_id'])
            if admin and admin.rol == 'administrador':
                is_admin_role = True
        
        return render_template('productos/ventas.html', 
                              ventas=ventas, 
                              is_admin=is_admin,
                              is_admin_role=is_admin_role)
    except Exception as e:
        flash(f"Error al cargar las ventas: {str(e)}", "danger")
        return redirect(url_for('main.index'))

@bp.route('/editar_venta/<int:venta_id>', methods=['GET', 'POST'])
@admin_required
def editar_venta(venta_id):
    try:
        venta = VentaProducto.query.get_or_404(venta_id)
        
        if request.method == 'POST':
            # Guardar datos originales para el registro
            datos_originales = {
                'cantidad': venta.cantidad,
                'precio_unitario': venta.precio_unitario,
                'total': venta.total,
                'metodo_pago': venta.metodo_pago,
                'usuario_id': venta.usuario_id
            }
            
            # Actualizar con los nuevos datos
            nueva_cantidad = int(request.form.get('cantidad', 1))
            nuevo_precio = float(request.form.get('precio_unitario', 0))
            nuevo_metodo_pago = request.form.get('metodo_pago', 'Efectivo')
            nuevo_usuario_id = request.form.get('usuario_id')
            if nuevo_usuario_id == '':
                nuevo_usuario_id = None
            
            # Calcular el nuevo total
            nuevo_total = nueva_cantidad * nuevo_precio
            
            # Verificar cambio en stock
            producto = Producto.query.get(venta.producto_id)
            if nueva_cantidad != venta.cantidad:
                # Ajustar el stock del producto
                diferencia = venta.cantidad - nueva_cantidad
                producto.stock += diferencia
            
            # Actualizar venta
            venta.cantidad = nueva_cantidad
            venta.precio_unitario = nuevo_precio
            venta.total = nuevo_total
            venta.metodo_pago = nuevo_metodo_pago
            venta.usuario_id = nuevo_usuario_id
            
            db.session.commit()
            
            # Registrar la edición
            admin = Admin.query.get(session['admin_id'])
            fecha_edicion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('modificaciones_ventas.log', 'a', encoding='utf-8') as f:
                f.write(f"{fecha_edicion},MODIFICACIÓN,VENTA,{venta_id},{producto.nombre},Cantidad:{datos_originales['cantidad']}->{nueva_cantidad},Precio:{datos_originales['precio_unitario']}->{nuevo_precio},Total:{datos_originales['total']}->{nuevo_total},{admin.nombre}\n")
            
            flash('Venta actualizada correctamente', 'success')
            return redirect(url_for('main.productos.ventas'))
        
        # GET: Mostrar formulario
        usuarios = Usuario.query.all()
        producto = Producto.query.get(venta.producto_id)
        return render_template('productos/editar_venta.html', 
                              venta=venta, 
                              usuarios=usuarios,
                              producto=producto)
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al editar la venta: {str(e)}', 'danger')
        return redirect(url_for('main.productos.ventas'))

@bp.route('/eliminar_venta/<int:venta_id>', methods=['POST'])
@admin_required
def eliminar_venta(venta_id):
    try:
        # Verificar que el usuario sea administrador
        if 'admin_id' not in session:
            flash('Debe iniciar sesión como administrador para realizar esta acción', 'danger')
            return redirect(url_for('main.productos.ventas'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            flash('Sesión de administrador inválida', 'danger')
            return redirect(url_for('main.productos.ventas'))
        
        venta = VentaProducto.query.get_or_404(venta_id)
        
        # Guardar datos para el reporte
        producto = Producto.query.get(venta.producto_id)
        producto_nombre = producto.nombre if producto else "Producto eliminado"
        venta_fecha = venta.fecha.strftime('%Y-%m-%d %H:%M:%S')
        venta_cantidad = venta.cantidad
        venta_total = venta.total
        venta_metodo = venta.metodo_pago
        usuario = Usuario.query.get(venta.usuario_id) if venta.usuario_id else None
        usuario_nombre = usuario.nombre if usuario else "Sin usuario"
        
        # Restaurar el stock
        if producto:
            producto.stock += venta.cantidad
        
        # Eliminar la venta
        db.session.delete(venta)
        db.session.commit()
        
        # Registrar la eliminación
        fecha_eliminacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('eliminaciones_ventas.log', 'a', encoding='utf-8') as f:
            f.write(f"{fecha_eliminacion},ELIMINACIÓN,VENTA,{venta_id},{producto_nombre},{venta_cantidad},{venta_total},{venta_metodo},{usuario_nombre},{admin.nombre}\n")
        
        flash('Venta eliminada correctamente', 'success')
        return redirect(url_for('main.productos.ventas'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la venta: {str(e)}', 'danger')
        return redirect(url_for('main.productos.ventas'))

@bp.route('/generar_reporte_ventas', methods=['POST'])
@admin_required
def generar_reporte_ventas():
    try:
        # Verificar que sea administrador
        if 'admin_id' not in session:
            flash('Debe iniciar sesión como administrador para realizar esta acción', 'danger')
            return redirect(url_for('main.productos.ventas'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin or admin.rol != 'administrador':
            flash('Solo los administradores pueden generar reportes', 'danger')
            return redirect(url_for('main.productos.ventas'))
        
        # Obtener datos del formulario
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        tipo_reporte = request.form.get('tipo_reporte', 'ventas')
        
        if not fecha_inicio or not fecha_fin:
            flash('Debe especificar un rango de fechas', 'warning')
            return redirect(url_for('main.productos.ventas'))
        
        # Convertir a objetos datetime
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        fecha_fin_dt = datetime.combine(fecha_fin_dt.date(), datetime.max.time())  # Hasta final del día
        
        # Generar nombre de archivo
        timestamp = datetime_colombia().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"reporte_{tipo_reporte}_{timestamp}.csv"
        
        # Generar contenido del reporte
        if tipo_reporte == 'ventas':
            # Consultar ventas en el rango de fechas
            ventas = db.session.query(
                VentaProducto, 
                Producto.nombre.label('producto_nombre'),
                Usuario.nombre.label('usuario_nombre')
            ).join(
                Producto, VentaProducto.producto_id == Producto.id
            ).outerjoin(
                Usuario, VentaProducto.usuario_id == Usuario.id
            ).filter(
                VentaProducto.fecha.between(fecha_inicio_dt, fecha_fin_dt)
            ).order_by(
                VentaProducto.fecha
            ).all()
            
            # Generar CSV
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                # Encabezado
                f.write('Fecha,ID,Producto,Cantidad,Precio Unitario,Total,Método de Pago,Usuario\n')
                
                # Datos
                for venta_data in ventas:
                    venta = venta_data[0]
                    producto_nombre = venta_data.producto_nombre
                    usuario_nombre = venta_data.usuario_nombre or 'Sin usuario'
                    
                    f.write(f'{venta.fecha.strftime("%Y-%m-%d %H:%M:%S")},{venta.id},{producto_nombre},{venta.cantidad},{venta.precio_unitario},{venta.total},{venta.metodo_pago},{usuario_nombre}\n')
        
        elif tipo_reporte == 'modificaciones':
            # Leer el archivo de log de modificaciones
            try:
                with open('modificaciones_ventas.log', 'r', encoding='utf-8') as f_in:
                    with open(nombre_archivo, 'w', encoding='utf-8') as f_out:
                        # Encabezado
                        f_out.write('Fecha,Tipo,Entidad,ID,Producto,Cambios,Administrador\n')
                        
                        # Filtrar por fecha
                        for linea in f_in:
                            partes = linea.strip().split(',')
                            if len(partes) >= 4:
                                fecha_log = datetime.strptime(partes[0], '%Y-%m-%d %H:%M:%S')
                                if fecha_inicio_dt <= fecha_log <= fecha_fin_dt:
                                    f_out.write(linea)
            except FileNotFoundError:
                with open(nombre_archivo, 'w', encoding='utf-8') as f:
                    f.write('Fecha,Tipo,Entidad,ID,Producto,Cambios,Administrador\n')
                    f.write('No hay registros de modificaciones en el período seleccionado\n')
        
        elif tipo_reporte == 'eliminaciones':
            # Leer el archivo de log de eliminaciones
            try:
                with open('eliminaciones_ventas.log', 'r', encoding='utf-8') as f_in:
                    with open(nombre_archivo, 'w', encoding='utf-8') as f_out:
                        # Encabezado
                        f_out.write('Fecha,Tipo,Entidad,ID,Producto,Cantidad,Total,Método de Pago,Usuario,Administrador\n')
                        
                        # Filtrar por fecha
                        for linea in f_in:
                            partes = linea.strip().split(',')
                            if len(partes) >= 4:
                                fecha_log = datetime.strptime(partes[0], '%Y-%m-%d %H:%M:%S')
                                if fecha_inicio_dt <= fecha_log <= fecha_fin_dt:
                                    f_out.write(linea)
            except FileNotFoundError:
                with open(nombre_archivo, 'w', encoding='utf-8') as f:
                    f.write('Fecha,Tipo,Entidad,ID,Producto,Cantidad,Total,Método de Pago,Usuario,Administrador\n')
                    f.write('No hay registros de eliminaciones en el período seleccionado\n')
        
        # Generar URL para descargar el reporte
        url_descarga = url_for('main.productos.descargar_reporte', nombre_archivo=nombre_archivo)
        flash(f'Reporte generado correctamente. <a href="{url_descarga}" class="alert-link">Haga clic aquí para descargar</a>', 'success')
        return redirect(url_for('main.productos.ventas'))
        
    except Exception as e:
        flash(f'Error al generar el reporte: {str(e)}', 'danger')
        return redirect(url_for('main.productos.ventas'))

@bp.route('/descargar_reporte/<nombre_archivo>')
@admin_required
def descargar_reporte(nombre_archivo):
    try:
        # Por seguridad, verificar que el archivo sea un reporte válido
        if not nombre_archivo.startswith('reporte_') or not nombre_archivo.endswith('.csv'):
            flash('Archivo no válido', 'danger')
            return redirect(url_for('main.productos.ventas'))
        
        # Enviar el archivo para descarga
        return send_file(nombre_archivo, 
                         as_attachment=True, 
                         download_name=nombre_archivo,
                         mimetype='text/csv')
    except Exception as e:
        flash(f'Error al descargar el reporte: {str(e)}', 'danger')
        return redirect(url_for('main.productos.ventas')) 