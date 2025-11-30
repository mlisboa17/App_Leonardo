"""Verifica credenciais da Binance"""
from dotenv import load_dotenv
import os

load_dotenv('config/.env')

key = os.getenv('BINANCE_TESTNET_API_KEY', '')
secret = os.getenv('BINANCE_TESTNET_API_SECRET', '')

print("=" * 50)
print("VERIFICAÇÃO DE CREDENCIAIS")
print("=" * 50)

if key and len(key) > 10:
    print(f"API Key: ✅ Configurada ({key[:8]}...)")
else:
    print("API Key: ❌ Não configurada")

if secret and len(secret) > 10:
    print(f"Secret: ✅ Configurada ({secret[:8]}...)")
else:
    print("Secret: ❌ Não configurada")

print("=" * 50)

if key and secret:
    print("\n🎉 Credenciais OK! Testando conexão...")
    
    try:
        import ccxt
        
        exchange = ccxt.binance({
            'apiKey': key,
            'secret': secret,
            'sandbox': True,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True,  # Ajusta diferença de tempo
                'recvWindow': 60000,  # Janela de tempo maior
            }
        })
        
        # Carrega mercados primeiro
        exchange.load_markets()
        
        balance = exchange.fetch_balance()
        
        print("\n💰 SALDO NA TESTNET:")
        for currency, amount in balance['free'].items():
            if float(amount) > 0:
                print(f"   {currency}: {float(amount):.4f}")
        
        usdt = float(balance['free'].get('USDT', 0))
        print(f"\n📊 USDT Disponível: ${usdt:.2f}")
        
        if usdt >= 100:
            print("✅ Pronto para operar!")
        else:
            print("⚠️ Pegue mais fundos em: https://testnet.binance.vision/")
            
    except Exception as e:
        print(f"\n❌ Erro ao conectar: {e}")
else:
    print("\n⚠️ Configure as credenciais no arquivo config/.env")
