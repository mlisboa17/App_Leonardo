def get_pnl_by_bot(history):
    pnl_by_bot = {}
    for trade in history:
        bot_type = trade.get('bot_type', 'unknown')
        stats = pnl_by_bot.setdefault(bot_type, {'total_pnl': 0, 'trades': 0, 'wins': 0, 'losses': 0})
        pnl = trade.get('pnl_usd', 0)
        stats['total_pnl'] += pnl
        stats['trades'] += 1
        if pnl > 0:
            stats['wins'] += 1
        else:
            stats['losses'] += 1
    return pnl_by_bot

def get_daily_pnl(history):
    from datetime import datetime, timedelta
    # Define o período diário: das 00:00:01 às 23:59:59 do dia atual
    today = datetime.now().date()
    start_of_day = datetime.combine(today, datetime.min.time()) + timedelta(seconds=1)  # 00:00:01
    end_of_day = datetime.combine(today, datetime.max.time())  # 23:59:59

    daily_pnl = {}
    for trade in history:
        exit_time_str = trade.get('exit_time', trade.get('timestamp', ''))
        if exit_time_str:
            try:
                exit_time = datetime.fromisoformat(exit_time_str.replace('Z', '+00:00'))
                if start_of_day <= exit_time <= end_of_day:
                    bot_type = trade.get('bot_type', 'unknown')
                    daily_pnl[bot_type] = daily_pnl.get(bot_type, 0) + trade.get('pnl_usd', 0)
            except ValueError:
                # Se não conseguir parsear a data, usa o método antigo como fallback
                if exit_time_str.startswith(today.isoformat()):
                    bot_type = trade.get('bot_type', 'unknown')
                    daily_pnl[bot_type] = daily_pnl.get(bot_type, 0) + trade.get('pnl_usd', 0)
    return daily_pnl

def get_monthly_pnl(history):
    from datetime import datetime, timedelta
    # Define o período mensal: do dia 01 às 23:59:59 do último dia do mês atual
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1, 0, 0, 1)  # 00:00:01 do dia 01
    # Último dia do mês
    if now.month == 12:
        end_of_month = datetime(now.year + 1, 1, 1, 23, 59, 59) - timedelta(days=1)
    else:
        end_of_month = datetime(now.year, now.month + 1, 1, 23, 59, 59) - timedelta(days=1)

    monthly_pnl = {}
    for trade in history:
        exit_time_str = trade.get('exit_time', trade.get('timestamp', ''))
        if exit_time_str:
            try:
                exit_time = datetime.fromisoformat(exit_time_str.replace('Z', '+00:00'))
                if start_of_month <= exit_time <= end_of_month:
                    bot_type = trade.get('bot_type', 'unknown')
                    monthly_pnl[bot_type] = monthly_pnl.get(bot_type, 0) + trade.get('pnl_usd', 0)
            except ValueError:
                # Se não conseguir parsear a data, usa o método antigo como fallback
                current_month = now.strftime('%Y-%m')
                if exit_time_str.startswith(current_month):
                    bot_type = trade.get('bot_type', 'unknown')
                    monthly_pnl[bot_type] = monthly_pnl.get(bot_type, 0) + trade.get('pnl_usd', 0)
    return monthly_pnl

# Configurações salvas dos períodos de métricas
METRICS_CONFIG = {
    'daily_period': {
        'start': '00:00:01',
        'end': '23:59:59',
        'description': 'Métricas diárias das 00:00:01 às 23:59:59'
    },
    'monthly_period': {
        'start': '01 00:00:01',
        'end': 'último_dia 23:59:59',
        'description': 'Métricas mensais do dia 01 às 23:59:59 do último dia'
    }
}


# Novo cálculo: Risk-Reward Ratio (R-R)
def calculate_risk_reward(trade_pnls):
    """
    Calcula o PnL médio vencedor e o Risco-Recompensa (RR) de uma lista de PnLs de trades.
    RR = PnL Médio de Vitórias / |PnL Médio de Perdas|
    Retorna (avg_win, risk_reward)
    """
    wins_pnl = [p for p in trade_pnls if p > 0]
    losses_pnl = [p for p in trade_pnls if p < 0]

    avg_win = sum(wins_pnl) / len(wins_pnl) if wins_pnl else 0
    avg_loss = sum(losses_pnl) / len(losses_pnl) if losses_pnl else 0

    if avg_loss == 0:
        return avg_win, float('inf')

    risk_reward = avg_win / abs(avg_loss)
    return avg_win, risk_reward
