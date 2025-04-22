import random
from datetime import datetime, timedelta
from app import app, db
from models import Usuario, Asistencia, Producto, VentaProducto

# Lista de nombres y apellidos para generar datos aleatorios
nombres = ["Carlos", "María", "Juan", "Ana", "Luis", "Laura", "Pedro", "Sofía", "Miguel", "Gabriela"]
apellidos = ["García", "Rodríguez", "López", "Martínez", "González", "Pérez", "Fernández", "Sánchez", "Ramírez", "Torres"]
planes = ["Diario", "Mensual", "Personalizado"]
metodos_pago = ["Efectivo", "Tarjeta", "Transferencia", "Nequi", "Daviplata"]

def generar_cedula():
    return f"{random.randint(1000000, 9999999)}"

def generar_usuario():
    nombre = f"{random.choice(nombres)} {random.choice(apellidos)}"
    cedula = generar_cedula()
    plan = random.choice(planes)
    metodo_pago = random.choice(metodos_pago)
    
    return Usuario(
        nombre=nombre, 
        cedula=cedula, 
        plan=plan, 
        metodo_pago=metodo_pago
    )

def generar_asistencias(usuario_id, cantidad=5):
    asistencias = []
    for i in range(cantidad):
        fecha = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        asistencia = Asistencia(usuario_id=usuario_id, fecha=fecha)
        asistencias.append(asistencia)
    return asistencias

def generar_producto():
    categorias = ['Suplementos', 'Ropa', 'Accesorios', 'Bebidas', 'Otro']
    nombres_suplementos = ['Proteína Whey', 'Creatina', 'Pre-entreno', 'BCAA', 'Multivitamínico']
    nombres_ropa = ['Camiseta de entrenamiento', 'Shorts deportivos', 'Leggins', 'Sudadera', 'Medias deportivas']
    nombres_accesorios = ['Guantes de entrenamiento', 'Cinturón de pesas', 'Mancuernas', 'Botella', 'Toalla']
    nombres_bebidas = ['Agua', 'Bebida energética', 'Bebida isotónica', 'Jugo natural', 'Batido']
    
    categoria = random.choice(categorias)
    
    if categoria == 'Suplementos':
        nombre = random.choice(nombres_suplementos)
        precio = random.randint(50000, 200000)
        descripcion = f"Suplemento de alta calidad para mejorar el rendimiento."
    elif categoria == 'Ropa':
        nombre = random.choice(nombres_ropa)
        precio = random.randint(30000, 100000)
        descripcion = f"Ropa deportiva cómoda y transpirable."
    elif categoria == 'Accesorios':
        nombre = random.choice(nombres_accesorios)
        precio = random.randint(20000, 80000)
        descripcion = f"Accesorio para mejorar tu entrenamiento."
    elif categoria == 'Bebidas':
        nombre = random.choice(nombres_bebidas)
        precio = random.randint(3000, 15000)
        descripcion = f"Bebida para hidratación y recuperación."
    else:
        nombre = f"Producto {random.randint(1, 100)}"
        precio = random.randint(10000, 50000)
        descripcion = f"Descripción del producto."
        
    # Agregar un número aleatorio al nombre para evitar duplicados
    nombre = f"{nombre} {random.choice(['Pro', 'Premium', 'Plus', 'Max', 'Ultra', 'Basic'])}"
    
    return Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=random.randint(5, 50),
        categoria=categoria
    )

def generar_venta(producto_id, usuarios):
    cantidad = random.randint(1, 5)
    producto = Producto.query.get(producto_id)
    
    # Algunas ventas sin usuario (cliente no registrado)
    if random.random() < 0.3:
        usuario_id = None
    else:
        usuario = random.choice(usuarios)
        usuario_id = usuario.id
        
    metodos_pago = ["Efectivo", "Tarjeta", "Transferencia", "Nequi", "Daviplata"]
    metodo_pago = random.choice(metodos_pago)
    
    # Fecha aleatoria en los últimos 60 días
    fecha = datetime.utcnow() - timedelta(days=random.randint(0, 60), 
                                         hours=random.randint(0, 23),
                                         minutes=random.randint(0, 59))
    
    total = producto.precio * cantidad
    
    return VentaProducto(
        producto_id=producto_id,
        usuario_id=usuario_id,
        cantidad=cantidad,
        precio_unitario=producto.precio,
        total=total,
        metodo_pago=metodo_pago,
        fecha=fecha
    )

def generar_datos_prueba(cantidad_usuarios=50, cantidad_productos=20):
    with app.app_context():
        # Limpiar datos existentes
        db.session.query(VentaProducto).delete()
        db.session.query(Asistencia).delete()
        db.session.query(Producto).delete()
        db.session.query(Usuario).delete()
        db.session.commit()
        
        print("Generando usuarios...")
        # Generar usuarios
        usuarios = []
        for i in range(cantidad_usuarios):
            usuario = generar_usuario()
            db.session.add(usuario)
            db.session.commit()
            usuarios.append(usuario)
            
            # Generar algunas asistencias aleatorias para cada usuario
            asistencias = generar_asistencias(usuario.id, random.randint(0, 15))
            for asistencia in asistencias:
                db.session.add(asistencia)
        
        print("Generando productos...")
        # Generar productos
        productos = []
        for i in range(cantidad_productos):
            producto = generar_producto()
            db.session.add(producto)
            db.session.commit()
            productos.append(producto)
        
        print("Generando ventas...")
        # Generar ventas aleatorias
        for producto in productos:
            # Cada producto tiene entre 0 y 10 ventas
            num_ventas = random.randint(0, 10)
            for _ in range(num_ventas):
                venta = generar_venta(producto.id, usuarios)
                db.session.add(venta)
                
                # Actualizar stock
                producto.stock -= venta.cantidad
                if producto.stock < 0:
                    producto.stock = 0
        
        db.session.commit()
        print(f"Se han generado {cantidad_usuarios} usuarios con sus asistencias aleatorias.")
        print(f"Se han generado {cantidad_productos} productos con ventas aleatorias.")

if __name__ == "__main__":
    generar_datos_prueba() 