"""
============================================================
DASHBOARD MULTI-BOT - App R7 (REFATORADO)
============================================================

Dashboard Streamlit simplificado que usa estrutura modular.

Uso:
    streamlit run frontend/dashboard_multibot_v2.py

============================================================
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports modulares
from frontend.utils.session_manager import (
    init_session_state,
    get_config,
    get_positions,
    get_history,
    get_balances,
    get_watchlist,
    get_unico_config,
    force_reload_all
)
from frontend.utils.calculators import (
    get_pnl_by_bot,
    get_daily_pnl,
    get_monthly_pnl
)

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
    .bot-unico { background: linear-gradient(135deg, #4a1e5f, #6d2d8f); }
    
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: bold;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 1.2rem !important;
    }
    
    h1 { font-size: 2.8rem !important; }
    h2 { font-size: 2.2rem !important; }
    h3 { font-size: 1.8rem !important; }
    
    .dataframe { font-size: 1.1rem !important; }
    
    .stButton > button {
        font-size: 1.2rem !important;
        padding: 0.8rem 1.5rem !important;
    }
    
    /* SIDEBAR AUMENTADO */
    section[data-testid="stSidebar"] {
        width: 350px !important;
        min-width: 350px !important;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-size: 2rem !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stMetricValue"] {
        font-size: 3rem !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stMetricLabel"] {
        font-size: 1.5rem !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button {
        font-size: 1.5rem !important;
        padding: 1rem 2rem !important;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def render_global_stats():
    """Renderiza estatísticas globais"""
    st.markdown('<div class="main-header">🚀 APP R7 - TRADING BOT SYSTEM</div>', unsafe_allow_html=True)
    
    history = get_history()
    balances = get_balances()
    config = get_config()
    unico_config = get_unico_config()
    
    # Modo ativo
    bot_unico_enabled = unico_config.get('enabled', False) if unico_config else False
    operation_mode = unico_config.get('operation_mode', 'SOLO') if unico_config else 'SOLO'
    
    if bot_unico_enabled:
        if operation_mode == 'SOLO':
            st.success("⚡ **MODO: BOT ÚNICO SOLO** - Controle centralizado de todas as cryptos")
        elif operation_mode == 'HYBRID':
            st.success("⚡ **MODO: BOT ÚNICO HÍBRIDO** - Trabalhando junto com os 4 bots (+1 no sistema)")
        elif operation_mode == 'FOMINHA':
            st.warning("🤑 **MODO: FOMINHA ATIVO** - IA AGRESSIVA | Bot Único leva 70% dos lucros | Monitoramento 24/7")
        elif operation_mode == 'EQUIPE':
            st.info("🤝 **MODO: EQUIPE COLABORATIVA** - 5 bots trabalhando juntos | Lucro dividido igualmente | IA coordena")
    else:
        st.info("🔵🟢🟡🔴 **MODO: 4 BOTS ESPECIALIZADOS** - Operação diversificada")
    
    # Capital e PnL
    CAPITAL_INICIAL = 1000.0
    saldo_total = balances['total_balance']
    pnl_real = saldo_total - CAPITAL_INICIAL
    pnl_real_pct = (pnl_real / CAPITAL_INICIAL * 100) if CAPITAL_INICIAL > 0 else 0
    
    # LINHA 1: SALDOS
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
    
    # LINHA 2: META DIÁRIA
    st.subheader("🎯 PROGRESSÃO META DIÁRIA")
    
    today = datetime.now().date().isoformat()
    daily_trades = [t for t in history if t.get('exit_time', t.get('timestamp', '')).startswith(today)]
    daily_pnl = sum(t.get('pnl_usd', 0) for t in daily_trades)
    daily_target = 3.33
    daily_progress = (daily_pnl / daily_target * 100) if daily_target > 0 else 0
    
    progress_color = "🟢" if daily_progress >= 100 else "🟡" if daily_progress >= 50 else "🔴"
    if daily_pnl < 0:
        progress_color = "🔴"
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        progress_value = min(daily_progress / 100, 1.0) if daily_progress >= 0 else 0
        st.progress(progress_value)
        
        if daily_pnl < 0:
            st.caption(f"{progress_color} Progresso: **{daily_pnl:.2f}$ de {daily_target:.2f}$ (Meta não atingida)**")
        else:
            st.caption(f"{progress_color} Progresso: **{daily_progress:.1f}% ({daily_pnl:.2f}$ de {daily_target:.2f}$)**")
    
    with col2:
        pnl_color = "📈" if daily_pnl >= 0 else "📉"
        st.metric(f"{pnl_color} PnL Hoje", f"${daily_pnl:+.2f}")
    
    with col3:
        st.metric(f"🎯 Meta Diária", f"${daily_target:.2f}")
    
    st.markdown("---")
    
    # LINHA 3: ESTATÍSTICAS
    st.subheader("📈 ESTATÍSTICAS")
    
    total_pnl = sum(t.get('pnl_usd', 0) for t in history)
    total_trades = len(history)
    wins = sum(1 for t in history if t.get('pnl_usd', 0) > 0)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    current_month = datetime.now().strftime('%Y-%m')
    monthly_trades = [t for t in history if t.get('exit_time', t.get('timestamp', '')).startswith(current_month)]
    monthly_pnl = sum(t.get('pnl_usd', 0) for t in monthly_trades)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💰 PnL Total", f"${total_pnl:.2f}")
    
    with col2:
        st.metric("📅 Lucro Mensal", f"${monthly_pnl:+.2f}")
    
    with col3:
        positions = get_positions()
        st.metric("📍 Posições Abertas", f"{len(positions)}")
    
    with col4:
        st.metric("📈 Total Trades", f"{total_trades}", delta=f"{win_rate:.1f}% WR")
    
    with col5:
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        st.metric("💵 Média/Trade", f"${avg_pnl:.2f}")


def render_bot_card(bot_type: str, bot_config: dict):
    """Renderiza card resumido de um bot"""
    
    bot_styles = {
        'bot_estavel': ('🔵', 'bot-estavel', '#4a90d9', 'Cryptos estáveis'),
        'bot_medio': ('🟢', 'bot-medio', '#4ad94a', 'Média volatilidade'),
        'bot_volatil': ('🟡', 'bot-volatil', '#d9d94a', 'Alta volatilidade'),
        'bot_meme': ('🔴', 'bot-meme', '#d94a4a', 'Meme coins'),
        'bot_unico': ('⚡', 'bot-unico', '#9b4de4', 'Bot Unificado')
    }
    
    emoji, css_class, color, tipo = bot_styles.get(bot_type, ('🤖', '', '#888', 'Bot'))
    name = bot_config.get('name', bot_type)
    enabled = bot_config.get('enabled', True)
    
    history = get_history()
    positions = get_positions()
    
    bot_trades = [t for t in history if t.get('bot_type') == bot_type]
    total_pnl = sum(t.get('pnl_usd', 0) for t in bot_trades)
    trades_count = len(bot_trades)
    wins = sum(1 for t in bot_trades if t.get('pnl_usd', 0) > 0)
    win_rate = (wins / trades_count * 100) if trades_count > 0 else 0
    
    today = datetime.now().date().isoformat()
    daily_trades = [t for t in bot_trades if t.get('exit_time', t.get('timestamp', '')).startswith(today)]
    daily_pnl = sum(t.get('pnl_usd', 0) for t in daily_trades)
    
    bot_positions = {k: v for k, v in positions.items() if v.get('bot_type') == bot_type}
    
    status = "🟢 ATIVO" if enabled else "⏸️ PAUSADO"
    pnl_emoji = "📈" if total_pnl >= 0 else "📉"
    
    with st.container():
        st.markdown(f"""
        <div class="bot-card {css_class}" style="border-left: 4px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin: 0;">{emoji} {name}</h2>
                <span style="font-size: 0.9rem;">{status}</span>
            </div>
            <p style="opacity: 0.7; margin: 5px 0;">{tipo}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 PnL Hoje", f"${daily_pnl:+.2f}")
        
        with col2:
            st.metric(f"{pnl_emoji} PnL Total", f"${total_pnl:+.2f}")
        
        with col3:
            st.metric("📍 Posições", f"{len(bot_positions)}")
        
        with col4:
            wr_emoji = "✅" if win_rate >= 60 else "🟡" if win_rate >= 40 else "❌"
            st.metric(f"{wr_emoji} Win Rate", f"{win_rate:.1f}%")


