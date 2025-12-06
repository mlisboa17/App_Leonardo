# -*- coding: utf-8 -*-
"""
App Leonardo v3.0 - Migração de Dados
=====================================

Script para migrar dados dos arquivos JSON existentes para o banco de dados SQLite.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List

from src.database import (
    get_db_manager, 
    Trade, 
    BotState, 
    DailyStats
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DataMigration')


def migrate_trades():
    """Migra histórico de trades para o banco"""
    db = get_db_manager()
    
    trade_files = [
        "data/multibot_history.json",
        "data/history/bot_estavel_trades.json",
        "data/history/bot_medio_trades.json",
        "data/history/bot_volatil_trades.json",
        "data/history/bot_meme_trades.json",
        "data/all_trades_history.json"
    ]
    
    total_migrated = 0
    
    for file_path in trade_files:
        if not os.path.exists(file_path):
            continue
        
        try:
            with open(file_path, 'r') as f:
                trades = json.load(f)
            
            if not isinstance(trades, list):
                continue
            
            logger.info(f"📁 Processando {file_path} ({len(trades)} trades)")
            
            for t in trades:
                try:
                    # Determinar bot_name
                    bot_name = t.get('bot_type', t.get('bot', 'unknown'))
                    
                    # Criar Trade
                    trade = Trade(
                        symbol=t.get('symbol', ''),
                        bot_name=bot_name,
                        side='BUY' if t.get('type', 'BUY') == 'BUY' else 'SELL',
                        entry_price=float(t.get('entry_price', t.get('buy_price', 0))),
                        exit_price=float(t.get('exit_price', t.get('sell_price', 0))),
                        quantity=float(t.get('quantity', t.get('amount', 0))),
                        profit_usdt=float(t.get('profit_usdt', t.get('profit', 0))),
                        profit_percent=float(t.get('profit_percent', t.get('profit_pct', 0))),
                        entry_time=t.get('entry_time', t.get('buy_time', t.get('timestamp', ''))),
                        exit_time=t.get('exit_time', t.get('sell_time', '')),
                        status='CLOSED' if t.get('exit_price') or t.get('sell_price') else 'OPEN',
                        buy_reason=t.get('buy_reason', ''),
                        sell_reason=t.get('sell_reason', ''),
                        stop_loss=float(t.get('stop_loss', 0)),
                        take_profit=float(t.get('take_profit', 0)),
                        indicators=json.dumps(t.get('indicators', {})),
                        ai_confidence=float(t.get('ai_confidence', 0))
                    )
                    
                    db.save_trade(trade)
                    total_migrated += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao migrar trade: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {file_path}: {e}")
    
    logger.info(f"✅ {total_migrated} trades migrados")
    return total_migrated


def migrate_daily_stats():
    """Migra estatísticas diárias"""
    db = get_db_manager()
    
    stats_file = "data/daily_stats.json"
    
    if not os.path.exists(stats_file):
        logger.info("📁 Arquivo daily_stats.json não encontrado")
        return 0
    
    try:
        with open(stats_file, 'r') as f:
            data = json.load(f)
        
        total = 0
        
        # Formato pode variar
        if isinstance(data, dict):
            for date, stats in data.items():
                if isinstance(stats, dict):
                    for bot_name, bot_stats in stats.items():
                        if isinstance(bot_stats, dict):
                            daily = DailyStats(
                                date=date,
                                bot_name=bot_name,
                                profit_usdt=float(bot_stats.get('profit_usdt', 0)),
                                profit_percent=float(bot_stats.get('profit_percent', 0)),
                                total_trades=int(bot_stats.get('total_trades', 0)),
                                winning_trades=int(bot_stats.get('winning_trades', 0)),
                                losing_trades=int(bot_stats.get('losing_trades', 0)),
                                best_trade=float(bot_stats.get('best_trade', 0)),
                                worst_trade=float(bot_stats.get('worst_trade', 0))
                            )
                            db.save_daily_stats(daily)
                            total += 1
        
        logger.info(f"✅ {total} registros de estatísticas diárias migrados")
        return total
        
    except Exception as e:
        logger.error(f"❌ Erro ao migrar daily_stats: {e}")
        return 0


def migrate_bot_states():
    """Migra estados dos bots"""
    db = get_db_manager()
    
    # Tentar carregar do bot_state.json
    state_file = "bot_state.json"
    
    if not os.path.exists(state_file):
        logger.info("📁 Arquivo bot_state.json não encontrado")
        return 0
    
    try:
        with open(state_file, 'r') as f:
            data = json.load(f)
        
        total = 0
        
        bots_data = data.get('bots', data)
        
        for bot_name, bot_data in bots_data.items():
            if isinstance(bot_data, dict):
                state = BotState(
                    bot_name=bot_name,
                    balance_usdt=float(bot_data.get('balance', bot_data.get('balance_usdt', 0))),
                    balance_initial=float(bot_data.get('initial_balance', bot_data.get('balance_initial', 0))),
                    total_profit=float(bot_data.get('total_profit', 0)),
                    total_trades=int(bot_data.get('total_trades', 0)),
                    winning_trades=int(bot_data.get('winning_trades', 0)),
                    losing_trades=int(bot_data.get('losing_trades', 0)),
                    current_positions=json.dumps(bot_data.get('positions', [])),
                    daily_profit=float(bot_data.get('daily_profit', 0)),
                    daily_trades=int(bot_data.get('daily_trades', 0)),
                    status='RUNNING',
                    config=json.dumps(bot_data.get('config', {}))
                )
                db.save_bot_state(state)
                total += 1
        
        logger.info(f"✅ {total} estados de bots migrados")
        return total
        
    except Exception as e:
        logger.error(f"❌ Erro ao migrar bot_states: {e}")
        return 0


def run_migration():
    """Executa migração completa"""
    logger.info("=" * 50)
    logger.info("🚀 INICIANDO MIGRAÇÃO DE DADOS")
    logger.info("=" * 50)
    
    db = get_db_manager()
    
    # Criar backup antes
    logger.info("\n💾 Criando backup do banco antes da migração...")
    db.create_backup("before_migration")
    
    # Migrar dados
    logger.info("\n📊 Migrando trades...")
    trades = migrate_trades()
    
    logger.info("\n📈 Migrando estatísticas diárias...")
    stats = migrate_daily_stats()
    
    logger.info("\n🤖 Migrando estados dos bots...")
    bots = migrate_bot_states()
    
    # Estatísticas finais
    logger.info("\n" + "=" * 50)
    logger.info("✅ MIGRAÇÃO CONCLUÍDA")
    logger.info("=" * 50)
    
    final_stats = db.get_statistics()
    logger.info(f"\n📊 Resumo do Banco de Dados:")
    logger.info(f"  - Trades: {final_stats['trades']['total']}")
    logger.info(f"  - Bots: {final_stats['bots']['total']}")
    logger.info(f"  - Tamanho: {final_stats['db_size_mb']:.2f} MB")
    
    return {
        'trades_migrated': trades,
        'stats_migrated': stats,
        'bots_migrated': bots,
        'final_stats': final_stats
    }


if __name__ == "__main__":
    result = run_migration()
    print(f"\n✅ Migração concluída: {result}")
