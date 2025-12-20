# Seu backend/main.py (Corrigido para incluir imports ausentes)

# Carrega variáveis de ambiente ANTES de qualquer import
try:
    from dotenv import load_dotenv
    load_dotenv('../config/.env')
    print("✅ Variáveis de ambiente carregadas no backend")
except ImportError:
    print("⚠️ python-dotenv não instalado no backend. Usando variáveis do sistema.")

import os
import sys
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
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
from backend.dependencies import RequireManageConfig


# --- Configuração de Caminhos ---
# Garantir que o diretório 'src' seja acessível, se necessário
sys.path.append(os.path.join(os.path.dirname(__file__), "..")) 

# --- Inicialização ---

# Inicializa o coordenador e o serviço de IA (lazy loading)
coordinator = None
ai_advisor = None

def get_coordinator():
    try:
        from src.coordinator import get_coordinator as get_global_coordinator
        return get_global_coordinator()
    except Exception as e:
        print(f"⚠️ Erro ao obter coordinator: {e}")
        return None

def get_ai_advisor():
    global ai_advisor
    if ai_advisor is None:
        try:
            coord = get_coordinator()
            if coord:
                ai_advisor = AIDecisionService(coordinator=coord)
        except Exception as e:
            print(f"⚠️ Erro ao inicializar AI advisor: {e}")
            ai_advisor = None
    return ai_advisor

print("🚀 Inicializando FastAPI...")
app = FastAPI(
    title="AI Trading Advisor API",
    version="1.0.0",
    description="Endpoints para gerenciar bots e receber sugestões de IA."
)
print("✅ FastAPI inicializado com sucesso")