def render_charts():
    """Renderiza gráficos principais"""
    st.header("📊 Gráficos de Performance")
    
    history = get_history()
    
    if not history:
        st.info("Nenhum histórico disponível")
        return
    
    pnl_by_bot = get_pnl_by_bot(history)
    bot_names = {
        'bot_estavel': '🔵 Estável',
        'bot_medio': '🟢 Médio',
        'bot_volatil': '🟡 Volátil',
        'bot_meme': '🔴 Meme',
        'bot_unico': '⚡ Unico'
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        chart_data = []
        for bot_type, stats in pnl_by_bot.items():
            chart_data.append({
                'Bot': bot_names.get(bot_type, bot_type),
                'PnL': stats['total_pnl']
            })
        
        if chart_data:
            df = pd.DataFrame(chart_data)
            fig = px.line(df, x='Bot', y='PnL', markers=True, title='PnL Total por Bot')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
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
            fig.add_trace(go.Scatter(name='Vitórias', x=df['Bot'], y=df['Vitórias'], mode='lines+markers'))
            fig.add_trace(go.Scatter(name='Derrotas', x=df['Bot'], y=df['Derrotas'], mode='lines+markers'))
            fig.update_layout(title='Vitórias vs Derrotas')
            st.plotly_chart(fig, use_container_width=True)


def main():
    """Função principal do dashboard"""
    
    # Inicializa session_state
    with st.spinner('🔄 Carregando dashboard...'):
        init_session_state()
    
    # Sidebar
    st.sidebar.markdown("# 🎛️ Controles")
    st.sidebar.markdown("---")
    
    num_positions = len(get_positions())
    st.sidebar.markdown(f"""
    <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #1e3a5f, #2d5a87); border-radius: 10px; margin-bottom: 1rem;'>
        <div style='font-size: 1.5rem; color: #aaa; margin-bottom: 0.5rem;'>📍 POSIÇÕES ABERTAS</div>
        <div style='font-size: 3.5rem; font-weight: bold; color: #fff;'>{num_positions}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🔄 ATUALIZAR TODOS OS DADOS", use_container_width=True):
        force_reload_all()
        st.rerun()
    
    # PÁGINA PRINCIPAL
    render_global_stats()
    
    st.markdown("---")
    
    # Cards dos bots
    st.header("🤖 Bots Ativos")
    
    config = get_config()
    
    if config:
        bot_types = ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme', 'bot_unico']
        
        col1, col2 = st.columns(2)
        
        for i, bot_type in enumerate(bot_types):
            if bot_type in config:
                with col1 if i % 2 == 0 else col2:
                    render_bot_card(bot_type, config[bot_type])
    
    st.markdown("---")
    
    # Gráficos
    render_charts()
    
    st.markdown("---")
    
    # Watchlist
    st.header("🔍 Watchlist - Oportunidades Detectadas")
    
    watchlist = get_watchlist()
    
    if watchlist:
        st.success(f"🎯 {len(watchlist)} oportunidades!")
        alert_data = []
        for alert in watchlist[:10]:
            alert_data.append({
                'Symbol': alert.get('symbol', ''),
                'Nome': alert.get('name', ''),
                'RSI': f"{alert.get('rsi', 0):.1f}",
                'Preço': f"${alert.get('price', 0):.4f}",
                'Categoria': alert.get('category', '').title()
            })
        
        st.dataframe(pd.DataFrame(alert_data), use_container_width=True)
    else:
        st.info("🔎 Nenhuma oportunidade detectada no momento")


if __name__ == "__main__":
    main()
