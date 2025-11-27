"""
Script de teste - Verifica se o bot inicializa corretamente
Não executa trades reais
"""
import sys
import logging

# Setup de logging simples
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    try:
        logger.info("🧪 Testando imports...")
        
        from src.core import ExchangeClient, load_config, load_env_credentials, setup_logging
        logger.info("✅ src.core - OK")
        
        from src.safety import SafetyManager
        logger.info("✅ src.safety - OK")
        
        from src.indicators import TechnicalIndicators
        logger.info("✅ src.indicators - OK")
        
        from src.strategies import SimpleRSIStrategy
        logger.info("✅ src.strategies - OK")
        
        logger.info("\n🎉 Todos os módulos importados com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao importar módulos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Testa se as configurações podem ser carregadas"""
    try:
        logger.info("\n🧪 Testando configurações...")
        
        from src.core import load_config
        config = load_config()
        
        if config:
            logger.info(f"✅ Config carregada: {config.get('trading', {}).get('symbol')}")
            logger.info(f"✅ Exchange: {config.get('exchange', {}).get('name')}")
            logger.info(f"✅ Testnet: {config.get('exchange', {}).get('testnet')}")
            return True
        else:
            logger.warning("⚠️ Configuração vazia")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao carregar config: {e}")
        return False

def test_indicators():
    """Testa cálculo de indicadores"""
    try:
        logger.info("\n🧪 Testando cálculo de indicadores...")
        
        import pandas as pd
        import numpy as np
        from src.indicators import TechnicalIndicators
        
        # Cria dados de teste
        df = pd.DataFrame({
            'close': np.random.uniform(40000, 50000, 100)
        })
        
        # Testa RSI
        rsi = TechnicalIndicators.calculate_rsi(df, period=14)
        logger.info(f"✅ RSI calculado: último valor = {rsi.iloc[-1]:.2f}")
        
        # Testa SMA
        sma = TechnicalIndicators.calculate_sma(df, period=20)
        logger.info(f"✅ SMA calculado: último valor = {sma.iloc[-1]:.2f}")
        
        # Testa MACD
        macd = TechnicalIndicators.calculate_macd(df)
        logger.info(f"✅ MACD calculado: {len(macd)} linhas")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao calcular indicadores: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes"""
    logger.info("="*60)
    logger.info("🤖 BOT DE TRADING LEONARDO - TESTE DE INSTALAÇÃO")
    logger.info("="*60)
    
    results = []
    
    # Teste 1: Imports
    results.append(("Imports", test_imports()))
    
    # Teste 2: Configurações
    results.append(("Configurações", test_config()))
    
    # Teste 3: Indicadores
    results.append(("Indicadores", test_indicators()))
    
    # Resumo
    logger.info("\n" + "="*60)
    logger.info("📊 RESUMO DOS TESTES")
    logger.info("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        logger.info(f"{test_name:20s} - {status}")
        if not passed:
            all_passed = False
    
    logger.info("="*60)
    
    if all_passed:
        logger.info("🎉 TODOS OS TESTES PASSARAM!")
        logger.info("\n📝 Próximos passos:")
        logger.info("1. Edite config/.env com suas credenciais da Binance Testnet")
        logger.info("2. Acesse: https://testnet.binance.vision/")
        logger.info("3. Execute: python main.py")
        return 0
    else:
        logger.error("❌ ALGUNS TESTES FALHARAM")
        logger.error("Verifique os erros acima e corrija antes de executar o bot")
        return 1

if __name__ == "__main__":
    sys.exit(main())
