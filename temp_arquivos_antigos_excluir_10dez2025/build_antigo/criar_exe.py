#!/usr/bin/env python3
"""
Script para criar os executáveis do App Leonardo
"""
import subprocess
import sys
import os

# Configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# Arquivos para criar executáveis
APPS = [
    {
        "script": "main.py",
        "name": "AppLeonardo_Bot",
        "console": True
    },
    {
        "script": "frontend/dashboard_saldo.py",
        "name": "AppLeonardo_Dashboard", 
        "console": True
    }
]

# Exclusões para reduzir tamanho (bibliotecas não usadas)
EXCLUDES = [
    "torch",
    "torchvision", 
    "torchaudio",
    "tensorflow",
    "keras",
    "matplotlib",
    "PIL",
    "cv2",
    "sklearn",
    "scipy.spatial",
    "scipy.ndimage",
    "scipy.signal",
    "tkinter",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "IPython",
    "notebook",
    "jupyter",
    "test",
    "tests",
    "testing"
]

# Hidden imports necessários
HIDDEN_IMPORTS = [
    "ccxt",
    "pandas",
    "pandas_ta",
    "numpy",
    "yaml",
    "dotenv",
    "sqlite3",
    "json",
    "datetime",
    "threading",
    "queue"
]

def build_exe(script: str, name: str, console: bool = True):
    """Cria executável para um script"""
    
    print(f"\n{'='*60}")
    print(f"🔨 Criando: {name}")
    print(f"   Script: {script}")
    print(f"{'='*60}\n")
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--name", name,
        "--noconfirm",
        "--clean"
    ]
    
    # Modo console ou janela
    if console:
        cmd.append("--console")
    else:
        cmd.append("--windowed")
    
    # Adicionar exclusões
    for exclude in EXCLUDES:
        cmd.extend(["--exclude-module", exclude])
    
    # Adicionar hidden imports
    for hidden in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hidden])
    
    # Adicionar o script
    cmd.append(script)
    
    print(f"Comando: {' '.join(cmd[:10])}...")
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✅ {name} criado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao criar {name}: {e}")
        return False

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║       APP LEONARDO - CRIADOR DE EXECUTÁVEIS               ║
╠═══════════════════════════════════════════════════════════╣
║  Este script cria os executáveis do Bot e Dashboard       ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    success_count = 0
    
    for app in APPS:
        if build_exe(app["script"], app["name"], app.get("console", True)):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Resultado: {success_count}/{len(APPS)} executáveis criados")
    print(f"{'='*60}")
    
    if success_count == len(APPS):
        print("""
✅ SUCESSO! Executáveis criados em: dist/

📁 Arquivos criados:
   - dist/AppLeonardo_Bot.exe
   - dist/AppLeonardo_Dashboard.exe

🚀 Para iniciar:
   1. Copie a pasta 'config', 'data' e 'logs' para junto do .exe
   2. Crie o arquivo .env com suas credenciais
   3. Execute AppLeonardo_Bot.exe
   4. Execute AppLeonardo_Dashboard.exe
   5. Acesse http://localhost:8050
        """)
    else:
        print("\n⚠️ Alguns executáveis não foram criados. Verifique os erros acima.")

if __name__ == "__main__":
    main()
