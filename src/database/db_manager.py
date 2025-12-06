# -*- coding: utf-8 -*-
"""
App Leonardo v3.0 - Gerenciador de Banco de Dados
=================================================

Sistema robusto de banco de dados SQLite com:
- Transações ACID
- Backup automático diário
- Recuperação de falhas
- Índices otimizados
- Compressão de backups
"""

import os
import sqlite3
import json
import shutil
import hashlib
import gzip
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from contextlib import contextmanager

from .models import (
    Trade, BotState, AILearning, MarketData, Backup,
    DailyStats, CREATE_TABLES_SQL
)

logger = logging.getLogger('DatabaseManager')


class DatabaseManager:
    """
    Gerenciador central do banco de dados.
    
    Features:
    - Conexões thread-safe
    - Transações automáticas
    - Backup incremental e completo
    - Validação de integridade
    - Migração de esquema
    """
    
    VERSION = "3.0.0"
    
    def __init__(self, db_path: str = "data/app_leonardo.db"):
        self.db_path = db_path
        self.db_dir = os.path.dirname(db_path)
        self.backup_dir = os.path.join(self.db_dir, "db_backups")
        
        # Criar diretórios
        os.makedirs(self.db_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Lock para thread safety
        self._lock = threading.RLock()
        
        # Pool de conexões (por thread)
        self._local = threading.local()
        
        # Inicializar banco
        self._initialize_database()
        
        # Verificar integridade na inicialização
        self._check_integrity()
        
        logger.info(f"🗄️ Banco de dados inicializado: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Retorna conexão para a thread atual"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.conn.row_factory = sqlite3.Row
            # Configurações de performance
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn.execute("PRAGMA cache_size=10000")
            self._local.conn.execute("PRAGMA temp_store=MEMORY")
        return self._local.conn
    
    @contextmanager
    def transaction(self):
        """Context manager para transações"""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Transação revertida: {e}")
            raise
    
    def _initialize_database(self):
        """Cria tabelas se não existirem"""
        with self._lock:
            conn = self._get_connection()
            conn.executescript(CREATE_TABLES_SQL)
            conn.commit()
            
            # Salvar versão
            self._set_config('db_version', self.VERSION)
            self._set_config('db_created', datetime.now().isoformat())
    
    def _check_integrity(self) -> bool:
        """Verifica integridade do banco"""
        try:
            conn = self._get_connection()
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result[0] == 'ok':
                logger.info("✅ Integridade do banco OK")
                return True
            else:
                logger.error(f"❌ Problemas de integridade: {result[0]}")
                return False
        except Exception as e:
            logger.error(f"❌ Erro ao verificar integridade: {e}")
            return False
    
    # ============ TRADES ============
    
    def save_trade(self, trade: Trade) -> int:
        """Salva um trade no banco"""
        with self.transaction() as conn:
            if trade.id:
                # Update
                conn.execute("""
                    UPDATE trades SET
                        symbol=?, bot_name=?, side=?, entry_price=?, exit_price=?,
                        quantity=?, profit_usdt=?, profit_percent=?, entry_time=?,
                        exit_time=?, status=?, buy_reason=?, sell_reason=?,
                        stop_loss=?, take_profit=?, indicators=?, ai_confidence=?
                    WHERE id=?
                """, (
                    trade.symbol, trade.bot_name, trade.side, trade.entry_price,
                    trade.exit_price, trade.quantity, trade.profit_usdt,
                    trade.profit_percent, trade.entry_time, trade.exit_time,
                    trade.status, trade.buy_reason, trade.sell_reason,
                    trade.stop_loss, trade.take_profit, trade.indicators,
                    trade.ai_confidence, trade.id
                ))
                return trade.id
            else:
                # Insert
                cursor = conn.execute("""
                    INSERT INTO trades (
                        symbol, bot_name, side, entry_price, exit_price,
                        quantity, profit_usdt, profit_percent, entry_time,
                        exit_time, status, buy_reason, sell_reason,
                        stop_loss, take_profit, indicators, ai_confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.symbol, trade.bot_name, trade.side, trade.entry_price,
                    trade.exit_price, trade.quantity, trade.profit_usdt,
                    trade.profit_percent, trade.entry_time, trade.exit_time,
                    trade.status, trade.buy_reason, trade.sell_reason,
                    trade.stop_loss, trade.take_profit, trade.indicators,
                    trade.ai_confidence
                ))
                return cursor.lastrowid
    
    def get_trade(self, trade_id: int) -> Optional[Trade]:
        """Busca trade por ID"""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT * FROM trades WHERE id=?", (trade_id,)
        ).fetchone()
        
        if row:
            return Trade(**dict(row))
        return None
    
    def get_trades(self, 
                   bot_name: str = None, 
                   symbol: str = None,
                   status: str = None,
                   start_date: str = None,
                   end_date: str = None,
                   limit: int = 100) -> List[Trade]:
        """Busca trades com filtros"""
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if bot_name:
            query += " AND bot_name=?"
            params.append(bot_name)
        if symbol:
            query += " AND symbol=?"
            params.append(symbol)
        if status:
            query += " AND status=?"
            params.append(status)
        if start_date:
            query += " AND entry_time>=?"
            params.append(start_date)
        if end_date:
            query += " AND entry_time<=?"
            params.append(end_date)
        
        query += " ORDER BY entry_time DESC LIMIT ?"
        params.append(limit)
        
        conn = self._get_connection()
        rows = conn.execute(query, params).fetchall()
        
        return [Trade(**dict(row)) for row in rows]
    
    def get_open_trades(self, bot_name: str = None) -> List[Trade]:
        """Retorna trades abertos"""
        return self.get_trades(bot_name=bot_name, status='OPEN', limit=1000)
    
    def close_trade(self, trade_id: int, exit_price: float, 
                    exit_time: str, sell_reason: str) -> bool:
        """Fecha um trade"""
        trade = self.get_trade(trade_id)
        if not trade:
            return False
        
        profit_usdt = (exit_price - trade.entry_price) * trade.quantity
        profit_percent = ((exit_price / trade.entry_price) - 1) * 100
        
        with self.transaction() as conn:
            conn.execute("""
                UPDATE trades SET
                    exit_price=?, exit_time=?, status='CLOSED',
                    sell_reason=?, profit_usdt=?, profit_percent=?
                WHERE id=?
            """, (
                exit_price, exit_time, sell_reason,
                profit_usdt, profit_percent, trade_id
            ))
        
        return True
    
    # ============ BOT STATE ============
    
    def save_bot_state(self, state: BotState) -> int:
        """Salva estado do bot"""
        state.updated_at = datetime.now().isoformat()
        
        with self.transaction() as conn:
            # Upsert
            conn.execute("""
                INSERT INTO bot_states (
                    bot_name, balance_usdt, balance_initial, total_profit,
                    total_trades, winning_trades, losing_trades, current_positions,
                    daily_profit, daily_trades, last_trade_time, status, config, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(bot_name) DO UPDATE SET
                    balance_usdt=excluded.balance_usdt,
                    balance_initial=excluded.balance_initial,
                    total_profit=excluded.total_profit,
                    total_trades=excluded.total_trades,
                    winning_trades=excluded.winning_trades,
                    losing_trades=excluded.losing_trades,
                    current_positions=excluded.current_positions,
                    daily_profit=excluded.daily_profit,
                    daily_trades=excluded.daily_trades,
                    last_trade_time=excluded.last_trade_time,
                    status=excluded.status,
                    config=excluded.config,
                    updated_at=excluded.updated_at
            """, (
                state.bot_name, state.balance_usdt, state.balance_initial,
                state.total_profit, state.total_trades, state.winning_trades,
                state.losing_trades, state.current_positions, state.daily_profit,
                state.daily_trades, state.last_trade_time, state.status,
                state.config, state.updated_at
            ))
        
        return 1
    
    def get_bot_state(self, bot_name: str) -> Optional[BotState]:
        """Busca estado do bot"""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT * FROM bot_states WHERE bot_name=?", (bot_name,)
        ).fetchone()
        
        if row:
            return BotState(**dict(row))
        return None
    
    def get_all_bot_states(self) -> List[BotState]:
        """Retorna estado de todos os bots"""
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM bot_states").fetchall()
        return [BotState(**dict(row)) for row in rows]
    
    # ============ AI LEARNING ============
    
    def save_ai_model(self, learning: AILearning) -> int:
        """Salva modelo de IA"""
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO ai_learning (
                    model_name, model_type, accuracy, trades_trained,
                    features_used, model_data, insights, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                learning.model_name, learning.model_type, learning.accuracy,
                learning.trades_trained, learning.features_used,
                learning.model_data, learning.insights, learning.version
            ))
            return cursor.lastrowid
    
    def get_latest_model(self, model_name: str) -> Optional[AILearning]:
        """Busca modelo mais recente"""
        conn = self._get_connection()
        row = conn.execute("""
            SELECT * FROM ai_learning 
            WHERE model_name=? 
            ORDER BY version DESC LIMIT 1
        """, (model_name,)).fetchone()
        
        if row:
            return AILearning(**dict(row))
        return None
    
    # ============ MARKET DATA ============
    
    def save_market_data(self, data: MarketData):
        """Salva dados de mercado"""
        with self.transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO market_data (
                    symbol, timestamp, open_price, high_price, low_price,
                    close_price, volume, rsi, macd, macd_signal,
                    bb_upper, bb_lower, fear_greed, sentiment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.symbol, data.timestamp, data.open_price, data.high_price,
                data.low_price, data.close_price, data.volume, data.rsi,
                data.macd, data.macd_signal, data.bb_upper, data.bb_lower,
                data.fear_greed, data.sentiment
            ))
    
    def get_market_history(self, symbol: str, hours: int = 24) -> List[MarketData]:
        """Busca histórico de mercado"""
        start = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT * FROM market_data 
            WHERE symbol=? AND timestamp>=?
            ORDER BY timestamp
        """, (symbol, start)).fetchall()
        
        return [MarketData(**dict(row)) for row in rows]
    
    # ============ DAILY STATS ============
    
    def save_daily_stats(self, stats: DailyStats):
        """Salva estatísticas diárias"""
        with self.transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO daily_stats (
                    date, bot_name, profit_usdt, profit_percent,
                    total_trades, winning_trades, losing_trades,
                    best_trade, worst_trade, avg_trade_duration,
                    max_drawdown, sharpe_ratio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stats.date, stats.bot_name, stats.profit_usdt,
                stats.profit_percent, stats.total_trades, stats.winning_trades,
                stats.losing_trades, stats.best_trade, stats.worst_trade,
                stats.avg_trade_duration, stats.max_drawdown, stats.sharpe_ratio
            ))
    
    def get_daily_stats(self, bot_name: str = None, days: int = 30) -> List[DailyStats]:
        """Busca estatísticas diárias"""
        start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        query = "SELECT * FROM daily_stats WHERE date>=?"
        params = [start]
        
        if bot_name:
            query += " AND bot_name=?"
            params.append(bot_name)
        
        query += " ORDER BY date DESC"
        
        conn = self._get_connection()
        rows = conn.execute(query, params).fetchall()
        
        return [DailyStats(**dict(row)) for row in rows]
    
    # ============ EVENT LOG ============
    
    def log_event(self, event_type: str, message: str, 
                  bot_name: str = None, data: Dict = None, 
                  severity: str = 'INFO'):
        """Registra evento no log"""
        with self.transaction() as conn:
            conn.execute("""
                INSERT INTO event_log (event_type, bot_name, message, data, severity)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event_type, bot_name, message, 
                json.dumps(data) if data else None, severity
            ))
    
    def get_events(self, event_type: str = None, 
                   severity: str = None, hours: int = 24) -> List[Dict]:
        """Busca eventos do log"""
        start = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        query = "SELECT * FROM event_log WHERE created_at>=?"
        params = [start]
        
        if event_type:
            query += " AND event_type=?"
            params.append(event_type)
        if severity:
            query += " AND severity=?"
            params.append(severity)
        
        query += " ORDER BY created_at DESC LIMIT 1000"
        
        conn = self._get_connection()
        rows = conn.execute(query, params).fetchall()
        
        return [dict(row) for row in rows]
    
    # ============ CONFIGURAÇÕES ============
    
    def _set_config(self, key: str, value: Any, 
                    value_type: str = 'string', description: str = ''):
        """Salva configuração"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
            value_type = 'json'
        else:
            value = str(value)
        
        with self.transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO system_config (key, value, value_type, description, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (key, value, value_type, description, datetime.now().isoformat()))
    
    def _get_config(self, key: str, default: Any = None) -> Any:
        """Busca configuração"""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT value, value_type FROM system_config WHERE key=?", (key,)
        ).fetchone()
        
        if not row:
            return default
        
        value, value_type = row
        
        if value_type == 'int':
            return int(value)
        elif value_type == 'float':
            return float(value)
        elif value_type == 'bool':
            return value.lower() in ('true', '1', 'yes')
        elif value_type == 'json':
            return json.loads(value)
        return value
    
    # ============ PORTFOLIO HISTORY ============
    
    def save_portfolio_snapshot(self, total_usdt: float, total_crypto: float,
                                 bot_balances: Dict, positions: List):
        """Salva snapshot do portfólio"""
        with self.transaction() as conn:
            conn.execute("""
                INSERT INTO portfolio_history (
                    timestamp, total_balance_usdt, total_balance_crypto,
                    bot_balances, positions
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                total_usdt, total_crypto,
                json.dumps(bot_balances),
                json.dumps(positions)
            ))
    
    def get_portfolio_history(self, hours: int = 24) -> List[Dict]:
        """Busca histórico do portfólio"""
        start = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT * FROM portfolio_history 
            WHERE timestamp>=?
            ORDER BY timestamp
        """, (start,)).fetchall()
        
        return [dict(row) for row in rows]
    
    # ============ BACKUP ============
    
    def create_backup(self, backup_type: str = "manual") -> str:
        """
        Cria backup completo do banco de dados.
        
        Args:
            backup_type: manual, scheduled, before_update
            
        Returns:
            Caminho do backup
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"db_backup_{timestamp}_{backup_type}.db"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            with self._lock:
                # Fazer cópia usando backup API do SQLite
                conn = self._get_connection()
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()
            
            # Calcular checksum
            checksum = self._calculate_checksum(backup_path)
            
            # Comprimir
            compressed_path = backup_path + '.gz'
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remover não comprimido
            os.remove(backup_path)
            
            # Tamanho
            size = os.path.getsize(compressed_path)
            
            # Registrar backup
            backup = Backup(
                backup_type=backup_type,
                backup_path=compressed_path,
                size_bytes=size,
                tables_backed_up=json.dumps(self._get_table_names()),
                checksum=checksum
            )
            
            with self.transaction() as conn:
                conn.execute("""
                    INSERT INTO backups (backup_type, backup_path, size_bytes, 
                                        tables_backed_up, checksum)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    backup.backup_type, backup.backup_path, backup.size_bytes,
                    backup.tables_backed_up, backup.checksum
                ))
            
            # Limpar backups antigos
            self._cleanup_old_backups(keep=10)
            
            logger.info(f"✅ Backup criado: {compressed_path} ({size/1024:.1f} KB)")
            
            # Log event
            self.log_event('BACKUP', f'Backup criado: {backup_type}', 
                          data={'path': compressed_path, 'size': size})
            
            return compressed_path
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            return ""
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restaura backup do banco de dados.
        
        Args:
            backup_path: Caminho do backup (pode ser .db ou .db.gz)
            
        Returns:
            True se sucesso
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup não encontrado: {backup_path}")
            return False
        
        try:
            # Criar backup do estado atual antes de restaurar
            self.create_backup(backup_type="before_restore")
            
            # Descomprimir se necessário
            if backup_path.endswith('.gz'):
                temp_path = backup_path[:-3]
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_path = temp_path
            
            # Fechar conexões
            if hasattr(self._local, 'conn') and self._local.conn:
                self._local.conn.close()
                self._local.conn = None
            
            # Substituir banco
            shutil.copy(backup_path, self.db_path)
            
            # Limpar temp se foi descomprimido
            if backup_path != self.db_path:
                os.remove(backup_path)
            
            logger.info(f"✅ Backup restaurado: {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """Lista backups disponíveis"""
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT * FROM backups ORDER BY created_at DESC
        """).fetchall()
        
        return [dict(row) for row in rows]
    
    def _cleanup_old_backups(self, keep: int = 10):
        """Remove backups antigos"""
        try:
            backups = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith('db_backup_')
            ])
            
            for old in backups[:-keep]:
                old_path = os.path.join(self.backup_dir, old)
                os.remove(old_path)
                logger.info(f"🗑️ Backup antigo removido: {old}")
        except Exception as e:
            logger.warning(f"Erro ao limpar backups: {e}")
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calcula MD5 de um arquivo"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_table_names(self) -> List[str]:
        """Lista nomes das tabelas"""
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        return [row[0] for row in rows]
    
    # ============ ESTATÍSTICAS ============
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas do banco"""
        conn = self._get_connection()
        
        stats = {
            'trades': {
                'total': conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0],
                'open': conn.execute("SELECT COUNT(*) FROM trades WHERE status='OPEN'").fetchone()[0],
                'closed': conn.execute("SELECT COUNT(*) FROM trades WHERE status='CLOSED'").fetchone()[0],
            },
            'bots': {
                'total': conn.execute("SELECT COUNT(*) FROM bot_states").fetchone()[0],
                'running': conn.execute("SELECT COUNT(*) FROM bot_states WHERE status='RUNNING'").fetchone()[0],
            },
            'ai': {
                'models': conn.execute("SELECT COUNT(DISTINCT model_name) FROM ai_learning").fetchone()[0],
            },
            'events': {
                'total_24h': conn.execute(f"""
                    SELECT COUNT(*) FROM event_log 
                    WHERE created_at>='{(datetime.now() - timedelta(hours=24)).isoformat()}'
                """).fetchone()[0],
            },
            'backups': {
                'total': conn.execute("SELECT COUNT(*) FROM backups").fetchone()[0],
                'last': conn.execute("SELECT created_at FROM backups ORDER BY created_at DESC LIMIT 1").fetchone(),
            },
            'db_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
        }
        
        if stats['backups']['last']:
            stats['backups']['last'] = stats['backups']['last'][0]
        
        return stats
    
    def vacuum(self):
        """Compacta o banco de dados"""
        try:
            conn = self._get_connection()
            conn.execute("VACUUM")
            logger.info("✅ Banco de dados compactado")
        except Exception as e:
            logger.error(f"❌ Erro ao compactar: {e}")
    
    def close(self):
        """Fecha conexões"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# Singleton
