"""
Rotas de Configuração do Bot
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from datetime import datetime

from ..models import BotConfig, GlobalConfig, ConfigUpdate, APIResponse, UserInDB
from ..dependencies import get_current_user, require_role
from ..config import UserRole
from .actions_routes import get_bot_status, set_bot_status


def _schedule_restart_all(triggered_by: str = "system"):
    """Agenda reinicio para todos os bots de forma síncrona/rápida (usado em BackgroundTasks)."""
    status = get_bot_status()
    # debounce: don't schedule another restart within MIN_RESTART_INTERVAL seconds
    MIN_RESTART_INTERVAL = 5
    last = status.get("last_action_at")
    try:
        last_ts = datetime.fromisoformat(last) if last else None
        if last_ts and (datetime.now() - last_ts).total_seconds() < MIN_RESTART_INTERVAL and status.get('last_action') == 'restart':
            # skip scheduling
            return
    except Exception:
        pass
    status["running"] = True
    status["last_action"] = "restart"
    status["last_action_by"] = triggered_by
    status["last_action_at"] = datetime.now().isoformat()
    status["target_bot"] = None
    set_bot_status(status)


def _schedule_restart_bot(bot_name: str, triggered_by: str = "system"):
    """Agenda reinicio para um bot específico (usado em BackgroundTasks)."""
    status = get_bot_status()
    MIN_RESTART_INTERVAL = 5
    last = status.get("last_action_at")
    try:
        last_ts = datetime.fromisoformat(last) if last else None
        if last_ts and (datetime.now() - last_ts).total_seconds() < MIN_RESTART_INTERVAL and status.get('last_action') == 'restart' and status.get('target_bot') == bot_name:
            return
    except Exception:
        pass
    status["running"] = True
    status["last_action"] = "restart"
    status["last_action_by"] = triggered_by
    status["last_action_at"] = datetime.now().isoformat()
    status["target_bot"] = bot_name
    set_bot_status(status)


def _schedule_stop_bot(bot_name: str, triggered_by: str = "system"):
    """Agenda parada para um bot específico (usado em BackgroundTasks)."""
    status = get_bot_status()
    status["running"] = False
    status["last_action"] = "stop"
    status["last_action_by"] = triggered_by
    status["last_action_at"] = datetime.now().isoformat()
    status["target_bot"] = bot_name
    set_bot_status(status)


# Keys that require a restart when changed at bot level
RESTART_KEYS = {
    'perfil',
    'take_profit_dinamico',
    'rsi_dinamico',
    'trailing_stop',
    'take_profit',
    'stop_loss',
    'risk',
    'strategy',
}

# Global keys that require restart
GLOBAL_RESTART_KEYS = {
    'monthly_target',
    'risk_per_trade',
    'max_daily_loss',
    'trading_hours_start',
    'trading_hours_end',
    'poupanca_enabled',
    'poupanca_percentage',
}


router = APIRouter(prefix="/config", tags=["Configuração"])


CONFIG_PATH = Path("config/bots_config.yaml")


def load_config() -> dict:
    """Carrega configuração YAML"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def save_config(config: dict):
    """Salva configuração YAML"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


@router.get("/all")
async def get_all_config(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obter toda a configuração
    """
    # Viewer só vê algumas coisas
    config = load_config()
    
    if current_user.role == UserRole.VIEWER:
        # Remove informações sensíveis
        safe_config = {
            "global": config.get("global", {}),
            "bots": {}
        }
        for bot_name, bot_config in config.get("bots", {}).items():
            safe_config["bots"][bot_name] = {
                "name": bot_name,
                "enabled": bot_config.get("enabled", False),
                "symbols": bot_config.get("symbols", [])
            }
        return safe_config
    
    return config


