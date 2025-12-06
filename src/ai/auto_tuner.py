"""
🎛️ AUTO-TUNER - Ajuste Automático de Configurações R7_V1
========================================================
Sistema que ajusta automaticamente as configurações dos bots
baseado em:
1. Condições de mercado em tempo real
2. Performance histórica dos bots
3. Volatilidade atual
4. Tendências e momentum
5. 🆕 MODO OPORTUNISTA - Detecta condições favoráveis e aumenta agressividade

REGRAS DE AJUSTE:
- Stop Loss pela volatilidade (alto vol = stop mais largo)
- Take Profit pela tendência (alta = deixa correr)
- Posição pela volatilidade (extrema = reduz posição)
- RSI pela tendência (alta forte = compra RSI mais alto)
- 🆕 Agressividade pelo Modo Oportunista (condições favoráveis = mais agressivo)

NÍVEIS DO MODO OPORTUNISTA:
- 🟢 CONSERVADOR (1.0x) - Padrão, mercado incerto
- 🟡 MODERADO (1.3x) - Algumas condições favoráveis
- 🟠 AGRESSIVO (1.5x) - Múltiplas condições favoráveis
- 🔴 MÁXIMO (1.8x) - Oportunidade excepcional

Autor: Sistema R7_V1
"""

import logging
import json
import yaml
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from copy import deepcopy

logger = logging.getLogger('AutoTuner')


