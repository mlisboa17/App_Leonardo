"""
Teste de Conexão com Binance Testnet
Verifica se as credenciais estão funcionando
"""
import logging
from src.core import load_config, load_env_credentials, ExchangeClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    """Testa conexão com a exchange"""
    logger.info("="*60)
    logger.info("🧪 TESTE DE CONEXÃO COM BINANCE TESTNET")
    logger.info("="*60)
    
    # Carrega configurações
    config = load_config()
    credentials = load_env_credentials()
    
    # Mostra configuração (sem expor credenciais completas)
    logger.info(f"\n📋 Configuração:")
    logger.info(f"Exchange: {config['exchange']['name']}")
    logger.info(f"Testnet: {config['exchange']['testnet']}")
    logger.info(f"Par: {config['trading']['symbol']}")
    logger.info(f"API Key: {credentials['binance_testnet_api_key'][:10]}...{credentials['binance_testnet_api_key'][-10:]}")
    
    try:
        # Cria cliente
        logger.info(f"\n🔌 Conectando à Binance Testnet...")
        exchange = ExchangeClient(
            exchange_name=config['exchange']['name'],
            api_key=credentials['binance_testnet_api_key'],
            api_secret=credentials['binance_testnet_api_secret'],
            testnet=config['exchange']['testnet']
        )
        
        # Testa conexão
        logger.info("📡 Testando autenticação...")
        if exchange.test_connection():
            logger.info("\n✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
            
            # Busca saldo
            logger.info("\n💰 Consultando saldo da conta testnet...")
            balance = exchange.fetch_balance()
            if balance:
                logger.info(f"\n📊 Saldo disponível:")
                for currency, amount in balance['free'].items():
                    if amount > 0:
                        logger.info(f"  {currency}: {amount}")
                
                total_usdt = balance['total'].get('USDT', 0)
                logger.info(f"\n💵 USDT Total: {total_usdt}")
            
            # Busca preço atual
            logger.info(f"\n📈 Consultando preço de {config['trading']['symbol']}...")
            ticker = exchange.fetch_ticker(config['trading']['symbol'])
            if ticker:
                logger.info(f"  Preço atual: ${ticker['last']:,.2f}")
                logger.info(f"  24h High: ${ticker['high']:,.2f}")
                logger.info(f"  24h Low: ${ticker['low']:,.2f}")
                logger.info(f"  Volume: {ticker['baseVolume']:,.2f}")
            
            logger.info("\n" + "="*60)
            logger.info("🎉 TUDO PRONTO PARA OPERAR!")
            logger.info("="*60)
            logger.info("\n🚀 Próximo passo: python main.py")
            
        else:
            logger.error("\n❌ Falha na conexão - verifique suas credenciais")
            
    except Exception as e:
        logger.error(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
