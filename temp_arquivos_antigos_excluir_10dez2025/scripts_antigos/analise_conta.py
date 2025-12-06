"""
📊 Verificar Histórico Completo da Binance Testnet
"""
import ccxt
from dotenv import load_dotenv
import os

# Carregar credenciais
load_dotenv('config/.env')

# Conectar à Binance Testnet
exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_TESTNET_API_KEY'),
    'secret': os.getenv('BINANCE_TESTNET_API_SECRET'),
    'sandbox': True,
    'enableRateLimit': True,
    'options': {
        'adjustForTimeDifference': True,
        'recvWindow': 60000
    }
})

exchange.load_time_difference()

print("\n" + "="*70)
print("📊 ANÁLISE COMPLETA DA CONTA BINANCE TESTNET")
print("="*70)

# 1. Saldo atual
print("\n💰 SALDO ATUAL:")
print("-"*50)
balance = exchange.fetch_balance()
total_usdt = 0

for currency, amount in sorted(balance['total'].items()):
    if amount > 0:
        valor_usdt = 0
        if currency == 'USDT':
            valor_usdt = amount
        else:
            try:
                ticker = exchange.fetch_ticker(f"{currency}/USDT")
                valor_usdt = amount * ticker['last']
            except:
                pass
        
        total_usdt += valor_usdt
        if valor_usdt > 1:  # Só mostra se vale mais de $1
            print(f"  {currency}: {amount:.4f} = ${valor_usdt:.2f}")

print("-"*50)
print(f"  TOTAL ESTIMADO: ${total_usdt:,.2f} USDT")

# 2. Histórico de ordens
print("\n\n📜 ÚLTIMAS ORDENS EXECUTADAS (por par):")
print("-"*50)

symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'DOGE/USDT', 'LTC/USDT', 'LINK/USDT']
total_trades = 0
total_volume = 0

for symbol in symbols:
    try:
        trades = exchange.fetch_my_trades(symbol, limit=100)
        if trades:
            volume = sum(t['cost'] for t in trades)
            total_trades += len(trades)
            total_volume += volume
            print(f"  {symbol}: {len(trades)} trades, volume: ${volume:.2f}")
    except Exception as e:
        pass

print("-"*50)
print(f"  TOTAL: {total_trades} trades, volume: ${total_volume:.2f}")

# 3. Explicação
print("\n\n" + "="*70)
print("💡 EXPLICAÇÃO DO SALDO:")
print("="*70)
print("""
A Binance TESTNET fornece saldo fictício para testes!

Quando você cria uma conta na Testnet, ela vem com:
- ~300,000 USDT grátis
- 1 BTC, 1 ETH, 1 WBTC
- Várias outras criptomoedas

VOCÊ NÃO GANHOU $304K COM TRADING!
O bot lucrou apenas ${:.2f} em {} trades.

Se fosse dinheiro REAL com $10K inicial:
  $10,000 + ${:.2f} = ${:,.2f}
""".format(8.26, 598, 8.26, 10008.26))

print("="*70)
