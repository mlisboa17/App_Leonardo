"""
Rotas de Ações do Bot (trades, liquidação, etc.)
"""
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from ..models import (
    ManualTradeRequest, ClosePositionRequest, BotActionRequest,
    APIResponse, UserInDB
)
from ..dependencies import get_current_user, require_role, require_permission
from ..config import UserRole


router = APIRouter(prefix="/actions", tags=["Ações"])


# Flag global para controle do bot
BOT_STATUS_FILE = Path("data/bot_status.json")


def get_bot_status() -> dict:
    """Lê status do bot"""
    try:
        with open(BOT_STATUS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"running": False, "last_action": None}


def set_bot_status(status: dict):
    """Salva status do bot"""
    BOT_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BOT_STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)


@router.get("/status")
async def get_status(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Status atual do sistema
    """
    status = get_bot_status()
    
    return {
        "bot_running": status.get("running", False),
        "last_action": status.get("last_action"),
        "last_action_by": status.get("last_action_by"),
        "last_action_at": status.get("last_action_at")
    }


@router.post("/bot/start")
async def start_bot(
    bot_name: Optional[str] = None,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN, UserRole.TRADER]))
):
    """
    Iniciar o bot (ou um bot específico)
    """
    status = get_bot_status()
    status["running"] = True
    status["last_action"] = "start"
    status["last_action_by"] = current_user.username
    status["last_action_at"] = datetime.now().isoformat()
    status["target_bot"] = bot_name
    
    set_bot_status(status)
    
    msg = f"Bot '{bot_name}' iniciado" if bot_name else "Todos os bots iniciados"
    
    return APIResponse(
        success=True,
        message=msg,
        data={"action": "start", "bot": bot_name}
    )


@router.post("/bot/stop")
async def stop_bot(
    bot_name: Optional[str] = None,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN, UserRole.TRADER]))
):
    """
    Parar o bot (ou um bot específico)
    """
    status = get_bot_status()
    status["running"] = False
    status["last_action"] = "stop"
    status["last_action_by"] = current_user.username
    status["last_action_at"] = datetime.now().isoformat()
    status["target_bot"] = bot_name
    
    set_bot_status(status)
    
    msg = f"Bot '{bot_name}' parado" if bot_name else "Todos os bots parados"
    
    return APIResponse(
        success=True,
        message=msg,
        data={"action": "stop", "bot": bot_name}
    )


@router.post("/bot/restart")
async def restart_bot(
    bot_name: Optional[str] = None,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN, UserRole.TRADER]))
):
    """
    Reiniciar o bot
    """
    status = get_bot_status()
    status["running"] = True
    status["last_action"] = "restart"
    status["last_action_by"] = current_user.username
    status["last_action_at"] = datetime.now().isoformat()
    status["target_bot"] = bot_name
    
    set_bot_status(status)
    
    msg = f"Bot '{bot_name}' reiniciado" if bot_name else "Todos os bots reiniciados"
    
    return APIResponse(
        success=True,
        message=msg,
        data={"action": "restart", "bot": bot_name}
    )


@router.post("/liquidate/all")
async def liquidate_all(
    confirm: bool = False,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN]))
):
    """
    PERIGO: Liquidar todas as posições abertas
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirme a liquidação definindo confirm=true. ISSO FECHARÁ TODAS AS POSIÇÕES!"
        )
    
    # Carregar posições
    try:
        with open("data/multibot_positions.json", 'r') as f:
            positions = json.load(f).get("positions", [])
    except:
        positions = []
    
    if not positions:
        return APIResponse(
            success=True,
            message="Nenhuma posição aberta para liquidar"
        )
    
    # Registrar ação
    status = get_bot_status()
    status["last_action"] = "liquidate_all"
    status["last_action_by"] = current_user.username
    status["last_action_at"] = datetime.now().isoformat()
    status["liquidation_requested"] = True
    set_bot_status(status)
    
    return APIResponse(
        success=True,
        message=f"Liquidação de {len(positions)} posições solicitada",
        data={"positions_count": len(positions)}
    )


@router.post("/position/{position_id}/close")
async def close_position(
    position_id: int,
    reason: Optional[str] = None,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN, UserRole.TRADER]))
):
    """
    Fechar uma posição específica
    """
    # Carregar posições
    try:
        with open("data/multibot_positions.json", 'r') as f:
            data = json.load(f)
            positions = data.get("positions", [])
    except:
        positions = []
    
    # Encontrar posição
    position = None
    for p in positions:
        if p.get("id") == position_id:
            position = p
            break
    
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Posição {position_id} não encontrada"
        )
    
    # Marcar para fechamento
    position["close_requested"] = True
    position["close_reason"] = reason
    position["close_requested_by"] = current_user.username
    position["close_requested_at"] = datetime.now().isoformat()
    
    # Salvar
    with open("data/multibot_positions.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    return APIResponse(
        success=True,
        message=f"Fechamento da posição {position_id} ({position.get('symbol')}) solicitado",
        data=position
    )


@router.post("/emergency/stop")
async def emergency_stop(
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN]))
):
    """
    EMERGÊNCIA: Para tudo imediatamente
    """
    status = {
        "running": False,
        "emergency_stop": True,
        "last_action": "emergency_stop",
        "last_action_by": current_user.username,
        "last_action_at": datetime.now().isoformat()
    }
    
    set_bot_status(status)
    
    return APIResponse(
        success=True,
        message="🚨 PARADA DE EMERGÊNCIA ATIVADA! Todos os bots foram parados.",
        data=status
    )


@router.post("/emergency/clear")
async def clear_emergency(
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN]))
):
    """
    Limpar estado de emergência
    """
    status = get_bot_status()
    status["emergency_stop"] = False
    status["last_action"] = "clear_emergency"
    status["last_action_by"] = current_user.username
    status["last_action_at"] = datetime.now().isoformat()
    
    set_bot_status(status)
    
    return APIResponse(
        success=True,
        message="Estado de emergência limpo. Bots podem ser reiniciados.",
        data=status
    )
