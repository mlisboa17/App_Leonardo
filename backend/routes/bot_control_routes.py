"""
Rotas de Controle de Bots - Pausar/Ativar/UnicoBot
"""
import json
import yaml
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_current_user
from ..models import UserInDB


router = APIRouter(prefix="/bots/control", tags=["Bot Control"])


# Models
class ToggleBotRequest(BaseModel):
    bot_type: str
    enabled: bool


class UnicoBotRequest(BaseModel):
    enabled: bool


# Helper functions
def load_yaml(path: str):
    """Carrega arquivo YAML"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Erro ao carregar {path}: {e}")
        return {}


def save_yaml(path: str, data: dict):
    """Salva arquivo YAML"""
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def load_json(path: str, default=None):
    """Carrega arquivo JSON"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def save_json(path: str, data: dict):
    """Salva arquivo JSON"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@router.get("")
async def get_bots_status(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obter status de todos os bots
    """
    # Carregar configurações
    bots_config = load_yaml("config/bots_config.yaml")
    unico_config = load_yaml("config/unico_bot_config.yaml")
    coordinator_stats = load_json("data/coordinator_stats.json", {})
    daily_stats = load_json("data/daily_stats.json", {})
    positions = load_json("data/multibot_positions.json", {})
    
    # Stats dos bots
    bot_stats = daily_stats.get("bot_stats", {})
    
    # Lista de bots especializados
    bots = []
    for bot_type, bot_config in bots_config.get("bots", {}).items():
        stats = bot_stats.get(bot_type, {})
        
        # Contar posições abertas
        open_positions = 0
        if isinstance(positions, dict):
            for pos_list in positions.values():
                if isinstance(pos_list, list):
                    for pos in pos_list:
                        if pos.get("bot_name") == bot_type:
                            open_positions += 1
        
        bots.append({
            "name": bot_config.get("name", bot_type),
            "bot_type": bot_type,
            "enabled": bot_config.get("enabled", False),
            "status": "active" if bot_config.get("enabled", False) else "paused",
            "win_rate": stats.get("win_rate", 0),
            "total_trades": stats.get("total_trades", 0),
            "pnl_today": stats.get("daily_pnl", 0),
            "open_positions": open_positions
        })
    
    # UnicoBot status
    unico_bot = None
    if unico_config:
        unico_bot = {
            "enabled": unico_config.get("enabled", False),
            "name": unico_config.get("name", "UnicoBot"),
            "portfolio_size": len(unico_config.get("portfolio", {}).get("moedas", [])),
            "strategy": unico_config.get("strategy", {}).get("name", "Smart Strategy")
        }
    
    return {
        "bots": bots,
        "unico_bot": unico_bot
    }


