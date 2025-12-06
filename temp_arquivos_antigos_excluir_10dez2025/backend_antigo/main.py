"""
🚀 FastAPI Backend - App Leonardo Trading Bot
Motor principal do sistema de trading
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict
import asyncio
import json
from datetime import datetime

from backend.config import settings
from backend.database import (
    get_db, init_db, Trade, MarketData, Position, 
    Analysis, BotStatus, CryptoBalance
)
from backend.trading_engine import TradingEngine
from backend.redis_manager import RedisManager
from backend.api_endpoints import router as api_router

# ========================================
# FASTAPI APP
# ========================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de Trading Automatizado com FastAPI + Plotly Dash"
)

# Inclui routers
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gerenciadores
redis_manager = RedisManager()
trading_engine: TradingEngine = None


# ========================================
# WEBSOCKET MANAGER
# ========================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Envia mensagem para todos os clientes conectados"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()


# ========================================
# EVENTOS DE STARTUP/SHUTDOWN
# ========================================

@app.on_event("startup")
async def startup_event():
    """Inicialização do sistema"""
    global trading_engine
    
    print("="*60)
    print("🚀 Iniciando App Leonardo Trading Bot")
    print("="*60)
    
    # Inicializa banco de dados
    await init_db()
    
    # Conecta ao Redis
    await redis_manager.connect()
    
    # Inicializa engine de trading
    trading_engine = TradingEngine(redis_manager, manager)
    
    print("✅ Sistema inicializado com sucesso!")


@app.on_event("shutdown")
async def shutdown_event():
    """Encerramento graceful"""
    global trading_engine
    
    print("\n🛑 Encerrando sistema...")
    
    if trading_engine:
        await trading_engine.stop()
    
    await redis_manager.disconnect()
    
    print("✅ Sistema encerrado com sucesso!")


# ========================================
# API ENDPOINTS
# ========================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/api/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    """Status atual do bot"""
    # Busca do Redis (cache)
    cached_status = await redis_manager.get_status()
    if cached_status:
        return cached_status
    
    # Busca do banco
    result = await db.execute(select(BotStatus).order_by(BotStatus.id.desc()).limit(1))
    bot_status = result.scalar_one_or_none()
    
    if not bot_status:
        return {
            "is_running": False,
            "message": "Bot não iniciado"
        }
    
    status_data = {
        "is_running": bot_status.is_running,
        "balance": bot_status.balance,
        "daily_pnl": bot_status.daily_pnl,
        "total_pnl": bot_status.total_pnl,
        "total_trades": bot_status.total_trades,
        "winning_trades": bot_status.winning_trades,
        "losing_trades": bot_status.losing_trades,
        "win_rate": (bot_status.winning_trades / bot_status.total_trades * 100) if bot_status.total_trades > 0 else 0,
        "last_update": bot_status.last_update.isoformat()
    }
    
    # Cacheia no Redis
    await redis_manager.set_status(status_data)
    
    return status_data


@app.get("/api/trades")
async def get_trades(
    limit: int = 50,
    symbol: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Histórico de trades"""
    query = select(Trade).order_by(Trade.timestamp.desc())
    
    if symbol:
        query = query.where(Trade.symbol == symbol)
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "timestamp": t.timestamp.isoformat(),
            "symbol": t.symbol,
            "side": t.side,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "amount": t.amount,
            "pnl": t.pnl,
            "pnl_pct": t.pnl_pct,
            "duration_minutes": t.duration_minutes,
            "entry_reason": t.entry_reason,
            "exit_reason": t.exit_reason
        }
        for t in trades
    ]


@app.get("/api/positions")
async def get_positions(db: AsyncSession = Depends(get_db)):
    """Posições abertas"""
    result = await db.execute(
        select(Position).where(Position.is_open == True)
    )
    positions = result.scalars().all()
    
    return [
        {
            "symbol": p.symbol,
            "side": p.side,
            "entry_price": p.entry_price,
            "amount": p.amount,
            "entry_time": p.entry_time.isoformat(),
            "entry_reason": p.entry_reason
        }
        for p in positions
    ]


@app.get("/api/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Dados de mercado (OHLCV)"""
    result = await db.execute(
        select(MarketData)
        .where(MarketData.symbol == symbol)
        .order_by(MarketData.timestamp.desc())
        .limit(limit)
    )
    data = result.scalars().all()
    
    return [
        {
            "timestamp": d.timestamp.isoformat(),
            "open": d.open,
            "high": d.high,
            "low": d.low,
            "close": d.close,
            "volume": d.volume,
            "rsi": d.rsi,
            "macd": d.macd
        }
        for d in reversed(data)  # Ordem cronológica
    ]


@app.get("/api/statistics")
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """Estatísticas gerais"""
    # Total de trades
    total_trades = await db.execute(select(func.count(Trade.id)))
    total = total_trades.scalar()
    
    # Trades por símbolo
    result = await db.execute(
        select(
            Trade.symbol,
            func.count(Trade.id).label('count'),
            func.sum(Trade.pnl).label('total_pnl'),
            func.avg(Trade.pnl_pct).label('avg_pnl_pct')
        ).group_by(Trade.symbol)
    )
    
    by_symbol = [
        {
            "symbol": row.symbol,
            "count": row.count,
            "total_pnl": float(row.total_pnl) if row.total_pnl else 0,
            "avg_pnl_pct": float(row.avg_pnl_pct) if row.avg_pnl_pct else 0
        }
        for row in result
    ]
    
    return {
        "total_trades": total,
        "by_symbol": by_symbol
    }


@app.post("/api/bot/start")
async def start_bot():
    """Inicia o bot de trading"""
    global trading_engine
    
    if trading_engine.is_running:
        return {"status": "error", "message": "Bot já está rodando"}
    
    await trading_engine.start()
    
    return {"status": "success", "message": "Bot iniciado"}


@app.post("/api/bot/stop")
async def stop_bot():
    """Para o bot de trading"""
    global trading_engine
    
    if not trading_engine.is_running:
        return {"status": "error", "message": "Bot não está rodando"}
    
    await trading_engine.stop()
    
    return {"status": "success", "message": "Bot parado"}


# ========================================
# WEBSOCKET ENDPOINT
# ========================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para atualizações em tempo real"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Mantém conexão viva
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Cliente desconectado do WebSocket")


# ========================================
# RUN
# ========================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
