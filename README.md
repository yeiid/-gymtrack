# GimnasioDB - Sistema de Gestión para Gimnasios

Sistema para gestionar operaciones diarias de un gimnasio, incluyendo registro de usuarios, control de asistencia, seguimiento de pagos, medidas corporales, objetivos personales y venta de productos.

## Características

- **Gestión de Usuarios**: Registro, edición y consulta de usuarios
- **Control de Asistencia**: Registro y visualización de asistencias diarias
- **Gestión de Pagos**: Control de pagos y renovaciones de membresías
- **Seguimiento de Medidas**: Registro y seguimiento de medidas corporales
- **Objetivos Personales**: Establecimiento y seguimiento de objetivos
- **Venta de Productos**: Gestión de inventario y ventas
- **Reportes Financieros**: Informes de ingresos y estadísticas

## Requisitos

- Python 3.7 o superior
- Dependencias listadas en requirements.txt

## Instalación

1. Clonar el repositorio
2. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```
3. Iniciar la aplicación:
   ```
   python app_launcher.py
   ```

## Modos de Ejecución

El sistema ahora utiliza un lanzador unificado (`app_launcher.py`) que puede ejecutarse en diferentes modos:

### Modo Desarrollo
```
python app_launcher.py --mode development --debug
```

### Modo Producción
```
python app_launcher.py --mode production
```

### Opciones Adicionales
- `--no-browser`: No abrir el navegador automáticamente
- `--host`: Especificar dirección IP (por defecto: 127.0.0.1)
- `--port`: Especificar puerto (por defecto: 5000)
- `--debug`: Activar modo de depuración (solo funciona en modo development)
- `--fresh-db`: Recrear la base de datos desde cero

### Scripts Batch para Windows
El sistema incluye scripts batch para facilitar la ejecución:

#### Modo Producción
```
ejecutar_app.bat
```

#### Modo Desarrollo
```
dev_app.bat
```

Estos scripts configuran automáticamente el entorno virtual, instalan dependencias si es necesario y permiten elegir si se debe recrear la base de datos.

## Empaquetado para Distribución

Para crear un ejecutable independiente:

1. Instalar PyInstaller:
   ```
   pip install pyinstaller
   ```

2. Crear el ejecutable:
   ```
   python empaquetar_exe.py
   ```

3. El ejecutable se generará en la carpeta `dist/`

## Estructura del Proyecto

- `app_launcher.py`: Script unificado para iniciar la aplicación (reemplaza app.py, run_app.py y standalone_app.py)
- `models.py`: Definición de modelos de datos
- `routes.py`: Rutas y controladores de la aplicación
- `config.py`: Configuración de la aplicación
- `templates/`: Plantillas HTML
- `static/`: Archivos estáticos (CSS, JS, imágenes)
- `GimnasioDB.spec`: Especificación para PyInstaller
- `empaquetar_exe.py`: Script para crear el ejecutable
- `MANUAL_DE_USUARIO.md`: Manual detallado para usuarios
- `ejecutar_app.bat`: Script para ejecutar en modo producción (Windows)
- `dev_app.bat`: Script para ejecutar en modo desarrollo (Windows)

## Archivos Eliminados

Los siguientes archivos han sido eliminados porque su funcionalidad ha sido consolidada en `app_launcher.py`:

- `app.py`: Reemplazado por app_launcher.py
- `run_app.py`: Reemplazado por app_launcher.py
- `standalone_app.py`: Reemplazado por app_launcher.py
- `actualizar_db.py`: La funcionalidad está ahora incluida en app_launcher.py con la opción --fresh-db
- `probar_app.py`: Reemplazado por el comando `python app_launcher.py --mode development --debug`

## Manual de Usuario

Para obtener instrucciones detalladas sobre el uso del sistema, consulta el [Manual de Usuario](MANUAL_DE_USUARIO.md).

## Créditos

Desarrollado por el equipo de GimnasioDB.

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).