@router.get("/global")
async def get_global_config(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obter configurações globais
    """
    config = load_config()
    return config.get("global", {})


@router.put("/global")
async def update_global_config(
    updates: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN, UserRole.TRADER]))
):
    """
    Atualizar configurações globais
    """
    config = load_config()
    
    if "global" not in config:
        config["global"] = {}
    
    restart_needed = False
    for key, value in updates.items():
        old_val = config.get("global", {}).get(key)
        if key in GLOBAL_RESTART_KEYS and old_val != value:
            restart_needed = True
        config["global"][key] = value

    save_config(config)
    if restart_needed:
        try:
            actor = current_user.username if current_user else "system"
        except Exception:
            actor = "system"
        background_tasks.add_task(_schedule_restart_all, actor)

    return APIResponse(
        success=True,
        message=("Configurações globais atualizadas; reinício dos bots agendado" if restart_needed else "Configurações globais atualizadas"),
        data={"global": config["global"], "restart_scheduled": restart_needed}
    )


@router.get("/bots")
async def get_bots_config(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obter configurações de todos os bots
    """
    config = load_config()
    return config.get("bots", {})


@router.get("/bots/{bot_name}")
async def get_bot_config(
    bot_name: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obter configuração de um bot específico
    """
    config = load_config()
    bots = config.get("bots", {})
    
    if bot_name not in bots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot '{bot_name}' não encontrado"
        )
    
    return bots[bot_name]


@router.put("/bots/{bot_name}")
async def update_bot_config(
    bot_name: str,
    updates: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN, UserRole.TRADER]))
):
    """
    Atualizar configuração de um bot
    """
    config = load_config()
    
    if "bots" not in config:
        config["bots"] = {}
    
    if bot_name not in config["bots"]:
        config["bots"][bot_name] = {}
    
    old_config = config["bots"].get(bot_name, {})
    restart_needed = False
    for key, value in updates.items():
        # Update logic
        # If key is in RESTART_KEYS and value changed, mark restart
        if key in RESTART_KEYS:
            old_val = old_config.get(key)
            try:
                if json.dumps(old_val, sort_keys=True) != json.dumps(value, sort_keys=True):
                    restart_needed = True
            except Exception:
                if old_val != value:
                    restart_needed = True
        config["bots"][bot_name][key] = value

    save_config(config)
    if restart_needed:
        try:
            actor = current_user.username if current_user else "system"
        except Exception:
            actor = "system"
        background_tasks.add_task(_schedule_restart_bot, bot_name, actor)

    return APIResponse(
        success=True,
        message=(f"Configurações do bot '{bot_name}' atualizadas; reinício agendado" if restart_needed else f"Configurações do bot '{bot_name}' atualizadas"),
        data={"bot": config["bots"][bot_name], "restart_scheduled": restart_needed}
    )


@router.post("/bots/{bot_name}/enable")
async def enable_bot(
    bot_name: str,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN, UserRole.TRADER]))
):
    """
    Habilitar um bot
    """
    config = load_config()
    
    if bot_name not in config.get("bots", {}):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot '{bot_name}' não encontrado"
        )
    
    config["bots"][bot_name]["enabled"] = True
    save_config(config)
    # Agendar reinício do bot para aplicar nova configuração
    try:
        actor = current_user.username if current_user else "system"
    except Exception:
        actor = "system"
    background_tasks.add_task(_schedule_restart_bot, bot_name, actor)
    return APIResponse(
        success=True,
        message=f"Bot '{bot_name}' habilitado",
        data={"bot": config["bots"][bot_name], "restart_scheduled": True}
    )


@router.post("/bots/{bot_name}/disable")
async def disable_bot(
    bot_name: str,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN, UserRole.TRADER]))
):
    """
    Desabilitar um bot
    """
    config = load_config()
    
    if bot_name not in config.get("bots", {}):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot '{bot_name}' não encontrado"
        )
    
    config["bots"][bot_name]["enabled"] = False
    save_config(config)
    try:
        actor = current_user.username if current_user else "system"
    except Exception:
        actor = "system"
    # Stop the bot to apply new enabled=false state
    background_tasks.add_task(_schedule_stop_bot, bot_name, actor)
    return APIResponse(
        success=True,
        message=f"Bot '{bot_name}' desabilitado",
        data={"bot": config["bots"][bot_name], "restart_scheduled": True}
    )


@router.get("/user-control")
async def get_user_control(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obter configurações de controle do usuário vs IA
    """
    config = load_config()
    return config.get("user_control", {})


@router.put("/user-control")
async def update_user_control(
    updates: Dict[str, Any],
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN]))
):
    """
    Atualizar configurações de controle do usuário vs IA
    """
    config = load_config()
    
    if "user_control" not in config:
        config["user_control"] = {}
    
    for key, value in updates.items():
        config["user_control"][key] = value
    
    save_config(config)
    
    return APIResponse(
        success=True,
        message="Controle de usuário atualizado",
        data=config["user_control"]
    )
