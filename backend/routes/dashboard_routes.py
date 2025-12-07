"""
Rotas do Dashboard e Estatísticas
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..models import (
    DashboardSummary, DailyStats, Position, Trade,
    BotStatus, APIResponse, PaginatedResponse, UserInDB
)
from ..dependencies import get_current_user, require_permission
from ..config import UserRole


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def load_json_file(path: str, default=None):
    """Carrega arquivo JSON"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obter resumo do dashboard
    """
    # Carregar dados
    balances = load_json_file("data/dashboard_balances.json", {})
    positions = load_json_file("data/multibot_positions.json", {})
    coordinator = load_json_file("data/coordinator_stats.json", {})
    
    # Calcular totais - usando campos corretos do dashboard_balances.json
    total_balance = balances.get("total_balance", 0)
    available = balances.get("usdt_balance", 0)
    in_positions = balances.get("crypto_balance", 0)
    
    # PnL do coordinator_stats
    pnl_today = coordinator.get("daily_pnl", 0)
    pnl_week = coordinator.get("total_pnl", 0)  # Aproximação
    pnl_month = coordinator.get("monthly_pnl", 0)
    
    # Stats do coordinator
    total_trades = coordinator.get("total_trades", 0)
    win_rate = coordinator.get("global_win_rate", 0)
    
    # Posições e bots
    open_positions = coordinator.get("total_open_positions", 0)
    active_bots = coordinator.get("active_bots", 0)
    
    return DashboardSummary(
        total_balance=total_balance,
        available_balance=available,
        in_positions=in_positions,
        pnl_today=pnl_today,
        pnl_week=pnl_week,
        pnl_month=pnl_month,
        total_trades=total_trades,
        active_bots=active_bots,
        open_positions=open_positions,
        win_rate=win_rate
    )


@router.get("/stats/daily")
async def get_daily_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obter estatísticas diárias dos últimos N dias
    """
    daily_stats = load_json_file("data/daily_stats.json", {})
    history = daily_stats.get("daily_history", [])
    
    # Retornar últimos N dias
    return {
        "days": days,
        "stats": history[-days:] if history else []
    }


