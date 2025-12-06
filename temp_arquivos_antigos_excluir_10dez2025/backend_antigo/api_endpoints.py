"""
API Endpoints - Estatísticas e Dados do Bot
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
from typing import List, Dict
import ccxt.async_support as ccxt

from backend.database import (
    get_db, Trade, MarketData, Position, 
    BotStatus, CryptoBalance, AsyncSessionLocal
)
from backend.config import settings

router = APIRouter(prefix="/api", tags=["Trading Stats"])


# ========================================
# CCXT Exchange Client
# ========================================

async def get_exchange():
    """Inicializa conexão com Binance"""
    if settings.BINANCE_TESTNET:
        exchange = ccxt.binance({
            'apiKey': settings.BINANCE_TESTNET_API_KEY,
            'secret': settings.BINANCE_TESTNET_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'testnet': True
            }
        })
        exchange.set_sandbox_mode(True)
    else:
        exchange = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_API_SECRET,
            'enableRateLimit': True
        })
    
    return exchange


# ========================================
# ENDPOINTS
# ========================================

@router.get("/status")
async def get_status():
    """Status completo do bot com saldos e estatísticas"""
    try:
        async with AsyncSessionLocal() as session:
            # Status do bot
            result = await session.execute(select(BotStatus).limit(1))
            bot_status = result.scalar_one_or_none()
            
            if not bot_status:
                # Cria status inicial
                bot_status = BotStatus(
                    balance_usd=1000.0,
                    initial_balance=1000.0,
                    is_running=False
                )
                session.add(bot_status)
                await session.commit()
            
            # Saldos por cripto
            crypto_result = await session.execute(select(CryptoBalance))
            crypto_balances = crypto_result.scalars().all()
            
            balance_crypto = {}
            total_crypto_value = 0.0
            
            for cb in crypto_balances:
                balance_crypto[cb.symbol] = {
                    "amount": round(cb.amount, 8),
                    "invested_usd": round(cb.invested_usd, 2),
                    "current_value_usd": round(cb.current_value_usd, 2),
                    "pnl_usd": round(cb.pnl_usd, 2),
                    "pnl_pct": round(cb.pnl_pct, 2),
                    "trend": cb.trend,
                    "trend_strength": round(cb.trend_strength, 1),
                    "win_rate": round(cb.win_rate, 1),
                    "total_trades": cb.total_trades,
                    "last_price": cb.last_price
                }
                total_crypto_value += cb.current_value_usd
            
            # Posições abertas
            positions_result = await session.execute(
                select(Position).where(Position.is_open == True)
            )
            open_positions = positions_result.scalars().all()
            
            positions_data = []
            for pos in open_positions:
                positions_data.append({
                    "symbol": pos.symbol,
                    "amount": pos.amount,
                    "entry_price": pos.entry_price,
                    "entry_time": pos.entry_time.isoformat(),
                    "invested": round(pos.amount * pos.entry_price, 2)
                })
            
            win_rate = 0
            if bot_status.total_trades > 0:
                win_rate = (bot_status.winning_trades / bot_status.total_trades) * 100
            
            return {
                "is_running": bot_status.is_running,
                
                # Saldos
                "balance_usd": round(bot_status.balance_usd, 2),
                "balance_crypto": balance_crypto,
                "total_crypto_value_usd": round(total_crypto_value, 2),
                "total_value_usd": round(bot_status.balance_usd + total_crypto_value, 2),
                
                # Estatísticas de trades
                "total_trades": bot_status.total_trades,
                "total_trades_today": bot_status.total_trades_today,
                "winning_trades": bot_status.winning_trades,
                "losing_trades": bot_status.losing_trades,
                "win_rate": round(win_rate, 1),
                
                # Posições
                "open_positions_count": len(positions_data),
                "open_positions": positions_data,
                
                # PnL
                "daily_pnl": round(bot_status.daily_pnl, 2),
                "total_pnl": round(bot_status.total_pnl, 2),
                "total_pnl_pct": round((bot_status.total_pnl / bot_status.initial_balance) * 100, 2),
                
                # Timestamps
                "start_time": bot_status.start_time.isoformat() if bot_status.start_time else None,
                "last_update": bot_status.last_update.isoformat()
            }
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        return {"error": str(e)}


@router.get("/crypto/{symbol}/stats")
async def get_crypto_stats(symbol: str):
    """Estatísticas detalhadas de uma criptomoeda específica"""
    try:
        async with AsyncSessionLocal() as session:
            # Balance da cripto
            result = await session.execute(
                select(CryptoBalance).where(CryptoBalance.symbol == symbol)
            )
            crypto = result.scalar_one_or_none()
            
            if not crypto:
                return {
                    "symbol": symbol,
                    "invested_usd": 0,
                    "total_trades": 0,
                    "trend": "NEUTRAL"
                }
            
            # Últimos trades desta cripto
            trades_result = await session.execute(
                select(Trade)
                .where(Trade.symbol == symbol)
                .order_by(Trade.timestamp.desc())
                .limit(10)
            )
            recent_trades = trades_result.scalars().all()
            
            trades_list = []
            for trade in recent_trades:
                trades_list.append({
                    "timestamp": trade.timestamp.isoformat(),
                    "side": trade.side,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "pnl": round(trade.pnl, 2),
                    "pnl_pct": round(trade.pnl_pct, 2)
                })
            
            # Posição aberta
            pos_result = await session.execute(
                select(Position).where(
                    and_(Position.symbol == symbol, Position.is_open == True)
                )
            )
            position = pos_result.scalar_one_or_none()
            
            position_data = None
            if position:
                position_data = {
                    "amount": position.amount,
                    "entry_price": position.entry_price,
                    "entry_time": position.entry_time.isoformat(),
                    "invested": round(position.amount * position.entry_price, 2)
                }
            
            return {
                "symbol": crypto.symbol,
                "amount": crypto.amount,
                "invested_usd": round(crypto.invested_usd, 2),
                "current_value_usd": round(crypto.current_value_usd, 2),
                "pnl_usd": round(crypto.pnl_usd, 2),
                "pnl_pct": round(crypto.pnl_pct, 2),
                "total_trades": crypto.total_trades,
                "winning_trades": crypto.winning_trades,
                "losing_trades": crypto.losing_trades,
                "win_rate": round(crypto.win_rate, 1),
                "trend": crypto.trend,
                "trend_strength": round(crypto.trend_strength, 1),
                "last_price": crypto.last_price,
                "recent_trades": trades_list,
                "open_position": position_data
            }
    except Exception as e:
        print(f"❌ Error getting crypto stats: {e}")
        return {"error": str(e)}


@router.get("/crypto/{symbol}/chart")
async def get_crypto_chart(symbol: str, timeframe: str = "1h", limit: int = 100):
    """Dados de gráfico (OHLCV + indicadores) para uma cripto"""
    try:
        async with AsyncSessionLocal() as session:
            # Busca dados do banco
            result = await session.execute(
                select(MarketData)
                .where(MarketData.symbol == symbol)
                .order_by(MarketData.timestamp.desc())
                .limit(limit)
            )
            candles = result.scalars().all()
            
            if not candles:
                # Busca da API se não tiver no banco
                exchange = await get_exchange()
                try:
                    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                    await exchange.close()
                    
                    chart_data = []
                    for candle in ohlcv:
                        chart_data.append({
                            "timestamp": datetime.fromtimestamp(candle[0] / 1000).isoformat(),
                            "open": candle[1],
                            "high": candle[2],
                            "low": candle[3],
                            "close": candle[4],
                            "volume": candle[5]
                        })
                    
                    return {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "candles": list(reversed(chart_data))
                    }
                except Exception as e:
                    print(f"❌ Error fetching from exchange: {e}")
                    return {"error": str(e)}
            
            # Formata dados do banco
            chart_data = []
            for candle in reversed(candles):
                chart_data.append({
                    "timestamp": candle.timestamp.isoformat(),
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                    "rsi": candle.rsi,
                    "macd": candle.macd,
                    "macd_signal": candle.macd_signal,
                    "macd_histogram": candle.macd_histogram
                })
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": chart_data
            }
    except Exception as e:
        print(f"❌ Error getting chart: {e}")
        return {"error": str(e)}


@router.get("/prices/live")
async def get_live_prices():
    """Preços ao vivo de todas as 8 criptomoedas"""
    try:
        exchange = await get_exchange()
        prices = {}
        
        for symbol in settings.SYMBOLS:
            try:
                ticker = await exchange.fetch_ticker(symbol)
                prices[symbol] = {
                    "price": ticker['last'],
                    "change_24h": ticker['percentage'],
                    "high_24h": ticker['high'],
                    "low_24h": ticker['low'],
                    "volume_24h": ticker['quoteVolume']
                }
            except Exception as e:
                print(f"❌ Error fetching {symbol}: {e}")
                prices[symbol] = {"error": str(e)}
        
        await exchange.close()
        return prices
    except Exception as e:
        print(f"❌ Error getting live prices: {e}")
        return {"error": str(e)}


@router.get("/trades/recent")
async def get_recent_trades(limit: int = 20):
    """Trades recentes de todas as criptos"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Trade)
                .order_by(Trade.timestamp.desc())
                .limit(limit)
            )
            trades = result.scalars().all()
            
            trades_list = []
            for trade in trades:
                trades_list.append({
                    "id": trade.id,
                    "timestamp": trade.timestamp.isoformat(),
                    "symbol": trade.symbol,
                    "side": trade.side,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "amount": trade.amount,
                    "pnl": round(trade.pnl, 2),
                    "pnl_pct": round(trade.pnl_pct, 2),
                    "duration_minutes": trade.duration_minutes
                })
            
            return trades_list
    except Exception as e:
        print(f"❌ Error getting recent trades: {e}")
        return {"error": str(e)}


