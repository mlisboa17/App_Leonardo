"""
💰 Verificar Saldo Real da Binance Testnet
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
    'sandbox': True,  # Testnet
    'enableRateLimit': True,
    'options': {
        'adjustForTimeDifference': True,
        'recvWindow': 60000
    }
})

# Sincronizar tempo
exchange.load_time_difference()

print("\n" + "="*60)
print("💰 SALDO REAL DA BINANCE TESTNET")
print("="*60)

try:
    # Buscar saldo
    balance = exchange.fetch_balance()
    
    print("\n📊 SALDOS COM VALOR > 0:")
    print("-"*40)
    
    total_usdt = 0
    for currency, amount in balance['total'].items():
        if amount > 0:
            print(f"  {currency}: {amount}")
            
            # Se não for USDT, converter para USDT
            if currency == 'USDT':
                total_usdt += amount
            elif currency != 'USDT':
                try:
                    ticker = exchange.fetch_ticker(f"{currency}/USDT")
                    valor_usdt = amount * ticker['last']
                    total_usdt += valor_usdt
                    print(f"       ↳ Valor em USDT: ${valor_usdt:.2f}")
                except:
                    pass
    
    print("-"*40)
    print(f"\n💵 VALOR TOTAL ESTIMADO: ${total_usdt:.2f} USDT")
    print("="*60 + "\n")
    
except Exception as e:
    print(f"❌ Erro: {e}")
