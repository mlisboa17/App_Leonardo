"""
Estratégias de Trading Simples
Implementa estratégias baseadas em indicadores técnicos
"""
import logging
import pandas as pd
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class SimpleStrategy:
    """Estratégia de trading baseada em RSI e MACD"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.rsi_oversold = config.get('indicators', {}).get('rsi', {}).get('oversold', 30)
        self.rsi_overbought = config.get('indicators', {}).get('rsi', {}).get('overbought', 70)
        self.name = "RSI + MACD Strategy"
        
        logger.info(f"📊 Estratégia inicializada: {self.name}")
        logger.info(f"   RSI Oversold: {self.rsi_oversold}")
        logger.info(f"   RSI Overbought: {self.rsi_overbought}")
    
    def analyze(self, df: pd.DataFrame, symbol: str) -> Tuple[str, str, Dict]:
        """
        Analisa dados e gera sinal de trading
        
        Returns:
            Tuple[str, str, Dict]: (signal, reason, indicators)
            - signal: 'BUY', 'SELL', ou 'HOLD'
            - reason: Explicação do sinal
            - indicators: Valores dos indicadores
        """
        if df.empty or len(df) < 2:
            return 'HOLD', 'Dados insuficientes', {}
        
        # Obtém última linha de dados
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Extrai indicadores
        indicators = {
            'rsi': current.get('rsi', 50),
            'macd': current.get('MACD_12_26_9', 0),
            'macd_signal': current.get('MACDs_12_26_9', 0),
            'macd_histogram': current.get('MACDh_12_26_9', 0),
            'sma_20': current.get('sma_20', 0),
            'sma_50': current.get('sma_50', 0),
            'price': current.get('close', 0),
        }
        
        # Indicadores da vela anterior
        prev_indicators = {
            'macd': previous.get('MACD_12_26_9', 0),
            'macd_signal': previous.get('MACDs_12_26_9', 0),
        }
        
        # Lógica de COMPRA
        buy_conditions = []
        
        # Condição 1: RSI em oversold
        if indicators['rsi'] < self.rsi_oversold:
            buy_conditions.append(f"RSI oversold ({indicators['rsi']:.1f})")
        
        # Condição 2: MACD cruzou para cima
        if (prev_indicators['macd'] < prev_indicators['macd_signal'] and 
            indicators['macd'] > indicators['macd_signal']):
            buy_conditions.append("MACD cruzou para cima")
        
        # Condição 3: Preço acima da SMA20 (tendência de alta)
        if indicators['price'] > indicators['sma_20'] > 0:
            buy_conditions.append("Preço acima SMA20")
        
        # Lógica de VENDA
        sell_conditions = []
        
        # Condição 1: RSI em overbought
        if indicators['rsi'] > self.rsi_overbought:
            sell_conditions.append(f"RSI overbought ({indicators['rsi']:.1f})")
        
        # Condição 2: MACD cruzou para baixo
        if (prev_indicators['macd'] > prev_indicators['macd_signal'] and 
            indicators['macd'] < indicators['macd_signal']):
            sell_conditions.append("MACD cruzou para baixo")
        
        # Condição 3: Preço abaixo da SMA20 (tendência de baixa)
        if indicators['price'] < indicators['sma_20'] and indicators['sma_20'] > 0:
            sell_conditions.append("Preço abaixo SMA20")
        
        # Decisão final (precisa de pelo menos 2 condições)
        if len(buy_conditions) >= 2:
            reason = " + ".join(buy_conditions)
            logger.info(f"🟢 SINAL DE COMPRA para {symbol}: {reason}")
            return 'BUY', reason, indicators
        
        elif len(sell_conditions) >= 2:
            reason = " + ".join(sell_conditions)
            logger.info(f"🔴 SINAL DE VENDA para {symbol}: {reason}")
            return 'SELL', reason, indicators
        
        else:
            # Log das condições parciais
            if buy_conditions:
                logger.debug(f"⚪ {symbol} - Condições de compra parciais: {', '.join(buy_conditions)}")
            if sell_conditions:
                logger.debug(f"⚪ {symbol} - Condições de venda parciais: {', '.join(sell_conditions)}")
            
            return 'HOLD', 'Aguardando confirmação', indicators


class AggressiveStrategy(SimpleStrategy):
    """Estratégia mais agressiva (requer apenas 1 condição)"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "Aggressive RSI + MACD"
        self.rsi_oversold = 40  # Menos extremo
        self.rsi_overbought = 60
        logger.info(f"📊 Estratégia agressiva: RSI {self.rsi_oversold}/{self.rsi_overbought}")
    
    def analyze(self, df: pd.DataFrame, symbol: str) -> Tuple[str, str, Dict]:
        """Análise mais agressiva - aceita 1 condição"""
        signal, reason, indicators = super().analyze(df, symbol)
        
        # Se não teve sinal, tenta com critérios mais relaxados
        if signal == 'HOLD':
            if indicators.get('rsi', 50) < self.rsi_oversold:
                return 'BUY', f"RSI oversold agressivo ({indicators['rsi']:.1f})", indicators
            elif indicators.get('rsi', 50) > self.rsi_overbought:
                return 'SELL', f"RSI overbought agressivo ({indicators['rsi']:.1f})", indicators
        
        return signal, reason, indicators


class ConservativeStrategy(SimpleStrategy):
    """Estratégia conservadora (precisa de 3 condições)"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "Conservative RSI + MACD + Trend"
        self.rsi_oversold = 25  # Mais extremo
        self.rsi_overbought = 75
        logger.info(f"📊 Estratégia conservadora: RSI {self.rsi_oversold}/{self.rsi_overbought}")
    
    def analyze(self, df: pd.DataFrame, symbol: str) -> Tuple[str, str, Dict]:
        """Análise conservadora - exige 3 condições"""
        signal, reason, indicators = super().analyze(df, symbol)
        
        # Só aceita sinal se tiver TODAS as 3 condições principais
        if signal in ['BUY', 'SELL']:
            condition_count = len(reason.split('+'))
            if condition_count < 3:
                logger.debug(f"⚪ {symbol} - Sinal {signal} rejeitado (apenas {condition_count} condições)")
                return 'HOLD', 'Aguardando mais confirmações (conservador)', indicators
        
        return signal, reason, indicators


def get_strategy(strategy_name: str, config: Dict) -> SimpleStrategy:
    """Factory function para obter estratégia"""
    strategies = {
        'simple': SimpleStrategy,
        'aggressive': AggressiveStrategy,
        'conservative': ConservativeStrategy,
    }
    
    strategy_class = strategies.get(strategy_name.lower(), SimpleStrategy)
    return strategy_class(config)
