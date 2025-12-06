"""
🔧 Configurador de Credenciais da Binance Testnet
Execute este script para configurar suas API Keys
"""

import os

def setup_credentials():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  🔧 CONFIGURAÇÃO DA BINANCE TESTNET                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  PASSO 1: Acesse https://testnet.binance.vision/             ║
║  PASSO 2: Faça login com GitHub                              ║
║  PASSO 3: Clique em "Generate HMAC_SHA256 Key"               ║
║  PASSO 4: Copie as chaves geradas                            ║
║                                                              ║
║  💰 FUNDOS DE TESTE:                                         ║
║  - São creditados automaticamente ao criar a conta           ║
║  - Ou clique em "Faucet" para receber mais                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    print("\n📝 Cole suas credenciais da Testnet:\n")
    
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret: ").strip()
    
    if not api_key or not api_secret:
        print("\n❌ Credenciais vazias! Tente novamente.")
        return
    
    # Cria/atualiza arquivo .env
    env_path = ".env"
    env_content = ""
    
    # Lê conteúdo existente se houver
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                # Remove linhas antigas de testnet
                if not line.startswith('BINANCE_TESTNET_'):
                    env_content += line
    
    # Adiciona novas credenciais
    env_content += f"\n# Binance Testnet Credentials\n"
    env_content += f"BINANCE_TESTNET_API_KEY={api_key}\n"
    env_content += f"BINANCE_TESTNET_API_SECRET={api_secret}\n"
    
    # Salva
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  ✅ CREDENCIAIS SALVAS COM SUCESSO!                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Arquivo: .env                                               ║
║  API Key: {api_key[:20]}...                        ║
║                                                              ║
║  🚀 Agora você pode executar:                                ║
║     python main.py                                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Testa conexão
    test = input("\n🔌 Deseja testar a conexão agora? (s/n): ").strip().lower()
    
    if test == 's':
        test_connection()


def test_connection():
    """Testa conexão com a Binance Testnet"""
    print("\n🔄 Testando conexão...")
    
    try:
        import ccxt
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('BINANCE_TESTNET_API_KEY')
        api_secret = os.getenv('BINANCE_TESTNET_API_SECRET')
        
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': True,  # Testnet
            'options': {'defaultType': 'spot'}
        })
        
        # Testa conexão
        balance = exchange.fetch_balance()
        
        print("\n✅ CONEXÃO BEM SUCEDIDA!")
        print("\n💰 Saldos disponíveis:")
        print("-" * 40)
        
        for currency, amount in balance['free'].items():
            if float(amount) > 0:
                print(f"  {currency}: {float(amount):.4f}")
        
        print("-" * 40)
        
        usdt = float(balance['free'].get('USDT', 0))
        btc = float(balance['free'].get('BTC', 0))
        
        print(f"\n📊 Resumo:")
        print(f"   USDT: ${usdt:.2f}")
        print(f"   BTC: {btc:.6f}")
        
        if usdt < 100:
            print("\n⚠️ USDT baixo! Vá em https://testnet.binance.vision/ e clique em 'Faucet'")
        else:
            print("\n🎉 Você tem fundos suficientes para testar!")
            
    except Exception as e:
        print(f"\n❌ Erro ao conectar: {e}")
        print("\nVerifique:")
        print("  1. As credenciais estão corretas?")
        print("  2. Você usou as chaves da TESTNET (não da conta real)?")
        print("  3. A biblioteca ccxt está instalada? (pip install ccxt)")


def check_balance_only():
    """Apenas verifica o saldo atual"""
    print("\n🔄 Verificando saldo...")
    
    try:
        import ccxt
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('BINANCE_TESTNET_API_KEY')
        api_secret = os.getenv('BINANCE_TESTNET_API_SECRET')
        
        if not api_key:
            print("❌ Credenciais não encontradas! Execute 'setup' primeiro.")
            return
        
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': True,
            'options': {'defaultType': 'spot'}
        })
        
        balance = exchange.fetch_balance()
        
        print("\n💰 SALDO NA BINANCE TESTNET")
        print("=" * 40)
        
        total_usdt = 0
        for currency, amount in balance['free'].items():
            amt = float(amount)
            if amt > 0:
                print(f"  {currency}: {amt:.4f}")
                if currency == 'USDT':
                    total_usdt = amt
        
        print("=" * 40)
        print(f"  USDT Disponível: ${total_usdt:.2f}")
        
        if total_usdt >= 100:
            print("\n✅ Pronto para operar! Execute: python main.py")
        else:
            print("\n⚠️ Pegue mais fundos em: https://testnet.binance.vision/")
            
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║  🧪 BINANCE TESTNET - CONFIGURAÇÃO                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] Configurar credenciais (primeira vez)                   ║
║  [2] Verificar saldo atual                                   ║
║  [3] Testar conexão                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    choice = input("Escolha uma opção (1/2/3): ").strip()
    
    if choice == '1':
        setup_credentials()
    elif choice == '2':
        check_balance_only()
    elif choice == '3':
        test_connection()
    else:
        print("Opção inválida!")
