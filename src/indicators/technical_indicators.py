"""
Módulo de Indicadores Técnicos
Utiliza cálculos nativos com pandas/numpy (compatível com Python 3.14)
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Usando cálculos nativos - sem dependência de pandas_ta/TA-Lib
PANDAS_TA_AVAILABLE = False


class TechnicalIndicators:
    """Calcula indicadores técnicos"""
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
        """Calcula RSI (Relative Strength Index) - Implementação nativa"""
        delta = df[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, 
                      signal: int = 9, column: str = 'close') -> pd.DataFrame:
        """Calcula MACD - Implementação nativa"""
        exp1 = df[column].ewm(span=fast, adjust=False).mean()
        exp2 = df[column].ewm(span=slow, adjust=False).mean()
        
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_histogram = macd - macd_signal
        
        return pd.DataFrame({
            'MACD_12_26_9': macd,
            'MACDs_12_26_9': macd_signal,
            'MACDh_12_26_9': macd_histogram
        })
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
        """Calcula SMA (Simple Moving Average)"""
        return df[column].rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
        """Calcula EMA (Exponential Moving Average)"""
        return df[column].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, 
                                  std: float = 2, column: str = 'close') -> pd.DataFrame:
        """Calcula Bandas de Bollinger - Implementação nativa"""
        sma = df[column].rolling(window=period).mean()
        rolling_std = df[column].rolling(window=period).std()
        
        upper_band = sma + (rolling_std * std)
        lower_band = sma - (rolling_std * std)
        
        return pd.DataFrame({
            f'BBL_{period}_{std}': lower_band,
            f'BBM_{period}_{std}': sma,
            f'BBU_{period}_{std}': upper_band
        })
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """
        Calcula todos os indicadores configurados
        df deve ter colunas: open, high, low, close, volume
        """
        if df.empty:
            logger.warning("DataFrame vazio para cálculo de indicadores")
            return df
        
        # RSI
        if 'rsi' in config:
            rsi_config = config['rsi']
            df['rsi'] = TechnicalIndicators.calculate_rsi(
                df, 
                period=rsi_config.get('period', 14)
            )
        
        # MACD
        if 'macd' in config:
            macd_config = config['macd']
            macd_result = TechnicalIndicators.calculate_macd(
                df,
                fast=macd_config.get('fast', 12),
                slow=macd_config.get('slow', 26),
                signal=macd_config.get('signal', 9)
            )
            if not macd_result.empty:
                df = pd.concat([df, macd_result], axis=1)
        
        # SMAs
        if 'sma' in config:
            periods = config['sma'].get('periods', [20, 50, 200])
            for period in periods:
                df[f'sma_{period}'] = TechnicalIndicators.calculate_sma(df, period=period)
        
        logger.info(f"✅ Indicadores calculados: {df.columns.tolist()}")
        return df
