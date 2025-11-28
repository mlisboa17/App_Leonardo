"""
Script para iniciar o Bot e o Dashboard simultaneamente
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def main():
    print("=" * 60)
    print("🚀 Iniciando App Leonardo - Trading Bot + Dashboard")
    print("=" * 60)
    
    # Caminho do projeto
    project_dir = Path(__file__).parent
    
    # Inicia o servidor Django em background
    print("\n📊 Iniciando Dashboard Web...")
    django_process = subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver'],
        cwd=project_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
    )
    
    # Aguarda servidor iniciar
    print("⏳ Aguardando servidor Django inicializar...")
    time.sleep(3)
    
    print("\n✅ Dashboard disponível em: http://127.0.0.1:8000/")
    print("\n🤖 Iniciando Bot de Trading...")
    print("=" * 60)
    print("\nPressione Ctrl+C para parar ambos (bot e dashboard)\n")
    
    # Inicia o bot (roda no console atual)
    try:
        bot_process = subprocess.run(
            [sys.executable, 'main.py'],
            cwd=project_dir
        )
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupção detectada...")
    finally:
        # Para o servidor Django
        print("\n🛑 Parando Dashboard...")
        django_process.terminate()
        django_process.wait()
        print("✅ Todos os processos encerrados com segurança")

if __name__ == "__main__":
    main()
