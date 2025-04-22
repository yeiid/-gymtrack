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
- Navegador web moderno

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
   python app.py
   ```
6. Abrir el navegador en http://127.0.0.1:5000

### Método 2: Usando el Ejecutable (después de compilar)

1. Ejecute el archivo GimnasioDB (o GimnasioDB.exe en Windows)
2. Se abrirá automáticamente un navegador con la aplicación
3. Si el navegador no se abre, ingrese a http://127.0.0.1:5000 en su navegador

## Compilar el Ejecutable

Para crear un ejecutable independiente que pueda ejecutarse sin necesidad de instalar Python:

1. Asegúrese de tener PyInstaller instalado:
   ```
   pip install pyinstaller
   ```
2. Ejecute el script de construcción:
   ```
   python build_exe.py
   ```
3. El ejecutable se generará en la carpeta `dist`

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

## Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT.
