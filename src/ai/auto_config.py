# -*- coding: utf-8 -*-
"""
App Leonardo v3.0 - Auto Config
===============================

Sistema de ajuste automático de configurações dos bots.
Usa os insights da AI e do Market Scanner para modificar
parâmetros dos bots dinamicamente.

Features:
- Ajuste de stop loss/take profit baseado em volatilidade
- Modificação de RSI thresholds baseado em aprendizado
- Ajuste de max_positions baseado em risco de mercado
- Modo conservador/agressivo automático
- Histórico de mudanças para análise
"""

import os
import json
import yaml
import logging
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from copy import deepcopy

logger = logging.getLogger('AutoConfig')


class AutoConfig:
    """
    Gerenciador de configuração automática dos bots.
    
    Funcionalidades:
    - Carrega e salva configurações YAML
    - Aplica ajustes sugeridos pela AI
    - Mantém histórico de mudanças
    - Permite rollback de configurações
    - Respeita limites de segurança
    """
    
    # ============================================
    # LIMITES DE SEGURANCA ABSOLUTOS - IA NAO PODE ULTRAPASSAR
    # ============================================
    SAFETY_LIMITS = {
        # Stop Loss - OBRIGATORIO ter stop loss
        'stop_loss_min': 0.5,   # Minimo 0.5% stop loss
        'stop_loss_max': 5.0,   # Maximo 5% stop loss (reduzido de 10%)
        
        # Take Profit
        'take_profit_min': 0.3, # Minimo 0.3% take profit
        'take_profit_max': 5.0, # Maximo 5% take profit (reduzido de 15%)
        
        # RSI - Limites de compra/venda
        'rsi_buy_min': 20,      # RSI minimo para compra (nao comprar em RSI < 20)
        'rsi_buy_max': 40,      # RSI maximo para compra (nao comprar em RSI > 40)
        'rsi_sell_min': 60,     # RSI minimo para venda
        'rsi_sell_max': 80,     # RSI maximo para venda
        
        # Posicoes
        'max_positions_min': 1,  # Minimo 1 posicao
        'max_positions_max': 5,  # Maximo 5 posicoes por bot (reduzido de 10)
        
        # Tamanho de ordem
        'order_size_min': 10,    # Minimo $10 por ordem
        'order_size_max': 100,   # Maximo $100 por ordem (para capital de $1000)
        
        # LIMITES DE AJUSTE DA IA
        'max_adjustment_per_cycle': 10.0,   # IA so pode ajustar 10% por ciclo
        'max_adjustments_per_day': 5,       # Max 5 ajustes por dia
        'require_min_trades_for_learning': 20,  # Minimo 20 trades para IA aprender
        'min_confidence_for_adjustment': 0.7,   # 70% confianca minima
    }
    
    # Perfis de risco predefinidos - MAIS CONSERVADORES
    RISK_PROFILES = {
        'ultra_conservative': {
            'stop_loss_mult': 0.5,
            'take_profit_mult': 0.5,
            'max_positions_mult': 0.3,
            'order_size_mult': 0.3
        },
        'conservative': {
            'stop_loss_mult': 0.7,
            'take_profit_mult': 0.7,
            'max_positions_mult': 0.5,
            'order_size_mult': 0.5
        },
        'normal': {
            'stop_loss_mult': 1.0,
            'take_profit_mult': 1.0,
            'max_positions_mult': 1.0,
            'order_size_mult': 1.0
        },
        'aggressive': {
            'stop_loss_mult': 1.2,  # Reduzido de 1.3
            'take_profit_mult': 1.2,
            'max_positions_mult': 1.0,  # Nao aumenta posicoes
            'order_size_mult': 1.0      # Nao aumenta tamanho
        },
        'ultra_aggressive': {
            'stop_loss_mult': 1.3,  # Reduzido de 1.5
            'take_profit_mult': 1.3,
            'max_positions_mult': 1.0,  # Nao aumenta posicoes
            'order_size_mult': 1.0      # Nao aumenta tamanho
        }
    }
    
    def __init__(self, config_path: str = "config/bots_config.yaml", data_dir: str = "data"):
        self.config_path = config_path
        self.data_dir = data_dir
        self.config_history_dir = os.path.join(data_dir, "config_history")
        os.makedirs(self.config_history_dir, exist_ok=True)
        
        # Contador de ajustes diarios
        self.daily_adjustments = 0
        self.last_adjustment_date = None
        
        # Configuracao atual
        self.current_config = {}
        self.original_config = {}
        
        # Histórico de mudanças
        self.changes_history = []
        self._load_changes_history()
        
        # Modo atual
        self.current_mode = 'normal'
        
        # Histórico de edições manuais do usuário
        self.manual_edits = {}
        self._load_manual_edits()
        
        # Carregar configuração
        self._load_config()
    
    def _load_manual_edits(self):
        """Carrega histórico de edições manuais"""
        try:
            edits_file = os.path.join(self.config_history_dir, "manual_edits.json")
            if os.path.exists(edits_file):
                with open(edits_file, 'r') as f:
                    self.manual_edits = json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar edições manuais: {e}")
    
    def _save_manual_edits(self):
        """Salva histórico de edições manuais"""
        try:
            edits_file = os.path.join(self.config_history_dir, "manual_edits.json")
            with open(edits_file, 'w') as f:
                json.dump(self.manual_edits, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Erro ao salvar edições manuais: {e}")
    
    def _get_user_control_settings(self) -> Dict:
        """Retorna configurações de controle do usuário"""
        return self.current_config.get('user_control', {
            'locked_params': ['stop_loss', 'take_profit', 'amount_per_trade', 'max_positions'],
            'ai_permissions': {
                'can_adjust_rsi': True,
                'can_adjust_trailing': True,
                'can_adjust_urgency': True,
                'can_enable_disable_bots': False,
                'can_change_portfolio': False,
                'can_use_poupanca': False,
                'can_change_timeframe': False
            },
            'ai_adjustment_limits': {
                'rsi_max_change': 5,
                'trailing_max_change': 0.2,
                'urgency_max_change': 0.3
            },
            'manual_override_enabled': True,
            'override_cooldown_hours': 24,
            'notify_user_on_ai_change': True,
            'require_approval': False
        })
    
    def _is_param_locked(self, param: str) -> bool:
        """Verifica se um parâmetro está bloqueado para a IA"""
        user_control = self._get_user_control_settings()
        locked = user_control.get('locked_params', [])
        
        # Verifica se o parâmetro está na lista de bloqueados
        for locked_param in locked:
            if locked_param in param:
                return True
        return False
    
    def _is_param_in_cooldown(self, bot_name: str, param: str) -> bool:
        """Verifica se um parâmetro está em cooldown (editado recentemente pelo usuário)"""
        user_control = self._get_user_control_settings()
        
        if not user_control.get('manual_override_enabled', True):
            return False
        
        cooldown_hours = user_control.get('override_cooldown_hours', 24)
        key = f"{bot_name}.{param}"
        
        if key in self.manual_edits:
            last_edit = datetime.fromisoformat(self.manual_edits[key])
            elapsed = (datetime.now() - last_edit).total_seconds() / 3600
            if elapsed < cooldown_hours:
                logger.info(f"⏳ Parâmetro {key} em cooldown ({elapsed:.1f}h de {cooldown_hours}h)")
                return True
        
        return False
    
    def _has_ai_permission(self, action: str) -> bool:
        """Verifica se a IA tem permissão para uma ação"""
        user_control = self._get_user_control_settings()
        permissions = user_control.get('ai_permissions', {})
        return permissions.get(action, False)
    
    def _get_ai_adjustment_limit(self, param_type: str) -> float:
        """Retorna o limite de ajuste da IA para um tipo de parâmetro"""
        user_control = self._get_user_control_settings()
        limits = user_control.get('ai_adjustment_limits', {})
        
        if 'rsi' in param_type.lower():
            return limits.get('rsi_max_change', 5)
        elif 'trailing' in param_type.lower():
            return limits.get('trailing_max_change', 0.2)
        elif 'urgency' in param_type.lower():
            return limits.get('urgency_max_change', 0.3)
        
        return 0  # Sem limite definido = não pode alterar
    
    def can_ai_modify_param(self, bot_name: str, param: str, source: str = 'ai') -> tuple:
        """
        Verifica se a IA pode modificar um parâmetro.
        
        Returns:
            (can_modify: bool, reason: str)
        """
        # Se é edição manual, sempre pode
        if source == 'manual':
            return True, "Edição manual sempre permitida"
        
        # Verificar se está bloqueado
        if self._is_param_locked(param):
            return False, f"Parâmetro '{param}' bloqueado pelo usuário"
        
        # Verificar cooldown
        if self._is_param_in_cooldown(bot_name, param):
            return False, f"Parâmetro em cooldown após edição manual"
        
        # Verificar permissões específicas
        if 'rsi' in param.lower() and not self._has_ai_permission('can_adjust_rsi'):
            return False, "IA não tem permissão para ajustar RSI"
        
        if 'trailing' in param.lower() and not self._has_ai_permission('can_adjust_trailing'):
            return False, "IA não tem permissão para ajustar trailing"
        
        if 'urgency' in param.lower() and not self._has_ai_permission('can_adjust_urgency'):
            return False, "IA não tem permissão para ajustar urgência"
        
        if 'enabled' in param.lower() and not self._has_ai_permission('can_enable_disable_bots'):
            return False, "IA não tem permissão para habilitar/desabilitar bots"
        
        if 'portfolio' in param.lower() and not self._has_ai_permission('can_change_portfolio'):
            return False, "IA não tem permissão para mudar portfolio"
        
        if 'timeframe' in param.lower() and not self._has_ai_permission('can_change_timeframe'):
            return False, "IA não tem permissão para mudar timeframe"
        
        return True, "Permitido"
    
    def register_manual_edit(self, bot_name: str, param: str):
        """Registra uma edição manual do usuário"""
        key = f"{bot_name}.{param}"
        self.manual_edits[key] = datetime.now().isoformat()
        self._save_manual_edits()
        logger.info(f"📝 Edição manual registrada: {key}")
    
    def _load_config(self):
        """Carrega configuração atual do arquivo YAML"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.current_config = yaml.safe_load(f)
                    self.original_config = deepcopy(self.current_config)
                logger.info(f"✅ Configuração carregada de {self.config_path}")
            else:
                logger.warning(f"⚠️ Arquivo de configuração não encontrado: {self.config_path}")
                self.current_config = self._get_default_config()
        except Exception as e:
            logger.error(f"❌ Erro ao carregar configuração: {e}")
            self.current_config = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Retorna configuração padrão"""
        return {
            'global': {
                'order_size': 50,
                'stop_loss': 2.5,
                'take_profit': 2.0,
                'rsi_buy': 35,
                'rsi_sell': 65
            },
            'bots': {
                'bot_estavel': {
                    'name': 'Bot Estavel',
                    'enabled': True,
                    'order_size': 50,
                    'stop_loss': 2.0,
                    'take_profit': 1.5,
                    'max_positions': 6,
                    'rsi_buy': 30,
                    'rsi_sell': 70
                },
                'bot_medio': {
                    'name': 'Bot Medio',
                    'enabled': True,
                    'order_size': 40,
                    'stop_loss': 2.5,
                    'take_profit': 2.0,
                    'max_positions': 7,
                    'rsi_buy': 35,
                    'rsi_sell': 65
                },
                'bot_volatil': {
                    'name': 'Bot Volatil',
                    'enabled': True,
                    'order_size': 30,
                    'stop_loss': 3.0,
                    'take_profit': 2.5,
                    'max_positions': 5,
                    'rsi_buy': 40,
                    'rsi_sell': 60
                },
                'bot_meme': {
                    'name': 'Bot Meme',
                    'enabled': True,
                    'order_size': 20,
                    'stop_loss': 5.0,
                    'take_profit': 4.0,
                    'max_positions': 3,
                    'rsi_buy': 35,
                    'rsi_sell': 65
                }
            }
        }
    
    def _save_config(self, config: Dict = None, reason: str = ""):
        """Salva configuração no arquivo YAML"""
        if config is None:
            config = self.current_config
        
        try:
            # Backup antes de salvar
            self._create_backup()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"💾 Configuração salva: {reason}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao salvar configuração: {e}")
            return False
    
    def _create_backup(self):
        """Cria backup da configuração atual"""
        try:
            if os.path.exists(self.config_path):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = os.path.join(
                    self.config_history_dir,
                    f"config_backup_{timestamp}.yaml"
                )
                shutil.copy(self.config_path, backup_path)
                
                # Manter apenas últimos 50 backups
                self._cleanup_old_backups()
        except Exception as e:
            logger.warning(f"⚠️ Erro ao criar backup: {e}")
    
    def _cleanup_old_backups(self, keep: int = 50):
        """Remove backups antigos"""
        try:
            backups = sorted([
                f for f in os.listdir(self.config_history_dir)
                if f.startswith('config_backup_') and f.endswith('.yaml')
            ])
            
            for old_backup in backups[:-keep]:
                os.remove(os.path.join(self.config_history_dir, old_backup))
        except Exception as e:
            logger.warning(f"⚠️ Erro ao limpar backups: {e}")
    
    def _load_changes_history(self):
        """Carrega histórico de mudanças"""
        try:
            history_file = os.path.join(self.config_history_dir, "changes_history.json")
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.changes_history = json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar histórico: {e}")
    
    def _save_changes_history(self):
        """Salva histórico de mudanças"""
        try:
            history_file = os.path.join(self.config_history_dir, "changes_history.json")
            # Manter apenas últimas 500 mudanças
            self.changes_history = self.changes_history[-500:]
            with open(history_file, 'w') as f:
                json.dump(self.changes_history, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Erro ao salvar histórico: {e}")
    
    def _record_change(self, bot_name: str, param: str, old_value: Any, 
                       new_value: Any, reason: str, source: str):
        """Registra uma mudança no histórico"""
        change = {
            'timestamp': datetime.now().isoformat(),
            'bot': bot_name,
            'parameter': param,
            'old_value': old_value,
            'new_value': new_value,
            'reason': reason,
            'source': source
        }
        self.changes_history.append(change)
        self._save_changes_history()
    
    def _apply_safety_limits(self, param: str, value: float) -> float:
        """Aplica limites de segurança a um valor"""
        if 'stop_loss' in param:
            return max(self.SAFETY_LIMITS['stop_loss_min'],
                      min(self.SAFETY_LIMITS['stop_loss_max'], value))
        elif 'take_profit' in param:
            return max(self.SAFETY_LIMITS['take_profit_min'],
                      min(self.SAFETY_LIMITS['take_profit_max'], value))
        elif 'rsi_buy' in param:
            return max(self.SAFETY_LIMITS['rsi_buy_min'],
                      min(self.SAFETY_LIMITS['rsi_buy_max'], int(value)))
        elif 'rsi_sell' in param:
            return max(self.SAFETY_LIMITS['rsi_sell_min'],
                      min(self.SAFETY_LIMITS['rsi_sell_max'], int(value)))
        elif 'max_positions' in param:
            return max(self.SAFETY_LIMITS['max_positions_min'],
                      min(self.SAFETY_LIMITS['max_positions_max'], int(value)))
        elif 'order_size' in param:
            return max(self.SAFETY_LIMITS['order_size_min'],
                      min(self.SAFETY_LIMITS['order_size_max'], value))
        return value
    
    def get_bot_config(self, bot_name: str) -> Dict:
        """Retorna configuração de um bot específico"""
        bots = self.current_config.get('bots', {})
        return bots.get(bot_name, {})
    
    def get_all_configs(self) -> Dict:
        """Retorna todas as configurações"""
        return deepcopy(self.current_config)
    
    def update_bot_param(self, bot_name: str, param: str, value: Any, 
                         reason: str = "", source: str = "manual") -> bool:
        """
        Atualiza um parâmetro de um bot.
        
        Args:
            bot_name: Nome do bot (ex: bot_estavel)
            param: Nome do parâmetro (ex: stop_loss)
            value: Novo valor
            reason: Razão da mudança
            source: Fonte da mudança (manual, ai, market_scanner, market_adjustment)
            
        Returns:
            True se sucesso
        """
        # ===== VERIFICAR PERMISSÕES DO USUÁRIO =====
        can_modify, deny_reason = self.can_ai_modify_param(bot_name, param, source)
        
        if not can_modify:
            logger.warning(f"🚫 [{source}] Não pode modificar {bot_name}.{param}: {deny_reason}")
            return False
        
        if 'bots' not in self.current_config:
            self.current_config['bots'] = {}
        
        if bot_name not in self.current_config['bots']:
            logger.warning(f"⚠️ Bot {bot_name} não encontrado na configuração")
            return False
        
        old_value = self.current_config['bots'][bot_name].get(param)
        
        # ===== VERIFICAR LIMITES DE AJUSTE DA IA =====
        if source != 'manual' and old_value is not None:
            max_change = self._get_ai_adjustment_limit(param)
            if max_change > 0:
                actual_change = abs(float(value) - float(old_value))
                if actual_change > max_change:
                    # Limitar a mudança ao máximo permitido
                    direction = 1 if value > old_value else -1
                    value = old_value + (max_change * direction)
                    logger.info(f"⚠️ Mudança limitada pela IA: máximo ±{max_change}")
        
        # Aplicar limites de segurança
        safe_value = self._apply_safety_limits(param, value)
        
        if safe_value != value:
            logger.info(f"⚠️ Valor ajustado por segurança: {value} -> {safe_value}")
        
        # Atualizar
        self.current_config['bots'][bot_name][param] = safe_value
        
        # Registrar mudança
        self._record_change(bot_name, param, old_value, safe_value, reason, source)
        
        # Se é edição manual, registrar para cooldown
        if source == 'manual':
            self.register_manual_edit(bot_name, param)
        
        # Notificar usuário se configurado
        if source != 'manual':
            user_control = self._get_user_control_settings()
            if user_control.get('notify_user_on_ai_change', True):
                logger.info(f"🔔 [IA] Alterou {bot_name}.{param}: {old_value} -> {safe_value}")
        
        # Salvar
        self._save_config(reason=f"Update {bot_name}.{param}")
        
        logger.info(f"✅ [{bot_name}] {param}: {old_value} -> {safe_value} ({reason})")
        return True
    
    def apply_market_adjustment(self, market_regime: str, fear_greed: int = 50) -> Dict:
        """
        Aplica ajustes baseados nas condições de mercado.
        
        Args:
            market_regime: 'bullish', 'bearish', 'volatile', 'sideways'
            fear_greed: Índice Fear & Greed (0-100)
            
        Returns:
            Dict com mudanças aplicadas
        """
        changes = {'bots': {}, 'reason': '', 'mode': 'normal'}
        
        # Determinar perfil baseado em mercado
        if market_regime == 'volatile' or fear_greed <= 20 or fear_greed >= 80:
            profile = 'conservative'
            changes['reason'] = 'Mercado volátil/extremo - modo conservador'
        elif market_regime == 'bearish' or fear_greed <= 35:
            profile = 'conservative'
            changes['reason'] = 'Bear market - modo conservador'
        elif market_regime == 'bullish' and 45 <= fear_greed <= 70:
            profile = 'aggressive'
            changes['reason'] = 'Bull market saudável - modo agressivo'
        else:
            profile = 'normal'
            changes['reason'] = 'Mercado neutro - modo normal'
        
        changes['mode'] = profile
        multipliers = self.RISK_PROFILES[profile]
        
        # Aplicar a todos os bots
        for bot_name, bot_config in self.current_config.get('bots', {}).items():
            changes['bots'][bot_name] = {}
            
            # Buscar valores originais (ou usar atual se não tiver original)
            original = self.original_config.get('bots', {}).get(bot_name, bot_config)
            
            # Stop Loss
            if 'stop_loss' in original:
                new_sl = original['stop_loss'] * multipliers['stop_loss_mult']
                new_sl = self._apply_safety_limits('stop_loss', new_sl)
                if new_sl != bot_config.get('stop_loss'):
                    self.update_bot_param(bot_name, 'stop_loss', new_sl,
                                         changes['reason'], 'market_adjustment')
                    changes['bots'][bot_name]['stop_loss'] = new_sl
            
            # Take Profit
            if 'take_profit' in original:
                new_tp = original['take_profit'] * multipliers['take_profit_mult']
                new_tp = self._apply_safety_limits('take_profit', new_tp)
                if new_tp != bot_config.get('take_profit'):
                    self.update_bot_param(bot_name, 'take_profit', new_tp,
                                         changes['reason'], 'market_adjustment')
                    changes['bots'][bot_name]['take_profit'] = new_tp
            
            # Max Positions
            if 'max_positions' in original:
                new_max = int(original['max_positions'] * multipliers['max_positions_mult'])
                new_max = self._apply_safety_limits('max_positions', new_max)
                if new_max != bot_config.get('max_positions'):
                    self.update_bot_param(bot_name, 'max_positions', new_max,
                                         changes['reason'], 'market_adjustment')
                    changes['bots'][bot_name]['max_positions'] = new_max
        
        self.current_mode = profile
        logger.info(f"🔧 Ajuste de mercado aplicado: {changes['reason']}")
        return changes
    
    def apply_ai_recommendations(self, recommendations: Dict) -> Dict:
        """
        Aplica recomendações da AI adaptativa.
        
        Args:
            recommendations: Dict de recomendações da AdaptiveEngine
            
        Returns:
            Dict com mudanças aplicadas
        """
        changes = {'applied': [], 'skipped': []}
        
        for adjustment in recommendations.get('adjustments', []):
            param = adjustment.get('param')
            suggested = adjustment.get('suggested')
            reason = adjustment.get('reason', 'Recomendação da AI')
            bot_name = adjustment.get('bot', 'global')
            
            if not param or suggested is None:
                changes['skipped'].append(adjustment)
                continue
            
            # Aplicar para bot específico ou global
            if bot_name == 'global':
                for bn in self.current_config.get('bots', {}).keys():
                    success = self.update_bot_param(bn, param, suggested, reason, 'ai')
                    if success:
                        changes['applied'].append({
                            'bot': bn, 'param': param, 
                            'value': suggested, 'reason': reason
                        })
            else:
                success = self.update_bot_param(bot_name, param, suggested, reason, 'ai')
                if success:
                    changes['applied'].append({
                        'bot': bot_name, 'param': param,
                        'value': suggested, 'reason': reason
                    })
        
        if changes['applied']:
            logger.info(f"🤖 AI aplicou {len(changes['applied'])} ajustes")
        
        return changes
    
    def set_risk_profile(self, profile: str, bots: List[str] = None) -> Dict:
        """
        Define um perfil de risco para os bots.
        
        Args:
            profile: Nome do perfil (ultra_conservative, conservative, normal, aggressive, ultra_aggressive)
            bots: Lista de bots (None = todos)
            
        Returns:
            Dict com mudanças aplicadas
        """
        if profile not in self.RISK_PROFILES:
            logger.error(f"❌ Perfil desconhecido: {profile}")
            return {'error': f'Perfil {profile} não existe'}
        
        multipliers = self.RISK_PROFILES[profile]
        changes = {'profile': profile, 'bots': {}}
        
        target_bots = bots or list(self.current_config.get('bots', {}).keys())
        
        for bot_name in target_bots:
            if bot_name not in self.current_config.get('bots', {}):
                continue
            
            original = self.original_config.get('bots', {}).get(bot_name, {})
            changes['bots'][bot_name] = {}
            
            for param, mult_key in [
                ('stop_loss', 'stop_loss_mult'),
                ('take_profit', 'take_profit_mult'),
                ('max_positions', 'max_positions_mult'),
                ('order_size', 'order_size_mult')
            ]:
                if param in original:
                    new_value = original[param] * multipliers[mult_key]
                    if param == 'max_positions':
                        new_value = int(new_value)
                    new_value = self._apply_safety_limits(param, new_value)
                    
                    self.update_bot_param(bot_name, param, new_value,
                                         f'Perfil: {profile}', 'risk_profile')
                    changes['bots'][bot_name][param] = new_value
        
        self.current_mode = profile
        logger.info(f"🎚️ Perfil de risco definido: {profile}")
        return changes
    
    def reset_to_original(self, bot_name: str = None) -> bool:
        """
        Restaura configurações originais.
        
        Args:
            bot_name: Nome do bot (None = todos)
            
        Returns:
            True se sucesso
        """
        try:
            if bot_name:
                if bot_name in self.original_config.get('bots', {}):
                    self.current_config['bots'][bot_name] = deepcopy(
                        self.original_config['bots'][bot_name]
                    )
                    self._record_change(bot_name, 'all', 'modified', 'original',
                                       'Reset to original', 'manual')
            else:
                self.current_config = deepcopy(self.original_config)
                for bn in self.current_config.get('bots', {}).keys():
                    self._record_change(bn, 'all', 'modified', 'original',
                                       'Reset all to original', 'manual')
            
            self._save_config(reason='Reset to original')
            self.current_mode = 'normal'
            logger.info(f"↩️ Configurações restauradas para original")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar: {e}")
            return False
    
    def get_changes_summary(self, hours: int = 24) -> Dict:
        """
        Retorna resumo de mudanças nas últimas N horas.
        
        Args:
            hours: Número de horas para filtrar
            
        Returns:
            Dict com resumo das mudanças
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_changes = [
            c for c in self.changes_history
            if datetime.fromisoformat(c['timestamp']) > cutoff
        ]
        
        summary = {
            'total_changes': len(recent_changes),
            'by_bot': {},
            'by_source': {},
            'by_param': {},
            'recent': recent_changes[-10:]  # Últimas 10
        }
        
        for change in recent_changes:
            bot = change['bot']
            source = change['source']
            param = change['parameter']
            
            summary['by_bot'][bot] = summary['by_bot'].get(bot, 0) + 1
            summary['by_source'][source] = summary['by_source'].get(source, 0) + 1
            summary['by_param'][param] = summary['by_param'].get(param, 0) + 1
        
        return summary
    
    def get_current_mode(self) -> Dict:
        """Retorna modo atual e configurações resumidas"""
        return {
            'mode': self.current_mode,
            'profile': self.RISK_PROFILES.get(self.current_mode, {}),
            'bots_count': len(self.current_config.get('bots', {})),
            'safety_limits': self.SAFETY_LIMITS
        }
    
    def suggest_optimizations(self, trade_history: List[Dict]) -> List[Dict]:
        """
        Sugere otimizações baseadas no histórico de trades.
        
        Args:
            trade_history: Lista de trades recentes
            
        Returns:
            Lista de sugestões
        """
        suggestions = []
        
        if len(trade_history) < 10:
            return [{'type': 'info', 'message': 'Dados insuficientes para sugestões'}]
        
        # Analisar por bot
        bot_stats = {}
        for trade in trade_history:
            bot = trade.get('bot_name', trade.get('bot', 'unknown'))
            pnl = trade.get('pnl', trade.get('profit_loss', 0))
            
            if isinstance(pnl, str):
                try:
                    pnl = float(pnl.replace('$', '').replace(',', ''))
                except:
                    pnl = 0
            
            if bot not in bot_stats:
                bot_stats[bot] = {'wins': 0, 'losses': 0, 'total_pnl': 0, 'stop_hits': 0}
            
            if pnl > 0:
                bot_stats[bot]['wins'] += 1
            else:
                bot_stats[bot]['losses'] += 1
                # Verificar se foi stop loss
                reason = trade.get('sell_reason', trade.get('reason', ''))
                if 'STOP' in str(reason).upper():
                    bot_stats[bot]['stop_hits'] += 1
            
            bot_stats[bot]['total_pnl'] += pnl
        
        # Gerar sugestões
        for bot, stats in bot_stats.items():
            total = stats['wins'] + stats['losses']
            if total == 0:
                continue
            
            win_rate = stats['wins'] / total
            stop_rate = stats['stop_hits'] / total if total > 0 else 0
            
            # Stop loss muito apertado?
            if stop_rate > 0.3:
                suggestions.append({
                    'type': 'adjustment',
                    'bot': bot,
                    'param': 'stop_loss',
                    'action': 'increase',
                    'reason': f'Stop loss atingido em {stop_rate:.0%} dos trades',
                    'priority': 'high'
                })
            
            # Win rate baixo?
            if win_rate < 0.5 and total >= 5:
                suggestions.append({
                    'type': 'adjustment',
                    'bot': bot,
                    'param': 'rsi_buy',
                    'action': 'decrease',
                    'reason': f'Win rate baixo ({win_rate:.0%}), comprar em RSI mais baixo',
                    'priority': 'medium'
                })
            
            # PnL muito negativo?
            if stats['total_pnl'] < -20 and total >= 3:
                suggestions.append({
                    'type': 'risk',
                    'bot': bot,
                    'action': 'reduce_positions',
                    'reason': f'PnL negativo (${stats["total_pnl"]:.2f}), reduzir exposição',
                    'priority': 'high'
                })
        
        return suggestions


# Teste standalone
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    auto_config = AutoConfig()
    
    print("\n📋 Configuração atual:")
    config = auto_config.get_all_configs()
    for bot_name, bot_config in config.get('bots', {}).items():
        print(f"\n  {bot_name}:")
        print(f"    Stop Loss: {bot_config.get('stop_loss')}%")
        print(f"    Take Profit: {bot_config.get('take_profit')}%")
        print(f"    Max Positions: {bot_config.get('max_positions')}")
    
    print(f"\n🎚️ Modo atual: {auto_config.get_current_mode()}")
    
    # Testar ajuste de mercado
    print("\n🔧 Aplicando ajuste de mercado (bearish, F&G=25)...")
    changes = auto_config.apply_market_adjustment('bearish', fear_greed=25)
    print(f"  Razão: {changes['reason']}")
    print(f"  Modo: {changes['mode']}")
    
    # Testar reset
    print("\n↩️ Resetando para original...")
    auto_config.reset_to_original()
    
    print(f"\n📊 Resumo de mudanças (24h): {auto_config.get_changes_summary()}")
