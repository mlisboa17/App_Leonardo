"""
📊 Visualizador de Histórico do Bot de Trading
Mostra dados do banco de dados SQLite de forma organizada
"""
import sqlite3
import json
from datetime import datetime
from tabulate import tabulate

DB_PATH = 'data/trading_history.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def show_trades_summary():
    """Mostra resumo de todos os trades"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("📊 RESUMO DE TRADES")
    print("="*70)
    
    # Total de trades
    cursor.execute("SELECT COUNT(*) FROM trades")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trades WHERE pnl > 0")
    wins = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trades WHERE pnl <= 0")
    losses = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(pnl) FROM trades")
    total_pnl = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT MAX(pnl) FROM trades")
    best_trade = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT MIN(pnl) FROM trades")
    worst_trade = cursor.fetchone()[0] or 0
    
    win_rate = (wins / total * 100) if total > 0 else 0
    
    print(f"Total de Trades: {total}")
    print(f"  ✅ Ganhos: {wins}")
    print(f"  ❌ Perdas: {losses}")
    print(f"  🎯 Win Rate: {win_rate:.1f}%")
    print(f"  💰 PnL Total: ${total_pnl:.2f}")
    print(f"  📈 Melhor Trade: ${best_trade:.2f}")
    print(f"  📉 Pior Trade: ${worst_trade:.2f}")
    
    conn.close()

def show_recent_trades(limit=10):
    """Mostra os trades mais recentes"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print(f"📜 ÚLTIMOS {limit} TRADES")
    print("="*70)
    
    cursor.execute("""
        SELECT symbol, side, entry_price, exit_price, pnl, pnl_pct, exit_time
        FROM trades
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    
    trades = cursor.fetchall()
    
    if trades:
        headers = ['Símbolo', 'Lado', 'Entrada', 'Saída', 'PnL ($)', 'PnL (%)', 'Horário']
        table = []
        for t in trades:
            emoji = "🟢" if t[4] > 0 else "🔴"
            table.append([
                t[0],
                t[1],
                f"${t[2]:.4f}",
                f"${t[3]:.4f}",
                f"{emoji} ${t[4]:.2f}",
                f"{t[5]:.2f}%",
                t[6][:19] if t[6] else '-'
            ])
        print(tabulate(table, headers=headers, tablefmt="grid"))
    else:
        print("Nenhum trade registrado ainda.")
    
    conn.close()

def show_trades_by_symbol():
    """Mostra estatísticas por símbolo"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("📊 PERFORMANCE POR SÍMBOLO")
    print("="*70)
    
    cursor.execute("""
        SELECT 
            symbol,
            COUNT(*) as total,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(pnl) as total_pnl,
            AVG(pnl) as avg_pnl
        FROM trades
        GROUP BY symbol
        ORDER BY total_pnl DESC
    """)
    
    results = cursor.fetchall()
    
    if results:
        headers = ['Símbolo', 'Trades', 'Wins', 'Win Rate', 'PnL Total', 'PnL Médio']
        table = []
        for r in results:
            symbol, total, wins, total_pnl, avg_pnl = r
            win_rate = (wins / total * 100) if total > 0 else 0
            emoji = "🟢" if total_pnl > 0 else "🔴"
            table.append([
                symbol,
                total,
                wins,
                f"{win_rate:.1f}%",
                f"{emoji} ${total_pnl:.2f}",
                f"${avg_pnl:.2f}"
            ])
        print(tabulate(table, headers=headers, tablefmt="grid"))
    else:
        print("Nenhum dado disponível.")
    
    conn.close()

def show_daily_summary():
    """Mostra resumos diários"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("📅 RESUMOS DIÁRIOS")
    print("="*70)
    
    cursor.execute("""
        SELECT date, daily_pnl, total_trades, winning_trades, losing_trades, win_rate, daily_goal_reached
        FROM daily_summary
        ORDER BY date DESC
        LIMIT 7
    """)
    
    results = cursor.fetchall()
    
    if results:
        headers = ['Data', 'PnL', 'Trades', 'W', 'L', 'Win Rate', 'Meta']
        table = []
        for r in results:
            emoji = "🟢" if r[1] > 0 else "🔴"
            meta = "✅" if r[6] else "❌"
            table.append([
                r[0],
                f"{emoji} ${r[1]:.2f}",
                r[2],
                r[3],
                r[4],
                f"{r[5]:.1f}%",
                meta
            ])
        print(tabulate(table, headers=headers, tablefmt="grid"))
    else:
        print("Nenhum resumo diário encontrado.")
    
    conn.close()

def show_bot_events(limit=10):
    """Mostra eventos recentes do bot"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print(f"📝 ÚLTIMOS {limit} EVENTOS DO BOT")
    print("="*70)
    
    cursor.execute("""
        SELECT timestamp, event_type, description
        FROM bot_events
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    
    events = cursor.fetchall()
    
    if events:
        headers = ['Horário', 'Tipo', 'Descrição']
        table = []
        for e in events:
            table.append([
                e[0][:19] if e[0] else '-',
                e[1],
                e[2][:50] if e[2] else '-'
            ])
        print(tabulate(table, headers=headers, tablefmt="grid"))
    else:
        print("Nenhum evento registrado.")
    
    conn.close()

def show_portfolio_snapshots(limit=5):
    """Mostra snapshots recentes do portfolio"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print(f"📸 ÚLTIMOS {limit} SNAPSHOTS DO PORTFOLIO")
    print("="*70)
    
    cursor.execute("""
        SELECT timestamp, total_balance_usdt, available_usdt, positions_value_usdt, 
               open_positions, daily_pnl, total_pnl
        FROM portfolio_snapshots
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    
    snapshots = cursor.fetchall()
    
    if snapshots:
        headers = ['Horário', 'Total', 'Disponível', 'Em Posições', 'Pos.', 'PnL Dia', 'PnL Total']
        table = []
        for s in snapshots:
            table.append([
                s[0][:19] if s[0] else '-',
                f"${s[1]:.2f}",
                f"${s[2]:.2f}",
                f"${s[3]:.2f}",
                s[4],
                f"${s[5]:.2f}",
                f"${s[6]:.2f}"
            ])
        print(tabulate(table, headers=headers, tablefmt="grid"))
    else:
        print("Nenhum snapshot encontrado.")
    
    conn.close()

def show_market_analysis(limit=20):
    """Mostra análises de mercado recentes"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print(f"📈 ÚLTIMAS {limit} ANÁLISES DE MERCADO")
    print("="*70)
    
    cursor.execute("""
        SELECT timestamp, symbol, price, rsi, signal, reason
        FROM market_analysis
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    
    analyses = cursor.fetchall()
    
    if analyses:
        headers = ['Horário', 'Símbolo', 'Preço', 'RSI', 'Sinal', 'Razão']
        table = []
        for a in analyses:
            signal_emoji = "🟢" if a[4] == "BUY" else ("🔴" if a[4] == "SELL" else "⚪")
            table.append([
                a[0][11:19] if a[0] else '-',
                a[1],
                f"${a[2]:.2f}" if a[2] else '-',
                f"{a[3]:.1f}" if a[3] else '-',
                f"{signal_emoji} {a[4]}" if a[4] else '-',
                (a[5][:30] + '...') if a[5] and len(a[5]) > 30 else (a[5] or '-')
            ])
        print(tabulate(table, headers=headers, tablefmt="grid"))
    else:
        print("Nenhuma análise encontrada.")
    
    conn.close()

def main():
    """Menu principal"""
    try:
        from tabulate import tabulate
    except ImportError:
        print("Instalando tabulate...")
        import subprocess
        subprocess.run(['pip', 'install', 'tabulate'], check=True)
    
    print("\n" + "🎯"*35)
    print("    📊 HISTÓRICO DO BOT DE TRADING - APP LEONARDO")
    print("🎯"*35)
    
    show_trades_summary()
    show_recent_trades(10)
    show_trades_by_symbol()
    show_daily_summary()
    show_portfolio_snapshots(5)
    show_bot_events(10)
    
    print("\n" + "="*70)
    print("✅ Relatório completo gerado!")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
