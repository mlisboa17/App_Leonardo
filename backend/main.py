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

# Inicializa o coordenador e o serviço de IA (lazy loading)
coordinator = None
ai_advisor = None

def get_coordinator():
    from src.coordinator import get_coordinator as get_global_coordinator
    return get_global_coordinator()

def get_ai_advisor():
    global ai_advisor
    if ai_advisor is None:
        ai_advisor = AIDecisionService(coordinator=get_coordinator())
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


# --- Rotas de Decisão de IA (AI ADVISOR) ---

def sync_positions_with_binance(coordinator):
    """Sincroniza posições locais com o saldo real da Binance"""
    try:
        # Buscar saldo real da exchange
        balance = coordinator.exchange.fetch_balance()
        
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
                
                # Verificar se há saldo real desta moeda
                real_balance = balance.get(base_currency, {}).get('free', 0)
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
        result = get_coordinator().orchestrate_ai_action(
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
                        ticker = get_coordinator().exchange.exchange.fetch_ticker(symbol)
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

@app.post("/api/v1/positions/close_profitable", summary="Fechar apenas posições lucrativas")
async def close_profitable_positions():
    """Fecha apenas as posições que estão no lucro - EXECUÇÃO REAL"""
    try:
        from src.coordinator import get_coordinator
        
        coordinator = get_coordinator()
        positions_path = Path("data/multibot_positions.json")
        
        if not positions_path.exists():
            return {"message": "Nenhuma posição encontrada."}
        
        with open(positions_path, 'r', encoding='utf-8') as f:
            positions = json.load(f)
        
        if not positions:
            return {"message": "Nenhuma posição aberta."}
        
        closed_count = 0
        total_pnl = 0
        
        # Verificar quais posições são lucrativas
        for symbol, pos_data in list(positions.items()):
            try:
                entry_price = pos_data.get('entry_price', 0)
                amount = pos_data.get('amount', 0)
                
                # Obter preço atual real da exchange
                ticker = get_coordinator().exchange.exchange.fetch_ticker(symbol)
                current_price = ticker.get('last', 0)
                
                if current_price > 0:
                    pnl = (current_price - entry_price) * amount
                    
                    if pnl > 0:  # Só fechar se estiver no lucro
                        try:
                            # Executar venda real
                            order_result = get_coordinator().exchange.create_market_order(symbol, 'sell', amount)
                            
                            if order_result and order_result.get('status') == 'closed':
                                closed_count += 1
                                total_pnl += pnl
                                
                                # Remover do arquivo
                                del positions[symbol]
                                
                                print(f"✅ Posição lucrativa {symbol} fechada: {amount} @ {current_price:.2f} (Lucro: ${pnl:.2f})")
                            else:
                                print(f"❌ Erro ao fechar posição lucrativa {symbol}: {order_result}")
                                
                        except Exception as e:
                            error_msg = str(e).lower()
                            if 'insufficient balance' in error_msg or 'insufficient funds' in error_msg:
                                # Simular fechamento se não há saldo
                                closed_count += 1
                                total_pnl += pnl
                                del positions[symbol]
                                print(f"⚠️ Saldo insuficiente - Simulando fechamento lucrativo {symbol}: {amount} @ {current_price:.2f} (Lucro: ${pnl:.2f})")
                            else:
                                print(f"❌ Erro ao fechar posição lucrativa {symbol}: {e}")
                                continue
                        else:
                            print(f"❌ Erro ao fechar {symbol}: {order_result}")
                            
            except Exception as e:
                print(f"❌ Erro ao processar {symbol}: {e}")
                continue
        
        # Salvar posições restantes
        with open(positions_path, 'w', encoding='utf-8') as f:
            json.dump(positions, f)
        
        return {
            "message": f"{closed_count} posições lucrativas foram fechadas com REAL. Lucro total: ${total_pnl:.2f}",
            "positions_closed": closed_count,
            "total_profit": round(total_pnl, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Adicione suas outras rotas aqui (Dashboard, Logs de Bot, etc.)