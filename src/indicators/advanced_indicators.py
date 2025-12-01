"""
🚀 Indicadores Técnicos Avançados - App Leonardo
Powered by pandas-ta - 50+ indicadores profissionais
"""
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class AdvancedIndicators:
    """Classe com indicadores técnicos avançados usando pandas-ta"""
    
    def __init__(self):
        """Inicializa o módulo de indicadores avançados"""
        self.available_indicators = [
            'RSI', 'MACD', 'Bollinger Bands', 'Supertrend', 'Ichimoku',
            'Stochastic', 'Williams %R', 'CCI', 'ADX', 'Parabolic SAR',
            'VWAP', 'ATR', 'Fibonacci Retracements', 'Pivot Points',
            'Support/Resistance', 'Momentum Oscillators'
        ]
        print(f"🚀 AdvancedIndicators inicializado com {len(self.available_indicators)} categorias")
    
    def calculate_all_indicators(self, df: pd.DataFrame, symbol: str = "CRYPTO") -> pd.DataFrame:
        """
        Calcula TODOS os indicadores avançados em um DataFrame
        
        Args:
            df: DataFrame com colunas OHLCV
            symbol: Símbolo da crypto para logging
            
        Returns:
            DataFrame com todos os indicadores adicionados
        """
        try:
            print(f"📊 Calculando indicadores avançados para {symbol}...")
            
            # Garantir que temos as colunas necessárias
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"DataFrame precisa ter colunas: {required_cols}")
            
            # Fazer cópia para não modificar original
            df_enhanced = df.copy()
            
            # === TREND INDICATORS ===
            df_enhanced = self._add_trend_indicators(df_enhanced)
            
            # === MOMENTUM INDICATORS ===
            df_enhanced = self._add_momentum_indicators(df_enhanced)
            
            # === VOLATILITY INDICATORS ===
            df_enhanced = self._add_volatility_indicators(df_enhanced)
            
            # === VOLUME INDICATORS ===
            df_enhanced = self._add_volume_indicators(df_enhanced)
            
            # === SUPPORT/RESISTANCE ===
            df_enhanced = self._add_support_resistance(df_enhanced)
            
            # === PATTERN RECOGNITION ===
            df_enhanced = self._add_pattern_recognition(df_enhanced)
            
            # === MARKET STRUCTURE ===
            df_enhanced = self._add_market_structure(df_enhanced)
            
            print(f"✅ {symbol}: {len(df_enhanced.columns)} indicadores calculados")
            return df_enhanced
            
        except Exception as e:
            print(f"❌ Erro ao calcular indicadores para {symbol}: {e}")
            return df
    
    def _add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona indicadores de tendência"""
        try:
            # Supertrend (Melhor que SMA simples)
            supertrend = ta.supertrend(df['high'], df['low'], df['close'])
            df = pd.concat([df, supertrend], axis=1)
            
            # Ichimoku Cloud (Sistema completo japonês)
            ichimoku = ta.ichimoku(df['high'], df['low'], df['close'])
            df = pd.concat([df, ichimoku[0]], axis=1)  # Tenkan, Kijun, Senkou
            
            # Parabolic SAR (Stop and Reverse)
            df['PSAR'] = ta.psar(df['high'], df['low'], df['close'])
            
            # ADX (Average Directional Index) - Força da tendência
            adx = ta.adx(df['high'], df['low'], df['close'])
            df = pd.concat([df, adx], axis=1)
            
            # Aroon (Identificação de tendência)
            aroon = ta.aroon(df['high'], df['low'])
            df = pd.concat([df, aroon], axis=1)
            
            # VWAP (Volume Weighted Average Price)
            df['VWAP'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
            
            print("✅ Indicadores de tendência adicionados")
            return df
            
        except Exception as e:
            print(f"⚠️ Erro em indicadores de tendência: {e}")
            return df
    
    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona indicadores de momentum"""
        try:
            # RSI em múltiplos períodos
            df['RSI_14'] = ta.rsi(df['close'], length=14)
            df['RSI_21'] = ta.rsi(df['close'], length=21)
            
            # Stochastic (Oscilador estocástico)
            stoch = ta.stoch(df['high'], df['low'], df['close'])
            df = pd.concat([df, stoch], axis=1)
            
            # Williams %R
            df['WILLR'] = ta.willr(df['high'], df['low'], df['close'])
            
            # CCI (Commodity Channel Index)
            df['CCI'] = ta.cci(df['high'], df['low'], df['close'])
            
            # ROC (Rate of Change)
            df['ROC'] = ta.roc(df['close'])
            
            # MFI (Money Flow Index)
            df['MFI'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'])
            
            # MACD Aprimorado
            macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
            df = pd.concat([df, macd], axis=1)
            
            print("✅ Indicadores de momentum adicionados")
            return df
            
        except Exception as e:
            print(f"⚠️ Erro em indicadores de momentum: {e}")
            return df
    
    def _add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona indicadores de volatilidade"""
        try:
            # Bollinger Bands
            bbands = ta.bbands(df['close'])
            df = pd.concat([df, bbands], axis=1)
            
            # ATR (Average True Range)
            df['ATR'] = ta.atr(df['high'], df['low'], df['close'])
            
            # Keltner Channels
            kc = ta.kc(df['high'], df['low'], df['close'])
            df = pd.concat([df, kc], axis=1)
            
            # Donchian Channels
            dc = ta.donchian(df['high'], df['low'])
            df = pd.concat([df, dc], axis=1)
            
            # True Range
            df['TRANGE'] = ta.true_range(df['high'], df['low'], df['close'])
            
            print("✅ Indicadores de volatilidade adicionados")
            return df
            
        except Exception as e:
            print(f"⚠️ Erro em indicadores de volatilidade: {e}")
            return df
    
    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona indicadores de volume"""
        try:
            # On Balance Volume
            df['OBV'] = ta.obv(df['close'], df['volume'])
            
            # Volume SMA
            df['VOLUME_SMA'] = ta.sma(df['volume'], length=20)
            
            # A/D Line (Accumulation/Distribution)
            df['AD'] = ta.ad(df['high'], df['low'], df['close'], df['volume'])
            
            # Chaikin Money Flow
            df['CMF'] = ta.cmf(df['high'], df['low'], df['close'], df['volume'])
            
            # Volume Profile (aproximação)
            df['VOLUME_RATIO'] = df['volume'] / df['VOLUME_SMA']
            
            print("✅ Indicadores de volume adicionados")
            return df
            
        except Exception as e:
            print(f"⚠️ Erro em indicadores de volume: {e}")
            return df
    
    def _add_support_resistance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona níveis de suporte e resistência"""
        try:
            # Pivot Points
            pivot = ta.pivot_points(df['high'], df['low'], df['close'])
            if pivot is not None:
                df = pd.concat([df, pivot], axis=1)
            
            # Fibonacci Retracements (aproximação)
            high_20 = df['high'].rolling(20).max()
            low_20 = df['low'].rolling(20).min()
            
            df['FIB_236'] = low_20 + 0.236 * (high_20 - low_20)
            df['FIB_382'] = low_20 + 0.382 * (high_20 - low_20)
            df['FIB_500'] = low_20 + 0.500 * (high_20 - low_20)
            df['FIB_618'] = low_20 + 0.618 * (high_20 - low_20)
            
            # Support/Resistance dinâmicos
            df['RESISTANCE'] = df['high'].rolling(20).max()
            df['SUPPORT'] = df['low'].rolling(20).min()
            
            print("✅ Suporte e Resistência adicionados")
            return df
            
        except Exception as e:
            print(f"⚠️ Erro em suporte/resistência: {e}")
            return df
    
    def _add_pattern_recognition(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona reconhecimento de padrões"""
        try:
            # Hammer e Doji (padrões de candlestick)
            df['HAMMER'] = ta.cdl_pattern(df['open'], df['high'], df['low'], df['close'], name="hammer")
            df['DOJI'] = ta.cdl_pattern(df['open'], df['high'], df['low'], df['close'], name="doji")
            
            # Engulfing patterns
            df['ENGULFING'] = ta.cdl_pattern(df['open'], df['high'], df['low'], df['close'], name="engulfing")
            
            # Higher Highs / Lower Lows
            df['HIGHER_HIGH'] = (df['high'] > df['high'].shift(1)) & (df['high'].shift(1) > df['high'].shift(2))
            df['LOWER_LOW'] = (df['low'] < df['low'].shift(1)) & (df['low'].shift(1) < df['low'].shift(2))
            
            print("✅ Reconhecimento de padrões adicionado")
            return df
            
        except Exception as e:
            print(f"⚠️ Erro em padrões: {e}")
            return df
    
    def _add_market_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona análise de estrutura de mercado"""
        try:
            # Market Trend (baseado em múltiplas SMAs)
            df['SMA_9'] = ta.sma(df['close'], length=9)
            df['SMA_21'] = ta.sma(df['close'], length=21)
            df['SMA_50'] = ta.sma(df['close'], length=50)
            
            # Trend Score (0-100)
            conditions = [
                df['close'] > df['SMA_9'],
                df['SMA_9'] > df['SMA_21'],
                df['SMA_21'] > df['SMA_50'],
                df['RSI_14'] > 50,
                df['MACD_12_26_9'] > df['MACDs_12_26_9']
            ]
            
            df['TREND_SCORE'] = sum(conditions) * 20  # 0, 20, 40, 60, 80, 100
            
            # Market Phase
            df['MARKET_PHASE'] = 'NEUTRAL'
            df.loc[df['TREND_SCORE'] >= 80, 'MARKET_PHASE'] = 'BULLISH'
            df.loc[df['TREND_SCORE'] <= 20, 'MARKET_PHASE'] = 'BEARISH'
            
            # Volatility State
            volatility = df['ATR'] / df['close'] * 100
            df['VOLATILITY_STATE'] = 'NORMAL'
            df.loc[volatility > volatility.quantile(0.8), 'VOLATILITY_STATE'] = 'HIGH'
            df.loc[volatility < volatility.quantile(0.2), 'VOLATILITY_STATE'] = 'LOW'
            
            print("✅ Estrutura de mercado adicionada")
            return df
            
        except Exception as e:
            print(f"⚠️ Erro em estrutura de mercado: {e}")
            return df
    
    def get_signal_strength(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula força dos sinais baseado em múltiplos indicadores
        
        Returns:
            Dict com scores de 0-100 para diferentes aspectos
        """
        try:
            if len(df) < 2:
                return {'trend': 50, 'momentum': 50, 'volatility': 50, 'volume': 50, 'overall': 50}
            
            latest = df.iloc[-1]
            
            # Trend Strength (0-100)
            trend_signals = []
            if 'TREND_SCORE' in df.columns:
                trend_signals.append(latest['TREND_SCORE'])
            if all(col in df.columns for col in ['close', 'SMA_21']):
                trend_signals.append(100 if latest['close'] > latest['SMA_21'] else 0)
            if 'SUPERT_14_3.0' in df.columns:
                trend_signals.append(100 if latest['close'] > latest['SUPERT_14_3.0'] else 0)
            
            trend_strength = np.mean(trend_signals) if trend_signals else 50
            
            # Momentum Strength
            momentum_signals = []
            if 'RSI_14' in df.columns:
                rsi = latest['RSI_14']
                if 30 <= rsi <= 70:
                    momentum_signals.append(50 + (rsi - 50))
                else:
                    momentum_signals.append(25 if rsi < 30 else 75)
            
            if all(col in df.columns for col in ['MACD_12_26_9', 'MACDs_12_26_9']):
                momentum_signals.append(100 if latest['MACD_12_26_9'] > latest['MACDs_12_26_9'] else 0)
                
            momentum_strength = np.mean(momentum_signals) if momentum_signals else 50
            
            # Volume Strength
            volume_strength = 50
            if 'VOLUME_RATIO' in df.columns:
                ratio = latest['VOLUME_RATIO']
                volume_strength = min(100, max(0, ratio * 50))
            
            # Volatility Assessment
            volatility_strength = 50
            if 'VOLATILITY_STATE' in df.columns:
                state = latest['VOLATILITY_STATE']
                if state == 'HIGH':
                    volatility_strength = 80  # Alta volatilidade = oportunidade
                elif state == 'LOW':
                    volatility_strength = 30  # Baixa volatilidade = consolidação
            
            # Overall Score
            overall = np.mean([trend_strength, momentum_strength, volume_strength, volatility_strength])
            
            return {
                'trend': round(trend_strength, 1),
                'momentum': round(momentum_strength, 1),
                'volume': round(volume_strength, 1),
                'volatility': round(volatility_strength, 1),
                'overall': round(overall, 1)
            }
            
        except Exception as e:
            print(f"❌ Erro no cálculo de força dos sinais: {e}")
            return {'trend': 50, 'momentum': 50, 'volatility': 50, 'volume': 50, 'overall': 50}
    
    def get_trading_recommendation(self, df: pd.DataFrame, symbol: str) -> Dict[str, any]:
        """
        Gera recomendação de trading baseada em todos os indicadores
        
        Returns:
            Dict com recomendação completa
        """
        try:
            if len(df) < 2:
                return {
                    'action': 'WAIT',
                    'confidence': 0,
                    'reason': 'Dados insuficientes',
                    'signals': {}
                }
            
            latest = df.iloc[-1]
            signals = self.get_signal_strength(df)
            
            # Análise de múltiplos timeframes (simulado)
            short_term = signals['momentum']  # Baseado em momentum
            medium_term = signals['trend']    # Baseado em trend
            long_term = signals['overall']    # Overall
            
            # Decisão de trading
            buy_score = 0
            sell_score = 0
            
            # Critérios de COMPRA
            if signals['trend'] > 60:
                buy_score += 25
            if signals['momentum'] > 55:
                buy_score += 20
            if signals['volume'] > 60:
                buy_score += 15
            if 'RSI_14' in df.columns and 30 < latest['RSI_14'] < 70:
                buy_score += 20
            if 'MARKET_PHASE' in df.columns and latest['MARKET_PHASE'] == 'BULLISH':
                buy_score += 20
            
            # Critérios de VENDA
            if signals['trend'] < 40:
                sell_score += 25
            if signals['momentum'] < 45:
                sell_score += 20
            if 'RSI_14' in df.columns and latest['RSI_14'] > 70:
                sell_score += 30
            if 'MARKET_PHASE' in df.columns and latest['MARKET_PHASE'] == 'BEARISH':
                sell_score += 25
            
            # Decisão final
            if buy_score > 70 and buy_score > sell_score:
                action = 'BUY'
                confidence = min(95, buy_score)
                reason = f"Múltiplos sinais de alta: Trend={signals['trend']:.1f}%, Momentum={signals['momentum']:.1f}%"
            elif sell_score > 70 and sell_score > buy_score:
                action = 'SELL'
                confidence = min(95, sell_score)
                reason = f"Múltiplos sinais de baixa: Trend={signals['trend']:.1f}%, Momentum={signals['momentum']:.1f}%"
            else:
                action = 'WAIT'
                confidence = 100 - abs(buy_score - sell_score)
                reason = f"Sinais mistos: Buy={buy_score}, Sell={sell_score}"
            
            return {
                'action': action,
                'confidence': confidence,
                'reason': reason,
                'signals': signals,
                'timeframes': {
                    'short_term': short_term,
                    'medium_term': medium_term,
                    'long_term': long_term
                },
                'key_levels': {
                    'support': latest.get('SUPPORT', 0),
                    'resistance': latest.get('RESISTANCE', 0),
                    'pivot': latest.get('PP', 0)
                },
                'risk_assessment': {
                    'volatility': latest.get('VOLATILITY_STATE', 'UNKNOWN'),
                    'atr_percent': (latest.get('ATR', 0) / latest['close'] * 100) if 'ATR' in df.columns else 0
                }
            }
            
        except Exception as e:
            print(f"❌ Erro na recomendação para {symbol}: {e}")
            return {
                'action': 'WAIT',
                'confidence': 0,
                'reason': f'Erro: {str(e)}',
                'signals': {}
            }
    
    def print_indicator_summary(self, df: pd.DataFrame, symbol: str):
        """Imprime resumo dos indicadores calculados"""
        try:
            print(f"\n📊 === RESUMO TÉCNICO: {symbol} ===")
            
            if len(df) == 0:
                print("❌ Sem dados disponíveis")
                return
            
            latest = df.iloc[-1]
            
            # Indicadores principais
            print(f"💰 Preço: ${latest['close']:.4f}")
            
            if 'RSI_14' in df.columns:
                rsi = latest['RSI_14']
                rsi_status = "🔥Sobrecomprado" if rsi > 70 else "❄️Sobrevendido" if rsi < 30 else "⚖️Neutro"
                print(f"📈 RSI: {rsi:.1f} ({rsi_status})")
            
            if 'TREND_SCORE' in df.columns:
                trend = latest['TREND_SCORE']
                trend_status = "🚀Bullish" if trend > 60 else "📉Bearish" if trend < 40 else "➡️Lateral"
                print(f"📊 Tendência: {trend:.0f}/100 ({trend_status})")
            
            if 'VOLATILITY_STATE' in df.columns:
                vol_state = latest['VOLATILITY_STATE']
                vol_emoji = "🔥" if vol_state == "HIGH" else "😴" if vol_state == "LOW" else "📊"
                print(f"🌊 Volatilidade: {vol_emoji} {vol_state}")
            
            # Sinais
            recommendation = self.get_trading_recommendation(df, symbol)
            action = recommendation['action']
            confidence = recommendation['confidence']
            
            action_emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "🟡"
            print(f"🎯 Recomendação: {action_emoji} {action} ({confidence:.0f}% confiança)")
            print(f"💭 Razão: {recommendation['reason']}")
            
            print("=" * 40)
            
        except Exception as e:
            print(f"❌ Erro no resumo de {symbol}: {e}")

# ========================================
# TESTE RÁPIDO
# ========================================

if __name__ == "__main__":
    print("🧪 Testando AdvancedIndicators...")
    
    # Criar dados de teste
    import datetime
    dates = pd.date_range(start='2025-01-01', periods=100, freq='H')
    
    # Simular dados OHLCV
    np.random.seed(42)
    base_price = 50000
    
    # Criar arrays separados primeiro
    opens = base_price + np.cumsum(np.random.randn(100) * 100)
    highs = np.zeros(100)
    lows = np.zeros(100) 
    closes = np.zeros(100)
    volumes = np.random.randint(1000, 10000, 100)
    
    # Calcular high, low, close baseado no open
    for i in range(100):
        open_price = opens[i]
        change = np.random.randn() * 200
        close_price = open_price + change
        
        high_price = max(open_price, close_price) + abs(np.random.randn() * 50)
        low_price = min(open_price, close_price) - abs(np.random.randn() * 50)
        
        highs[i] = high_price
        lows[i] = low_price
        closes[i] = close_price
    
    test_data = {
        'timestamp': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    }
    
    df_test = pd.DataFrame(test_data)
    
    # Testar indicadores
    indicators = AdvancedIndicators()
    df_enhanced = indicators.calculate_all_indicators(df_test, "BTC/USDT")
    
    print(f"\n🎉 Teste concluído!")
    print(f"📊 Colunas originais: {len(df_test.columns)}")
    print(f"🚀 Colunas após indicadores: {len(df_enhanced.columns)}")
    print(f"✨ Novos indicadores: {len(df_enhanced.columns) - len(df_test.columns)}")
    
    # Mostrar resumo
    indicators.print_indicator_summary(df_enhanced, "BTC/USDT")
    
    print("\n🔥 AdvancedIndicators pronto para uso!")