@router.get("/summary")
async def get_summary():
    """Resumo geral para dashboard principal"""
    try:
        async with AsyncSessionLocal() as session:
            # Status
            status_result = await session.execute(select(BotStatus).limit(1))
            bot_status = status_result.scalar_one_or_none()
            
            # Todas as criptos
            crypto_result = await session.execute(select(CryptoBalance))
            cryptos = crypto_result.scalars().all()
            
            crypto_cards = []
            for crypto in cryptos:
                crypto_cards.append({
                    "symbol": crypto.symbol.replace('/USDT', ''),
                    "invested_usd": round(crypto.invested_usd, 2),
                    "current_value_usd": round(crypto.current_value_usd, 2),
                    "pnl_usd": round(crypto.pnl_usd, 2),
                    "pnl_pct": round(crypto.pnl_pct, 2),
                    "trend": crypto.trend,
                    "trend_strength": round(crypto.trend_strength, 1),
                    "amount": round(crypto.amount, 8),
                    "last_price": crypto.last_price
                })
            
            if not bot_status:
                return {
                    "balance_usd": 1000.0,
                    "total_value_usd": 1000.0,
                    "total_trades_today": 0,
                    "open_positions": 0,
                    "win_rate": 0,
                    "cryptos": crypto_cards
                }
            
            win_rate = 0
            if bot_status.total_trades > 0:
                win_rate = (bot_status.winning_trades / bot_status.total_trades) * 100
            
            # Valor total em criptos
            total_crypto_value = sum([c.current_value_usd for c in cryptos])
            
            return {
                "balance_usd": round(bot_status.balance_usd, 2),
                "total_value_usd": round(bot_status.balance_usd + total_crypto_value, 2),
                "total_pnl": round(bot_status.total_pnl, 2),
                "daily_pnl": round(bot_status.daily_pnl, 2),
                "total_trades": bot_status.total_trades,
                "total_trades_today": bot_status.total_trades_today,
                "open_positions": bot_status.open_positions,
                "win_rate": round(win_rate, 1),
                "cryptos": crypto_cards
            }
    except Exception as e:
        print(f"❌ Error getting summary: {e}")
        return {"error": str(e)}
