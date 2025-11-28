"""
Estratégia de Trading Exemplo
Baseada em RSI + SMA Cross
"""
import logging
from typing import Optional, Dict
import pandas as pd

logger = logging.getLogger(__name__)


class SimpleRSIStrategy:
    """
    Estratégia simples baseada em RSI com ajuste dinâmico e adaptativo
    - Monitora comportamento real do RSI (últimos 30 min)
    - Ajusta thresholds baseado no que realmente acontece
    - Reduz threshold de venda para compras antigas
    - Sem posição: Aumenta oversold para comprar mais fácil
    - Com posição: Diminui overbought para vender rápido
    """
    
    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70):
        self.rsi_period = rsi_period
        self.base_oversold = oversold
        self.base_overbought = overbought
        self.oversold = oversold
        self.overbought = overbought
        self.position = None
        
        # Monitoramento adaptativo
        from collections import deque
        from datetime import datetime
        
        self.rsi_history = deque(maxlen=30)  # Últimos 30 valores RSI (30 min @ 1min)
        self.rsi_max_observed = overbought
        self.rsi_min_observed = oversold
        self.last_adjustment = datetime.now()
        
    def add_rsi_observation(self, rsi_value: float):
        """Adiciona observação de RSI ao histórico"""
        from datetime import datetime
        
        if rsi_value is None or pd.isna(rsi_value):
            return
            
        self.rsi_history.append({
            'value': rsi_value,
            'timestamp': datetime.now()
        })
        
        # Atualiza máximo e mínimo observados
        if rsi_value > self.rsi_max_observed:
            self.rsi_max_observed = rsi_value
        if rsi_value < self.rsi_min_observed:
            self.rsi_min_observed = rsi_value
    
    def adapt_thresholds(self):
        """Ajusta thresholds baseado no comportamento real do RSI"""
        from datetime import datetime, timedelta
        
        # Só ajusta a cada 5 minutos
        if (datetime.now() - self.last_adjustment).total_seconds() < 300:
            return
        
        if len(self.rsi_history) < 10:  # Precisa de dados mínimos
            return
        
        # Pega valores RSI dos últimos 30 minutos
        recent_rsi = [obs['value'] for obs in self.rsi_history]
        
        if not recent_rsi:
            return
        
        # Calcula estatísticas reais
        actual_max = max(recent_rsi)
        actual_min = min(recent_rsi)
        
        # AJUSTE INTELIGENTE:
        # Se RSI nunca chega no threshold configurado, ajusta para 90% do máximo observado
        if actual_max < self.base_overbought:
            new_overbought = max(actual_max * 0.9, self.base_oversold + 5)
            if abs(new_overbought - self.base_overbought) > 2:
                logger.info(
                    f"📊 AJUSTE ADAPTATIVO: RSI max observado={actual_max:.1f} "
                    f"→ Novo threshold venda: {new_overbought:.1f} (era {self.base_overbought})"
                )
                self.base_overbought = new_overbought
        
        # Se RSI nunca desce ao threshold de compra, ajusta para 110% do mínimo
        if actual_min > self.base_oversold:
            new_oversold = min(actual_min * 1.1, self.base_overbought - 5)
            if abs(new_oversold - self.base_oversold) > 2:
                logger.info(
                    f"📊 AJUSTE ADAPTATIVO: RSI min observado={actual_min:.1f} "
                    f"→ Novo threshold compra: {new_oversold:.1f} (era {self.base_oversold})"
                )
                self.base_oversold = new_oversold
        
        self.last_adjustment = datetime.now()
        
    def adjust_thresholds(self, has_crypto: bool, purchase_age_minutes: float = 0):
        """
        Ajusta thresholds dinamicamente:
        - Sem cripto: oversold + 5 (mais fácil comprar)
        - Com cripto: overbought - 5 (mais fácil vender)
        - Compra antiga (>5min): reduz threshold progressivamente
        """
        # Primeiro aplica ajuste adaptativo
        self.adapt_thresholds()
        
        if not has_crypto:
            # Quer comprar - aumenta oversold
            self.oversold = min(self.base_oversold + 5, self.base_overbought - 2)
            self.overbought = self.base_overbought
            logger.info(f"🔵 SEM CRIPTO - Compra: RSI<{self.oversold:.1f} | Venda: RSI>{self.overbought:.1f}")
        else:
            # Quer vender rápido - diminui overbought
            self.oversold = self.base_oversold
            base_sell = self.base_overbought - 5
            
            # REDUÇÃO POR TEMPO: Compras antigas vendem mais fácil
            time_reduction = 0
            if purchase_age_minutes > 10:
                time_reduction = 3  # -3 pontos após 10min
            elif purchase_age_minutes > 5:
                time_reduction = 1  # -1 ponto após 5min
            
            self.overbought = max(base_sell - time_reduction, self.base_oversold + 2)
            
            if time_reduction > 0:
                logger.info(
                    f"🟢 COM CRIPTO ({purchase_age_minutes:.1f}min) - "
                    f"Compra: RSI<{self.oversold:.1f} | Venda: RSI>{self.overbought:.1f} "
                    f"(redução por tempo: -{time_reduction})"
                )
            else:
                logger.info(f"🟢 COM CRIPTO - Compra: RSI<{self.oversold:.1f} | Venda: RSI>{self.overbought:.1f}")
        
    def analyze(self, df: pd.DataFrame, has_crypto: bool = False, purchase_age_minutes: float = 0) -> Dict[str, any]:
        """
        Analisa o mercado e retorna sinais
        Retorna: {'signal': 'buy'/'sell'/'hold', 'reason': str, 'rsi': float}
        """
        if df.empty or 'rsi' not in df.columns:
            logger.warning("DataFrame sem dados ou sem RSI calculado")
            return {'signal': 'hold', 'reason': 'Dados insuficientes', 'rsi': None}
        
        # Pega último valor de RSI
        current_rsi = df['rsi'].iloc[-1]
        
        if pd.isna(current_rsi):
            return {'signal': 'hold', 'reason': 'RSI não disponível', 'rsi': None}
        
        # Adiciona à observação para aprendizado adaptativo
        self.add_rsi_observation(current_rsi)
        
        # Ajusta thresholds baseado se tem cripto e idade da compra
        self.adjust_thresholds(has_crypto, purchase_age_minutes)
        
        # Lógica de trading
        if current_rsi < self.oversold:
            return {
                'signal': 'buy',
                'reason': f'RSI sobrevenda ({current_rsi:.2f} < {self.oversold:.1f})',
                'rsi': current_rsi
            }
        
        elif current_rsi > self.overbought:
            return {
                'signal': 'sell',
                'reason': f'RSI sobrecompra ({current_rsi:.2f} > {self.overbought:.1f})',
                'rsi': current_rsi
            }
        
        else:
            return {
                'signal': 'hold',
                'reason': f'RSI neutro ({current_rsi:.2f})',
                'rsi': current_rsi
            }
    
    def update_position(self, new_position: Optional[str]):
        """Atualiza posição atual"""
        self.position = new_position
        logger.info(f"📊 Posição atualizada: {new_position}")


