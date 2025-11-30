"""Módulo de Estratégias"""
from .scalping_strategy import ScalpingStrategy
from .adaptive_strategy import AdaptiveStrategy

# Smart Strategy - Estratégia principal com RSI adaptativo e lógica de segurar até virar tendência
try:
    from .smart_strategy import SmartStrategy
    __all__ = ['ScalpingStrategy', 'AdaptiveStrategy', 'SmartStrategy']
except ImportError:
    __all__ = ['ScalpingStrategy', 'AdaptiveStrategy']
