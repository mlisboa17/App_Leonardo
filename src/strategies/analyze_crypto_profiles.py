"""
🔬 Analisador de Perfis de Criptomoedas
Usa API pública da Binance para analisar histórico de cada moeda
e descobrir os melhores pontos de entrada/saída
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# Bibliotecas de análise técnica
try:
    import ta  # pip install ta (Technical Analysis Library)
    HAS_TA = True
except ImportError:
    HAS_TA = False
    print("⚠️ Biblioteca 'ta' não instalada. Usando cálculos manuais.")
    print("   Para instalar: pip install ta")


class CryptoProfileAnalyzer:
    """
    Analisa 30 dias de histórico para descobrir:
    - RSI mínimo que cada moeda atinge
    - RSI máximo que cada moeda atinge
    - Melhor RSI para COMPRA (baseado em movimentos lucrativos)
    - Melhor RSI para VENDA (baseado em reversões)
    - Volatilidade média
    - Volume médio
    """
    
    def __init__(self):
        self.symbols = [
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT',
            'XRPUSDT', 'LINKUSDT', 'DOGEUSDT', 'LTCUSDT'
        ]
        self.profiles = {}
        self.base_url = "https://api.binance.com/api/v3"
    
    
    def fetch_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        Busca dados históricos da Binance (API pública)
        Retorna DataFrame com OHLCV + indicadores
        """
        print(f"\n📊 Buscando dados de {symbol} ({days} dias)...")
        
        all_candles = []
        end_time = int(datetime.now().timestamp() * 1000)
        
        # Binance retorna max 1000 candles por request
        # Para 30 dias em 5min = 8640 candles, precisamos de ~9 requests
        candles_needed = days * 24 * 12  # 12 candles de 5min por hora
        requests_needed = (candles_needed // 1000) + 1
        
        for i in range(requests_needed):
            try:
                params = {
                    'symbol': symbol,
                    'interval': '5m',  # 5 minutos para melhor análise
                    'endTime': end_time,
                    'limit': 1000
                }
                
                response = requests.get(f"{self.base_url}/klines", params=params)
                
                if response.status_code != 200:
                    print(f"   ❌ Erro API: {response.status_code}")
                    break
                
                data = response.json()
                
                if not data:
                    break
                
                all_candles.extend(data)
                
                # Próximo request começa antes do primeiro candle retornado
                end_time = data[0][0] - 1
                
                print(f"   ✓ Chunk {i+1}/{requests_needed}: {len(data)} candles")
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                break
        
        if not all_candles:
            return None
        
        # Converte para DataFrame
        df = pd.DataFrame(all_candles, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # Converte tipos
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Ordena por tempo
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Remove duplicatas
        df = df.drop_duplicates(subset=['timestamp'])
        
        print(f"   📈 Total: {len(df)} candles de {df['timestamp'].min()} a {df['timestamp'].max()}")
        
        return df
    
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula indicadores técnicos usando biblioteca 'ta' ou manual
        """
        
        if HAS_TA:
            # ============ USANDO BIBLIOTECA TA (PROFISSIONAL) ============
            
            # RSI (14 períodos)
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_histogram'] = macd.macd_diff()
            
            # Bandas de Bollinger
            bb = ta.volatility.BollingerBands(df['close'], window=20)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_middle'] = bb.bollinger_mavg()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_width'] = bb.bollinger_wband()
            
            # Médias Móveis
            df['sma20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
            df['sma50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
            df['ema9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
            df['ema21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
            
            # ATR (Average True Range) - Volatilidade
            df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
            
            # Stochastic RSI
            stoch = ta.momentum.StochRSIIndicator(df['close'])
            df['stoch_rsi'] = stoch.stochrsi()
            df['stoch_rsi_k'] = stoch.stochrsi_k()
            df['stoch_rsi_d'] = stoch.stochrsi_d()
            
            # ADX (Força da tendência)
            adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
            df['adx'] = adx.adx()
            df['adx_pos'] = adx.adx_pos()
            df['adx_neg'] = adx.adx_neg()
            
            # OBV (On Balance Volume)
            df['obv'] = ta.volume.OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume()
            
            # CCI (Commodity Channel Index)
            df['cci'] = ta.trend.CCIIndicator(df['high'], df['low'], df['close']).cci()
            
            # Williams %R
            df['williams_r'] = ta.momentum.WilliamsRIndicator(df['high'], df['low'], df['close']).williams_r()
            
            print("   ✅ Indicadores calculados com biblioteca 'ta'")
            
        else:
            # ============ CÁLCULO MANUAL (FALLBACK) ============
            
            # RSI Manual
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Médias Móveis
            df['sma20'] = df['close'].rolling(window=20).mean()
            df['sma50'] = df['close'].rolling(window=50).mean()
            df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
            
            # MACD Manual
            exp12 = df['close'].ewm(span=12, adjust=False).mean()
            exp26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = exp12 - exp26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # Bollinger Bands Manual
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            
            # ATR Manual
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['atr'] = tr.rolling(window=14).mean()
            
            print("   ⚠️ Indicadores calculados manualmente (instale 'ta' para mais precisão)")
        
        return df
    
    
    def analyze_optimal_entries(self, df: pd.DataFrame) -> dict:
        """
        Analisa quando compras teriam sido lucrativas
        Retorna RSI ideal para entrada
        """
        
        # Remove NaN
        df = df.dropna().copy()
        
        if len(df) < 100:
            return {'buy_rsi': 35, 'confidence': 'low'}
        
        # Calcula retorno futuro (15 candles = 75 minutos)
        df['future_return'] = df['close'].shift(-15) / df['close'] - 1
        
        # Encontra entradas lucrativas (subiu > 1% em 75min)
        profitable = df[df['future_return'] > 0.01]
        
        if len(profitable) < 20:
            return {
                'buy_rsi': 35,
                'confidence': 'low',
                'sample_size': len(profitable)
            }
        
        # RSI médio das entradas lucrativas
        optimal_rsi = profitable['rsi'].mean()
        
        # Percentil 25% (entradas mais seguras)
        conservative_rsi = profitable['rsi'].quantile(0.25)
        
        # Percentil 75% (entradas mais arriscadas mas frequentes)
        aggressive_rsi = profitable['rsi'].quantile(0.75)
        
        return {
            'buy_rsi_optimal': round(optimal_rsi, 1),
            'buy_rsi_conservative': round(conservative_rsi, 1),
            'buy_rsi_aggressive': round(aggressive_rsi, 1),
            'profitable_trades': len(profitable),
            'avg_profit': round(profitable['future_return'].mean() * 100, 2),
            'confidence': 'high' if len(profitable) > 100 else 'medium'
        }
    
    
    def analyze_optimal_exits(self, df: pd.DataFrame) -> dict:
        """
        Analisa quando vendas teriam evitado perdas
        Retorna RSI ideal para saída
        """
        
        df = df.dropna().copy()
        
        if len(df) < 100:
            return {'sell_rsi': 65, 'confidence': 'low'}
        
        # Calcula retorno futuro negativo (caiu > 1%)
        df['future_return'] = df['close'].shift(-15) / df['close'] - 1
        
        # Encontra topos (preço caiu depois)
        peaks = df[df['future_return'] < -0.01]
        
        if len(peaks) < 20:
            return {
                'sell_rsi': 65,
                'confidence': 'low',
                'sample_size': len(peaks)
            }
        
        # RSI médio nos topos
        optimal_rsi = peaks['rsi'].mean()
        
        # Percentil 75% (vende mais cedo, mais seguro)
        conservative_rsi = peaks['rsi'].quantile(0.75)
        
        # Percentil 25% (segura mais, pode perder o topo)
        aggressive_rsi = peaks['rsi'].quantile(0.25)
        
        return {
            'sell_rsi_optimal': round(optimal_rsi, 1),
            'sell_rsi_conservative': round(conservative_rsi, 1),
            'sell_rsi_aggressive': round(aggressive_rsi, 1),
            'peak_count': len(peaks),
            'avg_drop': round(peaks['future_return'].mean() * 100, 2),
            'confidence': 'high' if len(peaks) > 100 else 'medium'
        }
    
    
    def analyze_trend_reversals(self, df: pd.DataFrame) -> dict:
        """
        Analisa indicadores que melhor preveem reversões de tendência
        ESSENCIAL para sua estratégia de "vender só quando virar queda"
        """
        
        df = df.dropna().copy()
        
        if len(df) < 200:
            return {'best_indicator': 'macd', 'confidence': 'low'}
        
        # Identifica reversões reais (preço mudou > 2% na direção oposta)
        df['price_change_15'] = df['close'].shift(-15) / df['close'] - 1
        df['was_rising'] = df['close'].rolling(5).mean() > df['close'].rolling(20).mean()
        
        # Reversões de alta para queda
        high_to_low = df[(df['was_rising']) & (df['price_change_15'] < -0.015)]
        
        # Reversões de queda para alta
        low_to_high = df[(~df['was_rising']) & (df['price_change_15'] > 0.015)]
        
        # Analisa qual indicador previu melhor
        indicators_accuracy = {}
        
        # 1. MACD Crossover
        df['macd_cross_down'] = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        df['macd_cross_up'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        
        # Taxa de acerto MACD para quedas
        if len(high_to_low) > 0:
            macd_predicted = high_to_low[high_to_low['macd_cross_down'].shift(3).fillna(False)]
            indicators_accuracy['macd_for_sell'] = round(len(macd_predicted) / len(high_to_low) * 100, 1)
        
        # Taxa de acerto MACD para altas
        if len(low_to_high) > 0:
            macd_predicted = low_to_high[low_to_high['macd_cross_up'].shift(3).fillna(False)]
            indicators_accuracy['macd_for_buy'] = round(len(macd_predicted) / len(low_to_high) * 100, 1)
        
        # 2. EMA Crossover (9 cruza 21)
        df['ema_cross_down'] = (df['ema9'] < df['ema21']) & (df['ema9'].shift(1) >= df['ema21'].shift(1))
        df['ema_cross_up'] = (df['ema9'] > df['ema21']) & (df['ema9'].shift(1) <= df['ema21'].shift(1))
        
        if len(high_to_low) > 0:
            ema_predicted = high_to_low[high_to_low['ema_cross_down'].shift(3).fillna(False)]
            indicators_accuracy['ema_for_sell'] = round(len(ema_predicted) / len(high_to_low) * 100, 1)
        
        if len(low_to_high) > 0:
            ema_predicted = low_to_high[low_to_high['ema_cross_up'].shift(3).fillna(False)]
            indicators_accuracy['ema_for_buy'] = round(len(ema_predicted) / len(low_to_high) * 100, 1)
        
        return {
            'reversals_high_to_low': len(high_to_low),
            'reversals_low_to_high': len(low_to_high),
            'indicator_accuracy': indicators_accuracy,
            'best_sell_indicator': max(
                [(k, v) for k, v in indicators_accuracy.items() if 'sell' in k],
                key=lambda x: x[1],
                default=('macd_for_sell', 0)
            ),
            'best_buy_indicator': max(
                [(k, v) for k, v in indicators_accuracy.items() if 'buy' in k],
                key=lambda x: x[1],
                default=('macd_for_buy', 0)
            )
        }
    
    
    def create_full_profile(self, symbol: str) -> dict:
        """
        Cria perfil completo de uma moeda
        """
        
        print(f"\n{'='*60}")
        print(f"🔬 ANÁLISE COMPLETA: {symbol}")
        print('='*60)
        
        # 1. Busca dados
        df = self.fetch_historical_data(symbol, days=30)
        
        if df is None or len(df) < 100:
            return {
                'symbol': symbol,
                'error': 'Dados insuficientes',
                'use_default': True
            }
        
        # 2. Calcula indicadores
        df = self.calculate_indicators(df)
        
        # 3. Estatísticas básicas de RSI
        rsi_stats = {
            'rsi_min': round(df['rsi'].min(), 1),
            'rsi_max': round(df['rsi'].max(), 1),
            'rsi_mean': round(df['rsi'].mean(), 1),
            'rsi_std': round(df['rsi'].std(), 1),
            'rsi_p5': round(df['rsi'].quantile(0.05), 1),   # Percentil 5%
            'rsi_p25': round(df['rsi'].quantile(0.25), 1),  # Percentil 25%
            'rsi_p75': round(df['rsi'].quantile(0.75), 1),  # Percentil 75%
            'rsi_p95': round(df['rsi'].quantile(0.95), 1),  # Percentil 95%
        }
        
        # 4. Volatilidade
        volatility = {
            'atr_mean': round(df['atr'].mean(), 4),
            'atr_pct': round((df['atr'] / df['close'] * 100).mean(), 2),
            'daily_range_pct': round(((df['high'] - df['low']) / df['close'] * 100).mean(), 2),
            'bb_width_mean': round(df['bb_width'].mean() * 100, 2) if 'bb_width' in df else 0
        }
        
        # 5. Volume
        volume_stats = {
            'volume_mean': round(df['volume'].mean(), 2),
            'volume_usd_mean': round((df['volume'] * df['close']).mean(), 2),
            'volume_std': round(df['volume'].std(), 2)
        }
        
        # 6. Análise de entradas ótimas
        entry_analysis = self.analyze_optimal_entries(df)
        
        # 7. Análise de saídas ótimas
        exit_analysis = self.analyze_optimal_exits(df)
        
        # 8. Análise de reversões
        reversal_analysis = self.analyze_trend_reversals(df)
        
        # 9. Calcula thresholds recomendados
        # Compra: Um pouco acima do mínimo histórico, mas abaixo da média de entradas lucrativas
        buy_rsi = max(
            rsi_stats['rsi_p5'] + 3,  # 3 pontos acima do percentil 5%
            entry_analysis.get('buy_rsi_conservative', 35) - 2
        )
        buy_rsi = min(45, max(25, buy_rsi))  # Limita entre 25-45
        
        # Venda: Um pouco abaixo do máximo histórico
        sell_rsi = min(
            rsi_stats['rsi_p95'] - 3,  # 3 pontos abaixo do percentil 95%
            exit_analysis.get('sell_rsi_conservative', 65) + 2
        )
        sell_rsi = min(75, max(55, sell_rsi))  # Limita entre 55-75
        
        profile = {
            'symbol': symbol,
            'symbol_ccxt': symbol.replace('USDT', '/USDT'),
            'analysis_date': datetime.now().isoformat(),
            'candles_analyzed': len(df),
            'period_days': 30,
            
            'rsi_stats': rsi_stats,
            'volatility': volatility,
            'volume': volume_stats,
            
            'entry_analysis': entry_analysis,
            'exit_analysis': exit_analysis,
            'reversal_analysis': reversal_analysis,
            
            'recommended_thresholds': {
                'buy_rsi': round(buy_rsi, 1),
                'sell_rsi': round(sell_rsi, 1),
                'stop_loss_pct': round(-volatility['daily_range_pct'] * 0.8, 2),  # 80% do range diário
                'take_profit_pct': round(volatility['daily_range_pct'] * 1.2, 2)  # 120% do range diário
            }
        }
        
        # Print resumo
        print(f"""
📊 RESUMO {symbol}:
   RSI Histórico: {rsi_stats['rsi_min']:.1f} - {rsi_stats['rsi_max']:.1f} (média: {rsi_stats['rsi_mean']:.1f})
   
   🎯 THRESHOLDS RECOMENDADOS:
   ├─ RSI Compra: < {profile['recommended_thresholds']['buy_rsi']}
   ├─ RSI Venda: > {profile['recommended_thresholds']['sell_rsi']}
   ├─ Stop Loss: {profile['recommended_thresholds']['stop_loss_pct']}%
   └─ Take Profit: +{profile['recommended_thresholds']['take_profit_pct']}%
   
   📈 Volatilidade: {volatility['daily_range_pct']}% (range médio diário)
   💰 Volume Médio: ${volume_stats['volume_usd_mean']:,.0f}
   
   🔄 Precisão Indicadores:
   ├─ MACD para Venda: {reversal_analysis['indicator_accuracy'].get('macd_for_sell', 'N/A')}%
   └─ MACD para Compra: {reversal_analysis['indicator_accuracy'].get('macd_for_buy', 'N/A')}%
""")
        
        return profile
    
    
    def analyze_all_cryptos(self) -> dict:
        """
        Analisa todas as 8 criptomoedas e salva perfis
        """
        
        print("\n" + "="*60)
        print("🚀 INICIANDO ANÁLISE DE TODAS AS CRIPTOMOEDAS")
        print("="*60)
        print(f"Moedas: {', '.join(self.symbols)}")
        print(f"Período: 30 dias")
        print(f"Timeframe: 5 minutos")
        print("="*60)
        
        all_profiles = {}
        
        for symbol in self.symbols:
            try:
                profile = self.create_full_profile(symbol)
                all_profiles[symbol] = profile
            except Exception as e:
                print(f"❌ Erro ao analisar {symbol}: {e}")
                all_profiles[symbol] = {
                    'symbol': symbol,
                    'error': str(e),
                    'use_default': True,
                    'recommended_thresholds': {
                        'buy_rsi': 35,
                        'sell_rsi': 65,
                        'stop_loss_pct': -1.5,
                        'take_profit_pct': 2.0
                    }
                }
        
        # Salva em arquivo JSON
        output_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'data', 'crypto_profiles.json'
        )
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_profiles, f, indent=2, default=str)
        
        print(f"\n✅ Perfis salvos em: {output_path}")
        
        # Print tabela resumo
        self._print_summary_table(all_profiles)
        
        return all_profiles
    
    
    def _print_summary_table(self, profiles: dict):
        """Imprime tabela resumo de todos os perfis"""
        
        print("\n" + "="*80)
        print("📊 TABELA RESUMO - THRESHOLDS POR MOEDA")
        print("="*80)
        print(f"{'Moeda':<12} {'RSI Min':<8} {'RSI Max':<8} {'Compra':<8} {'Venda':<8} {'Stop':<8} {'Take':<8}")
        print("-"*80)
        
        for symbol, profile in profiles.items():
            if profile.get('use_default'):
                print(f"{symbol:<12} {'N/A':<8} {'N/A':<8} {35:<8} {65:<8} {-1.5:<8} {2.0:<8} ⚠️")
            else:
                rsi = profile['rsi_stats']
                rec = profile['recommended_thresholds']
                print(f"{symbol:<12} {rsi['rsi_min']:<8} {rsi['rsi_max']:<8} {rec['buy_rsi']:<8} {rec['sell_rsi']:<8} {rec['stop_loss_pct']:<8} {rec['take_profit_pct']:<8}")
        
        print("="*80)
        print("\n💡 Legenda:")
        print("   RSI Min/Max: Valores históricos dos últimos 30 dias")
        print("   Compra: RSI abaixo desse valor = sinal de compra")
        print("   Venda: RSI acima desse valor = sinal de venda")
        print("   Stop/Take: Baseados na volatilidade de cada moeda")


def main():
    """Executa análise completa"""
    
    print("""
╔══════════════════════════════════════════════════════════╗
║     🔬 ANALISADOR DE PERFIS DE CRIPTOMOEDAS             ║
║     Biblioteca: {'ta (Technical Analysis)' if HAS_TA else 'Cálculos Manuais'}
║     Meta: Descobrir melhor RSI de entrada/saída         ║
╚══════════════════════════════════════════════════════════╝
""")
    
    analyzer = CryptoProfileAnalyzer()
    profiles = analyzer.analyze_all_cryptos()
    
    print("\n✅ ANÁLISE COMPLETA!")
    print("Os perfis foram salvos e serão usados pela estratégia adaptativa.")
    
    return profiles


if __name__ == "__main__":
    main()
