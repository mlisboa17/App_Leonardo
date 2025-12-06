# -*- coding: utf-8 -*-
"""
App Leonardo v3.0 - Modelos do Banco de Dados
=============================================

Definição de todas as tabelas e estruturas de dados.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import json


@dataclass
class Trade:
    """Modelo de Trade"""
    id: int = None
    symbol: str = ""
    bot_name: str = ""
    side: str = ""  # BUY ou SELL
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: float = 0.0
    profit_usdt: float = 0.0
    profit_percent: float = 0.0
    entry_time: str = ""
    exit_time: str = ""
    status: str = "OPEN"  # OPEN, CLOSED, CANCELLED
    buy_reason: str = ""
    sell_reason: str = ""
    stop_loss: float = 0.0
    take_profit: float = 0.0
    indicators: str = "{}"  # JSON dos indicadores
    ai_confidence: float = 0.0
    created_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'bot_name': self.bot_name,
            'side': self.side,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'profit_usdt': self.profit_usdt,
            'profit_percent': self.profit_percent,
            'entry_time': self.entry_time,
            'exit_time': self.exit_time,
            'status': self.status,
            'buy_reason': self.buy_reason,
            'sell_reason': self.sell_reason,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'indicators': self.indicators,
            'ai_confidence': self.ai_confidence,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Trade':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class BotState:
    """Estado de um bot"""
    id: int = None
    bot_name: str = ""
    balance_usdt: float = 0.0
    balance_initial: float = 0.0
    total_profit: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    current_positions: str = "[]"  # JSON
    daily_profit: float = 0.0
    daily_trades: int = 0
    last_trade_time: str = ""
    status: str = "RUNNING"  # RUNNING, PAUSED, STOPPED
    config: str = "{}"  # JSON da config
    updated_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'bot_name': self.bot_name,
            'balance_usdt': self.balance_usdt,
            'balance_initial': self.balance_initial,
            'total_profit': self.total_profit,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'current_positions': self.current_positions,
            'daily_profit': self.daily_profit,
            'daily_trades': self.daily_trades,
            'last_trade_time': self.last_trade_time,
            'status': self.status,
            'config': self.config,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BotState':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AILearning:
    """Registro de aprendizado da IA"""
    id: int = None
    model_name: str = ""
    model_type: str = ""  # RandomForest, etc
    accuracy: float = 0.0
    trades_trained: int = 0
    features_used: str = "[]"  # JSON
    model_data: bytes = b""  # Pickle do modelo
    insights: str = "{}"  # JSON
    training_time: str = ""
    version: int = 1
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'model_name': self.model_name,
            'model_type': self.model_type,
            'accuracy': self.accuracy,
            'trades_trained': self.trades_trained,
            'features_used': self.features_used,
            'insights': self.insights,
            'training_time': self.training_time,
            'version': self.version
        }


@dataclass
class MarketData:
    """Dados de mercado históricos"""
    id: int = None
    symbol: str = ""
    timestamp: str = ""
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    close_price: float = 0.0
    volume: float = 0.0
    rsi: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    bb_upper: float = 0.0
    bb_lower: float = 0.0
    fear_greed: int = 50
    sentiment: str = "NEUTRAL"
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'close_price': self.close_price,
            'volume': self.volume,
            'rsi': self.rsi,
            'macd': self.macd,
            'macd_signal': self.macd_signal,
            'bb_upper': self.bb_upper,
            'bb_lower': self.bb_lower,
            'fear_greed': self.fear_greed,
            'sentiment': self.sentiment
        }


@dataclass
class Backup:
    """Registro de backups"""
    id: int = None
    backup_type: str = ""  # scheduled, manual, before_update
    backup_path: str = ""
    size_bytes: int = 0
    tables_backed_up: str = "[]"  # JSON
    created_at: str = ""
    checksum: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'backup_type': self.backup_type,
            'backup_path': self.backup_path,
            'size_bytes': self.size_bytes,
            'tables_backed_up': self.tables_backed_up,
            'created_at': self.created_at,
            'checksum': self.checksum
        }


@dataclass
class SystemConfig:
    """Configurações do sistema"""
    id: int = None
    key: str = ""
    value: str = ""
    value_type: str = "string"  # string, int, float, bool, json
    description: str = ""
    updated_at: str = ""
    
    def get_value(self) -> Any:
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == "json":
            return json.loads(self.value)
        return self.value


@dataclass
class DailyStats:
    """Estatísticas diárias"""
    id: int = None
    date: str = ""
    bot_name: str = ""
    profit_usdt: float = 0.0
    profit_percent: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    avg_trade_duration: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    created_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'date': self.date,
            'bot_name': self.bot_name,
            'profit_usdt': self.profit_usdt,
            'profit_percent': self.profit_percent,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'best_trade': self.best_trade,
            'worst_trade': self.worst_trade,
            'avg_trade_duration': self.avg_trade_duration,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'created_at': self.created_at
        }


# SQL para criar tabelas
CREATE_TABLES_SQL = """
-- Tabela de Trades
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    bot_name TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL DEFAULT 0,
    quantity REAL NOT NULL,
    profit_usdt REAL DEFAULT 0,
    profit_percent REAL DEFAULT 0,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    status TEXT DEFAULT 'OPEN',
    buy_reason TEXT,
    sell_reason TEXT,
    stop_loss REAL,
    take_profit REAL,
    indicators TEXT,
    ai_confidence REAL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Índices para trades
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_bot ON trades(bot_name);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);

