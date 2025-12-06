"""
Rotas de Configuração do Bot
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..models import BotConfig, GlobalConfig, ConfigUpdate, APIResponse, UserInDB
from ..dependencies import get_current_user, require_role
from ..config import UserRole


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
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN, UserRole.TRADER]))
):
    """
    Atualizar configurações globais
    """
    config = load_config()
    
    if "global" not in config:
        config["global"] = {}
    
    for key, value in updates.items():
        config["global"][key] = value
    
    save_config(config)
    
    return APIResponse(
        success=True,
        message="Configurações globais atualizadas",
        data=config["global"]
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
    
    for key, value in updates.items():
        config["bots"][bot_name][key] = value
    
    save_config(config)
    
    return APIResponse(
        success=True,
        message=f"Configurações do bot '{bot_name}' atualizadas",
        data=config["bots"][bot_name]
    )


@router.post("/bots/{bot_name}/enable")
async def enable_bot(
    bot_name: str,
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
    
    return APIResponse(
        success=True,
        message=f"Bot '{bot_name}' habilitado"
    )


@router.post("/bots/{bot_name}/disable")
async def disable_bot(
    bot_name: str,
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
    
    return APIResponse(
        success=True,
        message=f"Bot '{bot_name}' desabilitado"
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
