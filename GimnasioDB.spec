# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('database.db', '.'),
        ('config.py', '.'),
        ('models.py', '.'),
        ('routes.py', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_sqlalchemy',
        'sqlalchemy',
        'jinja2',
        'werkzeug',
        'itsdangerous',
        'click',
        'datetime',
        'random',
        'json',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GimnasioDB',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/img/favicon.ico',
) 