@router.post("/toggle")
async def toggle_bot(
    request: ToggleBotRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Pausar ou ativar um bot específico
    """
    bots_config_path = "config/bots_config.yaml"
    bots_config = load_yaml(bots_config_path)
    
    if not bots_config:
        raise HTTPException(status_code=500, detail="Erro ao carregar configuração")
    
    if request.bot_type not in bots_config.get("bots", {}):
        raise HTTPException(status_code=404, detail=f"Bot '{request.bot_type}' não encontrado")
    
    # Verificar se UnicoBot está ativo
    unico_config = load_yaml("config/unico_bot_config.yaml")
    if unico_config.get("enabled", False) and request.enabled:
        raise HTTPException(
            status_code=400, 
            detail="Não é possível ativar bots enquanto o UnicoBot está ativo. Desative o UnicoBot primeiro."
        )
    
    # Alterar estado do bot
    bot_name = bots_config["bots"][request.bot_type].get("name", request.bot_type)
    bots_config["bots"][request.bot_type]["enabled"] = request.enabled
    
    # Recalcular distribuição de capital se necessário
    active_bots = [k for k, v in bots_config["bots"].items() if v.get("enabled", False)]
    
    if active_bots:
        # Redistribuir capital igualmente entre bots ativos
        capital_per_bot = round(100 / len(active_bots), 1)
        
        for bot_type in bots_config["bots"]:
            if bots_config["bots"][bot_type].get("enabled", False):
                bots_config["bots"][bot_type]["capital_percent"] = capital_per_bot
            else:
                bots_config["bots"][bot_type]["capital_percent"] = 0
    
    # Salvar configuração
    save_yaml(bots_config_path, bots_config)
    
    # Log da ação
    log_action(
        current_user.username,
        "toggle_bot",
        f"Bot {bot_name} {'ativado' if request.enabled else 'pausado'}"
    )
    
    return {
        "success": True,
        "message": f"Bot {bot_name} {'ativado' if request.enabled else 'pausado'} com sucesso!",
        "bot_type": request.bot_type,
        "enabled": request.enabled,
        "active_bots": len(active_bots)
    }


@router.post("/unico-bot")
async def toggle_unico_bot(
    request: UnicoBotRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Ativar ou desativar o UnicoBot.
    Quando ativado, todos os outros bots são desativados.
    """
    unico_config_path = "config/unico_bot_config.yaml"
    bots_config_path = "config/bots_config.yaml"
    
    unico_config = load_yaml(unico_config_path)
    bots_config = load_yaml(bots_config_path)
    
    if not unico_config:
        raise HTTPException(status_code=500, detail="Configuração do UnicoBot não encontrada")
    
    if request.enabled:
        # Ativar UnicoBot e desativar todos os outros
        unico_config["enabled"] = True
        
        # Desativar todos os bots especializados
        for bot_type in bots_config.get("bots", {}):
            bots_config["bots"][bot_type]["enabled"] = False
            bots_config["bots"][bot_type]["capital_percent"] = 0
        
        save_yaml(unico_config_path, unico_config)
        save_yaml(bots_config_path, bots_config)
        
        log_action(
            current_user.username,
            "activate_unico_bot",
            "UnicoBot ativado - Todos os outros bots foram pausados"
        )
        
        return {
            "success": True,
            "message": "🤖 UnicoBot ATIVADO! Todos os outros bots foram pausados.",
            "unico_bot_enabled": True
        }
    else:
        # Desativar UnicoBot
        unico_config["enabled"] = False
        save_yaml(unico_config_path, unico_config)
        
        log_action(
            current_user.username,
            "deactivate_unico_bot",
            "UnicoBot desativado"
        )
        
        return {
            "success": True,
            "message": "UnicoBot desativado. Você pode ativar os bots especializados novamente.",
            "unico_bot_enabled": False
        }


@router.post("/restart")
async def restart_system(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Reiniciar o sistema de bots
    """
    try:
        # Criar flag para sinalizar restart
        restart_flag = Path("data/.restart_requested")
        restart_flag.write_text(datetime.now().isoformat())
        
        log_action(
            current_user.username,
            "restart_system",
            "Solicitação de restart do sistema"
        )
        
        return {
            "success": True,
            "message": "🔄 Restart solicitado. O sistema irá reiniciar em breve."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao solicitar restart: {str(e)}")


@router.post("/redistribute-capital")
async def redistribute_capital(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Redistribuir capital igualmente entre bots ativos
    """
    bots_config_path = "config/bots_config.yaml"
    bots_config = load_yaml(bots_config_path)
    
    if not bots_config:
        raise HTTPException(status_code=500, detail="Erro ao carregar configuração")
    
    # Contar bots ativos
    active_bots = [k for k, v in bots_config.get("bots", {}).items() if v.get("enabled", False)]
    
    if not active_bots:
        raise HTTPException(status_code=400, detail="Nenhum bot ativo para redistribuir capital")
    
    # Redistribuir igualmente
    capital_per_bot = round(100 / len(active_bots), 1)
    
    for bot_type in bots_config["bots"]:
        if bots_config["bots"][bot_type].get("enabled", False):
            bots_config["bots"][bot_type]["capital_percent"] = capital_per_bot
        else:
            bots_config["bots"][bot_type]["capital_percent"] = 0
    
    save_yaml(bots_config_path, bots_config)
    
    log_action(
        current_user.username,
        "redistribute_capital",
        f"Capital redistribuído: {capital_per_bot}% para cada bot ativo ({len(active_bots)} bots)"
    )
    
    return {
        "success": True,
        "message": f"Capital redistribuído: {capital_per_bot}% para cada bot ativo",
        "active_bots": len(active_bots),
        "capital_per_bot": capital_per_bot
    }


def log_action(username: str, action: str, details: str):
    """Log de ações do usuário"""
    log_path = "data/control_log.json"
    log_data = load_json(log_path, {"actions": []})
    
    log_data["actions"].append({
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "action": action,
        "details": details
    })
    
    # Manter apenas últimas 100 ações
    log_data["actions"] = log_data["actions"][-100:]
    
    save_json(log_path, log_data)