_db_manager: Optional[DatabaseManager] = None

def get_db_manager(db_path: str = "data/app_leonardo.db") -> DatabaseManager:
    """Retorna instância singleton do DatabaseManager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


# Teste
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    db = get_db_manager()
    
    print("\n🗄️ Banco de Dados App Leonardo")
    print("=" * 40)
    
    # Estatísticas
    stats = db.get_statistics()
    print("\n📊 Estatísticas:")
    for table, data in stats.items():
        print(f"  {table}: {data}")
    
    # Teste de trade
    print("\n📝 Testando operações...")
    
    trade = Trade(
        symbol="BTCUSDT",
        bot_name="bot_estavel",
        side="BUY",
        entry_price=96000,
        quantity=0.001,
        entry_time=datetime.now().isoformat(),
        status="OPEN",
        buy_reason="RSI 28 | MACD↑"
    )
    
    trade_id = db.save_trade(trade)
    print(f"  ✅ Trade salvo: ID {trade_id}")
    
    # Teste de bot state
    state = BotState(
        bot_name="bot_estavel",
        balance_usdt=1000,
        total_profit=50,
        total_trades=10,
        winning_trades=7,
        losing_trades=3
    )
    
    db.save_bot_state(state)
    print("  ✅ Estado do bot salvo")
    
    # Log event
    db.log_event("TEST", "Teste de log", bot_name="bot_estavel", 
                 data={"test": True})
    print("  ✅ Evento logado")
    
    # Backup
    print("\n💾 Criando backup...")
    backup_path = db.create_backup("test")
    
    # Listar backups
    print("\n📦 Backups disponíveis:")
    for b in db.list_backups()[:5]:
        print(f"  - {b['backup_path']} ({b['size_bytes']/1024:.1f} KB)")
    
    print("\n✅ Tudo funcionando!")
