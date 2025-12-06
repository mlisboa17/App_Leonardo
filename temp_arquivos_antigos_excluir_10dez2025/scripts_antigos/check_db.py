"""Script para verificar e inicializar o banco de dados de histórico"""
import sqlite3
import os

DB_PATH = 'data/trading_history.db'

def check_and_create_tables():
    """Verifica e cria tabelas necessárias"""
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/history', exist_ok=True)
    os.makedirs('data/backups', exist_ok=True)
    os.makedirs('data/reports', exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Lista tabelas existentes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [t[0] for t in cursor.fetchall()]
    print(f"📊 Tabelas existentes: {existing_tables}")
    
    # Tabela de trades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL NOT NULL,
            amount REAL NOT NULL,
            pnl REAL NOT NULL,
            pnl_pct REAL NOT NULL,
            entry_time TEXT NOT NULL,
            exit_time TEXT NOT NULL,
            entry_reason TEXT,
            exit_reason TEXT,
            duration_minutes REAL,
            entry_rsi REAL,
            entry_macd REAL,
            strategy TEXT
        )
    ''')
    
    # Tabela de análises de mercado
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            rsi REAL,
            macd REAL,
            macd_signal REAL,
            sma_20 REAL,
            signal TEXT,
            reason TEXT
        )
    ''')
    
    # Tabela de snapshots do portfolio
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            total_balance_usdt REAL NOT NULL,
            available_usdt REAL NOT NULL,
            positions_value_usdt REAL NOT NULL,
            open_positions INTEGER NOT NULL,
            positions_json TEXT,
            daily_pnl REAL,
            total_pnl REAL
        )
    ''')
    
    # Tabela de resumo diário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            starting_balance REAL NOT NULL,
            ending_balance REAL NOT NULL,
            daily_pnl REAL NOT NULL,
            total_trades INTEGER NOT NULL,
            winning_trades INTEGER NOT NULL,
            losing_trades INTEGER NOT NULL,
            win_rate REAL NOT NULL,
            best_trade_pnl REAL,
            worst_trade_pnl REAL,
            traded_symbols TEXT,
            daily_goal_reached INTEGER DEFAULT 0
        )
    ''')
    
    # Tabela de eventos do bot
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT,
            details TEXT
        )
    ''')
    
    conn.commit()
    
    # Verifica novamente
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    final_tables = [t[0] for t in cursor.fetchall()]
    print(f"✅ Tabelas finais: {final_tables}")
    
    # Conta registros em cada tabela
    for table in final_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   📁 {table}: {count} registros")
    
    conn.close()
    print("\n✅ Banco de dados de histórico inicializado com sucesso!")

if __name__ == '__main__':
    check_and_create_tables()
