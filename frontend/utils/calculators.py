"""
Calculators - Funções para cálculos de métricas e estatísticas
"""

from datetime import datetime
from typing import Dict, List
import numpy as np


def get_pnl_by_bot(history: List) -> Dict:
    """Agrupa PnL por bot"""
    pnl_by_bot = {}
    for trade in history:
        bot_type = trade.get('bot_type', 'unknown')
        if bot_type not in pnl_by_bot:
            pnl_by_bot[bot_type] = {
                'total_pnl': 0,
                'trades': 0,
                'wins': 0,
                'losses': 0
            }
        
        pnl = trade.get('pnl_usd', 0)
        pnl_by_bot[bot_type]['total_pnl'] += pnl
        pnl_by_bot[bot_type]['trades'] += 1
        if pnl > 0:
            pnl_by_bot[bot_type]['wins'] += 1
        else:
            pnl_by_bot[bot_type]['losses'] += 1
    
    return pnl_by_bot


def get_daily_pnl(history: List) -> Dict:
    """Calcula PnL diário por bot"""
    today = datetime.now().date().isoformat()
    daily_pnl = {}
    
    for trade in history:
        exit_time = trade.get('exit_time', trade.get('timestamp', ''))
        if exit_time.startswith(today):
            bot_type = trade.get('bot_type', 'unknown')
            if bot_type not in daily_pnl:
                daily_pnl[bot_type] = 0
            daily_pnl[bot_type] += trade.get('pnl_usd', 0)
    
    return daily_pnl


def get_monthly_pnl(history: List) -> Dict:
    """Calcula PnL mensal por bot"""
    current_month = datetime.now().strftime('%Y-%m')
    monthly_pnl = {}
    
    for trade in history:
        exit_time = trade.get('exit_time', trade.get('timestamp', ''))
        if exit_time.startswith(current_month):
            bot_type = trade.get('bot_type', 'unknown')
            if bot_type not in monthly_pnl:
                monthly_pnl[bot_type] = 0
            monthly_pnl[bot_type] += trade.get('pnl_usd', 0)
    
    return monthly_pnl


def calculate_sharpe_ratio(history: List, risk_free_rate: float = 0.0) -> float:
    """
    Calcula Sharpe Ratio (retorno ajustado ao risco)
    
    Args:
        history: Lista de trades
        risk_free_rate: Taxa livre de risco (default 0%)
    
    Returns:
        Sharpe Ratio (valores > 1 são bons, > 2 excelentes)
    """
    if not history:
        return 0.0
    
    returns = [t.get('pnl_pct', 0) for t in history]
    
    if len(returns) < 2:
        return 0.0
    
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    
    if std_return == 0:
        return 0.0
    
    sharpe = (mean_return - risk_free_rate) / std_return
    return round(sharpe, 2)


def calculate_max_drawdown(history: List) -> Dict:
    """
    Calcula Max Drawdown (maior queda desde o pico)
    
    Returns:
        Dict com max_drawdown (%), peak_value, trough_value, recovery_time
    """
    if not history:
        return {'max_drawdown': 0, 'peak_value': 0, 'trough_value': 0, 'recovery_time': 0}
    
    # Ordena por data
    sorted_history = sorted(history, key=lambda x: x.get('exit_time', ''))
    
    # Calcula PnL acumulado
    cumulative_pnl = 0
    cumulative_values = []
    
    for trade in sorted_history:
        cumulative_pnl += trade.get('pnl_usd', 0)
        cumulative_values.append(cumulative_pnl)
    
    if not cumulative_values:
        return {'max_drawdown': 0, 'peak_value': 0, 'trough_value': 0, 'recovery_time': 0}
    
    # Calcula drawdown
    peak = cumulative_values[0]
    max_dd = 0
    peak_value = 0
    trough_value = 0
    
    for value in cumulative_values:
        if value > peak:
            peak = value
        
        drawdown = ((peak - value) / peak * 100) if peak > 0 else 0
        
        if drawdown > max_dd:
            max_dd = drawdown
            peak_value = peak
            trough_value = value
    
    return {
        'max_drawdown': round(max_dd, 2),
        'peak_value': round(peak_value, 2),
        'trough_value': round(trough_value, 2),
        'recovery_time': 0  # TODO: calcular tempo de recuperação
    }


