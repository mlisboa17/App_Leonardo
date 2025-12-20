"""
Utilitários e funções auxiliares
"""
import yaml
import logging
import os
from typing import Dict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> Dict:
    """Carrega arquivo de configuração YAML"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"✅ Configuração carregada: {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"❌ Arquivo de configuração não encontrado: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"❌ Erro ao ler YAML: {e}")
        return {}


def load_env_credentials() -> Dict[str, str]:
    """Carrega credenciais do arquivo .env

    Procura por um `.env` no diretório raiz primeiro, depois em `config/.env`.
    """
    # Tenta carregar .env padrão do projeto (raiz) e, em seguida, o de `config/` como fallback
    load_dotenv()
    load_dotenv('config/.env')
    
    credentials = {
        'BINANCE_API_KEY': os.getenv('BINANCE_API_KEY', ''),
        'BINANCE_API_SECRET': os.getenv('BINANCE_API_SECRET', ''),
        'BINANCE_TESTNET_API_KEY': os.getenv('BINANCE_TESTNET_API_KEY', ''),
        'BINANCE_TESTNET_API_SECRET': os.getenv('BINANCE_TESTNET_API_SECRET', ''),
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
        'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', ''),
    }
    
    logger.info("✅ Credenciais carregadas do .env (se presentes)")
    return credentials


def setup_logging(log_level: str = "INFO", log_file: str = "logs/trading_bot.log"):
    """Configura sistema de logs

    Pode ser forçado para DEBUG por variável de ambiente:
      - LOG_LEVEL=DEBUG    (define o nível global)
      - DEBUG_NETWORK=1    (força DEBUG em bibliotecas de rede: ccxt, urllib3, requests)
    """
    # Cria diretório de logs se não existir
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Permite override via variáveis de ambiente (útil para debugging sem alterar código)
    env_level = os.getenv('LOG_LEVEL')
    if env_level:
        log_level = env_level

    # Formato dos logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Configuração
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Console
        ]
    )

    # Se solicitado, forçar DEBUG em bibliotecas de rede para capturar erros TLS/SSL
    if os.getenv('DEBUG_NETWORK') in ('1', 'true', 'True'):
        logging.getLogger('ccxt').setLevel(logging.DEBUG)
        logging.getLogger('urllib3').setLevel(logging.DEBUG)
        logging.getLogger('requests').setLevel(logging.DEBUG)
        logging.getLogger('websockets').setLevel(logging.DEBUG)
        logging.getLogger('asyncio').setLevel(logging.DEBUG)
        logger.debug('DEBUG_NETWORK ativado: ccxt/urllib3/requests/websockets/asyncio em DEBUG')

    logger.info("="*50)
    logger.info("🤖 Bot de Trading Leonardo Iniciado")
    logger.info("="*50)


def format_number(value: float, decimals: int = 2) -> str:
    """Formata números para exibição"""
    return f"{value:,.{decimals}f}"
