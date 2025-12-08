class RiskManagement:
    def __init__(self, max_loss_daily=30, max_trades_hour=10, max_exposure_coin=20):
        self.max_loss_daily = max_loss_daily
        self.max_trades_hour = max_trades_hour
        self.max_exposure_coin = max_exposure_coin

    def check_limits(self, bot_name, trades_today, loss_today, exposure_coin):
        if loss_today <= -self.max_loss_daily:
            return False, "Limite de perda diária atingido"
        if trades_today >= self.max_trades_hour:
            return False, "Limite de trades por hora atingido"
        if exposure_coin > self.max_exposure_coin:
            return False, "Exposição máxima por moeda excedida"
        return True, "OK"
