"""
Configuração do Backend - FastAPI
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv('config/.env')


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Aplicação
    APP_NAME: str = "App Leonardo Trading Bot"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # FastAPI
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    
    # Binance
    BINANCE_API_KEY: str = os.getenv('BINANCE_API_KEY', '')
    BINANCE_API_SECRET: str = os.getenv('BINANCE_API_SECRET', '')
    BINANCE_TESTNET_API_KEY: str = os.getenv('BINANCE_TESTNET_API_KEY', '')
    BINANCE_TESTNET_API_SECRET: str = os.getenv('BINANCE_TESTNET_API_SECRET', '')
    BINANCE_TESTNET: bool = True
    
    # PostgreSQL
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'leonardo')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', 'trading123')
    POSTGRES_HOST: str = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'trading_bot')
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Trading - 8 Criptomoedas de Alta Liquidez
    SYMBOLS: List[str] = [
        'BTC/USDT',   # 1. Bitcoin - Líder em liquidez
        'ETH/USDT',   # 2. Ethereum - Smart Contracts
        'SOL/USDT',   # 3. Solana - Alta velocidade
        'BNB/USDT',   # 4. Binance Coin - Utility token
        'XRP/USDT',   # 5. XRP - Pagamentos transfronteiriços
        'LINK/USDT',  # 6. Chainlink - Oráculos DeFi
        'DOGE/USDT',  # 7. Dogecoin - Alta volatilidade
        'LTC/USDT'    # 8. Litecoin - Prata digital
    ]
    TIMEFRAME: str = '1m'  # 1 minuto para scalping rápido
    AMOUNT_PER_TRADE: float = 20.0  # $20 por trade (maior exposição)
    MAX_POSITIONS: int = 8  # 1 posição por cripto
    
    # Estratégia ADAPTATIVA - Meta $100/dia
    # Cada moeda terá seu próprio RSI threshold baseado em histórico
    STRATEGY_TYPE: str = 'adaptive'  # Mudou de 'scalping' para 'adaptive'
    
    # Thresholds base (serão ajustados por moeda)
    RSI_OVERSOLD: int = 35  # Base, será adaptado por moeda
    RSI_OVERBOUGHT: int = 65  # Base, será adaptado por moeda
    STOP_LOSS_PCT: float = -1.5  # Stop menor para scalping
    TAKE_PROFIT_PCT: float = 0.8  # Take menor mas mais rápido (pode ir até 3% se tendência alta)
    
    # Meta Diária
    DAILY_PROFIT_TARGET: float = 100.0  # Meta de $100/dia
    MIN_TRADES_PER_DAY: int = 50  # Mínimo 50 trades/dia
    
    # Safety
    MAX_DAILY_LOSS: float = 50.0  # Limite de perda menor
    MAX_DRAWDOWN_PCT: float = 15.0  # Mais conservador no drawdown
    MAX_LOSS_PER_TRADE: float = 2.0  # Máximo $2 de perda por trade
    
    # Scalping Settings
    RAPID_TRADING: bool = True  # Ativa trading rápido
    MIN_PROFIT_PER_TRADE: float = 0.5  # Mínimo $0.50 lucro por trade
    TRADE_COOLDOWN_SECONDS: int = 10  # 10s entre trades do mesmo símbolo
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    
    class Config:
        case_sensitive = True


settings = Settings()