class AutoTuner:
    """
    Sistema de ajuste automático de configurações.
    Monitora o mercado e ajusta parâmetros dos bots dinamicamente.
    """
    
    def __init__(self, exchange_client, config_path: str = "config/bots_config.yaml"):
        self.exchange = exchange_client
        self.config_path = Path(config_path)
        
        # Carrega config base
        self.base_config = self._load_config()
        self.current_config = deepcopy(self.base_config)
        
        # Market analyzer
        from src.ai.market_analyzer import MarketAnalyzer
        self.market_analyzer = MarketAnalyzer(exchange_client)
        
        # 🆕 Modo Oportunista - detecta condições favoráveis
        from src.ai.opportunistic_mode import get_opportunistic_mode
        self.opportunistic_mode = get_opportunistic_mode()
        
        # Estado
        self.running = False
        self.thread = None
        self.last_adjustment = None
        self.adjustment_interval = 300  # 5 minutos
        
        # Histórico de ajustes
        self.adjustment_history = []
        self.max_history = 100
        
        # Arquivo de estado
        self.state_file = Path("data/autotuner_state.json")
        
        # Limites de segurança (nunca ultrapassar)
        self.SAFETY_LIMITS = {
            'rsi_oversold': {'min': 15, 'max': 45},
            'rsi_overbought': {'min': 55, 'max': 85},
            'stop_loss': {'min': -5.0, 'max': -0.2},
            'take_profit': {'min': 0.1, 'max': 5.0},
            'amount_per_trade': {'min': 10, 'max': 250},  # Aumentado para modo agressivo
            'max_positions': {'min': 1, 'max': 5},
        }
        
        # Configurações base por tipo de bot (referência)
        self.BOT_BASE_PARAMS = {
            'bot_estavel': {
                'rsi': {'oversold': 35, 'overbought': 65},
                'risk': {'stop_loss': -0.5, 'take_profit': 0.3},
                'trading': {'amount_per_trade': 50}
            },
            'bot_medio': {
                'rsi': {'oversold': 33, 'overbought': 67},
                'risk': {'stop_loss': -1.0, 'take_profit': 0.7},
                'trading': {'amount_per_trade': 40}
            },
            'bot_volatil': {
                'rsi': {'oversold': 28, 'overbought': 72},
                'risk': {'stop_loss': -1.2, 'take_profit': 1.0},
                'trading': {'amount_per_trade': 25}
            },
            'bot_meme': {
                'rsi': {'oversold': 25, 'overbought': 75},
                'risk': {'stop_loss': -1.5, 'take_profit': 1.5},
                'trading': {'amount_per_trade': 25}
            }
        }
        
        logger.info("🎛️ AutoTuner inicializado")
    
    def _load_config(self) -> dict:
        """Carrega configuração do YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar config: {e}")
            return {}
    
    def _save_config(self, config: dict) -> bool:
        """Salva configuração no YAML"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar config: {e}")
            return False
    
    def start(self):
        """Inicia o auto-tuner em background"""
        if self.running:
            logger.warning("AutoTuner já está rodando")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("🎛️ AutoTuner iniciado em background")
    
    def stop(self):
        """Para o auto-tuner"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("🎛️ AutoTuner parado")
    
    def _run_loop(self):
        """Loop principal do auto-tuner"""
        while self.running:
            try:
                # Analisa mercado e ajusta se necessário
                self.tune()
                
            except Exception as e:
                logger.error(f"Erro no loop do AutoTuner: {e}")
            
            # Aguarda intervalo
            time.sleep(self.adjustment_interval)
    
    def tune(self) -> Dict:
        """
        Analisa mercado e ajusta configurações.
        Inclui Modo Oportunista para situações favoráveis.
        Retorna dict com ajustes feitos.
        """
        # Analisa condições do mercado
        conditions = self.market_analyzer.analyze_sync()
        
        # Obtém ajustes recomendados do market analyzer
        adjustments = self.market_analyzer.get_config_adjustments()
        
        # 🆕 MODO OPORTUNISTA - Calcula score de oportunidade
        opp_score = self._calculate_opportunity_score(conditions)
        opp_level = self.opportunistic_mode.determine_level(opp_score)
        opp_params = self.opportunistic_mode.get_adjusted_params()
        
        # Log do modo oportunista
        if opp_level.multiplier > 1.0:
            logger.info(f"🎯 MODO OPORTUNISTA: {opp_level.emoji} {opp_level.name} (x{opp_level.multiplier})")
            logger.info(f"   Score: {opp_score.total_score}/100")
        
        # Aplica ajustes em cada bot
        changes_made = {}
        
        for bot_type in ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']:
            bot_changes = self._adjust_bot_config(bot_type, conditions, adjustments, opp_params)
            if bot_changes:
                changes_made[bot_type] = bot_changes
        
        # Salva estado
        self._save_state(conditions, changes_made, opp_params)
        
        # Log
        if changes_made:
            logger.info(f"🎛️ Ajustes aplicados em {len(changes_made)} bots")
            for bot, changes in changes_made.items():
                logger.info(f"   {bot}: {changes}")
        
        self.last_adjustment = datetime.now()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'market': {
                'trend': conditions.trend,
                'volatility': conditions.volatility_level,
                'action': conditions.recommended_action
            },
            'opportunistic': {
                'level': opp_level.name,
                'emoji': opp_level.emoji,
                'multiplier': opp_level.multiplier,
                'score': opp_score.total_score
            },
            'changes': changes_made
        }
    
    def _calculate_opportunity_score(self, conditions):
        """Calcula score de oportunidade baseado nas condições de mercado"""
        from src.ai.opportunistic_mode import OpportunityScore
        
        # Obtém dados para o score
        fear_greed = getattr(conditions, 'fear_greed_index', 50)
        avg_rsi = getattr(conditions, 'avg_rsi', 50)
        
        # Conta ativos sobrevendidos (RSI < 30)
        oversold_count = sum(1 for r in getattr(conditions, 'rsi_values', {}).values() if r < 30)
        total_assets = max(len(getattr(conditions, 'rsi_values', {})), 1)
        
        # Volume ratio
        volume_ratio = getattr(conditions, 'volume_ratio', 1.0)
        
        # BTC change
        btc_change = getattr(conditions, 'btc_change_24h', 0)
        
        # Performance recente (pega do estado se existir)
        recent_pnl = self._get_recent_pnl()
        recent_win_rate = self._get_recent_win_rate()
        
        return self.opportunistic_mode.calculate_opportunity_score(
            fear_greed_index=fear_greed,
            avg_rsi=avg_rsi,
            oversold_count=oversold_count,
            total_assets=total_assets,
            volume_ratio=volume_ratio,
            btc_change_24h=btc_change,
            recent_pnl=recent_pnl,
            recent_win_rate=recent_win_rate
        )
    
    def _get_recent_pnl(self) -> float:
        """Obtém PnL dos últimos 7 dias"""
        try:
            stats_file = Path("data/daily_stats.json")
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                    return stats.get('pnl_7d', 0)
        except:
            pass
        return 0
    
    def _get_recent_win_rate(self) -> float:
        """Obtém win rate recente"""
        try:
            stats_file = Path("data/daily_stats.json")
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                    return stats.get('win_rate', 0.5)
        except:
            pass
        return 0.5
    
    def _adjust_bot_config(self, bot_type: str, conditions, adjustments: Dict, opp_params: Dict = None) -> Dict:
        """
        Ajusta configuração de um bot específico.
        Inclui ajustes do Modo Oportunista quando condições favoráveis.
        Retorna dict com mudanças feitas.
        """
        if bot_type not in self.current_config.get('bots', {}):
            return {}
        
        bot_config = self.current_config['bots'][bot_type]
        base_params = self.BOT_BASE_PARAMS.get(bot_type, {})
        changes = {}
        
        # Multiplicadores de ajuste
        multipliers = adjustments.get('multipliers', {})
        
        # 🆕 Multiplicador do Modo Oportunista
        opp_multiplier = opp_params.get('multiplier', 1.0) if opp_params else 1.0
        
        # ==== AJUSTE DE RSI ====
        if 'rsi_buy' in multipliers:
            base_rsi = base_params.get('rsi', {}).get('oversold', 30)
            
            # Aplica ajuste do modo oportunista (RSI mais alto = compra mais cedo)
            opp_rsi_adj = opp_params.get('rsi_oversold', base_rsi) if opp_params else base_rsi
            new_rsi = int(max(base_rsi * multipliers['rsi_buy'], opp_rsi_adj))
            
            new_rsi = self._clamp(new_rsi, 
                                  self.SAFETY_LIMITS['rsi_oversold']['min'],
                                  self.SAFETY_LIMITS['rsi_oversold']['max'])
            
            if new_rsi != bot_config.get('rsi', {}).get('oversold'):
                bot_config.setdefault('rsi', {})['oversold'] = new_rsi
                changes['rsi_oversold'] = new_rsi
        
        # ==== AJUSTE DE STOP LOSS ====
        if 'stop_loss' in multipliers:
            base_sl = base_params.get('risk', {}).get('stop_loss', -1.0)
            
            # 🆕 Modo oportunista pode apertar stop loss (menos perda)
            opp_sl_adj = opp_params.get('stop_loss_pct', base_sl) if opp_params else base_sl
            new_sl = max(base_sl * multipliers['stop_loss'], opp_sl_adj)  # Menos negativo = mais apertado
            
            new_sl = self._clamp(new_sl,
                                 self.SAFETY_LIMITS['stop_loss']['min'],
                                 self.SAFETY_LIMITS['stop_loss']['max'])
            new_sl = round(new_sl, 2)
            
            if new_sl != bot_config.get('risk', {}).get('stop_loss'):
                bot_config.setdefault('risk', {})['stop_loss'] = new_sl
                changes['stop_loss'] = new_sl
        
        # ==== AJUSTE DE TAKE PROFIT ====
        if 'take_profit' in multipliers:
            base_tp = base_params.get('risk', {}).get('take_profit', 0.5)
            
            # 🆕 Modo oportunista pode aumentar take profit
            opp_tp_adj = opp_params.get('take_profit_pct', base_tp) if opp_params else base_tp
            new_tp = max(base_tp * multipliers['take_profit'], opp_tp_adj)
            
            new_tp = self._clamp(new_tp,
                                 self.SAFETY_LIMITS['take_profit']['min'],
                                 self.SAFETY_LIMITS['take_profit']['max'])
            new_tp = round(new_tp, 2)
            
            if new_tp != bot_config.get('risk', {}).get('take_profit'):
                bot_config.setdefault('risk', {})['take_profit'] = new_tp
                changes['take_profit'] = new_tp
        
        # ==== AJUSTE DE TAMANHO DE POSIÇÃO ====
        if 'position_size' in multipliers:
            base_amount = base_params.get('trading', {}).get('amount_per_trade', 50)
            
            # 🆕 Modo oportunista pode aumentar tamanho da posição
            new_amount = base_amount * multipliers['position_size'] * opp_multiplier
            
            # Limita pelo max_position_pct do modo oportunista
            max_pct = opp_params.get('position_pct', 25) if opp_params else 25
            max_amount = (self.current_config.get('global', {}).get('capital', 1000) * max_pct / 100)
            new_amount = min(new_amount, max_amount)
            
            new_amount = self._clamp(new_amount,
                                     self.SAFETY_LIMITS['amount_per_trade']['min'],
                                     self.SAFETY_LIMITS['amount_per_trade']['max'])
            new_amount = round(new_amount, 0)
            
            if new_amount != bot_config.get('trading', {}).get('amount_per_trade'):
                bot_config.setdefault('trading', {})['amount_per_trade'] = new_amount
                changes['amount_per_trade'] = new_amount
                if opp_multiplier > 1.0:
                    changes['opp_boost'] = f"+{int((opp_multiplier-1)*100)}%"
        
        # ==== AJUSTES ESPECÍFICOS POR CONDIÇÃO ====
        
        # Volatilidade extrema -> reduz max_positions
        if conditions.volatility_level == 'extreme':
            current_max = bot_config.get('trading', {}).get('max_positions', 3)
            new_max = max(1, current_max - 1)
            if new_max != current_max:
                bot_config.setdefault('trading', {})['max_positions'] = new_max
                changes['max_positions'] = new_max
        
        # Tendência forte de alta -> pode aumentar max_positions
        if conditions.trend == 'strong_up' and conditions.volatility_level in ['low', 'normal']:
            current_max = bot_config.get('trading', {}).get('max_positions', 3)
            if bot_type == 'bot_estavel' and current_max < 4:
                bot_config.setdefault('trading', {})['max_positions'] = current_max + 1
                changes['max_positions'] = current_max + 1
        
        # Atualiza config
        self.current_config['bots'][bot_type] = bot_config
        
        return changes
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Limita valor entre min e max"""
        return max(min_val, min(max_val, value))
    
    def _save_state(self, conditions, changes: Dict, opp_params: Dict = None):
        """Salva estado atual do tuner incluindo modo oportunista"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'market_conditions': {
                'trend': conditions.trend,
                'trend_strength': conditions.trend_strength,
                'volatility': conditions.volatility,
                'volatility_level': conditions.volatility_level,
                'volume_ratio': conditions.volume_ratio,
                'recommended_action': conditions.recommended_action,
                'btc_price': conditions.btc_price,
                'btc_change_24h': conditions.btc_change_24h
            },
            'opportunistic_mode': {
                'level': opp_params.get('level', 'CONSERVADOR') if opp_params else 'CONSERVADOR',
                'emoji': opp_params.get('emoji', '🟢') if opp_params else '🟢',
                'multiplier': opp_params.get('multiplier', 1.0) if opp_params else 1.0,
                'score': opp_params.get('score', 0) if opp_params else 0,
                'position_pct': opp_params.get('position_pct', 15) if opp_params else 15,
            },
            'last_changes': changes,
            'adjustment_count': len(self.adjustment_history) + 1
        }
        
        # Adiciona ao histórico
        self.adjustment_history.append(state)
        if len(self.adjustment_history) > self.max_history:
            self.adjustment_history = self.adjustment_history[-self.max_history:]
        
        # Salva em arquivo
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({
                    'current': state,
                    'history': self.adjustment_history[-10:]  # Últimos 10
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Erro ao salvar estado: {e}")
    
    def get_current_adjustments(self, bot_type: str) -> Dict:
        """
        Retorna os ajustes atuais para um bot.
        Usado pela estratégia para aplicar os ajustes em tempo real.
        """
        if bot_type not in self.current_config.get('bots', {}):
            return {}
        
        return self.current_config['bots'][bot_type]
    
    def get_status(self) -> Dict:
        """Retorna status do auto-tuner incluindo modo oportunista"""
        conditions = self.market_analyzer.current_conditions
        opp_level = self.opportunistic_mode.current_level
        opp_score = self.opportunistic_mode.current_score
        
        return {
            'running': self.running,
            'last_adjustment': self.last_adjustment.isoformat() if self.last_adjustment else None,
            'adjustment_interval': self.adjustment_interval,
            'total_adjustments': len(self.adjustment_history),
            'market': {
                'trend': conditions.trend if conditions else 'unknown',
                'volatility': conditions.volatility_level if conditions else 'unknown',
                'action': conditions.recommended_action if conditions else 'hold'
            } if conditions else {},
            'opportunistic_mode': {
                'enabled': self.opportunistic_mode.is_enabled(),
                'level': opp_level.name,
                'emoji': opp_level.emoji,
                'multiplier': opp_level.multiplier,
                'score': opp_score.total_score,
                'score_breakdown': {
                    'fear_greed': opp_score.fear_greed_score,
                    'rsi': opp_score.rsi_score,
                    'volume': opp_score.volume_score,
                    'btc_trend': opp_score.btc_trend_score,
                    'performance': opp_score.performance_score
                }
            }
        }
    
    def get_opportunistic_report(self) -> str:
        """Retorna relatório do modo oportunista"""
        return self.opportunistic_mode.get_status_report()
    
    def get_market_report(self) -> str:
        """Retorna relatório formatado do mercado"""
        return self.market_analyzer.get_status_report()
    
    def force_tune(self) -> Dict:
        """Força um ajuste imediato"""
        return self.tune()


# Singleton
_autotuner_instance = None

def get_autotuner(exchange_client=None, config_path: str = None) -> AutoTuner:
    """Retorna instância singleton do AutoTuner"""
    global _autotuner_instance
    
    if _autotuner_instance is None:
        if exchange_client is None:
            raise ValueError("Primeira chamada requer exchange_client")
        _autotuner_instance = AutoTuner(exchange_client, config_path or "config/bots_config.yaml")
    
    return _autotuner_instance


def reset_autotuner():
    """Reseta a instância singleton"""
    global _autotuner_instance
    if _autotuner_instance:
        _autotuner_instance.stop()
    _autotuner_instance = None
