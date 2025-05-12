from flask import render_template, request, redirect, url_for, flash
from models import db, Producto, VentaProducto
from routes.auth.routes import admin_required
from routes.productos.routes import bp

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