class SMACrossStrategy:
    """
    Estratégia de cruzamento de médias móveis
    - Compra quando SMA rápida cruza SMA lenta para cima
    - Vende quando SMA rápida cruza SMA lenta para baixo
    """
    
    def __init__(self, fast_period: int = 20, slow_period: int = 50):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.position = None
        
    def analyze(self, df: pd.DataFrame) -> Dict[str, any]:
        """Analisa cruzamento de médias"""
        sma_fast_col = f'sma_{self.fast_period}'
        sma_slow_col = f'sma_{self.slow_period}'
        
        if df.empty or sma_fast_col not in df.columns or sma_slow_col not in df.columns:
            logger.warning("DataFrame sem SMAs necessárias")
            return {'signal': 'hold', 'reason': 'Dados insuficientes'}
        
        # Últimos 2 valores para detectar cruzamento
        sma_fast_curr = df[sma_fast_col].iloc[-1]
        sma_fast_prev = df[sma_fast_col].iloc[-2]
        sma_slow_curr = df[sma_slow_col].iloc[-1]
        sma_slow_prev = df[sma_slow_col].iloc[-2]
        
        # Cruzamento para cima (golden cross)
        if sma_fast_prev <= sma_slow_prev and sma_fast_curr > sma_slow_curr:
            return {
                'signal': 'buy',
                'reason': f'Golden Cross (SMA{self.fast_period} > SMA{self.slow_period})'
            }
        
        # Cruzamento para baixo (death cross)
        elif sma_fast_prev >= sma_slow_prev and sma_fast_curr < sma_slow_curr:
            return {
                'signal': 'sell',
                'reason': f'Death Cross (SMA{self.fast_period} < SMA{self.slow_period})'
            }
        
        else:
            return {
                'signal': 'hold',
                'reason': 'Sem cruzamento detectado'
            }
    
    def update_position(self, new_position: Optional[str]):
        """Atualiza posição atual"""
        self.position = new_position
        logger.info(f"📊 Posição atualizada: {new_position}")
