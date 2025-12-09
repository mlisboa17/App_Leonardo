"""
Script para sincronizar os 4 dashboards para EC2
Windows compatible - Usar com Python 3.x
"""

import os
import sys
import subprocess
from pathlib import Path

def find_ssh_key():
    """Procura pela chave SSH em locais conhecidos"""
    possible_paths = [
        r"C:\Users\gabri\Downloads\r7_trade_key.pem",
        r"C:\Users\gabri\.ssh\r7_trade_key.pem",
        r"C:\Users\gabri\r7_trade_key.pem",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def sync_dashboard(local_file, ssh_key):
    """Sincroniza um dashboard para EC2"""
    
    if not os.path.exists(local_file):
        print(f"  ❌ Arquivo local não encontrado: {local_file}")
        return False
    
    if not os.path.exists(ssh_key):
        print(f"  ❌ Chave SSH não encontrada: {ssh_key}")
        return False
    
    # Configurações
    remote_user = "ubuntu"
    remote_host = "18.230.59.118"
    remote_path = "/home/ubuntu/App_Leonardo/frontend/pages/"
    
    # Montar comando SCP
    filename = os.path.basename(local_file)
    cmd = [
        "scp",
        "-i", ssh_key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        local_file,
        f"{remote_user}@{remote_host}:{remote_path}"
    ]
    
    try:
        print(f"  📤 Enviando {filename}...", end=" ", flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅")
            return True
        else:
            print(f"❌\n    Erro: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print("❌ (timeout)")
        return False
    except Exception as e:
        print(f"❌\n    {e}")
        return False

def main():
    """Função principal"""
    
    print("\n" + "="*70)
    print("🔄 Sincronizador de Dashboards - R7 Trading Bot")
    print("="*70 + "\n")
    
    # Encontrar chave SSH
    ssh_key = find_ssh_key()
    
    if not ssh_key:
        print("❌ Chave SSH não encontrada!")
        print("\n   Procurei em:")
        print("   - C:\\Users\\gabri\\Downloads\\r7_trade_key.pem")
        print("   - C:\\Users\\gabri\\.ssh\\r7_trade_key.pem")
        print("   - C:\\Users\\gabri\\r7_trade_key.pem")
        print("\n   Por favor, coloque a chave em um desses locais e tente novamente.")
        return False
    
    print(f"✅ Chave SSH encontrada: {ssh_key}\n")
    
    # Diretório do projeto
    project_dir = Path(__file__).parent
    
    # Dashboards a sincronizar
    dashboards = [
        "frontend/pages/01_positions_dashboard.py",
        "frontend/pages/02_capital_distribution.py",
        "frontend/pages/03_system_monitoring.py",
        "frontend/pages/04_pnl_detalhado.py",
    ]
    
    print("📋 Dashboards a sincronizar:\n")
    
    success_count = 0
    fail_count = 0
    
    for dashboard in dashboards:
        local_path = project_dir / dashboard
        status = sync_dashboard(str(local_path), ssh_key)
        
        if status:
            success_count += 1
        else:
            fail_count += 1
    
    # Resultado final
    print("\n" + "="*70)
    print(f"✅ Sucesso: {success_count}/{len(dashboards)}")
    if fail_count > 0:
        print(f"❌ Falhas: {fail_count}/{len(dashboards)}")
    print("="*70 + "\n")
    
    if success_count == len(dashboards):
        print("✨ Todos os dashboards sincronizados com sucesso!")
        print("\n📊 Acesse: http://18.230.59.118:8501\n")
        print("📋 Páginas disponíveis:")
        print("   1. 01_positions_dashboard.py - Posições com gráficos")
        print("   2. 02_capital_distribution.py - Distribuição de capital")
        print("   3. 03_system_monitoring.py - Monitoramento do sistema")
        print("   4. 04_pnl_detalhado.py (NOVO!) - PnL Dia/Mês/Geral")
        print("\n")
        return True
    else:
        print("⚠️ Alguns dashboards falharam. Verifique os erros acima.\n")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
