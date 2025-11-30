# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file para App Leonardo Bot

block_cipher = None

# Arquivos de dados a incluir
datas = [
    ('config/config.yaml', 'config'),
    ('config/.env.example', 'config'),
    ('data/crypto_profiles.json', 'data'),
]

# Imports ocultos necessários
hidden_imports = [
    'ccxt',
    'pandas',
    'numpy',
    'yaml',
    'dotenv',
    'pandas_ta',
    'logging',
    'sqlite3',
    'json',
    'csv',
]

a = Analysis(
    ['main.py'],
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
    name='AppLeonardo_Bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # True para ver logs no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
