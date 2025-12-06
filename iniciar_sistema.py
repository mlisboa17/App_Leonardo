# -*- coding: utf-8 -*-
"""
App Leonardo v3.0 - Script de Inicialização Completa
====================================================

Este script inicializa todos os serviços do sistema:
1. Banco de dados SQLite
2. Serviço de backup automático
3. Sistema de IA
4. Bots de trading

Execute com: python iniciar_sistema.py
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/sistema.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('SistemaInicio')


def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    required = [
        'ccxt',
        'pandas',
        'numpy',
        'schedule',
        'sklearn',
        'yaml',
        'requests'
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        logger.error(f"❌ Pacotes faltando: {missing}")
        logger.info("Execute: pip install -r requirements.txt")
        return False
    
    return True


def inicializar_banco_dados():
    """Inicializa o banco de dados"""
    from src.database import get_db_manager
    
    logger.info("🗄️ Inicializando banco de dados...")
    db = get_db_manager()
    
    # Verificar integridade
    stats = db.get_statistics()
    logger.info(f"  - Trades: {stats['trades']['total']}")
    logger.info(f"  - Bots: {stats['bots']['total']}")
    logger.info(f"  - Tamanho: {stats['db_size_mb']:.2f} MB")
    
    return db


def inicializar_backup_service():
    """Inicializa o serviço de backup"""
    from src.database import get_backup_service
    
    logger.info("💾 Inicializando serviço de backup...")
    
    # Backup diário às 03:00
    backup_service = get_backup_service(backup_time="03:00")
    backup_service.start()
    
    status = backup_service.get_status()
    logger.info(f"  - Backup diário: {status['backup_time']}")
    logger.info(f"  - Total backups: {status['total_backups']}")
    
    return backup_service


def inicializar_ia():
    """Inicializa o sistema de IA"""
    from src.ai import get_ai_manager
    
    logger.info("🤖 Inicializando sistema de IA...")
    
    ai = get_ai_manager()
    ai.start_background_tasks()
    
    data = ai.get_dashboard_data()
    logger.info(f"  - Auto-adjust: {data['status']['auto_adjust_enabled']}")
    logger.info(f"  - Learning: {data['status']['learning_enabled']}")
    
    return ai


def criar_backup_inicial():
    """Cria backup inicial do sistema"""
    from src.database import get_backup_service
    
    logger.info("📦 Criando backup inicial...")
    
    service = get_backup_service()
    result = service.force_backup("full")  # Usar full ao invés de startup
    
    if result.get('success'):
        logger.info(f"  ✅ Backup criado: {result.get('size_mb', 'N/A')} MB ({result.get('files_backed_up', 0)} arquivos)")
    else:
        logger.warning(f"  ⚠️ Erro no backup: {result.get('errors', [])}")


def mostrar_status():
    """Mostra status geral do sistema"""
    from src.database import get_db_manager, get_backup_service
    from src.ai import get_ai_manager
    
    print("\n" + "=" * 60)
    print("📊 STATUS DO SISTEMA APP LEONARDO v3.0")
    print("=" * 60)
    
    # Banco de dados
    db = get_db_manager()
    stats = db.get_statistics()
    print(f"\n🗄️ Banco de Dados:")
    print(f"   - Trades: {stats['trades']['total']} (Abertos: {stats['trades']['open']})")
    print(f"   - Bots: {stats['bots']['total']}")
    print(f"   - Tamanho: {stats['db_size_mb']:.2f} MB")
    
    # Backups
    backup = get_backup_service()
    status = backup.get_status()
    print(f"\n💾 Backup Service:")
    print(f"   - Running: {status['running']}")
    print(f"   - Último backup: {status['last_backup']}")
    print(f"   - Total backups: {status['total_backups']}")
    
    # IA
    try:
        ai = get_ai_manager()
        ai_data = ai.get_dashboard_data()
        print(f"\n🤖 Sistema de IA:")
        print(f"   - Auto-adjust: {ai_data['status']['auto_adjust_enabled']}")
        print(f"   - Último treino: {ai_data['status']['last_training']}")
        print(f"   - Último scan: {ai_data['status']['last_market_scan']}")
    except:
        print(f"\n🤖 Sistema de IA: Não inicializado")
    
    print("\n" + "=" * 60)


def main():
    """Função principal"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║            APP LEONARDO v3.0 - SISTEMA COMPLETO           ║
    ║    Bot de Trading com IA Adaptativa e Backup Robusto     ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Criar diretórios necessários
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/ai', exist_ok=True)
    os.makedirs('data/ai_models', exist_ok=True)
    os.makedirs('data/db_backups', exist_ok=True)
    os.makedirs('data/full_backups', exist_ok=True)
    
    logger.info("🚀 Iniciando sistema App Leonardo v3.0...")
    
    # Verificar dependências
    if not verificar_dependencias():
        sys.exit(1)
    
    try:
        # 1. Banco de dados
        db = inicializar_banco_dados()
        
        # 2. Backup service
        backup_service = inicializar_backup_service()
        
        # 3. IA
        ai = inicializar_ia()
        
        # 4. Backup inicial
        criar_backup_inicial()
        
        # Mostrar status
        mostrar_status()
        
        logger.info("✅ Sistema inicializado com sucesso!")
        logger.info("📊 Dashboard: http://192.168.68.101:8501")
        logger.info("💾 Backup automático: 03:00 (diário)")
        logger.info("🤖 IA: Ativa e aprendendo")
        
        print("\n✅ Sistema pronto! Você pode:")
        print("   1. Executar o bot: python main_multibot.py")
        print("   2. Abrir dashboard: streamlit run frontend/dashboard_multibot.py")
        print("   3. Forçar backup: python -c \"from src.database import get_backup_service; get_backup_service().force_backup('manual')\"")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
