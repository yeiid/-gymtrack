#!/usr/bin/env python
"""
Script para crear administradores por defecto en la base de datos.
Puede ser usado para crear un administrador inicial o restablecer acceso.
"""
import argparse
from models import Admin, db
from app_launcher import create_app

def crear_admin(username, password, nombre, rol):
    """Función para crear un nuevo administrador"""
    app = create_app()
    
    with app.app_context():
        # Verificar si ya existe el administrador
        admin_existente = Admin.query.filter_by(usuario=username).first()
        
        if not admin_existente:
            admin = Admin(
                nombre=nombre,
                usuario=username,
                rol=rol
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f'Administrador "{username}" creado exitosamente')
            return True
        else:
            print(f'El administrador "{username}" ya existe')
            return False

def actualizar_password(username, password):
    """Función para actualizar la contraseña de un administrador existente"""
    app = create_app()
    
    with app.app_context():
        admin = Admin.query.filter_by(usuario=username).first()
        
        if admin:
            admin.set_password(password)
            db.session.commit()
            print(f'Contraseña actualizada para "{username}"')
            return True
        else:
            print(f'El administrador "{username}" no existe')
            return False

def listar_admins():
    """Función para listar todos los administradores"""
    app = create_app()
    
    with app.app_context():
        admins = Admin.query.all()
        
        if admins:
            print("\nAdministradores en el sistema:")
            print("-" * 50)
            print(f"{'ID':<5} {'Usuario':<15} {'Nombre':<20} {'Rol':<15}")
            print("-" * 50)
            
            for admin in admins:
                print(f"{admin.id:<5} {admin.usuario:<15} {admin.nombre:<20} {admin.rol:<15}")
            
            print("-" * 50)
        else:
            print("No hay administradores registrados en el sistema")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gestión de administradores del sistema')
    subparsers = parser.add_subparsers(dest='comando', help='Comando a ejecutar')
    
    # Comando para crear administrador
    crear_parser = subparsers.add_parser('crear', help='Crear un nuevo administrador')
    crear_parser.add_argument('--username', default='admin', help='Nombre de usuario (por defecto: admin)')
    crear_parser.add_argument('--password', default='admin123', help='Contraseña (por defecto: admin123)')
    crear_parser.add_argument('--nombre', default='Administrador', help='Nombre completo (por defecto: Administrador)')
    crear_parser.add_argument('--rol', choices=['administrador', 'recepcionista'], default='administrador', 
                           help='Rol del usuario (por defecto: administrador)')
    
    # Comando para actualizar contraseña
    actualizar_parser = subparsers.add_parser('actualizar', help='Actualizar contraseña de un administrador')
    actualizar_parser.add_argument('--username', required=True, help='Nombre de usuario a actualizar')
    actualizar_parser.add_argument('--password', required=True, help='Nueva contraseña')
    
    # Comando para listar administradores
    listar_parser = subparsers.add_parser('listar', help='Listar administradores existentes')
    
    args = parser.parse_args()
    
    if args.comando == 'crear':
        crear_admin(args.username, args.password, args.nombre, args.rol)
    elif args.comando == 'actualizar':
        actualizar_password(args.username, args.password)
    elif args.comando == 'listar':
        listar_admins()
    else:
        # Si no se especifica un comando, crear el administrador por defecto
        print("Creando administrador por defecto...")
        crear_admin('admin', 'admin123', 'Administrador', 'administrador') 