"""
Database Configuration - PostgreSQL/TimescaleDB
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from backend.config import settings

# Base para modelos
Base = declarative_base()

# Engine assíncrono
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Session assíncrona
AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Engine síncrono (para Alembic)
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=settings.DEBUG
)


# ========================================
# MODELOS DE DADOS
# ========================================

class Trade(Base):
    """Modelo de Trade Executado"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    side = Column(String(10), nullable=False)  # BUY/SELL
    
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    
    pnl = Column(Float, nullable=False)
    pnl_pct = Column(Float, nullable=False)
    
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Float)
    
    entry_reason = Column(Text)
    exit_reason = Column(Text)
    
    # Indicadores no momento da entrada
    entry_rsi = Column(Float)
    entry_macd = Column(Float)
    entry_macd_signal = Column(Float)
    entry_sma_20 = Column(Float)
    
    strategy = Column(String(50))
    order_id = Column(String(100))
    
    def __repr__(self):
        return f"<Trade {self.symbol} {self.side} PnL:{self.pnl:.2f}>"


class MarketData(Base):
    """Modelo de Dados de Mercado (OHLCV) - TimescaleDB"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    symbol = Column(String(20), index=True, nullable=False)
    
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    # Indicadores calculados
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    
    def __repr__(self):
        return f"<MarketData {self.symbol} {self.timestamp}>"


class Position(Base):
    """Posições Abertas"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    side = Column(String(10), nullable=False)
    
    entry_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow)
    
    entry_reason = Column(Text)
    entry_rsi = Column(Float)
    entry_macd = Column(Float)
    
    is_open = Column(Boolean, default=True)
    order_id = Column(String(100))
    
    def __repr__(self):
        return f"<Position {self.symbol} {self.side} @ {self.entry_price}>"


class Analysis(Base):
    """Análises de Mercado (cada verificação)"""
    __tablename__ = 'market_analysis'
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    
    price = Column(Float, nullable=False)
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    sma_20 = Column(Float)
    
    signal = Column(String(10))  # BUY/SELL/HOLD
    reason = Column(Text)
    
    def __repr__(self):
        return f"<Analysis {self.symbol} {self.signal}>"


class BotStatus(Base):
    """Status do Bot"""
    __tablename__ = 'bot_status'
    
    id = Column(Integer, primary_key=True)
    is_running = Column(Boolean, default=False)
    start_time = Column(DateTime)
    last_update = Column(DateTime, default=datetime.utcnow)
    
    # Saldos
    balance_usd = Column(Float, default=1000.0)  # Saldo em USD
    initial_balance = Column(Float, default=1000.0)
    daily_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    
    # Estatísticas de trades
    total_trades = Column(Integer, default=0)
    total_trades_today = Column(Integer, default=0)  # Trades no dia
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    open_positions = Column(Integer, default=0)  # Posições abertas
    
    current_strategy = Column(String(50))
    last_trade_time = Column(DateTime)
    
    def __repr__(self):
        return f"<BotStatus running={self.is_running} positions={self.open_positions}>"


class CryptoBalance(Base):
    """Saldo de cada Criptomoeda"""
    __tablename__ = 'crypto_balances'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    
    # Saldos
    amount = Column(Float, default=0.0)  # Quantidade da cripto
    invested_usd = Column(Float, default=0.0)  # USD investido
    current_value_usd = Column(Float, default=0.0)  # Valor atual em USD
    pnl_usd = Column(Float, default=0.0)  # Lucro/Perda em USD
    pnl_pct = Column(Float, default=0.0)  # Lucro/Perda em %
    
    # Estatísticas
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # Preço
    avg_entry_price = Column(Float, default=0.0)
    last_price = Column(Float, default=0.0)
    
    # Tendência
    trend = Column(String(20), default='NEUTRAL')  # BULLISH/BEARISH/NEUTRAL
    trend_strength = Column(Float, default=0.0)  # 0-100
    
    last_update = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CryptoBalance {self.symbol} ${self.invested_usd:.2f}>"


# ========================================
# FUNÇÕES DE DATABASE
# ========================================

async def get_db():
    """Dependency para obter sessão do banco"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Inicializa o banco de dados"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database initialized")
    
    # Ativa TimescaleDB para market_data (se disponível)
    try:
        async with AsyncSessionLocal() as session:
            # Cria hypertable para dados de mercado
            await session.execute(
                "SELECT create_hypertable('market_data', 'timestamp', if_not_exists => TRUE);"
            )
            await session.commit()
            print("✅ TimescaleDB hypertable created for market_data")
    except Exception as e:
        print(f"⚠️  TimescaleDB not available (using regular PostgreSQL): {e}")
