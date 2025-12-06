# -*- coding: utf-8 -*-
"""
R7_V1 - Sistema de Banco de Dados
=============================================

Banco de dados robusto para persistência completa do sistema.
"""

from .db_manager import DatabaseManager, get_db_manager
from .models import Trade, BotState, AILearning, MarketData, Backup, DailyStats
from .backup_service import BackupService, get_backup_service

__all__ = [
    'DatabaseManager',
    'get_db_manager',
    'Trade',
    'BotState', 
    'AILearning',
    'MarketData',
    'Backup',
    'DailyStats',
    'BackupService',
    'get_backup_service'
]
