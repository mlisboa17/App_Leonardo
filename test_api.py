"""Teste de API da Binance"""
import ccxt
import os
from dotenv import load_dotenv

load_dotenv('config/.env')

api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

print(f"API Key: {api_key[:20]}...")
print(f"Secret: {api_secret[:10]}...")

exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True
})

print("\n1. Testando conexao...")
try:
    balance = exchange.fetch_balance()
    usdt = balance['USDT']['free']
    print(f"   OK! Saldo USDT: ${usdt:.2f}")
except Exception as e:
    print(f"   ERRO: {e}")

print("\n2. Testando permissao de TRADING...")
try:
    # Tenta criar ordem minima
    order = exchange.create_market_buy_order('BTC/USDT', 0.00001)
    print(f"   OK! Ordem criada: {order['id']}")
    print("   TRADING HABILITADO!")
except ccxt.PermissionDenied as e:
    print(f"   ERRO: Permissao negada!")
    print(f"   Voce precisa habilitar 'Ativar Trading Spot' na API da Binance")
except ccxt.InvalidOrder as e:
    print(f"   Ordem invalida (muito pequena), mas TRADING ESTA HABILITADO!")
except Exception as e:
    error_msg = str(e)
    if "Invalid API-key" in error_msg or "permissions" in error_msg:
        print(f"   ERRO: API sem permissao de Trading!")
        print(f"   VA NA BINANCE -> API -> Editar restricoes -> Marque 'Ativar Trading Spot'")
    else:
        print(f"   ERRO: {e}")
