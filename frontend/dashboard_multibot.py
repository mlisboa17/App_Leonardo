"""
============================================================
DASHBOARD MULTI-BOT - App R7   
============================================================

Dashboard Streamlit que mostra estatísticas de todos os bots.
Cada bot tem sua própria seção com métricas específicas.

Uso:
    streamlit run frontend/dashboard_multibot.py

============================================================
"""

import os
import sys
import json
import yaml
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuração da página
st.set_page_config(
    page_title="🚀 APP R7 - Trading Bot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    /* Aumenta tamanho geral das fontes */
    html, body, [class*="css"] {
        font-size: 18px !important;
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1a1a2e, #16213e);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .bot-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .bot-estavel { background: linear-gradient(135deg, #1e3a5f, #2d5a87); }
    .bot-medio { background: linear-gradient(135deg, #1e5f3a, #2d8757); }
    .bot-volatil { background: linear-gradient(135deg, #5f5f1e, #87872d); }
    .bot-meme { background: linear-gradient(135deg, #5f1e1e, #872d2d); }
    
    .metric-positive { color: #00ff88; }
    .metric-negative { color: #ff4444; }
    
    .stMetric {
        background-color: rgba(0,0,0,0.2);
        padding: 1.5rem;
        border-radius: 8px;
    }
    
    /* Valores das métricas maiores */
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: bold;
    }
    
    /* Labels das métricas maiores */
    div[data-testid="stMetricLabel"] {
        font-size: 1.2rem !important;
    }
    
    /* Títulos maiores */
    h1 { font-size: 2.8rem !important; }
    h2 { font-size: 2.2rem !important; }
    h3 { font-size: 1.8rem !important; }
    
    /* Tabelas com fonte maior */
    .dataframe { font-size: 1.1rem !important; }
    
    /* Botões maiores */
    .stButton > button {
        font-size: 1.2rem !important;
        padding: 0.8rem 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=10)  # Cache por 10 segundos
def load_coordinator_stats():
    """Carrega estatísticas do coordenador"""
    stats_file = Path("data/coordinator_stats.json")
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            return json.load(f)
    return None


@st.cache_data(ttl=5)  # Cache por 5 segundos
def load_dashboard_balances():
    """Carrega dados de saldos e meta diária"""
    balances_file = Path("data/dashboard_balances.json")
    if balances_file.exists():
        try:
            with open(balances_file, 'r') as f:
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
        'initial_capital': 1000.0,  # $1,000 USDT como referência
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


def load_bots_config():
    """Carrega configuração dos bots"""
    config_file = Path("config/bots_config.yaml")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None


def sync_bot_unico_state():
    """Sincroniza estado do bot_unico com os outros bots"""
    config = load_bots_config()
    if not config:
        return
    
    bot_unico_enabled = config.get('bot_unico', {}).get('enabled', False)
    other_bots = ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']
    
    changed = False
    if bot_unico_enabled:
        # Se bot_unico está ativo, garante que outros estão desativados
        for bot in other_bots:
            if bot in config and config[bot].get('enabled', False):
                config[bot]['enabled'] = False
                changed = True
    else:
        # Se bot_unico está inativo, garante que pelo menos um outro está ativo
        any_active = any(config.get(bot, {}).get('enabled', False) for bot in other_bots)
        if not any_active and other_bots[0] in config:
            config[other_bots[0]]['enabled'] = True
            changed = True
    
    if changed:
        try:
            config_file = Path("config/bots_config.yaml")
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"Erro ao sincronizar estado: {e}")


@st.cache_data(ttl=5)  # Cache por 5 segundos
def load_positions():
    """Carrega posições abertas"""
    positions_file = Path("data/multibot_positions.json")
    if positions_file.exists():
        with open(positions_file, 'r') as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=10)  # Cache por 10 segundos  
def load_trade_history():
    """Carrega histórico de trades (últimos 200 para performance)"""
    history_file = Path("data/multibot_history.json")
    if history_file.exists():
        with open(history_file, 'r') as f:
            all_trades = json.load(f)
            # Limita a 200 trades mais recentes para melhorar performance
            return all_trades[-200:] if len(all_trades) > 200 else all_trades
    return []


def get_pnl_by_bot(history: list) -> dict:
    """Agrupa PnL por bot"""
    pnl_by_bot = {}
    for trade in history:
        bot_type = trade.get('bot_type', 'unknown')
        if bot_type not in pnl_by_bot:
            pnl_by_bot[bot_type] = {
                'total_pnl': 0,
                'trades': 0,
                'wins': 0,
                'losses': 0
            }
        
        pnl = trade.get('pnl_usd', 0)
        pnl_by_bot[bot_type]['total_pnl'] += pnl
        pnl_by_bot[bot_type]['trades'] += 1
        if pnl > 0:
            pnl_by_bot[bot_type]['wins'] += 1
        else:
            pnl_by_bot[bot_type]['losses'] += 1
    
    return pnl_by_bot


def get_daily_pnl(history: list) -> dict:
    """Calcula PnL diário por bot"""
    today = datetime.now().date().isoformat()
    daily_pnl = {}
    
    for trade in history:
        exit_time = trade.get('exit_time', trade.get('timestamp', ''))
        if exit_time.startswith(today):
            bot_type = trade.get('bot_type', 'unknown')
            if bot_type not in daily_pnl:
                daily_pnl[bot_type] = 0
            daily_pnl[bot_type] += trade.get('pnl_usd', 0)
    
    return daily_pnl


def get_monthly_pnl(history: list) -> dict:
    """Calcula PnL mensal por bot"""
    current_month = datetime.now().strftime('%Y-%m')
    monthly_pnl = {}
    
    for trade in history:
        exit_time = trade.get('exit_time', trade.get('timestamp', ''))
        if exit_time.startswith(current_month):
            bot_type = trade.get('bot_type', 'unknown')
            if bot_type not in monthly_pnl:
                monthly_pnl[bot_type] = 0
            monthly_pnl[bot_type] += trade.get('pnl_usd', 0)
    
    return monthly_pnl


def load_watchlist_alerts() -> list:
    """Carrega alertas da watchlist"""
    alerts_file = Path("data/watchlist_alerts.json")
    if alerts_file.exists():
        with open(alerts_file, 'r') as f:
            return json.load(f)
    return []


def load_ai_data() -> dict:
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
    
    # Estado da AI
    if ai_state_file.exists():
        try:
            with open(ai_state_file, 'r') as f:
                state = json.load(f)
                ai_data['status'] = state
                ai_data['enabled'] = True
        except:
            pass
    
    # Scan de mercado
    if market_cache_file.exists():
        try:
            with open(market_cache_file, 'r') as f:
                ai_data['market'] = json.load(f)
        except:
            pass
    
    # Insights
    if insights_file.exists():
        try:
            with open(insights_file, 'r') as f:
                ai_data['insights'] = json.load(f)
        except:
            pass
    
    return ai_data


def load_config_changes() -> list:
    """Carrega histórico de mudanças de configuração"""
    changes_file = Path("data/config_history/changes_history.json")
    if changes_file.exists():
        try:
            with open(changes_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return []


def load_bot_specific_history(bot_type: str) -> list:
    """Carrega historico especifico de um bot"""
    history_file = Path(f"data/history/{bot_type}_trades.json")
    if history_file.exists():
        with open(history_file, 'r') as f:
            return json.load(f)
    return []


def load_autotuner_state() -> dict:
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


def render_global_stats(stats: dict, history: list):
    """Renderiza estatísticas globais"""
    st.markdown('<div class="main-header">🚀 APP R7 - TRADING BOT SYSTEM</div>', unsafe_allow_html=True)
    
    # Carrega saldos do dashboard
    balances = load_dashboard_balances()
    config = load_bots_config()
    bot_unico_enabled = config.get('bot_unico', {}).get('enabled', False) if config else False
    
    # Mostra modo ativo
    if bot_unico_enabled:
        st.success("⚡ **MODO: BOT UNICO ADAPTATIVO** - Sistema híbrido em operação")
    else:
        st.info("🔵🟢🟡🔴 **MODO: 4 BOTS ESPECIALIZADOS** - Operação diversificada")
    
    # ===== CAPITAL INICIAL E PNL REAL =====
    CAPITAL_INICIAL = 1000.0  # Capital inicial fixo
    saldo_total = balances['total_balance']
    pnl_real = saldo_total - CAPITAL_INICIAL  # PnL real = atual - inicial
    pnl_real_pct = (pnl_real / CAPITAL_INICIAL * 100) if CAPITAL_INICIAL > 0 else 0
    
    # ===== LINHA 1: SALDOS =====
    st.subheader("💰 SALDOS")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💵 SALDO USDT", f"${balances['usdt_balance']:.2f}")
    
    with col2:
        st.metric("🪙 SALDO CRIPTO", f"${balances['crypto_balance']:.2f}")
    
    with col3:
        delta_color = "normal" if pnl_real >= 0 else "inverse"
        st.metric("💎 SALDO TOTAL", f"${saldo_total:.2f}", 
                  delta=f"{pnl_real:+.2f} ({pnl_real_pct:+.1f}%)",
                  delta_color=delta_color)
    
    with col4:
        st.metric("🏦 POUPANÇA", f"${balances['poupanca']:.2f}")
    
    with col5:
        st.metric("🎯 CAPITAL INICIAL", f"${CAPITAL_INICIAL:.2f}")
    
    # ===== LINHA 2: META DIÁRIA (CORRIGIDO) =====
    st.subheader("🎯 PROGRESSÃO META DIÁRIA")
    
    # Calcula PnL do dia (desde 00:00 de hoje)
    today = datetime.now().date().isoformat()
    daily_trades = [t for t in history if t.get('exit_time', t.get('timestamp', '')).startswith(today)]
    daily_pnl = sum(t.get('pnl_usd', 0) for t in daily_trades)
    
    # Meta diária = 0.33% ao dia = $3.33
    daily_target = 3.33  # Meta fixa de $3.33/dia para 10% ao mês
    
    # Progresso = PnL do dia / Meta do dia * 100
    daily_progress = (daily_pnl / daily_target * 100) if daily_target > 0 else 0
    
    # Barra de progresso (0-100%)
    progress_color = "🟢" if daily_progress >= 100 else "🟡" if daily_progress >= 50 else "🔴"
    if daily_pnl < 0:
        progress_color = "🔴"
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Barra de progresso visual (capped a 100%)
        progress_value = min(daily_progress / 100, 1.0) if daily_progress >= 0 else 0
        st.progress(progress_value)
        
        # Explicação clara
        if daily_pnl < 0:
            st.caption(f"{progress_color} Progresso: **{daily_pnl:.2f}$ de {daily_target:.2f}$ (Meta não atingida)**")
        else:
            st.caption(f"{progress_color} Progresso: **{daily_progress:.1f}% ({daily_pnl:.2f}$ de {daily_target:.2f}$)**")
    
    with col2:
        # PnL do dia
        pnl_color = "📈" if daily_pnl >= 0 else "📉"
        st.metric(f"{pnl_color} PnL Hoje", f"${daily_pnl:+.2f}")
    
    with col3:
        # Meta: 10% ao mês = $3.33/dia
        st.metric(f"🎯 Meta Diária", f"${daily_target:.2f}")
    
    st.markdown("---")
    
    # ===== LINHA 3: ESTATÍSTICAS =====
    st.subheader("📈 ESTATÍSTICAS")
    
    # Calcula totais do histórico
    total_pnl = sum(t.get('pnl_usd', 0) for t in history)
    total_trades = len(history)
    wins = sum(1 for t in history if t.get('pnl_usd', 0) > 0)
    losses = total_trades - wins
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    # PnL do mes
    current_month = datetime.now().strftime('%Y-%m')
    monthly_trades = [t for t in history if t.get('exit_time', t.get('timestamp', '')).startswith(current_month)]
    monthly_pnl = sum(t.get('pnl_usd', 0) for t in monthly_trades)
    
    # Calcula receita com vendas (Total de vendas - Taxas)
    total_revenue_today = sum(t.get('exit_price', 0) * t.get('quantity', 0) for t in daily_trades)
    total_fees_today = sum(t.get('exchange_fee', 0) for t in daily_trades) if any('exchange_fee' in t for t in daily_trades) else 0
    net_usdt_today = total_revenue_today - total_fees_today
    
    total_revenue_month = sum(t.get('exit_price', 0) * t.get('quantity', 0) for t in monthly_trades)
    total_fees_month = sum(t.get('exchange_fee', 0) for t in monthly_trades) if any('exchange_fee' in t for t in monthly_trades) else 0
    net_usdt_month = total_revenue_month - total_fees_month
    
    # Row 1: PnL Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💰 PnL Total", f"${total_pnl:.2f}")
    
    with col2:
        st.metric("📅 Lucro Mensal", f"${monthly_pnl:+.2f}")
    
    with col3:
        positions = load_positions()
        st.metric("📍 Posições Abertas", f"{len(positions)}")
    
    with col4:
        st.metric("📈 Total Trades", f"{total_trades}", delta=f"{win_rate:.1f}% WR")
    
    with col5:
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        st.metric("💵 Média/Trade", f"${avg_pnl:.2f}")
    
    st.markdown("---")
    
    # Row 2: Receita com Vendas - Taxas = Saldo USDT
    st.subheader("💵 RECEITA COM VENDAS - TAXAS = SALDO USDT")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Vendas Hoje", f"${total_revenue_today:.2f}")
    
    with col2:
        st.metric("🔧 Taxas Hoje", f"-${total_fees_today:.2f}")
    
    with col3:
        net_color = "🟢" if net_usdt_today >= 0 else "🔴"
        st.metric(f"{net_color} Saldo USDT Hoje", f"${net_usdt_today:.2f}")
    
    with col4:
        st.info(f"📅 Mês: ${net_usdt_month:.2f}")
    
    st.markdown("---")


def render_bot_card(bot_type: str, bot_config: dict, history: list, positions: dict):
    """Renderiza card de um bot específico com informações principais"""
    
    # Cores e emojis por tipo
    bot_styles = {
        'bot_estavel': ('🔵', 'bot-estavel', '#4a90d9', 'Cryptos estáveis e seguras'),
        'bot_medio': ('🟢', 'bot-medio', '#4ad94a', 'Cryptos de média volatilidade'),
        'bot_volatil': ('🟡', 'bot-volatil', '#d9d94a', 'Cryptos de alta volatilidade'),
        'bot_meme': ('🔴', 'bot-meme', '#d94a4a', 'Meme coins de alto risco'),
        'bot_unico': ('⚡', 'bot-unico', '#9b4de4', 'Bot Unificado - Controla todos')
    }
    
    emoji, css_class, color, tipo = bot_styles.get(bot_type, ('🤖', '', '#888', 'Bot'))
    name = bot_config.get('name', bot_type)
    enabled = bot_config.get('enabled', True)
    
    # Filtra trades deste bot
    bot_trades = [t for t in history if t.get('bot_type') == bot_type]
    total_pnl = sum(t.get('pnl_usd', 0) for t in bot_trades)
    trades_count = len(bot_trades)
    wins = sum(1 for t in bot_trades if t.get('pnl_usd', 0) > 0)
    losses = trades_count - wins
    win_rate = (wins / trades_count * 100) if trades_count > 0 else 0
    
    # PnL do dia
    today = datetime.now().date().isoformat()
    daily_trades = [t for t in bot_trades if t.get('exit_time', t.get('timestamp', '')).startswith(today)]
    daily_pnl = sum(t.get('pnl_usd', 0) for t in daily_trades)
    
    # PnL do mes
    current_month = datetime.now().strftime('%Y-%m')
    monthly_trades = [t for t in bot_trades if t.get('exit_time', t.get('timestamp', '')).startswith(current_month)]
    monthly_pnl = sum(t.get('pnl_usd', 0) for t in monthly_trades)
    
    # Posições deste bot
    bot_positions = {k: v for k, v in positions.items() if v.get('bot_type') == bot_type}
    
    # Portfolio e configurações
    portfolio = bot_config.get('portfolio', [])
    trading = bot_config.get('trading', {})
    risk = bot_config.get('risk', {})
    
    # Calcula valor investido em posições abertas
    valor_investido = sum(pos.get('amount_usd', 0) for pos in bot_positions.values())
    
    # Status emoji
    status = "🟢 ATIVO" if enabled else "⏸️ PAUSADO"
    pnl_emoji = "📈" if total_pnl >= 0 else "📉"
    
    # Card do bot com todas informações principais
    with st.container():
        # Header do card
        st.markdown(f"""
        <div class="bot-card {css_class}" style="border-left: 4px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin: 0;">{emoji} {name}</h2>
                <span style="font-size: 0.9rem;">{status}</span>
            </div>
            <p style="opacity: 0.7; margin: 5px 0;">{tipo}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # ===== LINHA 1: LUCROS =====
        st.markdown("**💰 LUCROS**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            delta = f"{'+' if daily_pnl >= 0 else ''}{daily_pnl:.2f} hoje"
            st.metric("📊 Diário", f"${daily_pnl:+.2f}", delta=f"{len(daily_trades)} trades")
        
        with col2:
            st.metric("📅 Mensal", f"${monthly_pnl:+.2f}", delta=f"{len(monthly_trades)} trades")
        
        with col3:
            st.metric(f"{pnl_emoji} Total Acumulado", f"${total_pnl:+.2f}")
        
        # ===== LINHA 2: POSIÇÕES E TRADES =====
        st.markdown("**📍 POSIÇÕES & TRADES**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            max_pos = trading.get('max_positions', 5)
            st.metric("Posições Abertas", f"{len(bot_positions)}/{max_pos}")
        
        with col2:
            st.metric("Valor Investido", f"${valor_investido:.2f}")
        
        with col3:
            st.metric("Total Trades", f"{trades_count}")
        
        with col4:
            wr_emoji = "✅" if win_rate >= 60 else "🟡" if win_rate >= 40 else "❌"
            st.metric(f"{wr_emoji} Win Rate", f"{win_rate:.1f}%", delta=f"{wins}W / {losses}L")
        
        # ===== LINHA 3: CRYPTOS E CONFIG =====
        st.markdown("**🪙 CRYPTOS**")
        
        # Lista de cryptos do portfolio
        symbols = [c['symbol'].replace('USDT', '') for c in portfolio]
        symbols_str = " | ".join(symbols)
        st.caption(f"📦 Portfolio: **{symbols_str}**")
        
        # Cryptos com posição aberta
        if bot_positions:
            open_symbols = [s.replace('USDT', '') for s in bot_positions.keys()]
            st.caption(f"📍 Com posição: **{' | '.join(open_symbols)}**")
        
        # ===== LINHA 4: CONFIGURAÇÕES RESUMIDAS =====
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.caption(f"💵 **${trading.get('amount_per_trade', 0)}/trade**")
        
        with col2:
            st.caption(f"🛑 **SL: {risk.get('stop_loss', -1)}%**")
        
        with col3:
            st.caption(f"🎯 **TP: {risk.get('take_profit', 0.5)}%**")
        
        with col4:
            st.caption(f"⏱️ **Max: {risk.get('max_hold_minutes', 5)}min**")
        
        # Expander com detalhes extras
        with st.expander(f"📋 Ver Detalhes Completos"):
            # Posições abertas
            if bot_positions:
                st.subheader("📍 Posições Abertas")
                pos_data = []
                for symbol, pos in bot_positions.items():
                    entry_price = pos.get('entry_price', 0)
                    amount_usd = pos.get('amount_usd', 0)
                    time_str = pos.get('time', '')
                    if isinstance(time_str, str) and len(time_str) > 19:
                        time_str = time_str[:19]
                    
                    pos_data.append({
                        'Symbol': symbol,
                        'Entrada': f"${entry_price:.4f}",
                        'Valor': f"${amount_usd:.2f}",
                        'Hora': time_str
                    })
                st.dataframe(pd.DataFrame(pos_data), use_container_width=True)
            
            # Últimos trades
            if bot_trades:
                st.subheader("📜 Últimos 5 Trades")
                recent_trades = sorted(bot_trades, key=lambda x: x.get('exit_time', ''), reverse=True)[:5]
                
                trades_data = []
                for trade in recent_trades:
                    pnl = trade.get('pnl_usd', 0)
                    pnl_emoji = "✅" if pnl > 0 else "❌"
                    trades_data.append({
                        '': pnl_emoji,
                        'Symbol': trade.get('symbol', ''),
                        'PnL': f"${pnl:+.2f}",
                        '%': f"{trade.get('pnl_pct', 0):+.2f}%",
                        'Duração': f"{trade.get('duration_min', 0):.1f}m",
                    })
                
                st.dataframe(pd.DataFrame(trades_data), use_container_width=True)


def render_charts(history: list):
    """Renderiza gráficos de performance"""
    st.header("📊 Gráficos de Performance")
    
    if not history:
        st.info("Nenhum histórico de trades disponível")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # PnL por bot
        st.subheader("💰 PnL por Bot")
        
        pnl_by_bot = get_pnl_by_bot(history)
        bot_names = {
            'bot_estavel': '🔵 Estável',
            'bot_medio': '🟢 Médio',
            'bot_volatil': '🟡 Volátil',
            'bot_meme': '🔴 Meme',
            'bot_unico': '⚡ Unico'
        }
        
        chart_data = []
        for bot_type, stats in pnl_by_bot.items():
            chart_data.append({
                'Bot': bot_names.get(bot_type, bot_type),
                'PnL': stats['total_pnl'],
                'Trades': stats['trades']
            })
        
        if chart_data:
            df = pd.DataFrame(chart_data)
            colors = {'🔵 Estável': '#4a90d9', '🟢 Médio': '#4ad94a', '🟡 Volátil': '#d9d94a', '🔴 Meme': '#d94a4a', '⚡ Unico': '#9b4de4'}
            
            # Converte para linha (mais dinâmico)
            fig = px.line(df, x='Bot', y='PnL', 
                         color='Bot',
                         markers=True,
                         title='PnL Total por Bot')
            fig.update_layout(showlegend=False, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Trades por bot
        st.subheader("📈 Trades por Bot")
        
        trades_data = []
        for bot_type, stats in pnl_by_bot.items():
            trades_data.append({
                'Bot': bot_names.get(bot_type, bot_type),
                'Vitórias': stats['wins'],
                'Derrotas': stats['losses']
            })
        
        if trades_data:
            df = pd.DataFrame(trades_data)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(name='Vitórias', x=df['Bot'], y=df['Vitórias'], mode='lines+markers', marker_color='#00ff88'))
            fig.add_trace(go.Scatter(name='Derrotas', x=df['Bot'], y=df['Derrotas'], mode='lines+markers', marker_color='#ff4444'))

            fig.update_layout(title='Vitórias vs Derrotas por Bot')
            st.plotly_chart(fig, use_container_width=True)
    
    # PnL acumulado ao longo do tempo
    st.subheader("📈 PnL Acumulado")
    
    # Ordena por data
    sorted_history = sorted(history, key=lambda x: x.get('exit_time', ''))
    
    # Calcula PnL acumulado por bot
    cumulative_data = []
    cumulative_pnl = {bt: 0 for bt in bot_names.keys()}
    
    for trade in sorted_history:
        bot_type = trade.get('bot_type', 'unknown')
        if bot_type in cumulative_pnl:
            cumulative_pnl[bot_type] += trade.get('pnl_usd', 0)
            
            cumulative_data.append({
                'Data': trade.get('exit_time', '')[:10],
                'Bot': bot_names.get(bot_type, bot_type),
                'PnL Acumulado': cumulative_pnl[bot_type]
            })
    
    if cumulative_data:
        df = pd.DataFrame(cumulative_data)
        
        fig = px.line(df, x='Data', y='PnL Acumulado', color='Bot',
                     title='PnL Acumulado por Bot ao Longo do Tempo')
        st.plotly_chart(fig, use_container_width=True)


def render_sidebar():
    """Renderiza sidebar com controles"""
    st.sidebar.header("🎛️ Controles")
    
    # Navegação de páginas
    st.sidebar.subheader("📑 Páginas")
    page = st.sidebar.radio("Selecione", ["🏠 Dashboard", "🎮 Controle Bots", "🤖 AI Intelligence", "⚙️ Configurações"])
    
    st.sidebar.markdown("---")
    
    # Status
    positions = load_positions()
    st.sidebar.metric("📍 Total Posições", len(positions))
    
    # Refresh
    refresh_rate = st.sidebar.slider("🔄 Refresh (segundos)", 5, 60, 10)
    
    if st.sidebar.button("🔄 Atualizar Agora"):
        st.rerun()
    
    # Filtros
    st.sidebar.header("🔍 Filtros")
    
    config = load_bots_config()
    if config:
        bot_types = ['Todos', 'bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme', 'bot_unico']
        selected_bot = st.sidebar.selectbox("Filtrar por Bot", bot_types)
        
        return {
            'refresh_rate': refresh_rate,
            'selected_bot': selected_bot,
            'page': page
        }
    
    return {'refresh_rate': refresh_rate, 'selected_bot': 'Todos', 'page': page}


def render_ai_page():
    """Renderiza página de inteligência artificial"""
    st.markdown('<div class="main-header">🤖 AI INTELLIGENCE - App Leonardo v3.0</div>', unsafe_allow_html=True)
    
    # Carrega dados da AI
    ai_data = load_ai_data()
    config_changes = load_config_changes()
    
    # ===== SEÇÃO 1: STATUS DA AI =====
    st.header("📊 Status do Sistema de IA")
    
    col1, col2, col3, col4 = st.columns(4)
    
    status = ai_data.get('status', {})
    
    with col1:
        auto_adjust = "🟢 Ativo" if status.get('auto_adjust_enabled', False) else "🔴 Inativo"
        st.metric("Auto-Ajuste", auto_adjust)
    
    with col2:
        last_scan = status.get('last_market_scan', 'Nunca')
        if last_scan and last_scan != 'Nunca':
            last_scan = last_scan[:19].replace('T', ' ')
        st.metric("Último Scan", last_scan[:16] if last_scan else "Nunca")
    
    with col3:
        last_train = status.get('last_training', 'Nunca')
        if last_train and last_train != 'Nunca':
            last_train = last_train[:19].replace('T', ' ')
        st.metric("Último Treino", last_train[:16] if last_train else "Nunca")
    
    with col4:
        last_adjust = status.get('last_auto_adjust', 'Nunca')
        if last_adjust and last_adjust != 'Nunca':
            last_adjust = last_adjust[:19].replace('T', ' ')
        st.metric("Último Ajuste", last_adjust[:16] if last_adjust else "Nunca")
    
    st.markdown("---")
    
    # ===== SEÇÃO 2: FEAR & GREED + SENTIMENTO =====
    st.header("📈 Análise de Mercado")
    
    market = ai_data.get('market', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("😰 Fear & Greed Index")
        
        fear_greed = market.get('fear_greed', {})
        fg_value = fear_greed.get('value', 50)
        fg_class = fear_greed.get('classification', 'Neutral')
        fg_trend = fear_greed.get('trend', 'stable')
        
        # Gauge visual
        if fg_value <= 25:
            fg_color = "🔴"
            fg_emoji = "😱"
        elif fg_value <= 45:
            fg_color = "🟠"
            fg_emoji = "😟"
        elif fg_value <= 55:
            fg_color = "🟡"
            fg_emoji = "😐"
        elif fg_value <= 75:
            fg_color = "🟢"
            fg_emoji = "😊"
        else:
            fg_color = "🔴"
            fg_emoji = "🤑"
        
        st.metric(
            f"{fg_emoji} {fg_class}", 
            f"{fg_value}/100",
            delta=fg_trend
        )
        
        # Interpretação
        interpretation = fear_greed.get('interpretation', '')
        if interpretation:
            st.info(interpretation)
        
        # Histórico
        fg_history = fear_greed.get('history', [])
        if fg_history:
            hist_df = pd.DataFrame(fg_history)
            if not hist_df.empty:
                fig = px.line(hist_df, x='date', y='value', title='Fear & Greed - Últimos 7 dias')
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📰 Sentimento de Notícias")
        
        news_summary = market.get('news_summary', {})
        
        sentiment = market.get('overall_sentiment', 'NEUTRAL')
        sentiment_emoji = "🟢" if sentiment == "BULLISH" else "🔴" if sentiment == "BEARISH" else "🟡"
        
        st.metric(f"{sentiment_emoji} Sentimento Geral", sentiment)
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("📰 Notícias", news_summary.get('total_news', 0))
        with col_b:
            st.metric("🟢 Bullish", news_summary.get('bullish_count', 0))
        with col_c:
            st.metric("🔴 Bearish", news_summary.get('bearish_count', 0))
        
        # Headlines recentes
        headlines = news_summary.get('recent_headlines', [])
        if headlines:
            st.write("**📝 Headlines Recentes:**")
            for h in headlines[:5]:
                st.write(f"• {h[:80]}...")
    
    st.markdown("---")
    
    # ===== SEÇÃO 3: RECOMENDAÇÕES =====
    st.header("💡 Recomendações da AI")
    
    recommendations = market.get('recommendations', [])
    
    if recommendations:
        for rec in recommendations:
            st.info(rec)
    else:
        st.info("Nenhuma recomendação no momento. Execute um scan de mercado.")
    
    # Should trade?
    should_trade = market.get('should_trade', {})
    if should_trade:
        st.subheader("🎯 Devo Operar Agora?")
        
        rec_type = should_trade.get('recommendation', 'UNKNOWN')
        message = should_trade.get('message', '')
        
        if rec_type == 'TRADE':
            st.success(message)
        elif rec_type == 'WAIT':
            st.error(message)
        else:
            st.warning(message)
        
        reasons = should_trade.get('reasons', [])
        for reason in reasons:
            st.write(f"  {reason}")
    
    st.markdown("---")
    
    # ===== SEÇÃO 4: INSIGHTS =====
    st.header("🧠 Insights do Aprendizado")
    
    insights = ai_data.get('insights', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Melhor Range de RSI (por bot)")
        rsi_ranges = insights.get('best_rsi_range', {})
        if rsi_ranges:
            for bot, rng in rsi_ranges.items():
                st.write(f"**{bot}:** RSI {rng.get('min', '?')} - {rng.get('max', '?')} (média: {rng.get('mean', '?')})")
        else:
            st.info("Dados insuficientes para insights de RSI")
    
    with col2:
        st.subheader("⏰ Melhores Horários (por bot)")
        best_hours = insights.get('best_hours', {})
        if best_hours:
            for bot, hours in best_hours.items():
                st.write(f"**{bot}:** {hours}")
        else:
            st.info("Dados insuficientes para insights de horários")
    
    # Padrões perigosos
    dangerous = insights.get('dangerous_patterns', [])
    if dangerous:
        st.subheader("⚠️ Cryptos com Alta Taxa de Perda")
        danger_data = []
        for d in dangerous:
            danger_data.append({
                'Symbol': d.get('symbol', ''),
                'Taxa de Perda': f"{d.get('loss_rate', 0)}%",
                'PnL Total': f"${d.get('total_loss', 0):.2f}"
            })
        st.dataframe(pd.DataFrame(danger_data), use_container_width=True)
    
    st.markdown("---")
    
    # ===== SEÇÃO 5: AUTO-TUNER (NOVO!) =====
    st.header("🎛️ Auto-Tuner - Ajuste Dinâmico em Tempo Real")
    
    autotuner_state = load_autotuner_state()
    current = autotuner_state.get('current', {})
    market_cond = current.get('market_conditions', {})
    
    # Status do mercado
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        trend = market_cond.get('trend', 'unknown')
        trend_emoji = {
            'strong_up': '🚀',
            'up': '📈',
            'neutral': '➡️',
            'down': '📉',
            'strong_down': '💥',
            'unknown': '❓'
        }
        st.metric(f"{trend_emoji.get(trend, '❓')} Tendência", trend.upper())
    
    with col2:
        vol_level = market_cond.get('volatility_level', 'unknown')
        vol_emoji = {
            'low': '😴',
            'normal': '✅',
            'high': '⚡',
            'extreme': '🌋',
            'unknown': '❓'
        }
        vol_pct = market_cond.get('volatility', 0)
        st.metric(f"{vol_emoji.get(vol_level, '❓')} Volatilidade", f"{vol_level.upper()} ({vol_pct:.1f}%)")
    
    with col3:
        vol_ratio = market_cond.get('volume_ratio', 1.0)
        st.metric("📊 Volume", f"{vol_ratio:.2f}x média")
    
    with col4:
        action = market_cond.get('recommended_action', 'hold')
        action_emoji = {
            'aggressive_buy': '🟢🟢',
            'buy': '🟢',
            'hold': '🟡',
            'reduce': '🟠',
            'defensive': '🔴'
        }
        st.metric(f"{action_emoji.get(action, '⚪')} Ação Recomendada", action.upper())
    
    # BTC info
    btc_price = market_cond.get('btc_price', 0)
    btc_change = market_cond.get('btc_change_24h', 0)
    if btc_price:
        st.info(f"💰 BTC: ${btc_price:,.2f} ({btc_change:+.2f}% 24h)")
    
    # Últimos ajustes
    last_changes = current.get('last_changes', {})
    if last_changes:
        st.subheader("🔧 Últimos Ajustes Aplicados")
        changes_list = []
        for bot, changes in last_changes.items():
            for param, value in changes.items():
                changes_list.append({
                    'Bot': bot,
                    'Parâmetro': param,
                    'Novo Valor': value
                })
        if changes_list:
            st.dataframe(pd.DataFrame(changes_list), use_container_width=True)
    
    # Histórico de ajustes do AutoTuner
    tuner_history = autotuner_state.get('history', [])
    if tuner_history:
        st.subheader("📜 Histórico de Auto-Tuning")
        with st.expander("Ver histórico"):
            for entry in reversed(tuner_history[-10:]):
                ts = entry.get('timestamp', '')[:19].replace('T', ' ')
                mc = entry.get('market_conditions', {})
                st.write(f"**{ts}**: {mc.get('trend', '?')} | Vol: {mc.get('volatility_level', '?')} | Ação: {mc.get('recommended_action', '?')}")
    
    st.markdown("---")
    
    # ===== SEÇÃO 6: HISTÓRICO DE MUDANÇAS =====
    st.header("📝 Histórico de Ajustes Automáticos")
    
    if config_changes:
        # Últimas 20 mudanças
        recent_changes = config_changes[-20:][::-1]
        
        changes_data = []
        for change in recent_changes:
            changes_data.append({
                'Data/Hora': change.get('timestamp', '')[:19].replace('T', ' '),
                'Bot': change.get('bot', ''),
                'Parâmetro': change.get('parameter', ''),
                'Valor Anterior': str(change.get('old_value', '')),
                'Novo Valor': str(change.get('new_value', '')),
                'Fonte': change.get('source', ''),
                'Razão': change.get('reason', '')[:40]
            })
        
        st.dataframe(pd.DataFrame(changes_data), use_container_width=True, height=300)
    else:
        st.info("Nenhuma mudança automática registrada ainda")


def render_config_page():
    """Renderiza página de configurações"""
    st.markdown('<div class="main-header">⚙️ CONFIGURAÇÕES - App Leonardo v3.0</div>', unsafe_allow_html=True)
    
    config = load_bots_config()
    
    if not config:
        st.error("Arquivo de configuração não encontrado")
        return
    
    # Perfil de Risco
    st.header("🎚️ Perfil de Risco")
    
    st.info("""
    **Perfis disponíveis:**
    - 🛡️ **Ultra Conservador**: Stop apertado, menos posições, valores menores
    - 🔵 **Conservador**: Configurações defensivas
    - ⚪ **Normal**: Configurações padrão
    - 🟠 **Agressivo**: Mais posições, valores maiores
    - 🔴 **Ultra Agressivo**: Máxima exposição (maior risco)
    """)
    
    profile = st.selectbox(
        "Selecione o perfil de risco",
        ["ultra_conservative", "conservative", "normal", "aggressive", "ultra_aggressive"],
        index=2
    )
    
    if st.button("🔧 Aplicar Perfil"):
        st.success(f"Perfil {profile} aplicado! (Reinicie o bot para efetivar)")
    
    st.markdown("---")
    
    # Configurações por Bot
    st.header("🤖 Configurações dos Bots")
    
    bot_names = {
        'bot_estavel': '🔵 Bot Estável',
        'bot_medio': '🟢 Bot Médio',
        'bot_volatil': '🟡 Bot Volátil',
        'bot_meme': '🔴 Bot Meme',
        'bot_unico': '⚡ Bot Unico'
    }
    
    for bot_type in ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme', 'bot_unico']:
        if bot_type in config:
            bot_config = config[bot_type]
            
            with st.expander(f"{bot_names.get(bot_type, bot_type)} - Configurações"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.number_input(
                        "Stop Loss (%)",
                        value=float(bot_config.get('stop_loss', 2.5)),
                        key=f"{bot_type}_sl",
                        disabled=True
                    )
                    st.number_input(
                        "Take Profit (%)",
                        value=float(bot_config.get('take_profit', 2.0)),
                        key=f"{bot_type}_tp",
                        disabled=True
                    )
                
                with col2:
                    st.number_input(
                        "RSI Compra",
                        value=int(bot_config.get('rsi_buy', 35)),
                        key=f"{bot_type}_rsi_buy",
                        disabled=True
                    )
                    st.number_input(
                        "RSI Venda",
                        value=int(bot_config.get('rsi_sell', 65)),
                        key=f"{bot_type}_rsi_sell",
                        disabled=True
                    )
                
                with col3:
                    st.number_input(
                        "Max Posições",
                        value=int(bot_config.get('max_positions', 5)),
                        key=f"{bot_type}_max",
                        disabled=True
                    )
                    st.number_input(
                        "Valor por Trade ($)",
                        value=float(bot_config.get('amount_per_trade', 50)),
                        key=f"{bot_type}_amount",
                        disabled=True
                    )
    
    st.info("💡 As configurações são ajustadas automaticamente pela AI. Para edição manual, use o arquivo config/bots_config.yaml")


def load_unico_bot_config():
    """Carrega configuração do UnicoBot"""
    config_file = Path("config/unico_bot_config.yaml")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None


def save_bots_config(config: dict):
    """Salva configuração dos bots com sincronização automática"""
    # Sincroniza bot_unico com os outros 4 bots
    bot_unico_enabled = config.get('bot_unico', {}).get('enabled', False)
    other_bots = ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']
    
    if bot_unico_enabled:
        # Se bot_unico está ativo, desativa os outros
        for bot in other_bots:
            if bot in config:
                config[bot]['enabled'] = False
    else:
        # Se nenhum bot está ativo, ativa pelo menos os principais
        any_active = any(config.get(bot, {}).get('enabled', False) for bot in other_bots)
        if not any_active and other_bots[0] in config:
            config[other_bots[0]]['enabled'] = True
    
    config_file = Path("config/bots_config.yaml")
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def save_unico_bot_config(config: dict):
    """Salva configuração do UnicoBot"""
    config_file = Path("config/unico_bot_config.yaml")
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def render_bot_control_page():
    """Renderiza página de controle de bots - Ativar/Pausar/UnicoBot"""
    st.markdown('<div class="main-header">🎮 CONTROLE DE BOTS - App Leonardo v3.0</div>', unsafe_allow_html=True)
    
    # Carrega configurações
    config = load_bots_config()
    unico_config = load_unico_bot_config()
    
    if not config:
        st.error("❌ Arquivo de configuração não encontrado!")
        return
    
    # ===== SEÇÃO: UNICOBOT =====
    st.header("⚡ UnicoBot - Controle Unificado")
    
    unico_enabled = unico_config.get('enabled', False) if unico_config else False
    
    if unico_enabled:
        st.success("🟢 **Bot Unico ATIVO** - Operando com ajustes adaptativos inteligentes")
        st.warning("⚠️ Os 4 bots especializados (Estável, Médio, Volátil, Meme) estão **PAUSADOS** automaticamente")
    else:
        st.info("🔴 **Bot Unico INATIVO** - Os 4 bots especializados estão no controle")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ⚡ O que é o Bot Unico?
        
        Um sistema **híbrido e adaptativo** que:
        - ✅ Se adapta dinamicamente às condições de mercado
        - ✅ Ajusta % de venda quando saldo USDT é baixo
        - ✅ Reage à volatilidade (alta/baixa)
        - ✅ Ativa modo recuperação após perdas
        - ✅ **Garante margem mínima** de 0.5%
        - ✅ Controla **9 posições máx**
        """)
    
    with col2:
        st.markdown("""
        ### 🔄 Sistema Híbrido
        
        **Quando Bot Unico está ATIVO:**
        - Os 4 bots especializados são **pausados**
        - Capital gerenciado de forma unificada
        - Ajustes automáticos por condições de mercado
        
        **Quando Bot Unico está INATIVO:**
        - Os 4 bots especializados são **reativados**
        - Cada bot opera com sua estratégia própria
        - Diversificação máxima de abordagem
        """)
    
    
    st.markdown("---")
    
    # Botões de ação do UnicoBot
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if unico_enabled:
            if st.button("🔴 DESATIVAR UnicoBot", type="secondary", use_container_width=True):
                # Desativa UnicoBot
                if unico_config:
                    unico_config['enabled'] = False
                    save_unico_bot_config(unico_config)
                    st.success("✅ UnicoBot desativado! Você pode ativar os bots especializados agora.")
                    st.rerun()
        else:
            if st.button("⚡ ATIVAR UnicoBot", type="primary", use_container_width=True):
                # Ativa UnicoBot e desativa todos os outros
                if unico_config:
                    unico_config['enabled'] = True
                    save_unico_bot_config(unico_config)
                    
                    # Desativa todos os bots especializados
                    bots = config.get('bots', config)
                    for bot_type in bots:
                        if isinstance(bots[bot_type], dict):
                            bots[bot_type]['enabled'] = False
                    
                    if 'bots' in config:
                        config['bots'] = bots
                    save_bots_config(config)
                    
                    st.success("✅ UnicoBot ATIVADO! Todos os outros bots foram pausados.")
                    st.balloons()
                    st.rerun()
    
    st.markdown("---")
    
    # ===== SEÇÃO: BOTS ESPECIALIZADOS =====
    st.header("🤖 Bots Especializados")
    
    bot_info = {
        'bot_estavel': {'name': '🔵 Bot Estável', 'desc': 'BTC, ETH, BNB - Baixa volatilidade', 'color': '#1e3a5f'},
        'bot_medio': {'name': '🟢 Bot Médio', 'desc': 'SOL, ADA, DOT - Volatilidade moderada', 'color': '#1e5f3a'},
        'bot_volatil': {'name': '🟡 Bot Volátil', 'desc': 'DOGE, XRP - Alta volatilidade', 'color': '#5f5f1e'},
        'bot_meme': {'name': '🔴 Bot Meme', 'desc': 'SHIB, PEPE - Máxima volatilidade', 'color': '#5f1e1e'},
        'bot_unico': {'name': '⚡ Bot Unico', 'desc': 'Controle unificado de todas as operações', 'color': '#4a1e5f'}
    }
    
    # Carrega estatísticas
    history = load_trade_history()
    pnl_by_bot = get_pnl_by_bot(history)
    daily_pnl = get_daily_pnl(history)
    
    # Grid de bots (2x2)
    col1, col2 = st.columns(2)
    
    bots = config.get('bots', config)
    bot_types = ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme', 'bot_unico']
    
    for i, bot_type in enumerate(bot_types):
        if bot_type not in bots:
            continue
            
        bot_config = bots[bot_type] if isinstance(bots[bot_type], dict) else {}
        info = bot_info.get(bot_type, {'name': bot_type, 'desc': '', 'color': '#333'})
        
        is_enabled = bot_config.get('enabled', False)  # Sistema híbrido: todos podem operar
        stats = pnl_by_bot.get(bot_type, {})
        
        with col1 if i % 2 == 0 else col2:
            # Card do bot
            status_icon = "🟢" if is_enabled else "🔴"
            status_text = "ATIVO" if is_enabled else "PAUSADO"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {info['color']}, {info['color']}dd); 
                        padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
                <h3>{info['name']} {status_icon}</h3>
                <p style="color: #aaa; margin: 0.5rem 0;">{info['desc']}</p>
                <p><strong>Status:</strong> {status_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Métricas
            mcol1, mcol2, mcol3 = st.columns(3)
            with mcol1:
                win_rate = 0
                if stats.get('trades', 0) > 0:
                    win_rate = (stats.get('wins', 0) / stats['trades']) * 100
                st.metric("Win Rate", f"{win_rate:.1f}%")
            with mcol2:
                st.metric("Trades", stats.get('trades', 0))
            with mcol3:
                pnl_today = daily_pnl.get(bot_type, 0)
                st.metric("PnL Hoje", f"${pnl_today:+.2f}")
            
            # Botão de controle - Sistema híbrido: todos podem operar simultaneamente
            if is_enabled:
                if st.button(f"⏸️ Pausar {info['name']}", key=f"pause_{bot_type}", use_container_width=True):
                    bots[bot_type]['enabled'] = False
                    if 'bots' in config:
                        config['bots'] = bots
                    save_bots_config(config)
                    st.success(f"✅ {info['name']} pausado!")
                    st.rerun()
            else:
                if st.button(f"▶️ Ativar {info['name']}", key=f"activate_{bot_type}", type="primary", use_container_width=True):
                    bots[bot_type]['enabled'] = True
                    if 'bots' in config:
                        config['bots'] = bots
                    save_bots_config(config)
                    st.success(f"✅ {info['name']} ativado!")
                    st.rerun()
            
            st.markdown("---")
    
    # ===== SEÇÃO: AÇÕES RÁPIDAS =====
    st.header("🚀 Ações Rápidas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ Ativar TODOS", use_container_width=True):
            for bot_type in bot_types:
                if bot_type in bots and isinstance(bots[bot_type], dict):
                    bots[bot_type]['enabled'] = True
            if 'bots' in config:
                config['bots'] = bots
            save_bots_config(config)
            st.success("Todos os bots ativados!")
            st.rerun()
    
    with col2:
        if st.button("⏸️ Pausar TODOS", use_container_width=True):
            for bot_type in bot_types:
                if bot_type in bots and isinstance(bots[bot_type], dict):
                    bots[bot_type]['enabled'] = False
            if 'bots' in config:
                config['bots'] = bots
            save_bots_config(config)
            st.success("Todos os bots pausados!")
            st.rerun()
    
    with col3:
        if st.button("🔄 Redistribuir Capital", use_container_width=True):
            # Conta bots ativos
            active_bots = [bt for bt in bot_types if bt in bots and isinstance(bots[bt], dict) and bots[bt].get('enabled', False)]
            if active_bots:
                capital_each = round(100 / len(active_bots), 1)
                for bot_type in bot_types:
                    if bot_type in bots and isinstance(bots[bot_type], dict):
                        if bots[bot_type].get('enabled', False):
                            bots[bot_type]['capital_percent'] = capital_each
                        else:
                            bots[bot_type]['capital_percent'] = 0
                if 'bots' in config:
                    config['bots'] = bots
                save_bots_config(config)
                st.success(f"Capital redistribuído: {capital_each}% por bot ativo")
                st.rerun()
            else:
                st.warning("Nenhum bot ativo para redistribuir capital")
    
    with col4:
        if st.button("🔄 Atualizar Página", use_container_width=True):
            st.rerun()
    
    # ===== SEÇÃO: RESUMO =====
    st.header("📊 Resumo do Sistema")
    
    # Conta status
    active_specialized = sum(1 for bt in bot_types if bt in bots and isinstance(bots[bt], dict) and bots[bt].get('enabled', False))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if unico_enabled:
            st.metric("🎯 Modo Atual", "UnicoBot", delta="Unificado")
        else:
            st.metric("🎯 Modo Atual", "Especializado", delta=f"{active_specialized} bots")
    
    with col2:
        total_trades = sum(pnl_by_bot.get(bt, {}).get('trades', 0) for bt in bot_types)
        st.metric("📈 Total Trades", total_trades)
    
    with col3:
        total_pnl = sum(pnl_by_bot.get(bt, {}).get('total_pnl', 0) for bt in bot_types)
        st.metric("💰 PnL Total", f"${total_pnl:+.2f}")


def main():
    """Função principal do dashboard"""
    
    # Loading spinner
    with st.spinner('🔄 Carregando dashboard...'):
        # Sincroniza estado do bot_unico antes de fazer qualquer coisa
        sync_bot_unico_state()
        
        # Sidebar
        filters = render_sidebar()
        
        # Verifica qual página exibir
        page = filters.get('page', '🏠 Dashboard')
        
        if page == "🎮 Controle Bots":
            render_bot_control_page()
            return
        
        if page == "🤖 AI Intelligence":
            render_ai_page()
            # Auto-refresh
            import time
            time.sleep(filters['refresh_rate'])
            st.rerun()
            return
        
        if page == "⚙️ Configurações":
            render_config_page()
            return
        
        # ===== PÁGINA PRINCIPAL (DASHBOARD) =====
        
        # Carrega dados
        config = load_bots_config()
    history = load_trade_history()
    positions = load_positions()
    
    if not config:
        st.error("❌ Arquivo de configuração não encontrado!")
        st.info("Execute o coordenador primeiro ou verifique se o arquivo config/bots_config.yaml existe.")
        return
    
    # Estatísticas globais
    render_global_stats({}, history)
    
    st.markdown("---")
    
    # Cards dos bots
    st.header("🤖 Bots Especializados")
    
    bot_types = ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme', 'bot_unico']
    
    # 2 bots por linha
    col1, col2 = st.columns(2)
    
    for i, bot_type in enumerate(bot_types):
        if bot_type in config:
            # Filtra se necessário
            if filters['selected_bot'] != 'Todos' and filters['selected_bot'] != bot_type:
                continue
            
            with col1 if i % 2 == 0 else col2:
                render_bot_card(bot_type, config[bot_type], history, positions)
    
    st.markdown("---")
    
    # Watchlist - Oportunidades Detectadas
    st.header("🔍 Watchlist - Oportunidades em Cryptos Externas")
    
    watchlist_alerts = load_watchlist_alerts()
    
    if watchlist_alerts:
        st.success(f"🎯 {len(watchlist_alerts)} oportunidades detectadas!")
        
        alert_data = []
        for alert in watchlist_alerts[:10]:  # Top 10
            rsi = alert.get('rsi', 0)
            rsi_color = "🟢" if rsi < 25 else "🟡" if rsi < 30 else "🟠"
            
            bot_suggestion = {
                'bot_estavel': '🔵 Bot Estavel',
                'bot_medio': '🟢 Bot Medio',
                'bot_volatil': '🟡 Bot Volatil',
                'bot_meme': '🔴 Bot Meme'
            }
            
            alert_data.append({
                'Symbol': alert.get('symbol', ''),
                'Nome': alert.get('name', ''),
                'RSI': f"{rsi_color} {rsi:.1f}",
                'Categoria': alert.get('category', '').title(),
                'Preco': f"${alert.get('price', 0):.4f}",
                'Bot Sugerido': bot_suggestion.get(alert.get('suggested_bot', ''), '🤖'),
                'Hora': alert.get('timestamp', '')[:19] if alert.get('timestamp') else ''
            })
        
        df_alerts = pd.DataFrame(alert_data)
        st.dataframe(df_alerts, use_container_width=True, height=300)
        
        st.info("💡 Cryptos com RSI baixo podem ser boas oportunidades. Considere adicionar ao portfolio do bot correspondente.")
    else:
        st.info("🔎 Nenhuma oportunidade detectada no momento. O sistema escaneia a watchlist a cada 5 minutos.")
    
    st.markdown("---")
    
    # Gráficos
    render_charts(history)
    
    st.markdown("---")
    
    # Histórico completo
    st.header("📜 Histórico Completo de Trades")
    
    if history:
        # Filtra por bot se necessário
        if filters['selected_bot'] != 'Todos':
            filtered_history = [t for t in history if t.get('bot_type') == filters['selected_bot']]
        else:
            filtered_history = history
        
        # Ordena por data (mais recente primeiro)
        filtered_history = sorted(filtered_history, key=lambda x: x.get('exit_time', ''), reverse=True)
        
        # Limita a 100 registros
        filtered_history = filtered_history[:100]
        
        bot_names = {
            'bot_estavel': '🔵 Estável',
            'bot_medio': '🟢 Médio',
            'bot_volatil': '🟡 Volátil',
            'bot_meme': '🔴 Meme',
            'bot_unico': '⚡ Unico'
        }
        
        history_data = []
        for trade in filtered_history:
            pnl = trade.get('pnl_usd', 0)
            history_data.append({
                'Data/Hora': trade.get('exit_time', '')[:19],
                'Bot': bot_names.get(trade.get('bot_type', ''), '🤖'),
                'Symbol': trade.get('symbol', ''),
                'Entrada': f"${trade.get('entry_price', 0):.4f}",
                'Saída': f"${trade.get('exit_price', 0):.4f}",
                'PnL': f"${pnl:+.2f}",
                'PnL %': f"{trade.get('pnl_pct', 0):+.2f}%",
                'Duração': f"{trade.get('duration_min', 0):.1f}m",
                'Razão': trade.get('reason', '')[:40]
            })
        
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("Nenhum trade registrado ainda")
    
    # Auto-refresh
    import time
    time.sleep(filters['refresh_rate'])
    st.rerun()


if __name__ == "__main__":
    main()
