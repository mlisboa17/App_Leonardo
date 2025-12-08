class Logger:
    def log_trade(self, bot_name, result, profit, duration):
        print(f"[{bot_name}] Resultado: {result}, Lucro: {profit}, Tempo: {duration}min")

    def log_metrics(self, accuracy, avg_profit, max_drawdown, avg_position_time):
        print(f"Taxa de acerto: {accuracy}% | Lucro médio: {avg_profit} | Drawdown: {max_drawdown} | Tempo médio posição: {avg_position_time}min")
