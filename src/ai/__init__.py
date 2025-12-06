# -*- coding: utf-8 -*-
"""
R7_V1 - Módulo de Inteligência Artificial
=========================================

Sistema de IA adaptativa que aprende com os erros e acertos,
busca informações de mercado e ajusta os bots dinamicamente.

Módulos:
- adaptive_engine: Motor de ML que aprende com histórico de trades
- market_scanner: Scanner de notícias e sentimento de mercado
- auto_config: Ajuste automático de configurações dos bots
- ai_manager: Gerenciador central que integra todos os módulos
- ai_persistence: Backup e persistência do aprendizado
- market_analyzer: Análise de mercado em tempo real
- dynamic_config: Configurador dinâmico de parâmetros
- auto_tuner: Auto-ajuste baseado em condições de mercado
- goal_monitor: Monitor de metas mensais ($20-$40)
- opportunistic_mode: 🆕 Detecta condições favoráveis e aumenta agressividade
"""

from .adaptive_engine import AdaptiveEngine
from .market_scanner import MarketScanner
from .auto_config import AutoConfig
from .ai_manager import AIManager, get_ai_manager
from .ai_persistence import AIPersistence, get_ai_persistence
from .market_analyzer import MarketAnalyzer, MarketConditions
from .dynamic_config import DynamicConfigManager, get_dynamic_config_manager, MarketRegime
from .auto_tuner import AutoTuner, get_autotuner
from .goal_monitor import GoalMonitor, get_goal_monitor
from .opportunistic_mode import OpportunisticMode, get_opportunistic_mode, OpportunityScore, AggressivenessLevel

__all__ = [
    'AdaptiveEngine', 
    'MarketScanner', 
    'AutoConfig', 
    'AIManager', 
    'get_ai_manager',
    'AIPersistence',
    'get_ai_persistence',
    # Módulos de auto-ajuste
    'MarketAnalyzer',
    'MarketConditions',
    'DynamicConfigManager',
    'get_dynamic_config_manager',
    'MarketRegime',
    'AutoTuner',
    'get_autotuner',
    # Monitor de metas
    'GoalMonitor',
    'get_goal_monitor',
    # 🆕 Modo Oportunista
    'OpportunisticMode',
    'get_opportunistic_mode',
    'OpportunityScore',
    'AggressivenessLevel',
]