@router.get("/positions", response_model=PaginatedResponse)
async def get_positions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    bot_name: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Listar posições abertas
    """
    positions_data = load_json_file("data/multibot_positions.json", {})
    positions = positions_data.get("positions", [])
    
    # Filtrar por bot se especificado
    if bot_name:
        positions = [p for p in positions if p.get("bot_name") == bot_name]
    
    # Paginação
    total = len(positions)
    start = (page - 1) * per_page
    end = start + per_page
    
    return PaginatedResponse(
        items=positions[start:end],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.get("/trades", response_model=PaginatedResponse)
async def get_trades(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    bot_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Listar histórico de trades
    """
    history = load_json_file("data/multibot_history.json", {})
    trades = history.get("trades", [])
    
    # Filtros
    if bot_name:
        trades = [t for t in trades if t.get("bot_name") == bot_name]
    
    if start_date:
        trades = [t for t in trades if t.get("closed_at", "") >= start_date]
    
    if end_date:
        trades = [t for t in trades if t.get("closed_at", "") <= end_date]
    
    # Ordenar por data (mais recente primeiro)
    trades = sorted(trades, key=lambda x: x.get("closed_at", ""), reverse=True)
    
    # Paginação
    total = len(trades)
    start = (page - 1) * per_page
    end = start + per_page
    
    return PaginatedResponse(
        items=trades[start:end],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.get("/bots/status")
async def get_bots_status(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Status de todos os bots
    """
    coordinator = load_json_file("data/coordinator_stats.json", {})
    daily_stats = load_json_file("data/daily_stats.json", {})
    
    bots = coordinator.get("bots", {})
    
    result = []
    for bot_name, bot_data in bots.items():
        result.append({
            "name": bot_data.get("name", bot_name),
            "status": bot_data.get("status", "unknown"),
            "pnl_today": bot_data.get("daily_pnl", 0),
            "pnl_total": bot_data.get("total_pnl", 0),
            "trades_today": bot_data.get("total_trades", 0),
            "win_rate": bot_data.get("win_rate", 0),
            "open_positions": bot_data.get("open_positions", 0),
            "capital_allocated": bot_data.get("allocated_capital", 0),
            "last_trade": bot_data.get("last_trade_time")
        })
    
    return {"bots": result}


@router.get("/chart/pnl")
async def get_pnl_chart(
    period: str = Query("30d", regex="^(7d|30d|90d|1y|all)$"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Dados para gráfico de PnL
    """
    daily_stats = load_json_file("data/daily_stats.json", {})
    history = daily_stats.get("daily_history", [])
    
    # Filtrar por período
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365, "all": 99999}
    days = days_map.get(period, 30)
    
    data = history[-days:] if history else []
    
    # Preparar dados para gráfico
    chart_data = {
        "labels": [d.get("date", "") for d in data],
        "pnl": [d.get("pnl", 0) for d in data],
        "cumulative_pnl": [],
        "trades": [d.get("trades", 0) for d in data]
    }
    
    # Calcular PnL acumulado
    cumulative = 0
    for pnl in chart_data["pnl"]:
        cumulative += pnl
        chart_data["cumulative_pnl"].append(cumulative)
    
    return chart_data


@router.get("/indicators")
async def get_indicators(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obter indicadores técnicos de todas as moedas monitoradas
    """
    import yaml
    
    # Carregar configuração dos bots
    bots_config_path = Path("config/bots_config.yaml")
    bots_config = {}
    if bots_config_path.exists():
        with open(bots_config_path, 'r', encoding='utf-8') as f:
            bots_config = yaml.safe_load(f) or {}
    
    # Extrair configuração de indicadores de cada bot
    bots_indicator_config = []
    all_symbols = set()
    symbol_to_bot = {}
    
    for bot_key in ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']:
        bot = bots_config.get(bot_key, {})
        if not bot:
            continue
            
        symbols = [p.get('symbol', '') for p in bot.get('portfolio', [])]
        all_symbols.update(symbols)
        
        for symbol in symbols:
            symbol_to_bot[symbol] = bot.get('name', bot_key)
        
        bots_indicator_config.append({
            'name': bot.get('name', bot_key),
            'speed_profile': bot.get('speed_profile', 'medium'),
            'strategy_type': bot.get('strategy_type', 'unknown'),
            'symbols': symbols,
            'buy_conditions': bot.get('indicators', {}).get('buy_conditions', 'majority'),
            'sell_conditions': bot.get('indicators', {}).get('sell_conditions', 'majority')
        })
    
    # Carregar indicadores calculados (se existir arquivo de cache)
    indicators_cache = load_json_file("data/cache/indicators.json", {})
    
    # Carregar profiles de crypto
    crypto_profiles = load_json_file("data/crypto_profiles.json", {})
    
    indicators = []
    for symbol in sorted(all_symbols):
        cached = indicators_cache.get(symbol, {})
        profile = crypto_profiles.get(symbol, {})
        
        # Dados do cache ou valores mock para demonstração
        rsi = cached.get('rsi', profile.get('rsi_mean', 50))
        macd = cached.get('macd', 0)
        macd_signal = cached.get('macd_signal', 0)
        trend = cached.get('trend', 'LATERAL')
        trend_strength = cached.get('trend_strength', 2)
        
        # Determinar sinais baseados nos indicadores
        buy_rsi = profile.get('buy_rsi', 38)
        sell_rsi = profile.get('sell_rsi', 62)
        
        buy_signal = rsi < buy_rsi and macd > macd_signal
        sell_signal = rsi > sell_rsi or (trend == 'QUEDA' and trend_strength >= 3)
        
        indicators.append({
            'symbol': symbol,
            'price': cached.get('price', 0),
            'rsi': rsi,
            'macd': macd,
            'macd_signal': macd_signal,
            'trend': trend,
            'trend_strength': trend_strength,
            'sma20': cached.get('sma20', 0),
            'ema9': cached.get('ema9', 0),
            'ema21': cached.get('ema21', 0),
            'volume_ratio': cached.get('volume_ratio', 1.0),
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'bot_assigned': symbol_to_bot.get(symbol)
        })
    
    return {
        'indicators': indicators,
        'bots_config': bots_indicator_config,
        'last_update': indicators_cache.get('_timestamp', datetime.now().isoformat())
    }
