class PortfolioManager:
    def __init__(self, global_tp=50, global_sl=-30):
        self.global_tp = global_tp
        self.global_sl = global_sl

    def check_portfolio(self, total_profit):
        if total_profit >= self.global_tp:
            return "Take Profit Global atingido → liquidar tudo"
        elif total_profit <= self.global_sl:
            return "Stop Global atingido → pausar operações"
        return "OK"
