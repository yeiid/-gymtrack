# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates'), ('static', 'static'), ('database.db', '.'), ('config.py', '.')],
    hiddenimports=[
        'sqlalchemy.sql.default_comparator', 
        'sqlalchemy.ext.baked', 
        'flask_sqlalchemy',
        'werkzeug.serving',
        'werkzeug.debug',
        'werkzeug.debug.console',
        'werkzeug.middleware',
        'werkzeug.middleware.dispatcher',
        'werkzeug._internal',
        'webbrowser',
        'logging',
        'jinja2.ext',
        'click',
        'threading',
        'signal',
        'flask.cli',
        'argparse'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GimnasioDB',
    icon='static/img/favicon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
