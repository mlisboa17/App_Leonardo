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
    Estratégia simples baseada em RSI
    - Compra quando RSI < oversold
    - Vende quando RSI > overbought
    """
    
    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70):
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.position = None  # 'long', 'short', None
        
    def analyze(self, df: pd.DataFrame) -> Dict[str, any]:
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
        
        # Lógica de trading
        if current_rsi < self.oversold and self.position != 'long':
            return {
                'signal': 'buy',
                'reason': f'RSI em zona de sobrevenda ({current_rsi:.2f})',
                'rsi': current_rsi
            }
        
        elif current_rsi > self.overbought and self.position == 'long':
            return {
                'signal': 'sell',
                'reason': f'RSI em zona de sobrecompra ({current_rsi:.2f})',
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
