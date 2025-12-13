# Seu backend/main.py (Corrigido para incluir imports ausentes)

import os
import sys
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# CORREÇÃO: Importar 'List' do módulo 'typing'
from typing import Dict, Any, List 
from pathlib import Path
import yaml 


# Corrigir imports para funcionar mesmo rodando de backend/
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.audit import get_audit_logger, LogEntry
from src.coordinator import BotCoordinator, get_coordinator
from src.ai_advisor.decision_service import AIDecisionService, AISuggestion, AIExecutionCommand


# --- Configuração de Caminhos ---
# Garantir que o diretório 'src' seja acessível, se necessário
sys.path.append(os.path.join(os.path.dirname(__file__), "..")) 

# --- Inicialização ---

# Inicializa o coordenador e o serviço de IA
coordinator: BotCoordinator = BotCoordinator(config_path="config/bots_config.yaml")
ai_advisor = AIDecisionService(coordinator=coordinator)


# --- Aplicação FastAPI ---

app = FastAPI(
    title="AI Trading Advisor API",
    version="1.0.0",
    description="Endpoints para gerenciar bots e receber sugestões de IA."
)

# Adiciona CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Rotas de Decisão de IA (AI ADVISOR) ---

@app.post("/api/v1/ai/suggest", response_model=AISuggestion, summary="Obter Sugestão Otimizada da IA.")
async def suggest_ai_action():
    try:
        suggestion = ai_advisor.generate_ai_suggestion()
        return suggestion
    except Exception as e:
        # Registrar o erro antes de retornar uma HTTP 500
        get_audit_logger().error(f"Erro ao gerar sugestão da IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/execute_action", summary="Executar Ação Sugerida pela IA.")
async def execute_ai_action(command: AIExecutionCommand):
    try:
        # A ação real de orquestração acontece aqui
        result = coordinator.orchestrate_ai_action(
            action_type=command.action_type,
            details=command.details
        )
        return {"status": "success", "result": result}
    except Exception as e:
        get_audit_logger().error(f"Erro ao executar ação da IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/set-strategy", summary="Definir Estratégia Ativa")
async def set_strategy(strategy_data: Dict[str, Any]):
    """Define a estratégia ativa para os bots"""
    try:
        strategy = strategy_data.get("strategy", "")
        if not strategy:
            raise HTTPException(status_code=400, detail="Estratégia não especificada")
        
        # Salvar no config ou notificar coordinator
        # Por exemplo, atualizar config do unico_bot
        config_path = Path("config/unico_bot_config.yaml")
        if config_path.exists():
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # Atualizar operation_mode (que é a estratégia)
            config['operation_mode'] = strategy
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False)
        
        # Log da mudança
        get_audit_logger().log_config_change(
            bot_type='system',
            old_config={},
            new_config={'operation_mode': strategy},
            source='api'
        )
        
        return {"status": "success", "message": f"Modo de operação {strategy} aplicado com sucesso"}
    except Exception as e:
        get_audit_logger().error(f"Erro ao definir estratégia: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/start-bots", summary="Iniciar Todos os Bots")
async def start_bots():
    """Inicia todos os bots do sistema"""
    try:
        # Placeholder - implementar lógica de iniciar bots
        get_audit_logger().log_system_action("start_bots", "api")
        return {"status": "success", "message": "Todos os bots iniciados com sucesso"}
    except Exception as e:
        get_audit_logger().error(f"Erro ao iniciar bots: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/ai/stop-bots", summary="Parar Todos os Bots")
async def stop_bots():
    """Para todos os bots do sistema"""
    try:
        # Placeholder - implementar lógica de parar bots
        get_audit_logger().log_system_action("stop_bots", "api")
        return {"status": "success", "message": "Todos os bots parados com sucesso"}
    except Exception as e:
        get_audit_logger().error(f"Erro ao parar bots: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/ai/restart-system", summary="Reiniciar Sistema")
async def restart_system():
    """Reinicia o sistema de trading"""
    try:
        # Placeholder - implementar lógica de reiniciar sistema
        get_audit_logger().log_system_action("restart_system", "api")
        return {"status": "success", "message": "Sistema reiniciado com sucesso"}
    except Exception as e:
        get_audit_logger().error(f"Erro ao reiniciar sistema: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/ai/update-stats", summary="Atualizar Estatísticas")
async def update_stats():
    """Atualiza as estatísticas do sistema"""
    try:
        # Placeholder - implementar lógica de atualizar estatísticas
        get_audit_logger().log_system_action("update_stats", "api")
        return {"status": "success", "message": "Estatísticas atualizadas com sucesso"}
    except Exception as e:
        get_audit_logger().error(f"Erro ao atualizar estatísticas: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/ai/update-config", summary="Atualizar Configurações")
async def update_config(config_data: Dict[str, Any]):
    """Atualiza as configurações do sistema"""
    try:
        # Placeholder - implementar lógica de atualizar configurações
        get_audit_logger().log_config_change(
            bot_type='system',
            old_config={},
            new_config=config_data,
            source='api'
        )
        return {"status": "success", "message": "Configurações atualizadas com sucesso"}
    except Exception as e:
        get_audit_logger().error(f"Erro ao atualizar configurações: {e}")
        return {"status": "error", "message": str(e)}


# --- Rota de Logs (Onde o Erro Estava) ---

# Linha 48 original: @app.get("/api/v1/logs/ai", response_model=List[LogEntry], summary="Logs de Decisão, Aprendizado e Risco.")
@app.get("/api/v1/logs/ai", response_model=List[Dict], summary="Logs de Decisão, Aprendizado e Risco.")
async def get_ai_logs():
    return get_audit_logger().get_recent_events(limit=50)


# --- Novas rotas para o dashboard ---

@app.post("/api/v1/config/update", summary="Atualizar configurações do sistema")
async def update_config(config_data: Dict[str, Any]):
    """Atualiza configurações do sistema"""
    try:
        # Aqui você pode implementar a lógica para atualizar config
        # Por exemplo, salvar em arquivo ou atualizar em memória
        get_audit_logger().log_config_change(
            bot_type='system',
            old_config={},
            new_config=config_data,
            source='api'
        )
        return {"status": "success", "message": "Configurações atualizadas"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ai/diagnostics/status", summary="Status de diagnóstico da IA")
async def get_ai_diagnostics_status():
    """Retorna status de diagnóstico da IA"""
    try:
        # Status básico da IA
        status = {
            "ai_status": "active",
            "coordinator_status": "running",
            "last_update": datetime.now().isoformat(),
            "active_bots": len(coordinator.bots) if coordinator.bots else 0
        }
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/config", summary="Obter configurações do sistema")
async def get_dashboard_config():
    """Retorna as configurações do sistema"""
    try:
        # Carregar config do arquivo
        config_path = Path("config/config.yaml")
        if config_path.exists():
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        else:
            return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/history", summary="Obter histórico de trades")
async def get_dashboard_history():
    """Retorna o histórico de trades"""
    try:
        history_path = Path("data/multibot_history.json")
        if history_path.exists():
            with open(history_path, 'r') as f:
                history = json.load(f)
            return history
        else:
            return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/positions", summary="Obter posições abertas")
async def get_dashboard_positions():
    """Retorna as posições abertas"""
    try:
        positions_path = Path("data/multibot_positions.json")
        if positions_path.exists():
            with open(positions_path, 'r') as f:
                positions = json.load(f)
            return positions
        else:
            return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Adicione suas outras rotas aqui (Dashboard, Logs de Bot, etc.)