-- Tabela de Estado dos Bots
CREATE TABLE IF NOT EXISTS bot_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_name TEXT UNIQUE NOT NULL,
    balance_usdt REAL DEFAULT 0,
    balance_initial REAL DEFAULT 0,
    total_profit REAL DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    current_positions TEXT DEFAULT '[]',
    daily_profit REAL DEFAULT 0,
    daily_trades INTEGER DEFAULT 0,
    last_trade_time TEXT,
    status TEXT DEFAULT 'RUNNING',
    config TEXT DEFAULT '{}',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Aprendizado da IA
CREATE TABLE IF NOT EXISTS ai_learning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    model_type TEXT,
    accuracy REAL DEFAULT 0,
    trades_trained INTEGER DEFAULT 0,
    features_used TEXT,
    model_data BLOB,
    insights TEXT,
    training_time TEXT DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_ai_model ON ai_learning(model_name);

-- Tabela de Dados de Mercado
CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume REAL,
    rsi REAL,
    macd REAL,
    macd_signal REAL,
    bb_upper REAL,
    bb_lower REAL,
    fear_greed INTEGER DEFAULT 50,
    sentiment TEXT DEFAULT 'NEUTRAL',
    UNIQUE(symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_market_symbol ON market_data(symbol);
CREATE INDEX IF NOT EXISTS idx_market_timestamp ON market_data(timestamp);

-- Tabela de Backups
CREATE TABLE IF NOT EXISTS backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_type TEXT NOT NULL,
    backup_path TEXT NOT NULL,
    size_bytes INTEGER DEFAULT 0,
    tables_backed_up TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT
);

-- Tabela de Configurações
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    value_type TEXT DEFAULT 'string',
    description TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Estatísticas Diárias
CREATE TABLE IF NOT EXISTS daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    bot_name TEXT NOT NULL,
    profit_usdt REAL DEFAULT 0,
    profit_percent REAL DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    best_trade REAL DEFAULT 0,
    worst_trade REAL DEFAULT 0,
    avg_trade_duration REAL DEFAULT 0,
    max_drawdown REAL DEFAULT 0,
    sharpe_ratio REAL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, bot_name)
);

CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_stats(date);
CREATE INDEX IF NOT EXISTS idx_daily_bot ON daily_stats(bot_name);

-- Tabela de Log de Eventos
CREATE TABLE IF NOT EXISTS event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    bot_name TEXT,
    message TEXT,
    data TEXT,
    severity TEXT DEFAULT 'INFO',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_event_type ON event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_event_time ON event_log(created_at);

-- Tabela de Alertas
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    symbol TEXT,
    bot_name TEXT,
    condition TEXT,
    message TEXT,
    triggered_at TEXT,
    acknowledged INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Portfólio Histórico
CREATE TABLE IF NOT EXISTS portfolio_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    total_balance_usdt REAL,
    total_balance_crypto REAL,
    bot_balances TEXT,
    positions TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_portfolio_time ON portfolio_history(timestamp);
"""