def calculate_profit_factor(history: List) -> float:
    """
    Calcula Profit Factor (total wins / total losses)
    
    Returns:
        Profit Factor (valores > 1.5 são bons, > 2 excelentes)
    """
    if not history:
        return 0.0
    
    total_wins = sum(t.get('pnl_usd', 0) for t in history if t.get('pnl_usd', 0) > 0)
    total_losses = abs(sum(t.get('pnl_usd', 0) for t in history if t.get('pnl_usd', 0) < 0))
    
    if total_losses == 0:
        return float('inf') if total_wins > 0 else 0.0
    
    return round(total_wins / total_losses, 2)


def calculate_win_rate(history: List) -> float:
    """Calcula taxa de vitória"""
    if not history:
        return 0.0
    
    wins = sum(1 for t in history if t.get('pnl_usd', 0) > 0)
    return round((wins / len(history)) * 100, 2)


def calculate_avg_win_loss_ratio(history: List) -> Dict:
    """Calcula média de ganhos vs perdas"""
    wins = [t.get('pnl_usd', 0) for t in history if t.get('pnl_usd', 0) > 0]
    losses = [abs(t.get('pnl_usd', 0)) for t in history if t.get('pnl_usd', 0) < 0]
    
    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses) if losses else 0
    
    ratio = (avg_win / avg_loss) if avg_loss > 0 else 0
    
    return {
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'ratio': round(ratio, 2)
    }


def get_top_symbols(history: List, top_n: int = 5) -> List[Dict]:
    """
    Retorna top N symbols mais lucrativos
    
    Returns:
        Lista de dicts com symbol, total_pnl, trades, win_rate
    """
    symbol_stats = {}
    
    for trade in history:
        symbol = trade.get('symbol', '')
        if not symbol:
            continue
        
        if symbol not in symbol_stats:
            symbol_stats[symbol] = {
                'symbol': symbol,
                'total_pnl': 0,
                'trades': 0,
                'wins': 0
            }
        
        pnl = trade.get('pnl_usd', 0)
        symbol_stats[symbol]['total_pnl'] += pnl
        symbol_stats[symbol]['trades'] += 1
        if pnl > 0:
            symbol_stats[symbol]['wins'] += 1
    
    # Calcula win rate
    for symbol in symbol_stats.values():
        symbol['win_rate'] = (symbol['wins'] / symbol['trades'] * 100) if symbol['trades'] > 0 else 0
    
    # Ordena por PnL total
    sorted_symbols = sorted(symbol_stats.values(), key=lambda x: x['total_pnl'], reverse=True)
    
    return sorted_symbols[:top_n]


def get_worst_symbols(history: List, worst_n: int = 5) -> List[Dict]:
    """
    Retorna worst N symbols (maiores perdedores)
    
    Returns:
        Lista de dicts com symbol, total_pnl, trades, win_rate
    """
    symbol_stats = {}
    
    for trade in history:
        symbol = trade.get('symbol', '')
        if not symbol:
            continue
        
        if symbol not in symbol_stats:
            symbol_stats[symbol] = {
                'symbol': symbol,
                'total_pnl': 0,
                'trades': 0,
                'wins': 0
            }
        
        pnl = trade.get('pnl_usd', 0)
        symbol_stats[symbol]['total_pnl'] += pnl
        symbol_stats[symbol]['trades'] += 1
        if pnl > 0:
            symbol_stats[symbol]['wins'] += 1
    
    # Calcula win rate
    for symbol in symbol_stats.values():
        symbol['win_rate'] = (symbol['wins'] / symbol['trades'] * 100) if symbol['trades'] > 0 else 0
    
    # Ordena por PnL total (menor primeiro)
    sorted_symbols = sorted(symbol_stats.values(), key=lambda x: x['total_pnl'])
    
    return sorted_symbols[:worst_n]
