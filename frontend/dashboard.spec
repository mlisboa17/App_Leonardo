# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file para Dashboard

block_cipher = None

# Arquivos de dados a incluir
datas = [
    ('../config/config.yaml', 'config'),
    ('../config/.env.example', 'config'),
]

# Imports ocultos necessários
hidden_imports = [
    'dash',
    'dash_bootstrap_components',
    'dash.dcc',
    'dash.html',
    'plotly',
    'plotly.graph_objects',
    'plotly.express',
    'ccxt',
    'pandas',
    'numpy',
    'flask',
    'werkzeug',
    'dotenv',
]

a = Analysis(
    ['dashboard_saldo.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AppLeonardo_Dashboard',
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
)
