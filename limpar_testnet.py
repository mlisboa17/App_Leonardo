"""
Script para limpar TODOS os dados do Testnet
Prepara o sistema para producao com dinheiro real
"""
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")

def limpar_arquivos_json():
    """Limpa todos os arquivos JSON de dados"""
    arquivos = {
        "multibot_positions.json": {},
        "multibot_history.json": [],
        "all_trades_history.json": [],
        "daily_stats.json": {},
        "coordinator_stats.json": {},
        "dashboard_balances.json": {},
        "poupanca.json": {},
    }
    
    print("\n=== LIMPANDO ARQUIVOS JSON ===")
    for arquivo, conteudo_vazio in arquivos.items():
        caminho = DATA_DIR / arquivo
        if caminho.exists():
            # Backup antes de limpar
            backup_path = DATA_DIR / "backups" / f"{arquivo}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copia para backup
            with open(caminho, 'r') as f:
                dados_antigos = f.read()
            with open(backup_path, 'w') as f:
                f.write(dados_antigos)
            
            # Limpa arquivo
            with open(caminho, 'w') as f:
                json.dump(conteudo_vazio, f)
            print(f"  [OK] {arquivo} - limpo (backup salvo)")
        else:
            print(f"  [--] {arquivo} - nao existe")

def limpar_banco_dados():
    """Limpa as tabelas dos bancos de dados SQLite"""
    print("\n=== LIMPANDO BANCOS DE DADOS ===")
    
    # Lista de bancos de dados
    bancos = [
        DATA_DIR / "app_leonardo.db",
        DATA_DIR / "trading_history.db"
    ]
    
    for db_path in bancos:
        if db_path.exists():
            try:
                # Backup
                backup_path = DATA_DIR / "db_backups" / f"{db_path.name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                
                import shutil
                shutil.copy(db_path, backup_path)
                print(f"  [BACKUP] {db_path.name} -> {backup_path.name}")
                
                # Conecta e limpa tabelas
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Lista todas as tabelas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tabelas = cursor.fetchall()
                
                for (tabela,) in tabelas:
                    if tabela != 'sqlite_sequence':
                        cursor.execute(f"DELETE FROM {tabela};")
                        print(f"  [OK] {db_path.name} -> Tabela '{tabela}' limpa")
                
                conn.commit()
                conn.close()
                print(f"  [OK] {db_path.name} - todas as tabelas limpas")
                
            except Exception as e:
                print(f"  [ERRO] {db_path.name}: {e}")
        else:
            print(f"  [--] {db_path.name} - nao existe")

def limpar_ai_data():
    """Limpa dados da IA"""
    print("\n=== LIMPANDO DADOS DA IA ===")
    
    ai_dir = DATA_DIR / "ai"
    if ai_dir.exists():
        arquivos_ai = {
            "ai_state.json": {},
            "completed_trades.json": [],
            "metadata.json": {}
        }
        
        for arquivo, conteudo in arquivos_ai.items():
            caminho = ai_dir / arquivo
            if caminho.exists():
                with open(caminho, 'w') as f:
                    json.dump(conteudo, f)
                print(f"  [OK] ai/{arquivo} - limpo")
    
    # Limpa modelos da IA
    ai_models = DATA_DIR / "ai_models"
    if ai_models.exists():
        insights_path = ai_models / "insights.json"
        if insights_path.exists():
            with open(insights_path, 'w') as f:
                json.dump({}, f)
            print(f"  [OK] ai_models/insights.json - limpo")

def verificar_config():
    """Verifica se config esta em modo producao"""
    print("\n=== VERIFICANDO CONFIGURACAO ===")
    
    config_path = Path("config/bots_config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            conteudo = f.read()
        
        if "testnet: false" in conteudo:
            print("  [OK] Modo PRODUCAO ativo (testnet: false)")
        else:
            print("  [ATENCAO] Modo TESTNET ainda ativo!")
            print("  Altere 'testnet: true' para 'testnet: false' no config/bots_config.yaml")

def main():
    print("=" * 60)
    print(" LIMPEZA COMPLETA - REMOVER DADOS DO TESTNET")
    print("=" * 60)
    print(f"\nData: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Este script remove TODOS os dados de teste/simulacao")
    print("Backups serao criados antes de limpar")
    
    input("\nPressione ENTER para continuar ou Ctrl+C para cancelar...")
    
    limpar_arquivos_json()
    limpar_banco_dados()
    limpar_ai_data()
    verificar_config()
    
    print("\n" + "=" * 60)
    print(" LIMPEZA CONCLUIDA!")
    print("=" * 60)
    print("\nO sistema esta pronto para operar com dinheiro real.")
    print("Backups foram salvos em data/backups/ e data/db_backups/")


if __name__ == "__main__":
    main()
