"""
Script para criar executável do App Leonardo Bot v2
"""
import subprocess
import os
import shutil

def build():
    print("🔨 Criando executável do App Leonardo Bot v2...")
    
    # Comando PyInstaller
    cmd = [
        "venv_new\\Scripts\\pyinstaller.exe",
        "--onefile",
        "--console",
        "--name", "AppLeonardo_Bot_v2",
        "--add-data", "config;config",
        "--add-data", "src;src",
        "--hidden-import", "ccxt",
        "--hidden-import", "pandas",
        "--hidden-import", "python-dotenv",
        "--hidden-import", "pyyaml",
        "--hidden-import", "pandas_ta",
        "--hidden-import", "requests",
        "--hidden-import", "aiohttp",
        "--clean",
        "main.py"
    ]
    
    print(f"Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print("\n✅ Executável criado com sucesso!")
        print("📁 Localização: dist/AppLeonardo_Bot_v2.exe")
        
        # Copia arquivos necessários para dist
        os.makedirs("dist/config", exist_ok=True)
        os.makedirs("dist/data", exist_ok=True)
        
        if os.path.exists("config/config.yaml"):
            shutil.copy("config/config.yaml", "dist/config/")
            print("📋 config.yaml copiado")
        
        if os.path.exists(".env"):
            shutil.copy(".env", "dist/")
            print("🔑 .env copiado")
            
        print("\n🚀 Para usar:")
        print("   1. Vá para a pasta 'dist'")
        print("   2. Certifique-se que .env está configurado")
        print("   3. Execute AppLeonardo_Bot_v2.exe")
    else:
        print("❌ Erro ao criar executável")

if __name__ == "__main__":
    build()
