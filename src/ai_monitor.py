"""
============================================================
AI MONITOR - Sistema de Monitoramento Adaptativo Global
============================================================

Monitora TODOS os 5 bots (Estavel, Medio, Volatil, Meme, Unico)
e ajusta seus parâmetros dinamicamente baseado em:

- Performance individual de cada bot
- Condições de mercado em tempo real
- Volatilidade e tendências
- Saldo USDT disponível
- Histórico de wins/losses

Este módulo é inicializado automaticamente ao startar o sistema.

============================================================
"""

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import yaml


class AdaptiveAIMonitor:
    """
    Monitor de IA que ajusta TODOS os bots automaticamente
    """
    
    def __init__(self, config_path: str = "config/bots_config.yaml"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger('AdaptiveAIMonitor')
        self.logger.setLevel(logging.INFO)
        
        # Estado do monitor
        self.running = False
        self.monitor_thread = None
        
        # Configurações adaptativas
        self.monitoring_interval = 60  # Verifica a cada 60 segundos
        
        # Histórico de ajustes
        self.adjustments_history = []
        
        # Thresholds para ajustes
        self.thresholds = {
            'low_balance': 50.0,        # Se USDT < $50, aumenta urgência de venda
            'high_volatility': 0.05,    # 5% de volatilidade = alta
            'consecutive_losses': 3,    # 3 perdas seguidas = ajusta estratégia
            'win_rate_low': 0.40,       # < 40% win rate = precisa ajustar
        }
        
        # Cache de performance
        self.bot_performance = {
            'bot_estavel': {'wins': 0, 'losses': 0, 'pnl': 0, 'consecutive_losses': 0},
            'bot_medio': {'wins': 0, 'losses': 0, 'pnl': 0, 'consecutive_losses': 0},
            'bot_volatil': {'wins': 0, 'losses': 0, 'pnl': 0, 'consecutive_losses': 0},
            'bot_meme': {'wins': 0, 'losses': 0, 'pnl': 0, 'consecutive_losses': 0},
            'bot_unico': {'wins': 0, 'losses': 0, 'pnl': 0, 'consecutive_losses': 0},
        }
        
        self.logger.info("🤖 AI Monitor inicializado - monitorando 5 bots")
    
    def start(self):
        """Inicia o monitoramento em background"""
        if self.running:
            self.logger.warning("AI Monitor já está rodando")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("✅ AI Monitor iniciado em background")
    
    def stop(self):
        """Para o monitoramento"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("🛑 AI Monitor parado")
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self.running:
            try:
                # Atualiza performance dos bots
                self._update_bot_performance()
                
                # Analisa e ajusta cada bot
                self._analyze_and_adjust_bots()
                
                # Salva histórico de ajustes
                self._save_adjustments_history()
                
            except Exception as e:
                self.logger.error(f"Erro no monitoring loop: {e}")
            
            # Aguarda próximo ciclo
            time.sleep(self.monitoring_interval)
    
    def _update_bot_performance(self):
        """Atualiza métricas de performance de todos os bots"""
        try:
            # Carrega histórico de trades
            trades_file = Path("data/all_trades_history.json")
            if not trades_file.exists():
                return
            
            with open(trades_file, 'r') as f:
                trades = json.load(f)
            
            # Analisa últimos trades de cada bot
            for bot_type in self.bot_performance.keys():
                bot_trades = [t for t in trades if t.get('bot_type') == bot_type]
                
                if not bot_trades:
                    continue
                
                # Últimos 20 trades
                recent_trades = bot_trades[-20:]
                
                wins = sum(1 for t in recent_trades if t.get('pnl_usd', 0) > 0)
                losses = sum(1 for t in recent_trades if t.get('pnl_usd', 0) <= 0)
                total_pnl = sum(t.get('pnl_usd', 0) for t in recent_trades)
                
                # Perdas consecutivas
                consecutive_losses = 0
                for t in reversed(recent_trades):
                    if t.get('pnl_usd', 0) <= 0:
                        consecutive_losses += 1
                    else:
                        break
                
                self.bot_performance[bot_type] = {
                    'wins': wins,
                    'losses': losses,
                    'pnl': total_pnl,
                    'consecutive_losses': consecutive_losses,
                    'win_rate': wins / len(recent_trades) if recent_trades else 0,
                    'last_updated': datetime.now().isoformat()
                }
        
        except Exception as e:
            self.logger.error(f"Erro ao atualizar performance: {e}")
    
    def _analyze_and_adjust_bots(self):
        """Analisa e ajusta parâmetros de cada bot"""
        try:
            # Carrega configuração atual
            if not self.config_path.exists():
                self.logger.warning(f"Config não encontrado: {self.config_path}")
                return
            
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Carrega saldo atual
            balances = self._load_balances()
            usdt_balance = balances.get('usdt_balance', 0)
            
            adjustments_made = []
            
            # Ajusta cada bot
            for bot_type in ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme', 'bot_unico']:
                if bot_type not in config:
                    continue
                
                perf = self.bot_performance[bot_type]
                bot_config = config[bot_type]
                
                # === AJUSTE 1: Saldo baixo ===
                if usdt_balance < self.thresholds['low_balance']:
                    # Aumenta take profit (vender mais cedo)
                    current_tp = bot_config.get('risk', {}).get('take_profit', 1.0)
                    new_tp = max(0.3, current_tp - 0.2)
                    
                    if 'risk' not in bot_config:
                        bot_config['risk'] = {}
                    
                    bot_config['risk']['take_profit'] = new_tp
                    adjustments_made.append({
                        'bot': bot_type,
                        'reason': 'low_balance',
                        'adjustment': f'TP: {current_tp:.2f}% → {new_tp:.2f}%',
                        'timestamp': datetime.now().isoformat()
                    })
                
                # === AJUSTE 2: Perdas consecutivas ===
                if perf['consecutive_losses'] >= self.thresholds['consecutive_losses']:
                    # Pausa temporariamente ou reduz agressividade
                    current_sl = bot_config.get('risk', {}).get('stop_loss', -1.0)
                    new_sl = min(-0.3, current_sl + 0.3)  # Stop loss mais apertado
                    
                    bot_config['risk']['stop_loss'] = new_sl
                    adjustments_made.append({
                        'bot': bot_type,
                        'reason': 'consecutive_losses',
                        'adjustment': f'SL: {current_sl:.2f}% → {new_sl:.2f}% (proteção)',
                        'timestamp': datetime.now().isoformat()
                    })
                
                # === AJUSTE 3: Win rate baixo ===
                if perf.get('win_rate', 0) < self.thresholds['win_rate_low']:
                    # Reduz quantidade por trade
                    current_amount = bot_config.get('trading', {}).get('amount_per_trade', 20)
                    new_amount = max(10, current_amount - 5)
                    
                    if 'trading' not in bot_config:
                        bot_config['trading'] = {}
                    
                    bot_config['trading']['amount_per_trade'] = new_amount
                    adjustments_made.append({
                        'bot': bot_type,
                        'reason': 'low_win_rate',
                        'adjustment': f'Amount: ${current_amount} → ${new_amount}',
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Salva configuração ajustada
            if adjustments_made:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
                self.adjustments_history.extend(adjustments_made)
                
                for adj in adjustments_made:
                    self.logger.info(f"🎛️ Ajuste: {adj['bot']} | {adj['reason']} | {adj['adjustment']}")
        
        except Exception as e:
            self.logger.error(f"Erro ao ajustar bots: {e}")
    
    def _load_balances(self) -> Dict:
        """Carrega saldos atuais"""
        try:
            balances_file = Path("data/dashboard_balances.json")
            if balances_file.exists():
                with open(balances_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Erro ao carregar balances: {e}")
        
        return {'usdt_balance': 0, 'total_balance': 0}
    
    def _save_adjustments_history(self):
        """Salva histórico de ajustes"""
        try:
            history_file = Path("data/ai_adjustments_history.json")
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(history_file, 'w') as f:
                json.dump({
                    'adjustments': self.adjustments_history[-100:],  # Últimos 100
                    'bot_performance': self.bot_performance,
                    'last_update': datetime.now().isoformat()
                }, f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Erro ao salvar histórico: {e}")
    
    def get_status(self) -> Dict:
        """Retorna status do monitor"""
        return {
            'running': self.running,
            'bot_performance': self.bot_performance,
            'recent_adjustments': self.adjustments_history[-10:],
            'thresholds': self.thresholds
        }


# Singleton
_ai_monitor_instance = None

def get_ai_monitor() -> AdaptiveAIMonitor:
    """Retorna instância única do AI Monitor"""
    global _ai_monitor_instance
    if _ai_monitor_instance is None:
        _ai_monitor_instance = AdaptiveAIMonitor()
    return _ai_monitor_instance
