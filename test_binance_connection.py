"""
Teste de Conexão com Binance
"""
from binance.client import Client
from binance.exceptions import BinanceAPIException

def test_connection():
    # Credenciais diretas
    api_key = "R4So8k98GeMLDhNoMmAedjXjYnUBpxCVZKH9bNbMrM6lfbJzFlY9m3okEbXRuJqR"
    api_secret = "n00KKGAVD7QXbOd3fkCRLXKWFK3PuVS8WUk6wtfpRT0UJG9qRYsay9Qt6LoUKwCN"
    
    print("🔑 Testando credenciais da Binance...")
    print(f"API_KEY: {api_key[:10]}...{api_key[-10:]}")
    
    try:
        client = Client(api_key, api_secret)
        
        # Testa conexão com ping
        print("\n🔄 Testando ping...")
        client.ping()
        print("✅ Ping OK!")
        
        # Testa tempo do servidor
        print("\n🕐 Testando tempo do servidor...")
        server_time = client.get_server_time()
        print(f"✅ Servidor respondeu: {server_time}")
        
        # Testa informações da conta
        print("\n👤 Testando informações da conta...")
        account = client.get_account()
        print(f"✅ Conta ativa!")
        print(f"   - Can Trade: {account['canTrade']}")
        print(f"   - Can Withdraw: {account['canWithdraw']}")
        print(f"   - Can Deposit: {account['canDeposit']}")
        
        # Mostra saldo USDT
        balances = account['balances']
        usdt = next((b for b in balances if b['asset'] == 'USDT'), None)
        if usdt:
            total_usdt = float(usdt['free']) + float(usdt['locked'])
            print(f"\n💰 Saldo USDT:")
            print(f"   - Livre: {usdt['free']}")
            print(f"   - Bloqueado: {usdt['locked']}")
            print(f"   - Total: {total_usdt}")
        
        # Testa preço de BTC
        print("\n📊 Testando preços...")
        btc_price = client.get_symbol_ticker(symbol="BTCUSDT")
        print(f"✅ BTC/USDT: ${btc_price['price']}")
        
        print("\n" + "="*50)
        print("✅ CONEXÃO BINANCE OK! TODOS OS TESTES PASSARAM!")
        print("="*50)
        return True
        
    except BinanceAPIException as e:
        print(f"\n❌ ERRO Binance API: {e}")
        print(f"   Status Code: {e.status_code}")
        print(f"   Mensagem: {e.message}")
        return False
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        return False

if __name__ == "__main__":
    test_connection()
