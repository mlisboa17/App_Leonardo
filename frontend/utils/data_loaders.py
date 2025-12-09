"""
Data Loaders - Funções para carregar dados do sistema
"""

import json
import yaml
import streamlit as st
from pathlib import Path
from typing import Optional, Dict, List


@st.cache_data(ttl=10)
def load_coordinator_stats() -> Optional[Dict]:
    """Carrega estatísticas do coordenador"""
    stats_file = Path("data/coordinator_stats.json")
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            return json.load(f)
    return None


@st.cache_data(ttl=5)
def load_dashboard_balances() -> Dict:
    """Carrega dados de saldos e meta diária"""
    balances_file = Path("data/dashboard_balances.json")
    if balances_file.exists():
        try:
            with open(balances_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        'usdt_balance': 0,
        'crypto_balance': 0,
        'total_balance': 0,
        'crypto_positions': {},
        'poupanca': 0,
        'daily_target_pct': 1.0,
        'daily_target_usd': 0,
        'daily_pnl': 0,
        'daily_progress': 0,
        'initial_capital': 1000.0,
    }


def save_dashboard_balances(data: dict):
    """Salva dados de saldos e meta diária"""
    balances_file = Path("data/dashboard_balances.json")
    balances_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(balances_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Erro ao salvar balances: {e}")


@st.cache_data(ttl=5)
def load_bots_config() -> Optional[Dict]:
    """Carrega configuração dos bots"""
    config_file = Path("config/bots_config.yaml")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None


def save_bots_config(config: dict):
    """Salva configuração dos bots com sincronização automática"""
    bot_unico_enabled = config.get('bot_unico', {}).get('enabled', False)
    other_bots = ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']
    
    if bot_unico_enabled:
        for bot in other_bots:
            if bot in config:
                config[bot]['enabled'] = False
    else:
        any_active = any(config.get(bot, {}).get('enabled', False) for bot in other_bots)
        if not any_active and other_bots[0] in config:
            config[other_bots[0]]['enabled'] = True
    
    config_file = Path("config/bots_config.yaml")
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


@st.cache_data(ttl=5)
def load_positions() -> Dict:
    """Carrega posições abertas"""
    positions_file = Path("data/multibot_positions.json")
    if positions_file.exists():
        with open(positions_file, 'r') as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=10)
def load_trade_history() -> List:
    """Carrega histórico de trades (últimos 200 para performance)"""
    history_file = Path("data/multibot_history.json")
    if history_file.exists():
        with open(history_file, 'r') as f:
            all_trades = json.load(f)
            return all_trades[-200:] if len(all_trades) > 200 else all_trades
    return []


def load_watchlist_alerts() -> List:
    """Carrega alertas da watchlist"""
    alerts_file = Path("data/watchlist_alerts.json")
    if alerts_file.exists():
        with open(alerts_file, 'r') as f:
            return json.load(f)
    return []


def load_ai_data() -> Dict:
    """Carrega dados da IA"""
    ai_state_file = Path("data/ai/ai_state.json")
    market_cache_file = Path("data/market_cache/last_scan.json")
    insights_file = Path("data/ai_models/insights.json")
    
    ai_data = {
        'enabled': False,
        'market': {},
        'insights': {},
        'status': {}
    }
    
    if ai_state_file.exists():
        try:
            with open(ai_state_file, 'r') as f:
                state = json.load(f)
                ai_data['status'] = state
                ai_data['enabled'] = True
        except:
            pass
    
    if market_cache_file.exists():
        try:
            with open(market_cache_file, 'r') as f:
                ai_data['market'] = json.load(f)
        except:
            pass
    
    if insights_file.exists():
        try:
            with open(insights_file, 'r') as f:
                ai_data['insights'] = json.load(f)
        except:
            pass
    
    return ai_data


def load_config_changes() -> List:
    """Carrega histórico de mudanças de configuração"""
    changes_file = Path("data/config_history/changes_history.json")
    if changes_file.exists():
        try:
            with open(changes_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return []


def load_autotuner_state() -> Dict:
    """Carrega estado do AutoTuner"""
    state_file = Path("data/autotuner_state.json")
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'current': {
            'market_conditions': {
                'trend': 'unknown',
                'volatility_level': 'unknown',
                'recommended_action': 'hold'
            }
        },
        'history': []
    }


def load_unico_bot_config() -> Optional[Dict]:
    """Carrega configuração do UnicoBot"""
    config_file = Path("config/unico_bot_config.yaml")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None


def save_unico_bot_config(config: dict):
    """Salva configuração do UnicoBot"""
    config_file = Path("config/unico_bot_config.yaml")
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
