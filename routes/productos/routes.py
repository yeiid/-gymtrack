from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Usuario, Producto, VentaProducto
from datetime import datetime

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
        return redirect(url_for('main.productos.index', 
                              error="No se puede eliminar el producto porque tiene ventas asociadas"))
    
    db.session.delete(producto)
    db.session.commit()
    
    return redirect(url_for('main.productos.index', success="Producto eliminado correctamente"))

@bp.route('/registrar_venta', methods=['GET', 'POST'])
def registrar_venta():
    if request.method == 'POST':
        producto_id = int(request.form['producto_id'])
        cantidad = int(request.form['cantidad'])
        usuario_id = request.form.get('usuario_id')  # Puede ser None si es venta sin usuario
        metodo_pago = request.form['metodo_pago']
        
        producto = Producto.query.get_or_404(producto_id)
        
        # Verificar stock
        if producto.stock < cantidad:
            return render_template('productos/registrar_venta.html', 
                                productos=Producto.query.all(),
                                usuarios=Usuario.query.all(),
                                error=f"Stock insuficiente. Solo hay {producto.stock} unidades disponibles.",
                                hoy=datetime.now().strftime('%Y-%m-%d'))
        
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
        
        return redirect(url_for('main.productos.ventas', success="Venta registrada correctamente"))
    
    productos = Producto.query.filter(Producto.stock > 0).all()
    usuarios = Usuario.query.all()
    return render_template('productos/registrar_venta.html', 
                           productos=productos, 
                           usuarios=usuarios, 
                           hoy=datetime.now().strftime('%Y-%m-%d'))

@bp.route('/ventas')
def ventas():
    try:
        # Obtener todas las ventas con información de producto y usuario
        ventas = db.session.query(VentaProducto, Producto, Usuario).\
            join(Producto, VentaProducto.producto_id == Producto.id).\
            outerjoin(Usuario, VentaProducto.usuario_id == Usuario.id).\
            order_by(VentaProducto.fecha.desc()).all()
        
        success = request.args.get('success')
        
        return render_template('productos/ventas.html', ventas=ventas, success=success)
    except Exception as e:
        # Log del error
        print(f"Error al cargar ventas: {str(e)}")
        flash(f"Error al cargar las ventas: {str(e)}", "danger")
        return render_template('productos/ventas.html', ventas=[], error=f"Error al cargar las ventas") 