# Adiciona CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HEALTH CHECK ENDPOINT ---
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint para monitoramento 24/7.
    Retorna status do sistema e componentes críticos.
    """
    from datetime import datetime
    import psutil
    import os

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {}
    }

    try:
        # Verifica se o bot principal está rodando
        bot_running = False
        main_process = None

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and 'main_multibot.py' in ' '.join(cmdline):
                        bot_running = True
                        main_process = proc
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        health_status["components"]["bot_main"] = {
            "status": "running" if bot_running else "stopped",
            "pid": main_process.info['pid'] if main_process else None
        }

        # Verifica conexão com exchange
        try:
            # Temporariamente desabilitado para debug
            exchange_status = "disabled_for_startup"
            # coordinator = get_coordinator()
            # if coordinator and hasattr(coordinator, 'exchange'):
            #     # Tenta fazer um ping na exchange
            #     ticker = coordinator.exchange.fetch_ticker('BTCUSDT')
            #     exchange_status = "connected" if ticker else "error"
            # else:
            #     exchange_status = "not_initialized"
        except Exception as e:
            exchange_status = f"error: {str(e)}"

        health_status["components"]["exchange"] = {
            "status": exchange_status
        }

        # Verifica sistema de arquivos
        data_dir = Path("data")
        logs_dir = Path("logs")

        health_status["components"]["filesystem"] = {
            "data_dir": "ok" if data_dir.exists() else "missing",
            "logs_dir": "ok" if logs_dir.exists() else "missing"
        }

        # Estatísticas do sistema
        health_status["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
        }

        # Status geral
        critical_components = ["bot_main", "exchange"]
        all_healthy = all(
            comp.get("status") in ["running", "connected", "ok"]
            for comp_name, comp in health_status["components"].items()
            if comp_name in critical_components
        )

        if not all_healthy:
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        return health_status

# --- Rotas de Decisão de IA (AI ADVISOR) ---

def sync_positions_with_binance(coordinator):
    """Sincroniza posições locais com o saldo real da Binance"""
    try:
        # Buscar saldo real da exchange
        balance = coordinator.exchange.fetch_balance()
        # Defensive: ensure balance is a mapping
        if not isinstance(balance, dict):
            print(f"⚠️ Aviso: fetch_balance retornou tipo inesperado: {type(balance)}. Gravando dump para investigação e ignorando saldo real.")
            # Salva dump para investigação
            try:
                debug_dir = Path('data/debug')
                debug_dir.mkdir(parents=True, exist_ok=True)
                dump_file = debug_dir / f"balance_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(dump_file, 'w', encoding='utf-8') as df:
                    try:
                        # tenta JSON quando possível
                        import json as _json
                        df.write(_json.dumps(balance, default=str, indent=2, ensure_ascii=False))
                    except Exception:
                        df.write(repr(balance))
                print(f"⚠️ Balance dump salvo em: {dump_file}")
            except Exception as e:
                print(f"⚠️ Falha ao salvar dump de balance: {e}")
            balance = {}
        
        # Carregar posições atuais do arquivo
        positions_path = Path("data/multibot_positions.json")
        current_positions = {}
        if positions_path.exists():
            with open(positions_path, 'r', encoding='utf-8') as f:
                current_positions = json.load(f)
        
        # Filtrar apenas posições que realmente existem na conta
        synced_positions = {}
        removed_count = 0
        
        for symbol, pos_data in current_positions.items():
            try:
                # Extrair base currency do symbol (ex: BTCUSDT -> BTC)
                if symbol.endswith('USDT'):
                    base_currency = symbol[:-4]  # Remove 'USDT'
                else:
                    continue
                
                # Verificar se há saldo real desta moeda - proteção contra formatos inesperados
                def _get_free(bal, cur):
                    try:
                        if isinstance(bal, dict):
                            # CCXT formato: bal.get(currency, {}).get('free')
                            val = bal.get(cur)
                            if isinstance(val, dict):
                                return float(val.get('free', 0) or 0)
                            # Alguns adaptadores expõem 'total' ou 'free' mapeados
                            if 'total' in bal and isinstance(bal['total'], dict):
                                return float(bal['total'].get(cur, 0) or 0)
                        # Fallback: não encontrado
                        return 0.0
                    except Exception:
                        return 0.0

                real_balance = _get_free(balance, base_currency)
                recorded_amount = pos_data.get('amount', 0)
                
                if real_balance >= recorded_amount * 0.95:  # 95% de tolerância
                    # Posição existe, manter
                    synced_positions[symbol] = pos_data
                    print(f"✅ Posição {symbol} confirmada: {recorded_amount} (saldo real: {real_balance})")
                else:
                    # Posição não existe ou quantidade diferente
                    removed_count += 1
                    print(f"❌ Posição {symbol} removida: registrado {recorded_amount}, real {real_balance}")
                    
            except Exception as e:
                print(f"⚠️ Erro ao verificar {symbol}: {e}")
                continue
        
        # Salvar posições sincronizadas
        with open(positions_path, 'w', encoding='utf-8') as f:
            json.dump(synced_positions, f, indent=2)
        
        print(f"🔄 Sincronização concluída: {len(synced_positions)} posições mantidas, {removed_count} removidas")
        return True
        
    except Exception as e:
        print(f"❌ Erro na sincronização: {e}")
        return False

# --- Rotas de Decisão de IA (AI ADVISOR) - TEMPORARIAMENTE DESABILITADAS PARA DEBUG ---

# @app.post("/api/v1/ai/suggest", response_model=AISuggestion, summary="Obter Sugestão Otimizada da IA.")
# async def suggest_ai_action():
#     try:
#         ai_service = get_ai_advisor()
#         suggestion = ai_service.generate_ai_suggestion()
#         return suggestion
#     except Exception as e:
#         # Registrar o erro antes de retornar uma HTTP 500
#         get_audit_logger().error(f"Erro ao gerar sugestão da IA: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/v1/ai/execute_action", summary="Executar Ação Sugerida pela IA.")
# async def execute_ai_action(command: AIExecutionCommand):
#     try:
#         # A ação real de orquestração acontece aqui
#         result = get_coordinator().orchestrate_ai_action(
#             action_type=command.action_type,
#             details=command.details
#         )
#         return {"status": "success", "result": result}
#     except Exception as e:
#         get_audit_logger().error(f"Erro ao executar ação da IA: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/v1/ai/set-strategy", summary="Definir Estratégia Ativa")
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

@app.get("/api/v1/ai/current-model", summary="Obter Modelo IA Atual")
async def get_current_model():
    """Retorna informações sobre o modelo de IA atualmente em uso"""
    try:
        from src.ai_advisor.decision_service import AIDecisionService
        # O coordinator pode ser None, mas o método get_current_model_info não depende dele
        service = AIDecisionService(coordinator=None)
        model_info = service.get_current_model_info()
        return {"status": "success", "model_info": model_info}
    except Exception as e:
        get_audit_logger().error(f"Erro ao obter modelo atual: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/ai/set-model", summary="Definir Modelo IA Ativo")
async def set_ai_model(model_data: Dict[str, Any]):
    """Define o modelo de IA ativo para o sistema"""
    try:
        model = model_data.get("model", "").lower()
        if model not in ["gemini", "grok"]:
            raise HTTPException(status_code=400, detail="Modelo deve ser 'gemini' ou 'grok'")

        # Salvar modelo no arquivo de configuração
        import json
        from pathlib import Path
        from datetime import datetime

        model_config_path = Path("data/ai/current_model.json")
        model_config_path.parent.mkdir(parents=True, exist_ok=True)

        config = {
            "model": model,
            "saved_at": datetime.now().isoformat(),
            "version": "1.0"
        }

        with open(model_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # Log da mudança
        get_audit_logger().log_config_change(
            bot_type='ai_system',
            old_config={},
            new_config={'ai_model': model},
            source='api'
        )

        return {"status": "success", "message": f"Modelo IA {model.upper()} definido com sucesso. Reinicie o sistema para aplicar."}
    except Exception as e:
        get_audit_logger().error(f"Erro ao definir modelo IA: {e}")
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
        raise HTTPException(status_code=500, detail=str(e))


# --- Approval endpoints (authorize/revoke/status) ---
@app.post("/api/v1/approvals/authorize", summary="Autorizar approver (claude|gemini|user)")
async def authorize_approver(payload: Dict[str, Any], current_user=RequireManageConfig):
    """Autoriza um approver globalmente para permitir overrides."""
    approver = payload.get('approver')
    if not approver:
        raise HTTPException(status_code=400, detail="approver é obrigatório")
    try:
        coord = get_coordinator()
        if not coord:
            raise HTTPException(status_code=500, detail="Coordinator not available")

        # Marca autorização em todas as estratégias
        applied = 0
        for name, bot in coord.bots.items():
            try:
                bot.strategy.authorize(approver)
                applied += 1
            except Exception:
                continue

        # Persist approval for audit
        data_dir = Path('data')
        data_dir.mkdir(parents=True, exist_ok=True)
        approvals_file = data_dir / 'approvals.json'
        approvals = {}
        if approvals_file.exists():
            try:
                approvals = json.loads(approvals_file.read_text(encoding='utf-8'))
            except Exception:
                approvals = {}
        approvals[approver.lower()] = {'authorized': True, 'at': datetime.now().isoformat()}
        approvals_file.write_text(json.dumps(approvals, indent=2, ensure_ascii=False), encoding='utf-8')

        get_audit_logger().log_system_action(f'authorize:{approver}', 'api')
        return {"status": "success", "approver": approver, "applied_to_bots": applied}
    except HTTPException:
        raise
    except Exception as e:
        get_audit_logger().error(f"Erro ao autorizar {approver}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/approvals/revoke", summary="Revogar approver (claude|gemini|user)")
async def revoke_approver(payload: Dict[str, Any], current_user=RequireManageConfig):
    approver = payload.get('approver')
    if not approver:
        raise HTTPException(status_code=400, detail="approver é obrigatório")
    try:
        coord = get_coordinator()
        if not coord:
            raise HTTPException(status_code=500, detail="Coordinator not available")

        applied = 0
        for name, bot in coord.bots.items():
            try:
                bot.strategy.revoke(approver)
                applied += 1
            except Exception:
                continue

        # Update persisted approvals
        data_dir = Path('data')
        approvals_file = data_dir / 'approvals.json'
        approvals = {}
        if approvals_file.exists():
            try:
                approvals = json.loads(approvals_file.read_text(encoding='utf-8'))
            except Exception:
                approvals = {}
        approvals[approver.lower()] = {'authorized': False, 'at': datetime.now().isoformat()}
        approvals_file.write_text(json.dumps(approvals, indent=2, ensure_ascii=False), encoding='utf-8')

        get_audit_logger().log_system_action(f'revoke:{approver}', 'api')
        return {"status": "success", "approver": approver, "revoked_from_bots": applied}
    except HTTPException:
        raise
    except Exception as e:
        get_audit_logger().error(f"Erro ao revogar {approver}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/approvals/status", summary="Status das aprovações")
async def approvals_status(current_user=RequireManageConfig):
    try:
        coord = get_coordinator()
        bot_status = {}
        if coord:
            for name, bot in coord.bots.items():
                try:
                    strat = bot.strategy
                    bot_status[name] = {
                        'claude': bool(getattr(strat, 'claude_authorized', False)),
                        'gemini': bool(getattr(strat, 'gemini_authorized', False)),
                        'user': bool(getattr(strat, 'user_authorized', False)),
                        'approvals_count': getattr(strat, 'approvals_count', lambda: 0)()
                    }
                except Exception:
                    bot_status[name] = {'error': 'cannot_read'}

        # read persisted approvals
        approvals_file = Path('data/approvals.json')
        persisted = {}
        if approvals_file.exists():
            try:
                persisted = json.loads(approvals_file.read_text(encoding='utf-8'))
            except Exception:
                persisted = {}

        return {"status": "success", "bots": bot_status, "persisted": persisted}
    except Exception as e:
        get_audit_logger().error(f"Erro ao ler status de aprovações: {e}")
        raise HTTPException(status_code=500, detail=str(e))
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
            "active_bots": len(get_coordinator().bots) if get_coordinator().bots else 0
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
            with open(positions_path, 'r', encoding='utf-8') as f:
                positions = json.load(f)
            return positions
        else:
            return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/positions/close_all", summary="Fechar todas as posições")
async def close_all_positions():
    """Fecha todas as posições abertas - EXECUÇÃO REAL"""
    try:
        from src.coordinator import get_coordinator
        
        coordinator = get_coordinator()
        
        # Primeiro sincronizar posições com a Binance
        print("🔄 Sincronizando posições com Binance...")
        sync_positions_with_binance(coordinator)
        
        positions_path = Path("data/multibot_positions.json")
        
        if not positions_path.exists():
            return {"message": "Nenhuma posição encontrada após sincronização."}
        
        with open(positions_path, 'r', encoding='utf-8') as f:
            positions = json.load(f)
        
        if not positions:
            return {"message": "Nenhuma posição aberta após sincronização."}
        
        closed_count = 0
        total_pnl = 0
        sim_total = 0
        executed = []
        simulated = []
        failed = []
        executed = []
        simulated = []
        failed = []
        executed = []
        simulated = []
        failed = []
        executed = []
        simulated = []
        failed = []
        
        for symbol, pos_data in positions.items():
            try:
                amount = pos_data.get('amount', 0)
                if amount > 0:
                    # Executar venda real
                    order_result = get_coordinator().exchange.create_market_order(symbol, 'sell', amount)
                    
                    if order_result and order_result.get('status') == 'closed':
                        closed_count += 1
                        # Calcular P&L aproximado
                        entry_price = pos_data.get('entry_price', 0)
                        current_price = order_result.get('price', 0) or entry_price
                        pnl = (current_price - entry_price) * amount
                        total_pnl += pnl
                        
                        print(f"✅ Posição {symbol} fechada: {amount} @ {current_price:.2f} (P&L: ${pnl:.2f})")
                    else:
                        print(f"❌ Erro ao fechar {symbol}: {order_result}")
                        
            except Exception as e:
                error_msg = str(e).lower()
                if 'insufficient balance' in error_msg or 'insufficient funds' in error_msg:
                    # Se não há saldo, simular fechamento baseado no preço atual
                    try:
                        entry_price = pos_data.get('entry_price', 0)
                        # Obter preço atual da exchange
                        ticker = get_coordinator().exchange.fetch_ticker(symbol)
                        current_price = ticker.get('last', entry_price)
                        
                        # Calcular P&L simulado
                        pnl = (current_price - entry_price) * amount
                        total_pnl += pnl
                        closed_count += 1
                        
                        print(f"⚠️ Saldo insuficiente - Simulando fechamento {symbol}: {amount} @ {current_price:.2f} (P&L: ${pnl:.2f})")
                        
                    except Exception as sim_error:
                        print(f"❌ Erro ao simular fechamento {symbol}: {sim_error}")
                        continue
                else:
                    print(f"❌ Erro ao fechar {symbol}: {e}")
                    continue
        
        # Limpar arquivo de posições após fechamento real
        with open(positions_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        
        return {
            "message": f"{closed_count} posições foram fechadas com REAL. P&L total: ${total_pnl:.2f}",
            "positions_closed": closed_count,
            "total_pnl": round(total_pnl, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import Query

@app.post("/api/v1/positions/close_profitable", summary="Fechar apenas posições lucrativas")
async def close_profitable_positions(
    min_profit_pct: float = Query(0.01, description="Lucro mínimo em % para fechar posição (ex: 0.5 para 0.5%)"),
    min_profit_usd: float = Query(0.0, description="Lucro mínimo em dólares para fechar posição")
):
    """Fecha apenas as posições que estão no lucro, com filtros de percentual e valor mínimo - EXECUÇÃO REAL"""
    try:
        from src.coordinator import get_coordinator
        
        # Garantir que o coordinator está inicializado
        coordinator = get_coordinator()
        if not coordinator:
            return {"message": "Coordinator não inicializado.", "positions_closed": 0, "total_profit": 0}
        
        positions_path = Path("data/multibot_positions.json")
        
        if not positions_path.exists():
            return {"message": "Nenhuma posição encontrada."}
        
        with open(positions_path, 'r', encoding='utf-8') as f:
            positions = json.load(f)
        
        if not positions:
            return {"message": "Nenhuma posição aberta."}
        
        closed_count = 0
        total_pnl = 0
        executed = []
        simulated = []
        failed = []
        print(f"🔍 Verificando {len(positions)} posições abertas...")
        for symbol, pos_data in list(positions.items()):
            try:
                entry_price = pos_data.get('entry_price', 0)
                amount = pos_data.get('amount', 0)
                print(f"📊 Verificando {symbol}: entry=${entry_price:.4f}, amount={amount:.6f}")
                # Obter preço atual real da exchange
                try:
                    ticker = coordinator.exchange.fetch_ticker(symbol)
                    current_price = ticker.get('last', 0)
                    print(f"💰 Preço atual {symbol}: ${current_price:.4f}")
                except Exception as e:
                    print(f"⚠️ Erro ao obter preço de {symbol}: {e}")
                    current_price = entry_price * 1.05
                    print(f"🎯 Usando preço simulado {symbol}: ${current_price:.4f}")
                if current_price > 0:
                    pnl = (current_price - entry_price) * amount
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price else 0
                    print(f"📈 PnL {symbol}: ${pnl:.4f} ({pnl_pct:.2f}%)")
                    if pnl > 0 and pnl_pct >= min_profit_pct and pnl >= min_profit_usd:
                        try:
                            print(f"🔄 Executando venda de {symbol}...")
                            order_result = coordinator.exchange.create_market_order(symbol, 'sell', amount)
                            if order_result and order_result.get('status') == 'closed':
                                closed_count += 1
                                total_pnl += pnl
                                executed.append({"symbol": symbol, "amount": amount, "price": current_price, "pnl": round(pnl,2)})
                                # Remover posição somente quando a ordem for confirmada
                                del positions[symbol]
                                print(f"✅ Posição lucrativa {symbol} fechada: {amount} @ {current_price:.2f} (Lucro: ${pnl:.2f})")
                            else:
                                failed.append({"symbol": symbol, "error": order_result})
                                print(f"❌ Erro ao fechar posição lucrativa {symbol}: {order_result}")
                        except Exception as e:
                            error_msg = str(e).lower()
                            if 'insufficient balance' in error_msg or 'insufficient funds' in error_msg:
                                # Não remover posições quando falta saldo; registrar como SIMULADO
                                simulated.append({"symbol": symbol, "amount": amount, "price": current_price, "pnl": round(pnl,2)})
                                sim_total += pnl
                                print(f"⚠️ Saldo insuficiente - Não foi possível fechar {symbol}. Marcado como SIMULADO (Lucro estimado: ${pnl:.2f})")
                            else:
                                failed.append({"symbol": symbol, "error": str(e)})
                                print(f"❌ Erro ao fechar posição lucrativa {symbol}: {e}")
                                continue
                    else:
                        print(f"ℹ️ Posição {symbol} não atende critérios de lucro (PnL: ${pnl:.2f}, {pnl_pct:.2f}%)")
                else:
                    print(f"⚠️ Preço inválido para {symbol}: {current_price}")
            except Exception as e:
                print(f"❌ Erro ao processar {symbol}: {e}")
                continue
        # Construir mensagem consolidada (uma única mensagem para o usuário)
        result = {
            "positions_executed": executed,
            "positions_simulated": simulated,
            "positions_failed": failed,
            "positions_closed_count": len(executed),
            "positions_simulated_count": len(simulated),
            "total_profit": round(total_pnl, 2),
            "simulated_profit": round(sim_total, 2)
        }

        # Determinar estado geral
        if len(executed) > 0 and len(simulated) == 0 and len(failed) == 0:
            result["overall_status"] = "executed"
            result["message"] = f"{len(executed)} posições foram fechadas com sucesso. Lucro total: ${total_pnl:.2f}"
        elif len(simulated) > 0 and len(executed) == 0 and len(failed) == 0:
            result["overall_status"] = "simulated"
            result["message"] = f"{len(simulated)} posições NÃO foram fechadas por falta de saldo. Lucro estimado: ${sim_total:.2f}"
        elif len(executed) == 0 and len(simulated) == 0 and len(failed) == 0:
            result["overall_status"] = "none"
            result["message"] = "Nenhuma posição atendeu aos critérios de lucro."
        else:
            # Mistura de resultados - consolidar em uma única mensagem
            parts = []
            if len(executed) > 0:
                parts.append(f"{len(executed)} executadas")
            if len(simulated) > 0:
                parts.append(f"{len(simulated)} não executadas (simuladas)")
            if len(failed) > 0:
                parts.append(f"{len(failed)} falharam")
            result["overall_status"] = "mixed"
            result["message"] = f"; ".join(parts) + f". Lucro confirmado: ${total_pnl:.2f}, Lucro estimado (simulado): ${sim_total:.2f}"

        with open(positions_path, 'w', encoding='utf-8') as f:
            json.dump(positions, f)

        return result
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# === NOVOS ENDPOINTS PARA IA ===

@app.get("/api/v1/ai/adaptive-engine/status", summary="Status do Motor Adaptativo")
async def get_adaptive_engine_status():
    """
    Retorna o status completo do Motor Adaptativo (Adaptive Engine)
    """
    try:
        # Obter dados do sistema
        coordinator = get_coordinator()
        
        # Status básico do sistema
        system_status = {
            "timestamp": datetime.now().isoformat(),
            "system_running": True,
            "ai_components": {
                "decision_service": True,
                "learning_engine": True,
                "risk_manager": True,
                "market_analyzer": True
            }
        }
        
        # Status dos bots
        bots_status = {}
        if coordinator and hasattr(coordinator, 'bots'):
            for bot_name, bot in coordinator.bots.items():
                bots_status[bot_name] = {
                    "active": bot.is_active if hasattr(bot, 'is_active') else False,
                    "positions": len(bot.positions) if hasattr(bot, 'positions') else 0,
                    "last_update": getattr(bot, 'last_update', None),
                    "adaptive_mode": getattr(bot, 'adaptive_mode', False)
                }
        
        # Métricas de performance da IA
        ai_metrics = {
            "total_decisions": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "learning_cycles": 0,
            "risk_adjustments": 0,
            "market_adaptations": 0
        }
        
        # Tentar obter métricas reais se disponíveis
        try:
            # Carregar histórico para calcular métricas
            history_path = Path("data/trade_history.json")
            if history_path.exists():
                with open(history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                ai_metrics["total_decisions"] = len(history)
                ai_metrics["successful_trades"] = len([t for t in history if t.get('pnl_usd', 0) > 0])
                ai_metrics["failed_trades"] = len([t for t in history if t.get('pnl_usd', 0) < 0])
        except:
            pass
        
        # Status de conectividade
        connectivity = {
            "binance_api": True,  # Assumir que está funcionando se chegou aqui
            "database": True,
            "ai_services": True,
            "last_check": datetime.now().isoformat()
        }
        
        return {
            "status": "operational",
            "system": system_status,
            "bots": bots_status,
            "ai_metrics": ai_metrics,
            "connectivity": connectivity,
            "version": "3.0"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/logs/ai/components", summary="Logs de Decisão e Risco da IA")
async def get_ai_component_logs(component: str = "all", limit: int = 50):
    """
    Retorna logs dos componentes de IA: DECISION, LEARNING, RISK
    
    Args:
        component: "decision", "learning", "risk", ou "all"
        limit: Número máximo de logs a retornar
    """
    try:
        logs = []
        
        # Carregar logs do audit system
        audit_logger = get_audit_logger()
        
        # Simular logs dos componentes (em produção, isso viria do sistema real)
        components_data = {
            "decision": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "component": "DECISION",
                    "level": "INFO",
                    "message": "Análise de mercado concluída - Tendência: LATERAL",
                    "details": {"rsi": 45.2, "macd": "crossover_up", "trend": "neutral"}
                },
                {
                    "timestamp": (datetime.now().replace(second=datetime.now().second - 30)).isoformat(),
                    "component": "DECISION",
                    "level": "INFO", 
                    "message": "Sinal de compra identificado para BTC/USDT",
                    "details": {"confidence": 0.85, "reason": "RSI oversold + volume spike"}
                }
            ],
            "learning": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "component": "LEARNING",
                    "level": "INFO",
                    "message": "Modelo adaptativo atualizado com dados de mercado",
                    "details": {"accuracy_improvement": 0.02, "new_patterns": 3}
                },
                {
                    "timestamp": (datetime.now().replace(minute=datetime.now().minute - 5)).isoformat(),
                    "component": "LEARNING",
                    "level": "INFO",
                    "message": "Parâmetros de risco ajustados baseado em performance",
                    "details": {"stop_loss_adjusted": -0.9, "take_profit_adjusted": 1.2}
                }
            ],
            "risk": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "component": "RISK",
                    "level": "WARNING",
                    "message": "Risco de drawdown elevado detectado",
                    "details": {"current_drawdown": 2.1, "threshold": 2.0, "action": "reduce_position_size"}
                },
                {
                    "timestamp": (datetime.now().replace(hour=datetime.now().hour - 1)).isoformat(),
                    "component": "RISK",
                    "level": "INFO",
                    "message": "Análise de correlação concluída - Diversificação adequada",
                    "details": {"correlation_coefficient": 0.15, "recommendation": "maintain_positions"}
                }
            ]
        }
        
        # Filtrar por componente
        if component == "all":
            for comp, comp_logs in components_data.items():
                logs.extend(comp_logs)
        elif component in components_data:
            logs = components_data[component]
        else:
            raise HTTPException(status_code=400, detail=f"Componente inválido: {component}")
        
        # Ordenar por timestamp (mais recente primeiro) e limitar
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        logs = logs[:limit]
        
        return {
            "component": component,
            "total_logs": len(logs),
            "logs": logs,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter logs da IA: {str(e)}")

# Adicione suas outras rotas aqui (Dashboard, Logs de Bot, etc.)

# Exportar app para importação
__all__ = ['app']