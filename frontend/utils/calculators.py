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
    from datetime import datetime
    today = datetime.now().date().isoformat()
    daily_pnl = {}
    for trade in history:
        exit_time = trade.get('exit_time', trade.get('timestamp', ''))
        if exit_time.startswith(today):
            bot_type = trade.get('bot_type', 'unknown')
            daily_pnl[bot_type] = daily_pnl.get(bot_type, 0) + trade.get('pnl_usd', 0)
    return daily_pnl

def get_monthly_pnl(history):
    from datetime import datetime
    current_month = datetime.now().strftime('%Y-%m')
    monthly_pnl = {}
    for trade in history:
        exit_time = trade.get('exit_time', trade.get('timestamp', ''))
        if exit_time.startswith(current_month):
            bot_type = trade.get('bot_type', 'unknown')
            monthly_pnl[bot_type] = monthly_pnl.get(bot_type, 0) + trade.get('pnl_usd', 0)
    return monthly_pnl


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
