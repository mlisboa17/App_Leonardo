"""
Dashboard PnL Detalhado - Ganho do Dia/Mês/Geral
Mostra por que não está ganhando com análise diagnostica
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(
    page_title="PnL Detalhado - R7 Trading",
    page_icon="💰",
    layout="wide"
)

st.title("💰 PnL Detalhado")
st.markdown("**Ganho do Dia | Mês | Geral com análise de problemas**")

# ============================================================================
# FUNÇÕES DE CARREGAMENTO
# ============================================================================

@st.cache_data(ttl=3)
def load_all_data():
    """Carrega todos os dados necessários"""
    data = {
        'trades': [],
        'coordinator': {},
        'balances': {},
        'positions': {},
        'initial_capital': 1000.0,
        'timestamp': datetime.now()
    }
    
    # Histórico de trades
    try:
        with open('data/all_trades_history.json') as f:
            data['trades'] = json.load(f)
    except:
        data['trades'] = []
    
    # Coordinator stats
    try:
        with open('data/coordinator_stats.json') as f:
            data['coordinator'] = json.load(f)
    except:
        data['coordinator'] = {}
    
    # Balances
    try:
        with open('data/dashboard_balances.json') as f:
            data['balances'] = json.load(f)
    except:
        data['balances'] = {}
    
    # Positions
    try:
        with open('data/multibot_positions.json') as f:
            data['positions'] = json.load(f)
    except:
        data['positions'] = {}
    
    # Capital inicial
    try:
        with open('data/initial_capital.json') as f:
            info = json.load(f)
            data['initial_capital'] = info.get('capital', 1000.0)
    except:
        pass
    
    return data

def calc_pnl_by_period(trades):
    """Calcula PnL por período (dia, mês, geral)"""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    pnl_dia = 0
    pnl_mes = 0
    pnl_geral = 0
    count_dia = 0
    count_mes = 0
    count_geral = len(trades)
    
    for trade in trades:
        try:
            profit = float(trade.get('profit_loss', 0))
            pnl_geral += profit
            
            trade_time = datetime.fromisoformat(trade.get('timestamp', ''))
            
            if trade_time >= today_start:
                pnl_dia += profit
                count_dia += 1
            
            if trade_time >= month_start:
                pnl_mes += profit
                count_mes += 1
        except:
            pass
    
    return {
        'pnl_dia': pnl_dia,
        'count_dia': count_dia,
        'pnl_mes': pnl_mes,
        'count_mes': count_mes,
        'pnl_geral': pnl_geral,
        'count_geral': count_geral,
    }

def calc_pnl_per_bot(trades):
    """Calcula PnL por bot em cada período (dia, mês, geral)"""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Inicializar estrutura de dados
    bots = {
        'bot_estavel': {'nome': '🐢 Estável', 'dia': 0, 'mes': 0, 'geral': 0, 'count_dia': 0, 'count_mes': 0},
        'bot_medio': {'nome': '⚖️ Médio', 'dia': 0, 'mes': 0, 'geral': 0, 'count_dia': 0, 'count_mes': 0},
        'bot_volatil': {'nome': '📈 Volátil', 'dia': 0, 'mes': 0, 'geral': 0, 'count_dia': 0, 'count_mes': 0},
        'bot_meme': {'nome': '🎲 Meme', 'dia': 0, 'mes': 0, 'geral': 0, 'count_dia': 0, 'count_mes': 0},
        'unico_bot': {'nome': '🤖 Unico', 'dia': 0, 'mes': 0, 'geral': 0, 'count_dia': 0, 'count_mes': 0},
    }
    
    # Processar trades
    for trade in trades:
        try:
            bot_type = trade.get('bot_type', '')
            profit = float(trade.get('profit_loss', 0))
            trade_time = datetime.fromisoformat(trade.get('timestamp', ''))
            
            # Encontrar bot correspondente
            for bot_key in bots.keys():
                if bot_key in bot_type.lower():
                    bots[bot_key]['geral'] += profit
                    
                    if trade_time >= today_start:
                        bots[bot_key]['dia'] += profit
                        bots[bot_key]['count_dia'] += 1
                    
                    if trade_time >= month_start:
                        bots[bot_key]['mes'] += profit
                        bots[bot_key]['count_mes'] += 1
                    break
        except:
            pass
    
    return bots

def calc_balance_info(data, initial_capital):
    """Calcula informações de saldo"""
    current_balance = data['balances'].get('total_balance', initial_capital)
    
    return {
        'current_balance': current_balance,
        'initial_capital': initial_capital,
        'pnl': current_balance - initial_capital,
        'pnl_pct': ((current_balance - initial_capital) / initial_capital * 100) if initial_capital > 0 else 0
    }

def get_bots_info(data):
    """Retorna info dos 5 bots"""
    bots = {
        'bot_estavel': {
            'name': '🐢 Bot Estável',
            'icon': '🐢',
            'color': '#1e3a5f',
            'amount': 39.15,
            'max_pos': 4,
            'active': False,
            'positions': 0,
            'pnl': 0
        },
        'bot_medio': {
            'name': '⚖️ Bot Médio',
            'icon': '⚖️',
            'color': '#1e5f3a',
            'amount': 39.15,
            'max_pos': 4,
            'active': False,
            'positions': 0,
            'pnl': 0
        },
        'bot_volatil': {
            'name': '📈 Bot Volátil',
            'icon': '📈',
            'color': '#5f5f1e',
            'amount': 39.15,
            'max_pos': 3,
            'active': False,
            'positions': 0,
            'pnl': 0
        },
        'bot_meme': {
            'name': '🎲 Bot Meme',
            'icon': '🎲',
            'color': '#5f1e1e',
            'amount': 30.00,
            'max_pos': 2,
            'active': False,
            'positions': 0,
            'pnl': 0
        },
        'unico_bot': {
            'name': '🤖 Unico Bot',
            'icon': '🤖',
            'color': '#1a1a2e',
            'amount': 50.00,
            'max_pos': 9,
            'active': False,
            'positions': 0,
            'pnl': 0
        }
    }
    
    # Atualizar com dados do coordinator
    coordinator = data.get('coordinator', {})
    bots_coord = coordinator.get('bots', {})
    
    for bot_key, bot_info in bots.items():
        if bot_key in bots_coord:
            bot_coord = bots_coord[bot_key]
            bots[bot_key]['active'] = bot_coord.get('is_active', False)
            bots[bot_key]['positions'] = len(bot_coord.get('positions', []))
            bots[bot_key]['pnl'] = bot_coord.get('total_pnl', 0)
    
    return bots

# ============================================================================
# CARREGAR DADOS
# ============================================================================

data = load_all_data()
pnl_periods = calc_pnl_by_period(data['trades'])
pnl_per_bot = calc_pnl_per_bot(data['trades'])
balance_info = calc_balance_info(data, 1000.0)
bots_info = get_bots_info(data)

# ============================================================================
# SEÇÃO 1: KPIs PRINCIPAIS COM CORES
# ============================================================================

st.subheader("📊 KPIs Principais")

col1, col2, col3, col4 = st.columns(4)

with col1:
    capital_color = "🟢" if balance_info['pnl'] >= 0 else "🔴"
    st.markdown(f"""
    ### {capital_color} Capital Atual
    **${balance_info['current_balance']:.2f}**
    
    Inicial: ${balance_info['initial_capital']:.2f}
    """)

with col2:
    dia_color = "🟢" if pnl_periods['pnl_dia'] >= 0 else "🔴"
    st.markdown(f"""
    ### {dia_color} PnL Hoje
    **${pnl_periods['pnl_dia']:+.2f}**
    
    {pnl_periods['count_dia']} trades
    """)

with col3:
    mes_color = "🟢" if pnl_periods['pnl_mes'] >= 0 else "🔴"
    st.markdown(f"""
    ### {mes_color} PnL Este Mês
    **${pnl_periods['pnl_mes']:+.2f}**
    
    {pnl_periods['count_mes']} trades
    """)

with col4:
    geral_color = "🟢" if pnl_periods['pnl_geral'] >= 0 else "🔴"
    roi_color = "🟢" if balance_info['pnl_pct'] >= 0 else "🔴"
    st.markdown(f"""
    ### {geral_color} PnL Geral
    **${pnl_periods['pnl_geral']:+.2f}**
    
    {roi_color} ROI: {balance_info['pnl_pct']:+.2f}%
    """)

# ============================================================================
# SEÇÃO 2: INDICADORES COM CORES HTML
# ============================================================================

st.divider()
st.subheader("🎯 Indicadores Visuais")

col1, col2, col3 = st.columns(3)

# Ganho do dia
with col1:
    if pnl_periods['pnl_dia'] >= 0:
        st.success(f"✅ Ganho Hoje: ${pnl_periods['pnl_dia']:.2f}")
    else:
        st.error(f"❌ Perda Hoje: ${pnl_periods['pnl_dia']:.2f}")
    
    st.progress(
        min((pnl_periods['pnl_dia'] + 50) / 100, 1.0),
        text=f"Meta dia: $2.50"
    )

# Ganho do mês
with col2:
    if pnl_periods['pnl_mes'] >= 0:
        st.success(f"✅ Ganho Mês: ${pnl_periods['pnl_mes']:.2f}")
    else:
        st.error(f"❌ Perda Mês: ${pnl_periods['pnl_mes']:.2f}")
    
    st.progress(
        min(pnl_periods['pnl_mes'] / 75, 1.0),
        text=f"Meta mês: $75.00"
    )

# Ganho geral
with col3:
    if pnl_periods['pnl_geral'] >= 0:
        st.success(f"✅ Ganho Total: ${pnl_periods['pnl_geral']:.2f}")
    else:
        st.error(f"❌ Perda Total: ${pnl_periods['pnl_geral']:.2f}")
    
    st.progress(
        min(pnl_periods['pnl_geral'] / 250, 1.0),
        text=f"Meta geral: $250+"
    )

# ============================================================================
# SEÇÃO 3: STATUS DOS 5 BOTS
# ============================================================================

st.divider()
st.subheader("🤖 Status dos 5 Bots")

bots_ativos = sum(1 for b in bots_info.values() if b['active'])
total_posicoes = sum(b['positions'] for b in bots_info.values())
total_pnl_bots = sum(b['pnl'] for b in bots_info.values())

cols = st.columns(5)

for idx, (bot_key, bot_info) in enumerate(bots_info.items()):
    with cols[idx]:
        status = "🟢 Ativo" if bot_info['active'] else "⏹️ Inativo"
        pnl_cor = "🟢" if bot_info['pnl'] >= 0 else "🔴"
        
        st.markdown(f"""
        ### {bot_info['icon']} {bot_info['name'].split()[1]}
        
        **Status**: {status}
        
        **Posições**: {bot_info['positions']}/{bot_info['max_pos']}
        
        **Amount**: ${bot_info['amount']:.2f}
        
        **{pnl_cor} PnL**: ${bot_info['pnl']:+.2f}
        """)

# ============================================================================
# SEÇÃO 3.5: PnL POR BOT (Dia e Mês)
# ============================================================================

st.divider()
st.subheader("📊 PnL por Bot - Dia | Mês | Geral")

# Criar tabela com PnL por bot
pnl_bot_data = []
for bot_key, bot_pnl in pnl_per_bot.items():
    pnl_bot_data.append({
        'Bot': bot_pnl['nome'],
        'Hoje 📅': f"${bot_pnl['dia']:+.2f}" if bot_pnl['count_dia'] > 0 else "$0.00",
        'Trades Hoje': bot_pnl['count_dia'],
        'Este Mês 📆': f"${bot_pnl['mes']:+.2f}" if bot_pnl['count_mes'] > 0 else "$0.00",
        'Trades Mês': bot_pnl['count_mes'],
        'Geral 📊': f"${bot_pnl['geral']:+.2f}",
    })

df_pnl_bot = pd.DataFrame(pnl_bot_data)

# Exibir tabela colorida
st.markdown("### 📋 Ganho/Perda por Bot")

# Criar HTML colorido para a tabela
html_table = '<table style="width:100%; border-collapse: collapse; font-size: 14px;">'
html_table += '<tr style="background-color: #1a1a2e; color: white;">'
html_table += '<th style="padding: 10px; border: 1px solid #444;">Bot</th>'
html_table += '<th style="padding: 10px; border: 1px solid #444;">Hoje</th>'
html_table += '<th style="padding: 10px; border: 1px solid #444;">Trades</th>'
html_table += '<th style="padding: 10px; border: 1px solid #444;">Este Mês</th>'
html_table += '<th style="padding: 10px; border: 1px solid #444;">Trades</th>'
html_table += '<th style="padding: 10px; border: 1px solid #444;">Geral</th>'
html_table += '</tr>'

for _, row in df_pnl_bot.iterrows():
    # Cores para hoje
    hoje_val = float(row['Hoje 📅'].replace('$', '').replace('+', '').replace('-', '') if row['Hoje 📅'] != '$0.00' else '0')
    hoje_color = '#00cc00' if float(row['Hoje 📅'].split('$')[1].replace('+', '')) > 0 else ('#cc0000' if float(row['Hoje 📅'].split('$')[1].replace('+', '')) < 0 else '#999')
    
    # Cores para mês
    mes_val = float(row['Este Mês 📆'].replace('$', '').replace('+', '').replace('-', '') if row['Este Mês 📆'] != '$0.00' else '0')
    mes_color = '#00cc00' if float(row['Este Mês 📆'].split('$')[1].replace('+', '')) > 0 else ('#cc0000' if float(row['Este Mês 📆'].split('$')[1].replace('+', '')) < 0 else '#999')
    
    # Cores para geral
    geral_color = '#00cc00' if float(row['Geral 📊'].split('$')[1].replace('+', '')) > 0 else ('#cc0000' if float(row['Geral 📊'].split('$')[1].replace('+', '')) < 0 else '#999')
    
    html_table += '<tr style="background-color: #2a2a3e;">'
    html_table += f'<td style="padding: 10px; border: 1px solid #444; font-weight: bold;">{row["Bot"]}</td>'
    html_table += f'<td style="padding: 10px; border: 1px solid #444; color: {hoje_color}; font-weight: bold;">{row["Hoje 📅"]}</td>'
    html_table += f'<td style="padding: 10px; border: 1px solid #444; text-align: center;">{int(row["Trades Hoje"])}</td>'
    html_table += f'<td style="padding: 10px; border: 1px solid #444; color: {mes_color}; font-weight: bold;">{row["Este Mês 📆"]}</td>'
    html_table += f'<td style="padding: 10px; border: 1px solid #444; text-align: center;">{int(row["Trades Mês"])}</td>'
    html_table += f'<td style="padding: 10px; border: 1px solid #444; color: {geral_color}; font-weight: bold;">{row["Geral 📊"]}</td>'
    html_table += '</tr>'

html_table += '</table>'

st.markdown(html_table, unsafe_allow_html=True)

# Cards com resumo visual por bot
st.markdown("### 💳 Resumo Visual")

col1, col2, col3, col4, col5 = st.columns(5)

cols = [col1, col2, col3, col4, col5]
for idx, (bot_key, bot_pnl) in enumerate(pnl_per_bot.items()):
    with cols[idx]:
        dia_color = "🟢" if bot_pnl['dia'] >= 0 else "🔴"
        mes_color = "🟢" if bot_pnl['mes'] >= 0 else "🔴"
        geral_color = "🟢" if bot_pnl['geral'] >= 0 else "🔴"
        
        st.markdown(f"""
        ### {bot_pnl['nome']}
        
        {dia_color} **Hoje**: ${bot_pnl['dia']:+.2f}
        
        {mes_color} **Mês**: ${bot_pnl['mes']:+.2f}
        
        {geral_color} **Geral**: ${bot_pnl['geral']:+.2f}
        """)

# ============================================================================
# SEÇÃO 4: POR QUE NÃO ESTÁ GANHANDO?
# ============================================================================

st.divider()
st.subheader("🔍 Análise: Por Que Não Está Ganhando?")

problemas = []
avisos = []

# Checklist
st.markdown("### ⚠️ Checklist de Diagnóstico")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"**Bots Ativos**: {bots_ativos}/5")
    if bots_ativos == 0:
        st.error("❌ CRÍTICO: Nenhum bot ativo!")
        problemas.append("Nenhum bot está rodando - o sistema não consegue fazer nada.")
    elif bots_ativos < 3:
        st.warning(f"⚠️ Apenas {bots_ativos} bots - baixa diversificação")
        avisos.append(f"Apenas {bots_ativos} bots ativos. Idealmente 4-5 para rentabilidade.")
    else:
        st.success(f"✅ {bots_ativos} bots operando")

with col2:
    st.markdown(f"**Posições Abertas**: {total_posicoes}")
    if total_posicoes == 0:
        st.error("❌ Sem operações ativas!")
        problemas.append("Nenhuma posição aberta - sem exposição ao mercado.")
    elif total_posicoes < 5:
        st.warning(f"⚠️ Poucas posições ({total_posicoes})")
        avisos.append(f"Apenas {total_posicoes} posição(ões). Idealmente 8-15 para ganho consistente.")
    else:
        st.success(f"✅ {total_posicoes} posições ativas")

with col3:
    st.markdown(f"**PnL Total Bots**: ${total_pnl_bots:+.2f}")
    if total_pnl_bots < 0:
        st.error(f"❌ Em prejuízo: ${total_pnl_bots:.2f}")
        problemas.append(f"PnL negativo (${total_pnl_bots:.2f}) - estratégia gerando perdas.")
    else:
        st.success(f"✅ Em lucro: ${total_pnl_bots:.2f}")

# Análise de trades
st.markdown("### 📊 Análise de Trades")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**Total de Trades**: {pnl_periods['count_geral']}")
    if pnl_periods['count_geral'] == 0:
        st.error("❌ Nenhum trade realizado!")
        problemas.append("Nenhum trade foi realizado - verifique a conexão com Binance.")
    elif pnl_periods['count_geral'] < 5:
        st.warning(f"⚠️ Muito poucos trades ({pnl_periods['count_geral']})")
        avisos.append("Poucos trades realizados - bots podem estar com problemas na estratégia.")
    else:
        st.success(f"✅ {pnl_periods['count_geral']} trades realizados")

with col2:
    taxa_lucro = 0
    if pnl_periods['count_geral'] > 0:
        trades_lucro = len([t for t in data['trades'] if float(t.get('profit_loss', 0)) > 0])
        taxa_lucro = (trades_lucro / pnl_periods['count_geral']) * 100
    
    st.markdown(f"**Taxa de Acerto**: {taxa_lucro:.1f}%")
    if taxa_lucro < 40:
        st.warning(f"⚠️ Taxa baixa ({taxa_lucro:.1f}%)")
        avisos.append("Taxa de acerto baixa - revisar estratégia de entrada/saída.")
    else:
        st.success(f"✅ Boa taxa: {taxa_lucro:.1f}%")

# ============================================================================
# SEÇÃO 5: RECOMENDAÇÕES
# ============================================================================

st.divider()
st.subheader("🚀 Recomendações Imediatas")

if problemas:
    st.error("### ❌ Problemas Críticos Encontrados:")
    for problema in problemas:
        st.markdown(f"- {problema}")
    
    st.warning("""
    ### Ações Corretivas:
    1. **Verificar se bots estão rodando**:
       ```bash
       ps aux | grep main_multibot
       ```
    2. **Se não tiver processo, iniciar**:
       ```bash
       cd /home/ubuntu/App_Leonardo
       nohup ./venv/bin/python main_multibot.py > logs/bot.log 2>&1 &
       ```
    3. **Verificar logs**:
       ```bash
       tail -f logs/bot.log
       ```
    """)

if avisos:
    st.warning("### ⚠️ Avisos e Sugestões:")
    for aviso in avisos:
        st.markdown(f"- {aviso}")

if not problemas and not avisos:
    st.success("""
    ### ✅ Sistema Operando Normalmente!
    - Todos os bots estão ativos
    - Posições abertas e monitoradas
    - Estratégia gerando lucro
    
    **Continue monitorando o progresso nos próximos dias.**
    """)

# ============================================================================
# SEÇÃO 6: GRÁFICOS
# ============================================================================

st.divider()
st.subheader("📈 Gráficos de Análise")

col1, col2 = st.columns(2)

with col1:
    # Gráfico PnL por período (Linha)
    periodos = ['Hoje', 'Este Mês', 'Geral']
    valores = [pnl_periods['pnl_dia'], pnl_periods['pnl_mes'], pnl_periods['pnl_geral']]
    cores = ['green' if v >= 0 else 'red' for v in valores]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=periodos, y=valores, mode='lines+markers', marker=dict(color=cores, size=10), text=[f"${v:.2f}" for v in valores], textposition='top center', name='PnL'))
    fig.update_layout(
        title="PnL por Período",
        yaxis_title="USD",
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Gráfico PnL por bot
    bot_names = [b['icon'] + ' ' + b['name'].split()[1] for b in bots_info.values()]
    bot_pnls = [b['pnl'] for b in bots_info.values()]
    bot_cores = ['green' if p >= 0 else 'red' for p in bot_pnls]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bot_names, y=bot_pnls, mode='lines+markers', marker=dict(color=bot_cores, size=10), text=[f"${p:.2f}" for p in bot_pnls], textposition='top center', name='PnL por Bot'))
    fig.update_layout(
        title="PnL por Bot (Geral)",
        yaxis_title="USD",
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# GRÁFICO COMPARATIVO: PnL por Bot - Dia vs Mês vs Geral
# ============================================================================

st.subheader("📊 Comparativo de PnL por Bot")

# Preparar dados para gráfico comparativo
bot_names_compare = [pnl['nome'].split()[1] for pnl in pnl_per_bot.values()]
bot_dias = [pnl['dia'] for pnl in pnl_per_bot.values()]
bot_meses = [pnl['mes'] for pnl in pnl_per_bot.values()]
bot_gerais = [pnl['geral'] for pnl in pnl_per_bot.values()]

fig_compare = go.Figure()
fig_compare.add_trace(go.Scatter(name='Hoje', x=bot_names_compare, y=bot_dias, mode='lines+markers', marker_color='#1f77b4'))
fig_compare.add_trace(go.Scatter(name='Este Mês', x=bot_names_compare, y=bot_meses, mode='lines+markers', marker_color='#ff7f0e'))
fig_compare.add_trace(go.Scatter(name='Geral', x=bot_names_compare, y=bot_gerais, mode='lines+markers', marker_color='#2ca02c'))

fig_compare.update_layout(
    title="PnL Comparativo: Hoje vs Mês vs Geral",
    yaxis_title="USD",
    xaxis_title="Bot",
    height=450,
    hovermode='x unified'
)

st.plotly_chart(fig_compare, use_container_width=True)

# ============================================================================
# SEÇÃO 7: TABELA DE TRADES RECENTES
# ============================================================================

st.divider()
st.subheader("📜 Últimos 20 Trades")

if data['trades']:
    trades_recentes = data['trades'][-20:]
    trades_list = []
    
    for trade in reversed(trades_recentes):
        trades_list.append({
            'Hora': trade.get('timestamp', 'N/A')[:19],
            'Bot': trade.get('bot_type', 'N/A'),
            'Par': trade.get('symbol', 'N/A'),
            'Tipo': trade.get('type', 'N/A'),
            'Preço': f"${float(trade.get('price', 0)):.4f}",
            'Quantidade': f"{float(trade.get('quantity', 0)):.4f}",
            'USD': f"${float(trade.get('amount_usd', 0)):.2f}",
            'PnL': f"${float(trade.get('profit_loss', 0)):+.2f}"
        })
    
    df = pd.DataFrame(trades_list)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Nenhum trade registrado ainda.")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown(f"""
---
**R7 Trading Bot v2.0** | Dashboard PnL Detalhado  
Capital Inicial: $1,000.00 USDT | 5 Bots Paralelos | SmartStrategy v2.0  
Atualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
