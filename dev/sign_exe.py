#!/usr/bin/env python
"""
Script para firmar digitalmente el ejecutable GimnasioDB.exe
Esto ayuda a reducir los falsos positivos en antivirus.

Desarrollado por: YEIFRAN HERNANDEZ
NEURALJIRA_DEV - Visión inteligente para gestión de gimnasios
"""
import os
import sys
import subprocess
import datetime
import tempfile
import platform

def crear_certificado():
    """Crea un certificado autofirmado para firmar el ejecutable"""
    print("[INFO] Creando certificado autofirmado...")
    
    # Verificar si OpenSSL está instalado
    try:
        subprocess.run(['openssl', 'version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] OpenSSL no está instalado o no se encuentra en el PATH.")
        print("[INFO] Por favor, instale OpenSSL o asegúrese de que esté en el PATH.")
        return None
    
    # Crear directorio para certificados si no existe
    cert_dir = 'certs'
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    
    cert_name = 'neuraljiradev_cert'
    key_path = os.path.join(cert_dir, f'{cert_name}.key')
    csr_path = os.path.join(cert_dir, f'{cert_name}.csr')
    cert_path = os.path.join(cert_dir, f'{cert_name}.crt')
    pfx_path = os.path.join(cert_dir, f'{cert_name}.pfx')
    
    # Verificar si ya existe el certificado PFX
    if os.path.exists(pfx_path):
        print(f"[INFO] Usando certificado existente: {pfx_path}")
        return pfx_path
    
    # Crear archivo de configuración para OpenSSL
    config_content = """
    [req]
    default_bits = 2048
    prompt = no
    default_md = sha256
    distinguished_name = dn

    [dn]
    C=CO
    ST=Bogota
    L=Bogota
    O=NEURALJIRA_DEV
    OU=Software Development
    emailAddress=neuraljiradev@example.com
    CN=YEIFRAN HERNANDEZ
    """
    
    config_path = os.path.join(cert_dir, 'openssl.cnf')
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    try:
        # 1. Generar clave privada
        subprocess.run([
            'openssl', 'genrsa',
            '-out', key_path,
            '2048'
        ], check=True)
        
        # 2. Generar solicitud de firma de certificado (CSR)
        subprocess.run([
            'openssl', 'req',
            '-new',
            '-key', key_path,
            '-out', csr_path,
            '-config', config_path
        ], check=True)
        
        # 3. Generar certificado autofirmado
        subprocess.run([
            'openssl', 'x509',
            '-req',
            '-days', '365',
            '-in', csr_path,
            '-signkey', key_path,
            '-out', cert_path
        ], check=True)
        
        # 4. Convertir a formato PFX
        subprocess.run([
            'openssl', 'pkcs12',
            '-export',
            '-out', pfx_path,
            '-inkey', key_path,
            '-in', cert_path,
            '-passout', 'pass:neuraljiradev'
        ], check=True)
        
        print(f"[INFO] Certificado creado exitosamente: {pfx_path}")
        return pfx_path
    
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error al crear certificado: {e}")
        return None

def firmar_ejecutable(cert_path):
    """Firma digitalmente el ejecutable con un certificado"""
    if not cert_path or not os.path.exists(cert_path):
        print("[ERROR] No se pudo encontrar el certificado para firmar.")
        return False
    
    exe_path = os.path.abspath('dist/GimnasioDB.exe')
    if not os.path.exists(exe_path):
        print(f"[ERROR] No se encontró el ejecutable: {exe_path}")
        return False
    
    print(f"[INFO] Firmando ejecutable: {exe_path}")
    
    # Verificar si signtool está instalado (Windows SDK)
    signtool_path = None
    possible_paths = [
        r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe",
        r"C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe",
        r"C:\Program Files (x86)\Windows Kits\10\bin\signtool.exe"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            signtool_path = path
            break
    
    if not signtool_path:
        print("[ERROR] No se encontró signtool. Por favor, instale Windows SDK.")
        print("[INFO] Puede descargar Windows SDK desde: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/")
        return False
    
    try:
        # Firmar el ejecutable con signtool
        subprocess.run([
            signtool_path, 'sign',
            '/f', cert_path,
            '/p', 'neuraljiradev',
            '/d', 'GimnasioDB - Sistema de gestión para gimnasios',
            '/du', 'https://neuraljiradev.example.com',
            '/t', 'http://timestamp.sectigo.com',
            exe_path
        ], check=True)
        
        print(f"[INFO] Ejecutable firmado exitosamente: {exe_path}")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error al firmar ejecutable: {e}")
        return False

def main():
    """Función principal"""
    print("="*60)
    print("FIRMADOR DE EJECUTABLES - NEURALJIRA_DEV")
    print("="*60)
    
    if platform.system() != 'Windows':
        print("[ERROR] Este script solo funciona en Windows.")
        sys.exit(1)
    
    # Verificar que existe el ejecutable
    exe_path = os.path.abspath('dist/GimnasioDB.exe')
    if not os.path.exists(exe_path):
        print(f"[ERROR] No se encontró el ejecutable: {exe_path}")
        print("[INFO] Primero debe compilar la aplicación con empaquetar_exe.py")
        sys.exit(1)
    
    # Crear certificado para firma
    cert_path = crear_certificado()
    
    # Firmar el ejecutable
    if cert_path:
        success = firmar_ejecutable(cert_path)
        if success:
            print("\n[ÉXITO] El ejecutable ha sido firmado correctamente.")
            print("[INFO] Esto debería reducir las detecciones falsas por antivirus.")
            print("[INFO] Si aún hay problemas, configure una excepción en su antivirus.")
        else:
            print("\n[ERROR] No se pudo firmar el ejecutable.")
    else:
        print("\n[ERROR] No se pudo crear o encontrar un certificado válido.")
    
    print("\nProceso finalizado. Presione cualquier tecla para salir...")
    input()

if __name__ == '__main__':
    main() 