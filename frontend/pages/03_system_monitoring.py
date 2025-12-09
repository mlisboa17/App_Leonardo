"""
Dashboard de Monitoramento de Sistemas Automáticos
Monitora status dos sistemas auto-balance, auto-confirm e bot principal
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import math
from pathlib import Path
from datetime import datetime, timedelta

# Auto-refresh (optional - requires streamlit-autorefresh in the environment)
try:
    from streamlit_autorefresh import st_autorefresh
    _ = st_autorefresh(interval=5 * 1000, key="autorefresh_system_monitor")
except Exception:
    # If package not available, page will not auto-refresh but cached data has ttl=5
    pass

st.set_page_config(
    page_title="Sistemas - R7 Trading",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Dashboard de Monitoramento de Sistemas")

# Função para verificar status de arquivo
def check_file_status(filepath):
    """Verifica o status e data da última modificação de um arquivo"""
    path = Path(filepath)
    if path.exists():
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        age = datetime.now() - mtime
        return True, mtime, age
    return False, None, None

@st.cache_data(ttl=5)
def load_system_data():
    """Carrega dados de status dos sistemas"""
    data = {}
    
    # Auto-balance history
    try:
        with open('data/auto_balance_history.json') as f:
            data['auto_balance'] = json.load(f)
    except:
        data['auto_balance'] = []
    
    # Distribution history
    try:
        with open('data/distribution_history.json') as f:
            data['distribution'] = json.load(f)
    except:
        data['distribution'] = []
    
    # Coordinator stats
    try:
        with open('data/coordinator_stats.json') as f:
            data['coordinator'] = json.load(f)
    except:
        data['coordinator'] = {}
    
    # Control log
    try:
        with open('data/control_log.json') as f:
            data['control_log'] = json.load(f)
    except:
        data['control_log'] = []
    
    return data


# ----------------- Novas funções: histórico de trades e métricas -----------------
def _parse_dt(s: str):
    """Parse timestamps robustly, supporting ISO + 'Z'."""
    if not s:
        return None
    try:
        # handle trailing Z
        if s.endswith('Z'):
            s = s.replace('Z', '+00:00')
        # replace space variant
        s = s.replace(' ', 'T') if ' ' in s else s
        return datetime.fromisoformat(s)
    except Exception:
        try:
            # fallback: try to parse common format
            return datetime.strptime(s[:19], '%Y-%m-%dT%H:%M:%S')
        except Exception:
            return None


@st.cache_data(ttl=5)
def load_trades_history():
    """Carrega histórico de trades a partir de alguns caminhos possíveis."""
    candidates = [
        Path('data/all_trades_history.json'),
        Path('data/trades_history.json'),
        Path('data/history/all_trades.json'),
        Path('data/history/trades.json')
    ]
    trades = []
    for p in candidates:
        if p.exists():
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    trades = json.load(f)
                break
            except Exception:
                continue

    # normalize datetime
    for t in trades:
        if '_dt' not in t:
            ts = t.get('timestamp') or t.get('exit_time') or t.get('time') or t.get('date')
            t['_dt'] = _parse_dt(ts) if ts else None
    return trades


def period_bounds(period='day'):
    now = datetime.utcnow()
    if period == 'day':
        start = datetime(now.year, now.month, now.day)
    elif period == 'month':
        start = datetime(now.year, now.month, 1)
    else:
        start = datetime(1970, 1, 1)
    return start, now


def compute_pnl_and_sales(trades, bots_list=None):
    """Compute aggregated pnl, sales (gross SELL value) and fees for global/day/month and per-bot.

    trades: list of trade dicts. Expected keys: bot (or bot_type), side, price, qty, fee, pnl_usd, entry_price, exit_price, timestamp
    returns: (agg_all, agg_day, agg_month) where each is dict mapping bot/global->{pnl,sales,fees,trades}
    """
    start_day, end = period_bounds('day')
    start_month, _ = period_bounds('month')

    def new_bucket():
        return {'pnl': 0.0, 'sales': 0.0, 'fees': 0.0, 'trades': 0}

    agg_all = {'global': new_bucket()}
    agg_day = {'global': new_bucket()}
    agg_month = {'global': new_bucket()}

    for t in trades:
        bot = t.get('bot') or t.get('bot_type') or 'global'
        side = (t.get('side') or '').upper()
        price = float(t.get('price') or t.get('exit_price') or 0)
        qty = float(t.get('qty') or t.get('quantity') or 0)
        fee = float(t.get('fee', 0) or t.get('exchange_fee', 0) or 0)
        pnl = float(t.get('pnl_usd', 0) or 0)
        value = price * qty

        # fallback compute pnl if not provided
        if (not pnl or pnl == 0) and 'entry_price' in t and 'exit_price' in t:
            try:
                entry = float(t.get('entry_price') or 0)
                exitp = float(t.get('exit_price') or 0)
                pnl = (exitp - entry) * qty
            except Exception:
                pnl = 0.0

        for d in (agg_all, agg_day, agg_month):
            if bot not in d:
                d[bot] = new_bucket()

        # update all
        agg_all['global']['pnl'] += pnl
        agg_all['global']['trades'] += 1
        agg_all['global']['fees'] += fee
        agg_all[bot]['pnl'] += pnl
        agg_all[bot]['trades'] += 1
        agg_all[bot]['fees'] += fee
        if side == 'SELL':
            agg_all['global']['sales'] += value
            agg_all[bot]['sales'] += value

        # day/month
        dt = t.get('_dt')
        if dt:
            if start_day <= dt <= end:
                agg_day['global']['pnl'] += pnl
                agg_day['global']['trades'] += 1
                agg_day['global']['fees'] += fee
                agg_day[bot]['pnl'] += pnl
                agg_day[bot]['trades'] += 1
                agg_day[bot]['fees'] += fee
                if side == 'SELL':
                    agg_day['global']['sales'] += value
                    agg_day[bot]['sales'] += value
            if start_month <= dt <= end:
                agg_month['global']['pnl'] += pnl
                agg_month['global']['trades'] += 1
                agg_month['global']['fees'] += fee
                agg_month[bot]['pnl'] += pnl
                agg_month[bot]['trades'] += 1
                agg_month[bot]['fees'] += fee
                if side == 'SELL':
                    agg_month['global']['sales'] += value
                    agg_month[bot]['sales'] += value

    return agg_all, agg_day, agg_month


# ----------------- Fim das novas funções -----------------


system_data = load_system_data()

# Status dos Sistemas
col1, col2, col3, col4 = st.columns(4)

# Auto-Balance Status
with col1:
    ab_exists, ab_mtime, ab_age = check_file_status('data/auto_balance_history.json')
    if ab_exists and ab_age and ab_age < timedelta(hours=1):
        st.metric("✅ Auto-Balance", "Ativo", f"Há {ab_age.seconds//60}m")
    elif ab_exists:
        st.metric("⚠️ Auto-Balance", "Inativo", f"Há {int(ab_age.total_seconds()/3600)}h")
    else:
        st.metric("❌ Auto-Balance", "Erro", "Arquivo não encontrado")

# Auto-Confirm Status
with col2:
    ac_exists, ac_mtime, ac_age = check_file_status('src/auto_confirm.py')
    if ac_exists:
        st.metric("✅ Auto-Confirm", "Instalado", "Pronto para usar")
    else:
        st.metric("❌ Auto-Confirm", "Erro", "Arquivo não encontrado")

# Main Bot Status
with col3:
    coord_exists, coord_mtime, coord_age = check_file_status('src/coordinator.py')
    if coord_exists and coord_age and coord_age < timedelta(hours=1):
        st.metric("✅ Bot Principal", "Rodando", f"Modificado há {coord_age.seconds//60}m")
    elif coord_exists:
        st.metric("⚠️ Bot Principal", "Desconhecido", "Verificar manualmente")
    else:
        st.metric("❌ Bot Principal", "Erro", "Arquivo não encontrado")

# Streamlit Dashboard
with col4:
    st.metric("✅ Dashboard", "Ativo", "Você está aqui")

st.divider()

# Tabs para diferentes sistemas
tab1, tab2, tab3, tab4 = st.tabs([
    "🤖 Auto-Balance",
    "✋ Auto-Confirm", 
    "📊 Coordinator",
    "📜 Control Log"
])

# TAB 1: Auto-Balance
with tab1:
    st.subheader("Auto-Balance History")
    
    if system_data['auto_balance']:
        df_ab = pd.DataFrame([
            {
                'Timestamp': ab.get('timestamp', 'N/A'),
                'Saldo': f"${ab.get('total_balance', 0):.2f}",
                'Bots': len(ab.get('allocations', {})),
                'Status': '✅ Sucesso' if ab.get('success', False) else '❌ Erro'
            }
            for ab in system_data['auto_balance'][-20:]
        ])
        st.dataframe(df_ab, use_container_width=True)
        
        # Gráfico de evolução
        if len(system_data['auto_balance']) > 1:
            fig = go.Figure()
            
            balances = [ab.get('total_balance', 0) for ab in system_data['auto_balance']]
            
            fig.add_trace(go.Scatter(
                y=balances,
                mode='lines+markers',
                name='Saldo Total',
                fill='tozeroy',
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Evolução do Saldo",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum histórico de auto-balance encontrado")

# TAB 2: Auto-Confirm
with tab2:
    st.subheader("Auto-Confirm Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("⏱️ Timeout Padrão", "5 segundos")
        st.metric("🔄 Modo", "Automático")
    
    with col2:
        st.metric("⌨️ Cancelar", "Ctrl+C")
        st.metric("📊 Fila", "Thread-safe")
    
    st.code("""
