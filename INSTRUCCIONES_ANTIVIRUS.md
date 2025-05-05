# Instrucciones para configurar excepciones en antivirus

Si su antivirus detecta GimnasioDB como un posible virus o malware, esto es un **falso positivo**. Un falso positivo ocurre cuando un programa legítimo es incorrectamente identificado como malicioso por un antivirus.

**IMPORTANTE:** GimnasioDB es software seguro desarrollado por YEIFRAN HERNANDEZ (NEURALJIRA_DEV). No contiene código malicioso ni realiza acciones dañinas en su sistema.

## ¿Por qué ocurre esto?

Los antivirus a veces marcan aplicaciones empaquetadas con PyInstaller como sospechosas debido a:
- Técnicas de compresión similares a las usadas por algunos malwares
- Código autogenerado que puede parecer sospechoso para los sistemas de heurística
- Falta de certificados de firma digital reconocidos

## Cómo agregar excepciones en Avast Antivirus

1. Abra Avast Antivirus.
2. Haga clic en "Menú" en la esquina superior derecha.
3. Seleccione "Configuración".
4. Haga clic en "Protección".
5. Seleccione "Escudo de archivos".
6. Haga clic en "Excepciones".
7. Haga clic en "Agregar excepción".
8. Navegue hasta la ubicación donde se encuentra GimnasioDB.exe.
9. Seleccione el archivo y haga clic en "Abrir".
10. Haga clic en "Agregar excepción" para confirmar.

## Cómo agregar excepciones en Windows Defender

1. Abra "Seguridad de Windows" (busque en la barra de búsqueda de Windows).
2. Haga clic en "Protección contra virus y amenazas".
3. Haga clic en "Administrar configuración" bajo "Configuración de protección contra virus y amenazas".
4. Desplácese hacia abajo hasta "Exclusiones".
5. Haga clic en "Agregar o quitar exclusiones".
6. Haga clic en "Agregar una exclusión".
7. Seleccione "Archivo".
8. Navegue hasta la ubicación de GimnasioDB.exe y selecciónelo.
9. Haga clic en "Abrir" para confirmar.

## Cómo agregar excepciones en otros antivirus

### Para McAfee:
1. Abra el panel de McAfee.
2. Haga clic en "Configuración" (icono de engranaje).
3. Haga clic en "Protección en tiempo real".
4. Seleccione "Agregar archivo" bajo "Elementos excluidos".
5. Navegue hasta GimnasioDB.exe y selecciónelo.
6. Haga clic en "Abrir" para confirmar.

### Para Kaspersky:
1. Abra Kaspersky.
2. Vaya a "Configuración".
3. Seleccione "Protección".
4. Haga clic en "Antivirus de archivos".
5. Haga clic en "Administrar exclusiones".
6. Haga clic en "Agregar".
7. Seleccione "Archivo o carpeta".
8. Navegue hasta GimnasioDB.exe y selecciónelo.
9. Haga clic en "Agregar" para confirmar.

## Verificación de seguridad

Para mayor tranquilidad, puede verificar que el software es seguro de las siguientes maneras:

1. **Inspeccione el código fuente**: El código fuente está disponible para revisión.
2. **Verifique los hash MD5/SHA**: Compare los hash del ejecutable con los oficiales publicados.
3. **Utilice múltiples escáneres**: Puede verificar el archivo en servicios como VirusTotal.

## Soporte técnico

Si tiene preguntas adicionales o necesita asistencia, contacte a:

YEIFRAN HERNANDEZ
NEURALJIRA_DEV
Email: neuraljiradev@example.com 