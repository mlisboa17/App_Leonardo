import json
from pathlib import Path
import streamlit as st

def init_session_state():
    if 'initialized' not in st.session_state:
        st.session_state['initialized'] = True
        st.session_state['force_reload'] = False

def get_config():
    config_path = Path('config/bots_config.yaml')
    if config_path.exists():
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def get_positions():
    path = Path('data/multibot_positions.json')
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_history():
    path = Path('data/multibot_history.json')
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def get_balances():
    path = Path('data/dashboard_balances.json')
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'usdt_balance': 0, 'crypto_balance': 0, 'poupanca': 0, 'total_balance': 0}

def get_watchlist():
    path = Path('data/watchlist_alerts.json')
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def get_unico_config():
    path = Path('config/unico_bot_config.yaml')
    if path.exists():
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def force_reload_all():
    st.session_state['force_reload'] = True
