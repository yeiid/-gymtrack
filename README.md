# GymWeb

Sistema de gestión para gimnasios desarrollado con Flask.

## Características

- Registro y gestión de usuarios
- Control de asistencia
- Inventario de productos
- Registro de ventas
- Informes financieros

## Requisitos

- Python 3.7+
- Flask
- SQLAlchemy
- Otras dependencias (ver requirements.txt)

## Instalación

1. Clonar el repositorio

   ```
   git clone <url-del-repositorio>
   cd gymWeb
   ```

2. Crear y activar entorno virtual

   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias

   ```
   pip install -r requirements.txt
   ```

4. Inicializar la base de datos

   ```
   python generar_datos.py
   ```

5. Ejecutar la aplicación
   ```
   python app.py
   ```

## Estructura del Proyecto

- `app.py`: Punto de entrada de la aplicación
- `models.py`: Modelos de datos
- `routes.py`: Rutas y controladores
- `config.py`: Configuración de la aplicación
- `templates/`: Plantillas HTML
- `static/`: Archivos estáticos (CSS, JS, imágenes)
