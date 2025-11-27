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
    """Carrega credenciais do arquivo .env"""
    load_dotenv('config/.env')
    
    credentials = {
        'binance_api_key': os.getenv('BINANCE_API_KEY', ''),
        'binance_api_secret': os.getenv('BINANCE_API_SECRET', ''),
        'binance_testnet_api_key': os.getenv('BINANCE_TESTNET_API_KEY', ''),
        'binance_testnet_api_secret': os.getenv('BINANCE_TESTNET_API_SECRET', ''),
        'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
        'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
    }
    
    logger.info("✅ Credenciais carregadas do .env")
    return credentials


def setup_logging(log_level: str = "INFO", log_file: str = "logs/trading_bot.log"):
    """Configura sistema de logs"""
    # Cria diretório de logs se não existir
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
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
    
    logger.info("="*50)
    logger.info("🤖 Bot de Trading Leonardo Iniciado")
    logger.info("="*50)


def format_number(value: float, decimals: int = 2) -> str:
    """Formata números para exibição"""
    return f"{value:,.{decimals}f}"
