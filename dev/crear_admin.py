import sqlite3
from werkzeug.security import generate_password_hash

# Conectar a la base de datos
conn = sqlite3.connect('database.db')
cur = conn.cursor()

# Mostrar usuarios actuales
print("Administradores existentes:")
cur.execute('SELECT id, nombre, usuario, rol FROM admin')
for row in cur.fetchall():
    print(row)

# Verificar si existe el usuario "admin"
cur.execute('SELECT COUNT(*) FROM admin WHERE usuario = "admin"')
count = cur.fetchone()[0]

if count == 0:
    # Crear el usuario admin
    print("\nCreando usuario administrador...")
    password_hash = generate_password_hash("admin123")
    cur.execute('''
        INSERT INTO admin (nombre, usuario, password_hash, rol, fecha_creacion)
        VALUES (?, ?, ?, ?, datetime('now'))
    ''', ('Administrador Principal', 'admin', password_hash, 'administrador'))
    conn.commit()
    print("Usuario admin creado con éxito.")
else:
    # Actualizar el usuario admin para que sea administrador
    print("\nActualizando usuario admin existente...")
    cur.execute('UPDATE admin SET rol = "administrador" WHERE usuario = "admin"')
    conn.commit()
    print("Usuario admin actualizado a rol administrador.")

# Verificar después de los cambios
print("\nAdministradores después de los cambios:")
cur.execute('SELECT id, nombre, usuario, rol FROM admin')
for row in cur.fetchall():
    print(row)

conn.close()
print("\nListo! Por favor, cierra sesión y vuelve a iniciar sesión con:")
print("Usuario: admin")
print("Contraseña: admin123") 