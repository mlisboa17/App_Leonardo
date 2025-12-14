"""
🚀 Análise Rápida de Criptomoedas
Versão otimizada - 7 dias de dados, mais rápido
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import time

# Verifica se tem biblioteca TA
try:
    import ta
    HAS_TA = True
    print("✅ Biblioteca 'ta' encontrada!")
except ImportError:
    HAS_TA = False
    print("⚠️ Biblioteca 'ta' não encontrada, usando cálculos manuais")


def fetch_data(symbol: str, limit: int = 1000) -> pd.DataFrame:
    """Busca dados da Binance (versão rápida)"""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': '15m',  # 15 minutos (mais rápido)
        'limit': limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if not data or isinstance(data, dict):
            print(f"   ❌ Erro: {data}")
            return None
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        return df
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return None


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calcula RSI"""
    if HAS_TA:
        return ta.momentum.RSIIndicator(df['close'], window=period).rsi()
    else:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))


def analyze_symbol(symbol: str) -> dict:
    """Analisa uma moeda"""
    print(f"\n📊 Analisando {symbol}...")
    
    df = fetch_data(symbol, 1000)  # ~10 dias de 15min
    
    if df is None or len(df) < 100:
        return {
            'symbol': symbol,
            'buy_rsi': 35,
            'sell_rsi': 65,
            'error': True
        }
    
    # Calcula RSI
    df['rsi'] = calculate_rsi(df)
    df = df.dropna()
    
    # Estatísticas RSI
    rsi_min = df['rsi'].min()
    rsi_max = df['rsi'].max()
    rsi_mean = df['rsi'].mean()
    rsi_p10 = df['rsi'].quantile(0.10)  # Percentil 10%
    rsi_p90 = df['rsi'].quantile(0.90)  # Percentil 90%
    
    # Volatilidade (range médio %)
    volatility = ((df['high'] - df['low']) / df['close'] * 100).mean()
    
    # Volume médio em USD
    volume_usd = (df['volume'] * df['close']).mean()
    
    # Thresholds recomendados
    # Compra: Um pouco acima do mínimo histórico
    buy_rsi = round(max(25, min(42, rsi_p10 + 3)), 1)
    
    # Venda: Um pouco abaixo do máximo histórico
    sell_rsi = round(max(58, min(75, rsi_p90 - 3)), 1)
    
    result = {
        'symbol': symbol,
        'symbol_ccxt': symbol.replace('USDT', '/USDT'),
        'rsi_min': round(rsi_min, 1),
        'rsi_max': round(rsi_max, 1),
        'rsi_mean': round(rsi_mean, 1),
        'buy_rsi': buy_rsi,
        'sell_rsi': sell_rsi,
        'volatility_pct': round(volatility, 2),
        'volume_usd': round(volume_usd, 0),
        'candles': len(df)
    }
    
    print(f"   RSI: {rsi_min:.1f} - {rsi_max:.1f} (média: {rsi_mean:.1f})")
    print(f"   🎯 Compra: RSI < {buy_rsi} | Venda: RSI > {sell_rsi}")
    print(f"   📈 Volatilidade: {volatility:.2f}% | Volume: ${volume_usd:,.0f}")
    
    return result


def main():
    print("""
╔════════════════════════════════════════════════════════╗
║  🔬 ANÁLISE RÁPIDA DE CRIPTOMOEDAS                     ║
║  Biblioteca TA: """ + ("SIM ✅" if HAS_TA else "NÃO ❌") + """                               ║
║  Período: ~10 dias | Timeframe: 15min                  ║
╚════════════════════════════════════════════════════════╝
""")
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 
               'XRPUSDT', 'LINKUSDT', 'DOGEUSDT', 'LTCUSDT']
    
    profiles = {}
    
    for symbol in symbols:
        try:
            result = analyze_symbol(symbol)
            profiles[symbol] = result
            time.sleep(0.5)  # Respeita rate limit
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            profiles[symbol] = {'symbol': symbol, 'buy_rsi': 35, 'sell_rsi': 65, 'error': True}
    
    # Salva resultados
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'crypto_profiles.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=2)
    
    # Tabela resumo
    print("\n" + "="*75)
    print("📊 TABELA RESUMO - THRESHOLDS RECOMENDADOS")
    print("="*75)
    print(f"{'Moeda':<12} {'RSI Min':<10} {'RSI Max':<10} {'COMPRA':<10} {'VENDA':<10} {'Volat%':<10}")
    print("-"*75)
    
    for symbol, p in profiles.items():
        if p.get('error'):
            print(f"{symbol:<12} {'ERR':<10} {'ERR':<10} {35:<10} {65:<10} {'N/A':<10}")
        else:
            print(f"{symbol:<12} {p['rsi_min']:<10} {p['rsi_max']:<10} {p['buy_rsi']:<10} {p['sell_rsi']:<10} {p['volatility_pct']:<10}")
    
    print("="*75)
    print(f"\n✅ Perfis salvos em: {output_path}")
    
    # Explicação
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║  🎯 COMO O BOT VAI USAR ESSES DADOS:                                   ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1️⃣ COMPRA - Quando RSI cai abaixo do threshold da moeda:             ║
║     • BTC: RSI < 38 (ele raramente cai mais que isso)                  ║
║     • DOGE: RSI < 30 (mais volátil, cai mais)                          ║
║                                                                        ║
║  2️⃣ SEGURA - Enquanto tendência for de ALTA:                          ║
║     • MACD acima da linha de sinal                                     ║
║     • Preço acima da SMA20                                             ║
║     • RSI subindo                                                      ║
║                                                                        ║
║  3️⃣ VENDE - Quando tendência VIRAR para QUEDA:                        ║
║     • MACD cruzou para baixo ↓                                         ║
║     • Preço caiu abaixo da SMA20                                       ║
║     • RSI começou a cair                                               ║
║     • OU RSI passou do threshold de venda da moeda                     ║
║                                                                        ║
║  4️⃣ URGÊNCIA - Se bot ficar parado sem trades:                        ║
║     • 5min parado: RSI compra +1 (35→36)                               ║
║     • 10min parado: RSI compra +2 (35→37)                              ║
║     • 30min parado: RSI compra +5 (35→40)                              ║
║     • Nunca passa do RSI médio da moeda                                ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
""")
    
    return profiles


if __name__ == "__main__":
    main()
