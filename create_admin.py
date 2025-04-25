from models import Admin, db
from app import app

with app.app_context():
    # Verificar si ya existe el administrador
    admin_existente = Admin.query.filter_by(usuario='admin').first()
    
    if not admin_existente:
        admin = Admin(
            nombre='Administrador', 
            usuario='admin', 
            rol='administrador'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Administrador creado exitosamente')
    else:
        print('El administrador ya existe') 