# GimnasioDB - Sistema de Gestión para Gimnasios

Sistema de gestión para gimnasios con funcionalidades para administración de socios, control de pagos, seguimiento de medidas corporales, asistencias y más.

## Estructura del Proyecto

La estructura del proyecto ha sido organizada para separar claramente el código de producción del código de desarrollo:

```
GimnasioDB/
├── app_launcher.py     # Punto de entrada principal de la aplicación
├── models.py           # Modelos de datos (SQLAlchemy)
├── config.py           # Configuración global
├── requirements.txt    # Dependencias para producción
├── ejecutar_app.bat    # Script para ejecutar la aplicación
├── ejecutar_windows.bat # Script para ejecutar en Windows
├── templates/          # Plantillas HTML
├── static/             # Archivos estáticos (CSS, JS, imágenes)
├── routes/             # Rutas y endpoints de la aplicación
└── dev/                # Archivos y herramientas de desarrollo
    ├── empaquetar_optimizado.bat   # Script para empaquetar la aplicación
    ├── GimnasioDB_optimizado.spec  # Configuración de PyInstaller optimizada
    ├── reorganizacion_proyecto.py  # Script para reorganizar el proyecto
    ├── actualizar_db.py            # Herramienta para actualizar la BD
    ├── empaquetar_exe.py           # Script para empaquetar (antigua versión)
    ├── test/                       # Pruebas automatizadas
    └── ...                         # Otros archivos de desarrollo
```

## Requisitos

- Python 3.8 o superior
- Flask y sus dependencias (ver requirements.txt)
- Base de datos SQLite (generada automáticamente)

## Instalación

1. Clonar el repositorio
2. Instalar dependencias: `pip install -r requirements.txt`
3. Ejecutar la aplicación: `python app_launcher.py`

También puede usar los scripts incluidos para facilitar la ejecución:

- En Windows: `ejecutar_windows.bat` o `ejecutar_app.bat`

## Desarrollo

Para tareas de desarrollo, utilice los scripts en la carpeta `dev/`:

- **Empaquetar la aplicación**:

  ```
  cd dev
  empaquetar_optimizado.bat
  ```

- **Reorganizar el proyecto**:

  ```
  cd dev
  python reorganizacion_proyecto.py
  ```

- **Actualizar la estructura de la base de datos**:
  ```
  cd dev
  python actualizar_db.py
  ```

## Empaquetado

Para generar un ejecutable para distribución:

1. Navegar a la carpeta `dev/`
2. Ejecutar `empaquetar_optimizado.bat`
3. Seguir las instrucciones en pantalla
4. El ejecutable se generará en la carpeta `dist/`

## Notas de Uso

- Al ejecutar por primera vez se creará automáticamente un usuario administrador (usuario: `admin`, contraseña: `admin123`)
- Se recomienda cambiar la contraseña del administrador inmediatamente

## Características Principales

- **Gestión de Usuarios**: Registro, edición y seguimiento de miembros del gimnasio
- **Control de Productos**: Inventario, precios y categorías
- **Sistema de Ventas**: Registro de ventas con múltiples métodos de pago
- **Reportes**: Informes de ventas, usuarios y actividades
- **Interfaz Responsiva**: Diseño adaptado a múltiples dispositivos

## Instalación

### Instalación para Desarrollo

1. Clona el repositorio:

```bash
git clone https://github.com/tuusuario/gymtrack.git
cd gymtrack
```

2. Crea un entorno virtual e instala las dependencias:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Ejecuta la aplicación en modo desarrollo:

```bash
python app_launcher.py --dev
```

### Instalación para Producción

1. Clona el repositorio y configura el entorno:

```bash
git clone https://github.com/tuusuario/gymtrack.git
cd gymtrack
pip install -r requirements.txt
```

2. Ejecuta la aplicación:

```bash
python app_launcher.py
```

## Empaquetado para Distribución

Para crear un ejecutable independiente, usa el script `empaquetar_exe.py`:

```bash
python empaquetar_exe.py
```

### Opciones de Empaquetado

- `--sign`: Firma digitalmente el ejecutable (requiere certificado)
- `--no-backup`: No crea respaldo de la base de datos
- `--help`: Muestra la ayuda del script

## Uso

### Modo de Desarrollo

```bash
python app_launcher.py --dev
```

### Modo de Producción

```bash
python app_launcher.py
```

### Ejecutable Independiente

1. Descarga el archivo `GimnasioDB.exe`
2. Ejecuta el archivo directamente
3. La aplicación abrirá automáticamente el navegador

## Contribuir

