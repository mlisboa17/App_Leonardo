"""
Script para sincronizar dashboards para EC2 (Windows compatible)
Usa SCP nativo do Windows para enviar arquivos
"""

import os
import subprocess
import sys
from pathlib import Path

# Configurações
REMOTE_USER = "ubuntu"
REMOTE_HOST = "18.230.59.118"
SSH_KEY = r"C:\Users\gabri\Downloads\r7_trade_key.pem"
REMOTE_PATH = "/home/ubuntu/App_Leonardo"

# Arquivo a sincronizar
LOCAL_FILE = r"frontend\pages\04_pnl_detalhado.py"

def sync_files():
    """Sincroniza arquivos para EC2"""
    
    # Verificar se arquivo existe
    if not os.path.exists(LOCAL_FILE):
        print(f"❌ Arquivo não encontrado: {LOCAL_FILE}")
        return False
    
    # Verificar se SSH key existe
    if not os.path.exists(SSH_KEY):
        print(f"❌ SSH key não encontrada: {SSH_KEY}")
        return False
    
    try:
        print("🔄 Sincronizando dashboards para EC2...")
        print(f"📤 Enviando: {LOCAL_FILE}")
        
        # Comando SCP
        cmd = [
            "scp",
            "-i", SSH_KEY,
            LOCAL_FILE,
            f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PATH}/frontend/pages/"
        ]
        
        # Executar
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dashboard sincronizado com sucesso!")
            print(f"📊 Acesse: http://{REMOTE_HOST}:8501")
            print("\n📋 Páginas disponíveis:")
            print("  - 04_pnl_detalhado.py (NOVA!) - PnL Dia/Mês/Geral com diagnóstico")
            print("  - 01_positions_dashboard.py - Posições com gráficos")
            print("  - 02_capital_distribution.py - Distribuição de capital")
            print("  - 03_system_monitoring.py - Monitoramento do sistema")
            return True
        else:
            print(f"❌ Erro ao sincronizar: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Sincronizador de Dashboards - R7 Trading Bot")
    print("=" * 60)
    
    if sync_files():
        print("\n✅ Sincronização concluída!")
    else:
        print("\n❌ Sincronização falhou!")
        sys.exit(1)