from src.auto_confirm import AutoConfirm

# Usar auto-confirm em qualquer lugar
confirm = AutoConfirm()
result = confirm.confirm_action("Deseja executar esta ação?", timeout=5)
""", language="python")
    
    st.info("""
    ✅ **Auto-Confirm Ativo**
    
    - Executa automaticamente em 5 segundos
    - Pode ser cancelado com Ctrl+C
    - Ideal para operações noturnas
    - Integrado ao sistema de distribuição
    """)

# TAB 3: Coordinator
with tab3:
    st.subheader("Coordinator Status")

    if system_data['coordinator']:
        coord = system_data['coordinator']

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🤖 Bots Ativos", len(coord.get('bots', {})))
        with col2:
            st.metric("📊 Posições Abertas", coord.get('total_positions', 0))
        with col3:
            st.metric("💰 Capital Total", f"${coord.get('total_balance', 0):.2f}")

        # Load trades and compute PnL / Sales / Fees
        trades = load_trades_history()
        agg_all, agg_day, agg_month = compute_pnl_and_sales(trades)

        # Global KPIs
        st.subheader("Métricas Globais")
        gcol1, gcol2, gcol3, gcol4 = st.columns(4)
        with gcol1:
            st.metric("PnL Hoje (USDT)", f"${agg_day['global']['pnl']:.2f}")
        with gcol2:
            st.metric("PnL Mês (USDT)", f"${agg_month['global']['pnl']:.2f}")
        with gcol3:
            st.metric("Vendas Hoje (USDT)", f"${agg_day['global']['sales']:.2f}")
        with gcol4:
            st.metric("Taxas Hoje (USDT)", f"${agg_day['global']['fees']:.4f}")

        # Breakdown per-bot
        if 'bots' in coord:
            st.subheader("Detalhes por Bot (PnL / Vendas / Taxas)")
            rows = []
            for bot_name, bot_info in coord.get('bots', {}).items():
                bot_key = bot_name
                display_name = bot_name.replace('bot_', '').title()
                all_b = agg_all.get(bot_key, {'pnl': 0.0, 'sales': 0.0, 'fees': 0.0})
                day_b = agg_day.get(bot_key, {'pnl': 0.0, 'sales': 0.0, 'fees': 0.0})
                month_b = agg_month.get(bot_key, {'pnl': 0.0, 'sales': 0.0, 'fees': 0.0})

                rows.append({
                    'Bot': display_name,
                    'Posições': bot_info.get('positions', 0),
                    'Capital': f"${bot_info.get('capital', 0):.2f}",
                    'PnL Hoje (USDT)': f"${day_b['pnl']:.2f}",
                    'PnL Mês (USDT)': f"${month_b['pnl']:.2f}",
                    'Vendas Hoje (USDT)': f"${day_b['sales']:.2f}",
                    'Taxas Hoje (USDT)': f"${day_b['fees']:.4f}",
                    'Status': '✅ Ativo' if bot_info.get('active', False) else '⏸️ Parado'
                })

            df_bots = pd.DataFrame(rows)
            st.dataframe(df_bots, use_container_width=True)
        else:
            st.info("Nenhum bot encontrado na configuração do coordinator")
    else:
        st.info("Nenhuma estatística do coordinator encontrada")

# TAB 4: Control Log
with tab4:
    st.subheader("Control Log")
    
    if system_data.get('control_log'):
        df_log = pd.DataFrame([
            {
                'Timestamp': log.get('timestamp', 'N/A'),
                'Ação': log.get('action', 'N/A'),
                'Status': log.get('status', 'N/A'),
                'Detalhes': log.get('details', '')[:50] + '...' if log.get('details') else ''
            }
            for log in system_data.get('control_log', [])[-30:]
        ])
        st.dataframe(df_log, use_container_width=True)
        
        # Gráfico de ações ao longo do tempo
        action_counts = {}
        for log in system_data.get('control_log', []):
            action = log.get('action', 'Unknown')
            action_counts[action] = action_counts.get(action, 0) + 1
        
        if action_counts:
            fig_actions = go.Figure(data=[
                go.Scatter(
                    x=list(action_counts.keys()),
                    y=list(action_counts.values()),
                    mode='lines+markers+text',
                    marker=dict(size=12, color='steelblue'),
                    line=dict(width=3, color='steelblue'),
                    text=list(action_counts.values()),
                    textposition='top center'
                )
            ])
            fig_actions.update_layout(
                title="Ações por Tipo",
                xaxis_title="Tipo de Ação",
                yaxis_title="Contagem",
                height=400
            )
            st.plotly_chart(fig_actions, use_container_width=True)
    else:
        st.info("Nenhum controle de log encontrado")

st.divider()

# Recomendações de saúde do sistema
st.subheader("🏥 Diagnóstico do Sistema")

health_checks = []

# Auto-balance
if system_data['auto_balance']:
    last_ab = system_data['auto_balance'][-1]
    ab_age = (datetime.now() - datetime.fromisoformat(last_ab['timestamp'].replace('Z', '+00:00').replace(' ', 'T'))).total_seconds() if 'timestamp' in last_ab else float('inf')
    if ab_age < 3600:
        health_checks.append(("✅", "Auto-Balance", "Executado recentemente"))
    else:
        health_checks.append(("⚠️", "Auto-Balance", f"Última execução há {int(ab_age/3600)}h"))
else:
    health_checks.append(("❌", "Auto-Balance", "Nenhuma execução registrada"))

# Bot coordinator
if system_data['coordinator']:
    if system_data['coordinator'].get('bots'):
        health_checks.append(("✅", "Bot Coordinator", f"{len(system_data['coordinator']['bots'])} bots ativo"))
    else:
        health_checks.append(("⚠️", "Bot Coordinator", "Nenhum bot ativo"))
else:
    health_checks.append(("⚠️", "Bot Coordinator", "Sem dados disponíveis"))

# Control log
if system_data['control_log']:
    health_checks.append(("✅", "Control Log", f"{len(system_data['control_log'])} ações registradas"))
else:
    health_checks.append(("⚠️", "Control Log", "Sem ações registradas"))

for status, sistema, msg in health_checks:
    st.markdown(f"{status} **{sistema}**: {msg}")

st.divider()

# Footer
st.markdown("""
---
**R7 Trading Bot v2.0** | Dashboard de Sistemas
- ⚙️ Monitoramento em tempo real
- 📊 Histórico completo de operações
- 🔧 Status de todos os sistemas automáticos
- 🏥 Diagnóstico de saúde
""")
