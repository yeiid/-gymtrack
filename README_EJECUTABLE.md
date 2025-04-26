# Instrucciones para Crear y Usar el Ejecutable de GimnasioDB

Este documento explica cómo crear y utilizar el ejecutable de GimnasioDB para Windows, que permitirá ejecutar la aplicación con un solo clic sin necesidad de instalar Python ni sus dependencias.

## Requisitos Previos

- Windows 10 o superior
- Python instalado (solo para la creación del ejecutable)
- PyInstaller (`pip install pyinstaller`)
- PyWin32 (`pip install pywin32`) - Opcional, para crear acceso directo

## Pasos para Crear el Ejecutable

1. **Preparar el Entorno**: 
   - Asegúrate de tener todas las dependencias del proyecto instaladas:
   ```
   pip install -r requirements.txt
   ```

2. **Probar la Aplicación** (recomendado antes de empaquetar):
   - Ejecuta el script de prueba para verificar que todo funciona correctamente:
   ```
   python probar_app.py
   ```
   - Confirma que la aplicación se abre en el navegador y funciona correctamente
   - Cierra la aplicación utilizando el botón "Cerrar" en la barra de navegación

3. **Ejecutar el Script de Empaquetado**:
   - Abre una terminal en la carpeta del proyecto
   - Ejecuta el siguiente comando:
   ```
   python empaquetar_exe.py
   ```
   - El proceso puede tomar varios minutos

4. **Resultado**:
   - El ejecutable se creará en la carpeta `dist/` (como `GimnasioDB.exe`)
   - Se intentará crear un acceso directo en tu escritorio (requiere pywin32)

## Uso del Ejecutable

1. **Ejecutar la Aplicación**:
   - Haz doble clic en `GimnasioDB.exe`
   - Se abrirá automáticamente una ventana del navegador con la aplicación
   - Si el navegador no se abre automáticamente, navega a `http://127.0.0.1:5000`

2. **Cerrar la Aplicación**:
   - Haz clic en el botón "Cerrar" en la barra de navegación
   - Confirma que deseas cerrar la aplicación

## Solución de Problemas

- **El navegador no se abre**: Abre manualmente cualquier navegador e ingresa a `http://127.0.0.1:5000`
- **Error "Puerto en uso"**: Asegúrate de que no haya otra instancia de la aplicación ejecutándose
- **Fallos al cerrar la aplicación**: Si la aplicación no se cierra correctamente, busca el proceso GimnasioDB.exe en el Administrador de tareas y finalízalo

## Distribuir la Aplicación

Para compartir la aplicación con otros usuarios:
1. Copia el ejecutable `GimnasioDB.exe` y todos los archivos generados en la carpeta `dist/`
2. Comprime estos archivos en un ZIP
3. Los usuarios solo necesitan extraer el ZIP y hacer doble clic en `GimnasioDB.exe`

*Nota: El ejecutable contiene todos los archivos y dependencias necesarios para funcionar en cualquier PC con Windows, sin necesidad de instalar Python.* 