# Sistema de Gestión de Gimnasio

Sistema completo para administrar un gimnasio, incluyendo gestión de usuarios, asistencias, pagos, productos, ventas y reportes financieros.

## Características

- **Gestión de Usuarios**: Registro, edición y visualización de miembros
- **Control de Asistencia**: Registro de entradas de usuarios
- **Gestión de Membresías**: Diferentes planes y renovaciones
- **Venta de Productos**: Inventario y registro de ventas
- **Reportes Financieros**: Análisis de ingresos y márgenes de ganancia

## Requisitos

- Python 3.8 o superior
- Navegador web moderno (Google Chrome o Microsoft Edge recomendados)

## Instalación y Ejecución

### Método 1: Usando Python directamente

1. Clonar o descargar este repositorio
2. Crear un entorno virtual:
   ```
   python -m venv venv
   ```
3. Activar el entorno virtual:
   - En Windows: `venv\Scripts\activate`
   - En Linux/Mac: `source venv/bin/activate`
4. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```
5. Ejecutar la aplicación:
   ```
   python run_app.py
   ```
6. Se abrirá automáticamente un navegador con la aplicación
7. Si no se abre, accede a http://127.0.0.1:5000

### Método 2: Usando el Ejecutable (Windows)

1. Ejecuta el script de generación de Windows:
   ```
   build_windows.bat
   ```
2. Espera a que termine el proceso:
   - Se instalarán las dependencias necesarias
   - Se generará el ejecutable en la carpeta `dist\GimnasioDB`
3. Ejecuta la aplicación:
   - Navega a la carpeta `dist\GimnasioDB`
   - Haz doble clic en `GimnasioDB.exe`
   - Se abrirá un navegador web con la aplicación

## Estructura del Proyecto

- **app.py**: Punto de entrada de la aplicación
- **models.py**: Definición de modelos de datos
- **routes.py**: Rutas y funcionalidad principal
- **config.py**: Configuración de la aplicación
- **templates/**: Plantillas HTML
- **static/**: Archivos CSS, JS e imágenes
- **database.db**: Base de datos SQLite

## Planes y Precios

El sistema incluye los siguientes planes predefinidos:

- **Diario**: $5,000 COP (1 día)
- **Quincenal**: $35,000 COP (15 días)
- **Mensual**: $70,000 COP (30 días)
- **Dirigido**: $130,000 COP (30 días con entrenamiento dirigido)
- **Personalizado**: $250,000 COP (30 días con entrenador personal)

## Resolución de problemas

### Si hay errores al instalar dependencias

1. Asegúrate de tener permisos de administrador
   - En Windows: Ejecuta CMD como administrador (clic derecho > Ejecutar como administrador)
2. Actualiza pip
   ```
   python -m pip install --upgrade pip
   ```

### Si hay errores al generar el ejecutable

1. Asegúrate de tener instalado PyInstaller
   ```
   pip install pyinstaller
   ```
2. Verifica que todas las dependencias estén instaladas
   ```
   pip install -r requirements.txt
   ```

### Si el ejecutable no funciona

1. Intenta ejecutarlo desde la línea de comandos para ver mensajes de error
2. Asegúrate de que el firewall no esté bloqueando la aplicación
3. No muevas archivos individuales fuera de la carpeta `dist\GimnasioDB`

## Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT.
