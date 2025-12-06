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
    daily_stats = load_json_file("data/daily_stats.json", {})
    positions = load_json_file("data/multibot_positions.json", {})
    coordinator = load_json_file("data/coordinator_stats.json", {})
    
    # Calcular totais
    total_balance = balances.get("total_usdt", 0)
    available = balances.get("available_usdt", 0)
    in_positions = balances.get("in_positions", 0)
    
    # PnL
    pnl_today = daily_stats.get("pnl_today", 0)
    pnl_week = daily_stats.get("pnl_week", 0)
    pnl_month = daily_stats.get("pnl_month", 0)
    
    # Stats
    total_trades = daily_stats.get("total_trades", 0)
    win_rate = daily_stats.get("win_rate", 0)
    
    # Posições e bots
    open_positions = len(positions.get("positions", []))
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
            "name": bot_name,
            "status": bot_data.get("status", "unknown"),
            "pnl_today": bot_data.get("pnl_today", 0),
            "pnl_total": bot_data.get("pnl_total", 0),
            "trades_today": bot_data.get("trades_today", 0),
            "win_rate": bot_data.get("win_rate", 0),
            "open_positions": bot_data.get("open_positions", 0),
            "capital_allocated": bot_data.get("capital", 0),
            "last_trade": bot_data.get("last_trade")
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
