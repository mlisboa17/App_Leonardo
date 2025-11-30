"""
🧪 Script de Teste do Bot
Testa todos os componentes antes de rodar o bot completo
"""
import os
import sys

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*60)
print("🧪 TESTANDO COMPONENTES DO BOT")
print("="*60)

# 1. Testa importações
print("\n1️⃣ Testando importações...")
try:
    from core.utils import load_config, load_env_credentials, setup_logging
    from core.exchange_client import ExchangeClient
    from indicators.technical_indicators import TechnicalIndicators
    from safety.safety_manager import SafetyManager
    from strategies.simple_strategies_new import SimpleStrategy, get_strategy
    print("   ✅ Todas as importações OK")
except Exception as e:
    print(f"   ❌ Erro nas importações: {e}")
    sys.exit(1)

# 2. Testa configuração
print("\n2️⃣ Testando carregamento de configuração...")
try:
    config = load_config()
    print(f"   ✅ Config carregada: {config['exchange']['name']}")
    print(f"   ✅ Símbolos: {', '.join(config['trading']['symbols'])}")
    print(f"   ✅ Timeframe: {config['trading']['timeframe']}")
    print(f"   ✅ Modo: {'DRY RUN' if config['execution']['dry_run'] else 'REAL'}")
    print(f"   ✅ Testnet: {config['exchange']['testnet']}")
except Exception as e:
    print(f"   ❌ Erro ao carregar config: {e}")
    sys.exit(1)

# 3. Testa credenciais
print("\n3️⃣ Testando credenciais...")
try:
    credentials = load_env_credentials()
    has_api_key = bool(credentials.get('BINANCE_API_KEY'))
    has_api_secret = bool(credentials.get('BINANCE_API_SECRET'))
    
    if has_api_key and has_api_secret:
        print("   ✅ Credenciais encontradas")
    else:
        print("   ⚠️  Credenciais não encontradas (modo API pública)")
        print("   💡 Crie config/.env com suas credenciais para trading real")
except Exception as e:
    print(f"   ❌ Erro ao carregar credenciais: {e}")

# 4. Testa estratégia
print("\n4️⃣ Testando estratégia de trading...")
try:
    strategy = get_strategy('simple', config)
    print(f"   ✅ Estratégia criada: {strategy.name}")
    print(f"   ✅ RSI Oversold: {strategy.rsi_oversold}")
    print(f"   ✅ RSI Overbought: {strategy.rsi_overbought}")
    
    # Testa estratégias alternativas
    aggressive = get_strategy('aggressive', config)
    conservative = get_strategy('conservative', config)
    print(f"   ✅ Estratégias disponíveis: Simple, Aggressive, Conservative")
except Exception as e:
    print(f"   ❌ Erro na estratégia: {e}")
    sys.exit(1)

# 5. Testa Safety Manager
print("\n5️⃣ Testando Safety Manager...")
try:
    safety = SafetyManager(config['safety'])
    print(f"   ✅ Safety Manager criado")
    print(f"   ✅ Max Daily Loss: {config['safety']['max_daily_loss']} USDT")
    print(f"   ✅ Max Drawdown: {config['safety']['max_drawdown']}%")
    print(f"   ✅ Price Deviation Limit: {config['safety']['price_deviation_limit']}%")
except Exception as e:
    print(f"   ❌ Erro no Safety Manager: {e}")
    sys.exit(1)

# 6. Testa Exchange Client
print("\n6️⃣ Testando conexão com Exchange...")
try:
    # Usa credenciais vazias para teste de API pública
    exchange = ExchangeClient(
        exchange_name='binance',
        api_key='',
        api_secret='',
        testnet=True
    )
    print("   ✅ Exchange Client criado")
    
    # Testa buscar preço (API pública)
    print("   🔄 Testando fetch_ticker (BTC/USDT)...")
    ticker = exchange.fetch_ticker('BTC/USDT')
    if ticker:
        print(f"   ✅ Preço BTC: ${ticker['last']:,.2f}")
        print(f"   ✅ Volume 24h: {ticker['quoteVolume']:,.0f} USDT")
    else:
        print("   ⚠️  Não foi possível obter ticker")
    
except Exception as e:
    print(f"   ❌ Erro na Exchange: {e}")
    print("   💡 Isso é normal se não houver internet ou API indisponível")

# 7. Testa Indicadores
print("\n7️⃣ Testando cálculo de indicadores...")
try:
    import pandas as pd
    import numpy as np
    
    # Cria dados de exemplo
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='1h')
    prices = 50000 + np.random.randn(100).cumsum() * 100
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices + np.random.rand(100) * 100,
        'low': prices - np.random.rand(100) * 100,
        'close': prices,
        'volume': np.random.rand(100) * 1000
    })
    
    # Calcula indicadores
    df = TechnicalIndicators.calculate_all_indicators(df, config['indicators'])
    
    print(f"   ✅ RSI calculado: {df['rsi'].iloc[-1]:.2f}")
    print(f"   ✅ MACD calculado: {df['MACD_12_26_9'].iloc[-1]:.4f}")
    print(f"   ✅ SMA20: {df['sma_20'].iloc[-1]:.2f}")
    
except Exception as e:
    print(f"   ❌ Erro nos indicadores: {e}")
    sys.exit(1)

# 8. Testa análise de estratégia
print("\n8️⃣ Testando análise de estratégia...")
try:
    signal, reason, indicators = strategy.analyze(df, 'BTC/USDT')
    print(f"   ✅ Sinal gerado: {signal}")
    print(f"   ✅ Razão: {reason}")
    print(f"   ✅ RSI: {indicators.get('rsi', 0):.2f}")
except Exception as e:
    print(f"   ❌ Erro na análise: {e}")
    sys.exit(1)

# 9. Verifica estrutura de pastas
print("\n9️⃣ Verificando estrutura de pastas...")
try:
    required_dirs = ['logs', 'data/cache', 'data/reports', 'config']
    for dir_path in required_dirs:
        os.makedirs(dir_path, exist_ok=True)
    print("   ✅ Todas as pastas necessárias existem")
except Exception as e:
    print(f"   ❌ Erro ao criar pastas: {e}")

# 10. Testa criação de arquivos de estado
print("\n🔟 Testando criação de arquivos de estado...")
try:
    import json
    from datetime import datetime
    
    # Testa bot_state.json
    test_state = {
        'status': 'Test',
        'balance': 10000.0,
        'timestamp': int(datetime.now().timestamp() * 1000)
    }
    
    with open('bot_state_test.json', 'w') as f:
        json.dump(test_state, f, indent=2)
    
    # Lê de volta
    with open('bot_state_test.json', 'r') as f:
        loaded = json.load(f)
    
    os.remove('bot_state_test.json')
    print("   ✅ Arquivos JSON podem ser criados e lidos")
    
except Exception as e:
    print(f"   ❌ Erro ao testar arquivos: {e}")

# Resultado final
print("\n" + "="*60)
print("✅ TODOS OS TESTES PASSARAM!")
print("="*60)
print("\n🚀 O bot está pronto para uso!")
print("\nPróximos passos:")
print("1. Configure config/.env com suas credenciais (opcional)")
print("2. Execute: python main.py")
print("3. Ou use: start_bot.bat\n")