1. Haz un fork del repositorio
2. Crea una rama para tu función: `git checkout -b nueva-funcionalidad`
3. Haz commit a tus cambios: `git commit -m 'Añadir nueva funcionalidad'`
4. Haz push a la rama: `git push origin nueva-funcionalidad`
5. Envía un pull request

## Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT.

## Contacto

- Desarrollador: Yeifran Hernandez
- Email: neuraljiradev@example.com

## Distribución de la aplicación

### Cómo crear un ejecutable para distribución

Este proyecto incluye un script para generar un ejecutable autónomo que puede distribuirse fácilmente a otros usuarios sin necesidad de instalar Python o las dependencias:

1. Asegúrate de tener todas las dependencias instaladas:

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Ejecuta el script de empaquetado:

   ```bash
   # En Linux/macOS
   python empaquetar_exe.py

   # En Windows
   python empaquetar_exe.py
   ```

3. El ejecutable y los archivos de distribución se crearán en la carpeta `dist/` y también se generará un archivo ZIP con la distribución completa en la raíz del proyecto.

### Opciones al crear el ejecutable

El script `empaquetar_exe.py` soporta varias opciones:

- `--help`: Muestra la ayuda del script
- `--sign`: Firma el ejecutable después de crearlo (si tienes configurado el script `sign_exe.py`)
- `--no-backup`: No crea respaldo de la base de datos
- `--include-db`: Incluye la base de datos actual en la distribución

### Empaquetado específico para Windows

Para crear un ejecutable específicamente para Windows:

1. Desde un sistema Windows:

   ```
   python empaquetar_exe.py
   ```

2. El ejecutable se creará como `dist/GimnasioDB.exe` y se generará un archivo ZIP con formato `GimnasioDB_windows_[FECHA].zip`

3. Para incluir la base de datos actual en la distribución:
   ```
   python empaquetar_exe.py --include-db
   ```

### Distribución a usuarios finales

Para compartir la aplicación con usuarios finales:

1. Comparte el archivo ZIP generado por el script de empaquetado (`GimnasioDB_[PLATAFORMA]_[FECHA].zip`)
2. Los usuarios solo necesitan extraer el ZIP y ejecutar el archivo `GimnasioDB` (o `GimnasioDB.exe` en Windows)
3. La aplicación se abrirá automáticamente en su navegador predeterminado

### Posibles problemas y soluciones

- **Alertas de antivirus**: Algunos antivirus pueden marcar el ejecutable como sospechoso. Esto es normal para ejecutables empaquetados con PyInstaller. Puedes:

  - Añadir una exclusión en el antivirus
  - Considerar firmar digitalmente el ejecutable (opción `--sign`)
  - Distribuir a los usuarios el archivo `INSTRUCCIONES_ANTIVIRUS.md`

- **Errores de ejecución**: Si el ejecutable no se abre, asegúrate de que los usuarios tienen los permisos de ejecución correctos:

  - Windows: No suele requerir permisos especiales
  - Linux: `chmod +x GimnasioDB`
  - macOS: `chmod +x GimnasioDB`

- **Base de datos**: El ejecutable crea una base de datos nueva si no existe. Si deseas distribuir una base de datos inicial, usa la opción `--include-db` al empaquetar o colócala junto al ejecutable.

## Empaquetado para múltiples sistemas operativos

Esta aplicación ahora puede ser empaquetada para diferentes sistemas operativos (Windows, Linux y macOS) sin importar en qué sistema operativo te encuentres.

### Usando los scripts asistentes

Para facilitar el proceso de empaquetado, se han incluido scripts que automatizan el proceso:

**En Windows:**

1. Ejecuta `empaquetar_multisistema.bat`
2. Selecciona la opción deseada del menú

**En Linux/macOS:**

1. Ejecuta `./empaquetar_multisistema.sh`
2. Selecciona la opción deseada del menú

### Usando directamente el script de empaquetado

También puedes usar directamente el script `empaquetar_app.py` con las siguientes opciones:

```
python empaquetar_app.py [opciones]

Opciones disponibles:
  --help        : Muestra la ayuda
  --no-backup   : No crea respaldo de la base de datos
  --include-db  : Incluye la base de datos actual en la distribución
  --windows     : Crea un ejecutable para Windows
  --linux       : Crea un ejecutable para Linux
  --macos       : Crea un ejecutable para macOS
  --all         : Crea ejecutables para todas las plataformas soportadas
```

Ejemplos:

- Para crear un ejecutable Windows: `python empaquetar_app.py --windows`
- Para crear ejecutables para todos los sistemas: `python empaquetar_app.py --all`
- Para incluir la base de datos: `python empaquetar_app.py --windows --include-db`

Los ejecutables generados estarán disponibles en la carpeta `dist/` con nombres específicos para cada plataforma.
