"""
Session Manager - Gerencia st.session_state para evitar carregamentos repetidos
"""

import streamlit as st
from typing import Any, Optional
from .data_loaders import (
    load_bots_config,
    load_positions,
    load_trade_history,
    load_dashboard_balances,
    load_ai_data,
    load_watchlist_alerts,
    load_config_changes,
    load_autotuner_state,
    load_unico_bot_config
)


def init_session_state():
    """Inicializa session_state com todos os dados necessários"""
    
    # Config dos bots
    if 'config' not in st.session_state or st.session_state.get('force_reload_config', False):
        st.session_state.config = load_bots_config()
        st.session_state.force_reload_config = False
    
    # Posições abertas
    if 'positions' not in st.session_state or st.session_state.get('force_reload_positions', False):
        st.session_state.positions = load_positions()
        st.session_state.force_reload_positions = False
    
    # Histórico de trades
    if 'history' not in st.session_state or st.session_state.get('force_reload_history', False):
        st.session_state.history = load_trade_history()
        st.session_state.force_reload_history = False
    
    # Saldos do dashboard
    if 'balances' not in st.session_state or st.session_state.get('force_reload_balances', False):
        st.session_state.balances = load_dashboard_balances()
        st.session_state.force_reload_balances = False
    
    # Dados da AI
    if 'ai_data' not in st.session_state or st.session_state.get('force_reload_ai', False):
        st.session_state.ai_data = load_ai_data()
        st.session_state.force_reload_ai = False
    
    # Watchlist
    if 'watchlist_alerts' not in st.session_state or st.session_state.get('force_reload_watchlist', False):
        st.session_state.watchlist_alerts = load_watchlist_alerts()
        st.session_state.force_reload_watchlist = False
    
    # Mudanças de config
    if 'config_changes' not in st.session_state or st.session_state.get('force_reload_changes', False):
        st.session_state.config_changes = load_config_changes()
        st.session_state.force_reload_changes = False
    
    # AutoTuner
    if 'autotuner_state' not in st.session_state or st.session_state.get('force_reload_autotuner', False):
        st.session_state.autotuner_state = load_autotuner_state()
        st.session_state.force_reload_autotuner = False
    
    # UnicoBot config
    if 'unico_config' not in st.session_state or st.session_state.get('force_reload_unico', False):
        st.session_state.unico_config = load_unico_bot_config()
        st.session_state.force_reload_unico = False


def get_config() -> Optional[Any]:
    """Retorna config do session_state"""
    return st.session_state.get('config')


def get_positions() -> dict:
    """Retorna posições do session_state"""
    return st.session_state.get('positions', {})


def get_history() -> list:
    """Retorna histórico do session_state"""
    return st.session_state.get('history', [])


def get_balances() -> dict:
    """Retorna balances do session_state"""
    return st.session_state.get('balances', {})


def get_ai_data() -> dict:
    """Retorna ai_data do session_state"""
    return st.session_state.get('ai_data', {})


def get_watchlist() -> list:
    """Retorna watchlist_alerts do session_state"""
    return st.session_state.get('watchlist_alerts', [])


def get_config_changes() -> list:
    """Retorna config_changes do session_state"""
    return st.session_state.get('config_changes', [])


def get_autotuner_state() -> dict:
    """Retorna autotuner_state do session_state"""
    return st.session_state.get('autotuner_state', {})


def get_unico_config() -> Optional[dict]:
    """Retorna unico_config do session_state"""
    return st.session_state.get('unico_config')


def force_reload_all():
    """Força recarregamento de todos os dados"""
    st.session_state.force_reload_config = True
    st.session_state.force_reload_positions = True
    st.session_state.force_reload_history = True
    st.session_state.force_reload_balances = True
    st.session_state.force_reload_ai = True
    st.session_state.force_reload_watchlist = True
    st.session_state.force_reload_changes = True
    st.session_state.force_reload_autotuner = True
    st.session_state.force_reload_unico = True
    
    # Limpa cache do Streamlit
    st.cache_data.clear()
    
    # Reinicializa
    init_session_state()


def force_reload(data_type: str):
    """
    Força recarregamento de um tipo específico de dado
    
    Args:
        data_type: 'config', 'positions', 'history', 'balances', 'ai', 'watchlist', 'changes', 'autotuner', 'unico'
    """
    st.session_state[f'force_reload_{data_type}'] = True
    init_session_state()
