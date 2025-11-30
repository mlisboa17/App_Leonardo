"""
🎯 Estratégia de SCALPING - Meta $100/dia
Múltiplas operações rápidas com lucros pequenos
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta


class ScalpingStrategy:
    """
    Estratégia de Scalping para atingir $100/dia
    
    Características:
    - Múltiplas operações (50+ trades/dia)
    - Take profit pequeno (0.8%)
    - Stop loss apertado (1.5%)
    - RSI mais agressivo (35/65)
    - Timeframe de 1 minuto
    """
    
    def __init__(self):
        self.name = "Scalping Strategy"
        
        # Parâmetros de scalping
        self.rsi_oversold = 35
        self.rsi_overbought = 65
        self.stop_loss_pct = 1.5  # 1.5% stop
        self.take_profit_pct = 0.8  # 0.8% take
        
        # Meta diária
        self.daily_target = 100.0  # $100/dia
        self.min_trades_per_day = 50
        
        # Controle de trades
        self.last_trade_time = {}
        self.cooldown_seconds = 10
        
        # Estatísticas
        self.trades_today = 0
        self.profit_today = 0.0
        self.last_reset = datetime.now().date()
    
    def reset_daily_stats(self):
        """Reseta estatísticas diárias"""
        today = datetime.now().date()
        if today != self.last_reset:
            self.trades_today = 0
            self.profit_today = 0.0
            self.last_reset = today
            print(f"📅 Nova sessão de trading: {today}")
    
    def can_trade(self, symbol: str) -> bool:
        """Verifica se pode tradear (cooldown)"""
        if symbol not in self.last_trade_time:
            return True
        
        time_since_last = (datetime.now() - self.last_trade_time[symbol]).total_seconds()
        return time_since_last >= self.cooldown_seconds
    
    def should_buy(self, df: pd.DataFrame, symbol: str) -> Tuple[bool, str]:
        """
        Sinal de COMPRA - Scalping
        
        Condições:
        1. RSI < 35 (oversold agressivo)
        2. MACD cruzando pra cima
        3. Volume acima da média
        4. Preço tocou SMA 20 (suporte)
        5. Sem cooldown
        """
        if df.empty or len(df) < 20:
            return False, "Dados insuficientes"
        
        # Reseta stats diárias
        self.reset_daily_stats()
        
        # Verifica cooldown
        if not self.can_trade(symbol):
            return False, f"Cooldown ({self.cooldown_seconds}s)"
        
        # Verifica se já atingiu meta
        if self.profit_today >= self.daily_target:
            return False, f"Meta diária atingida: ${self.profit_today:.2f}"
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Indicadores
        rsi = last.get('rsi', 50)
        macd = last.get('macd', 0)
        macd_signal = last.get('macd_signal', 0)
        macd_prev = prev.get('macd', 0)
        macd_signal_prev = prev.get('macd_signal', 0)
        volume = last.get('volume', 0)
        avg_volume = df['volume'].tail(20).mean()
        close = last.get('close', 0)
        sma_20 = last.get('sma_20', close)
        
        # Condições de COMPRA (Scalping)
        conditions = []
        
        # 1. RSI oversold agressivo
        rsi_buy = rsi < self.rsi_oversold
        conditions.append(('RSI < 35', rsi_buy, f'{rsi:.1f}'))
        
        # 2. MACD cruzando pra cima (momentum)
        macd_cross = (macd > macd_signal) and (macd_prev <= macd_signal_prev)
        conditions.append(('MACD Cruz ↑', macd_cross, f'{macd:.2f}'))
        
        # 3. Volume forte (confirmação)
        volume_ok = volume > avg_volume * 1.2
        conditions.append(('Volume ↑', volume_ok, f'{volume/avg_volume:.2f}x'))
        
        # 4. Preço próximo de suporte (SMA 20)
        near_support = abs(close - sma_20) / sma_20 < 0.005  # 0.5% de distância
        conditions.append(('Próx SMA20', near_support, f'{abs(close-sma_20)/sma_20*100:.2f}%'))
        
        # Decisão: pelo menos 3 de 4 condições
        true_conditions = sum([c[1] for c in conditions])
        
        if true_conditions >= 3:
            reason = "SCALP BUY: " + ", ".join([f"{c[0]}={c[2]}" for c in conditions if c[1]])
            return True, reason
        
        return False, "Aguardando setup completo"
    
    def should_sell(self, df: pd.DataFrame, entry_price: float, current_price: float, symbol: str) -> Tuple[bool, str]:
        """
        Sinal de VENDA - Scalping
        
        Condições de Saída:
        1. Take profit atingido (0.8%)
        2. Stop loss atingido (1.5%)
        3. RSI overbought (> 65)
        4. MACD cruzando pra baixo
        5. Volume fraco
        """
        if df.empty:
            return False, "Dados insuficientes"
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Calcula PnL
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # 1. TAKE PROFIT (0.8%)
        if pnl_pct >= self.take_profit_pct:
            return True, f"✅ TAKE PROFIT: +{pnl_pct:.2f}% (meta: {self.take_profit_pct}%)"
        
        # 2. STOP LOSS (1.5%)
        if pnl_pct <= -self.stop_loss_pct:
            return True, f"🛑 STOP LOSS: {pnl_pct:.2f}% (limite: -{self.stop_loss_pct}%)"
        
        # Indicadores
        rsi = last.get('rsi', 50)
        macd = last.get('macd', 0)
        macd_signal = last.get('macd_signal', 0)
        macd_prev = prev.get('macd', 0)
        macd_signal_prev = prev.get('macd_signal', 0)
        
        # 3. RSI OVERBOUGHT (vende mesmo com lucro pequeno)
        if rsi > self.rsi_overbought and pnl_pct > 0.3:  # Pelo menos 0.3% lucro
            return True, f"📈 RSI OVERBOUGHT: {rsi:.1f} | Lucro: +{pnl_pct:.2f}%"
        
        # 4. MACD virando pra baixo (perda de momentum)
        macd_cross_down = (macd < macd_signal) and (macd_prev >= macd_signal_prev)
        if macd_cross_down and pnl_pct > 0.2:  # Realiza lucro pequeno
            return True, f"📉 MACD Cruz ↓ | Lucro: +{pnl_pct:.2f}%"
        
        # 5. Proteção: se está há mais de 5 minutos e lucro > 0.5%
        # (evita deixar trade muito tempo aberto)
        # Esta verificação seria feita no trading_engine
        
        return False, f"Mantendo posição | PnL: {pnl_pct:+.2f}%"
    
    def update_stats(self, profit: float, symbol: str):
        """Atualiza estatísticas após trade"""
        self.trades_today += 1
        self.profit_today += profit
        self.last_trade_time[symbol] = datetime.now()
        
        # Log de progresso
        progress = (self.profit_today / self.daily_target) * 100
        print(f"📊 Trade #{self.trades_today} | Lucro: ${profit:+.2f} | Total hoje: ${self.profit_today:+.2f} | Meta: {progress:.1f}%")
    
    def get_daily_stats(self) -> Dict:
        """Retorna estatísticas do dia"""
        progress = (self.profit_today / self.daily_target) * 100 if self.daily_target > 0 else 0
        avg_profit_per_trade = self.profit_today / self.trades_today if self.trades_today > 0 else 0
        
        return {
            'trades_today': self.trades_today,
            'profit_today': self.profit_today,
            'daily_target': self.daily_target,
            'progress_pct': progress,
            'avg_profit_per_trade': avg_profit_per_trade,
            'target_achieved': self.profit_today >= self.daily_target,
            'min_trades_met': self.trades_today >= self.min_trades_per_day
        }
    
    def calculate_position_size(self, balance: float, max_risk_pct: float = 2.0) -> float:
        """
        Calcula tamanho da posição baseado no risco
        
        Para scalping:
        - Risco de 2% do balance por trade
        - Com stop de 1.5%, isso permite recuperar rápido
        """
        risk_amount = balance * (max_risk_pct / 100)
        
        # Posição = Risco / Stop Loss %
        position_size = risk_amount / (self.stop_loss_pct / 100)
        
        # Limita a $20 por trade
        return min(position_size, 20.0)
    
    def get_optimal_symbols(self, market_data: Dict) -> list:
        """
        Retorna símbolos mais propícios para scalping
        
        Prioriza:
        1. Alta volatilidade intraday
        2. Volume alto
        3. Spreads baixos
        """
        scored_symbols = []
        
        for symbol, data in market_data.items():
            score = 0
            
            # Volume (peso 40%)
            volume_score = data.get('volume_24h', 0) / 1000000  # Normaliza
            score += min(volume_score * 0.4, 40)
            
            # Volatilidade (peso 40%)
            high = data.get('high_24h', 0)
            low = data.get('low_24h', 0)
            current = data.get('price', 0)
            if current > 0:
                volatility = ((high - low) / current) * 100
                score += min(volatility * 2, 40)
            
            # Spread (peso 20% - quanto menor, melhor)
            spread = data.get('spread', 0.1)
            spread_score = max(0, 20 - (spread * 100))
            score += spread_score
            
            scored_symbols.append((symbol, score))
        
        # Ordena por score e retorna top 4
        scored_symbols.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored_symbols[:4]]


# Estratégia global
scalping_strategy = ScalpingStrategy()


def get_strategy():
    """Retorna instância da estratégia"""
    return scalping_strategy
