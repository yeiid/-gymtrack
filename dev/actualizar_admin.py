import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('database.db')
cur = conn.cursor()

# Mostrar usuarios actuales
print("Administradores antes de la actualización:")
cur.execute('SELECT id, nombre, usuario, rol FROM admin')
for row in cur.fetchall():
    print(row)

# Actualizar el rol del usuario admin a administrador
cur.execute('UPDATE admin SET rol = "administrador" WHERE usuario = "admin"')
conn.commit()

# Verificar la actualización
print("\nAdministradores después de la actualización:")
cur.execute('SELECT id, nombre, usuario, rol FROM admin')
for row in cur.fetchall():
    print(row)

print("\n¡Usuario actualizado correctamente!")
conn.close()
print("Ahora cierra sesión y vuelve a iniciar sesión para ver los cambios.") 