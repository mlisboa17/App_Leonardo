"""
Dashboard de Posições - Gráficos em Tempo Real
Visualiza as posições abertas com gráficos interativos
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from pathlib import Path

# Auto-refresh (optional)
try:
    from streamlit_autorefresh import st_autorefresh
    _ = st_autorefresh(interval=5 * 1000, key="autorefresh_positions")
except Exception:
    pass

st.set_page_config(
    page_title="Posições - R7 Trading",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Dashboard de Posições - R7 Trading Bot")

# Carregar dados
@st.cache_data(ttl=3)
def load_data():
    """Carrega dados de posições e saldo"""
    try:
        with open('data/multibot_positions.json') as f:
            positions = json.load(f)
    except:
        positions = {}
    
    try:
        with open('data/dashboard_balances.json') as f:
            balances = json.load(f)
    except:
        balances = {'total_balance': 0, 'bots': {}}
    
    return positions, balances

positions, balances = load_data()

# ============ MÉTRICAS PRINCIPAIS ============
st.subheader("📈 Métricas Principais")
col1, col2, col3, col4 = st.columns(4)

with col1:
    num_pos = len(positions)
    st.metric("📍 Posições Abertas", num_pos, delta=None)

with col2:
    total_pnl = sum([float(p.get('pnl', 0)) for p in positions.values() if isinstance(p, dict)])
    delta_color = "🟢" if total_pnl >= 0 else "🔴"
    st.metric(f"{delta_color} PnL Total", f"${total_pnl:.2f}", 
              delta=f"{(total_pnl/100):.1f}%" if total_pnl else "0%")

with col3:
    total_capital = sum([float(p.get('valor_entrada', 0)) for p in positions.values() if isinstance(p, dict)])
    st.metric("💰 Capital Investido", f"${total_capital:.2f}")

with col4:
    saldo = balances.get('total_balance', 0)
    st.metric("💎 Saldo Disponível", f"${saldo:.2f}")

st.divider()

# ============ GRÁFICOS ============
if positions:
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Gráficos", "📋 Tabela Detalhada", "🤖 Por Bot", "💹 Performance"])
    
    # Preparar dados
    cryptos_list = []
    pnls_list = []
    valores_list = []
    bots_list = []
    
    for crypto, data in positions.items():
        if isinstance(data, dict):
            cryptos_list.append(crypto.replace('USDT', ''))
            pnls_list.append(float(data.get('pnl', 0)))
            valores_list.append(float(data.get('valor_entrada', 0)))
            bots_list.append(data.get('bot', 'Unknown'))
    
    # ======= TAB 1: GRÁFICOS =======
    with tab1:
        col1, col2 = st.columns(2)
        
            # Gráfico 1: PnL por Crypto (Linha)
        with col1:
                fig_pnl = px.line(
                    x=cryptos_list,
                    y=pnls_list,
                    title="📊 Profit/Loss por Posição",
                    labels={'x': 'Cryptocurrency', 'y': 'PnL (USDT)'},
                    markers=True
                )
                fig_pnl.update_traces(marker=dict(size=10), text=[f"${v:.2f}" for v in pnls_list], textposition='top center')
                fig_pnl.update_layout(
                    height=450,
                    hovermode='x unified',
                    showlegend=False
                )
                st.plotly_chart(fig_pnl, use_container_width=True)
        
        # Gráfico 2: Distribuição de Capital (Pizza)
        with col2:
            fig_dist = go.Figure(data=[go.Pie(
                labels=cryptos_list,
                values=valores_list,
                title="💰 Distribuição do Capital",
                hole=0,
                textposition='inside',
                textinfo='label+percent'
            )])
            fig_dist.update_layout(height=450)
            st.plotly_chart(fig_dist, use_container_width=True)
        
        # Gráfico 3: Quantidade por Crypto (Scatter)
        st.subheader("📍 Quantidade de Coins por Posição")
        qtds_list = [float(p.get('quantidade', 0)) for p in positions.values() if isinstance(p, dict)]
        
        fig_qtd = px.scatter(
            x=cryptos_list, 
            y=qtds_list,
            size=qtds_list,
            color=pnls_list,
            color_continuous_scale='RdYlGn',
            title="Quantidade de Coins",
            labels={'x': 'Cryptocurrency', 'y': 'Quantidade'},
            text=cryptos_list
        )
        fig_qtd.update_traces(textposition='top center')
        fig_qtd.update_layout(height=400)
        st.plotly_chart(fig_qtd, use_container_width=True)
    
    # ======= TAB 2: TABELA DETALHADA =======
    with tab2:
        st.subheader("📋 Detalhes das Posições")
        
        df_positions = pd.DataFrame([
            {
                'Crypto': k.replace('USDT', ''),
                'Quantidade': f"{v.get('quantidade', 0):.6f}",
                'Valor Entrada': f"${v.get('valor_entrada', 0):.2f}",
                'Preço Atual': f"${v.get('preco_atual', 0):.2f}",
                'PnL': f"${v.get('pnl', 0):.2f}",
                'PnL %': f"{v.get('pnl_percent', 0):.2f}%",
                'Bot': v.get('bot', 'Unknown'),
                'Status': '🟢' if v.get('pnl', 0) >= 0 else '🔴'
            }
            for k, v in positions.items() if isinstance(v, dict)
        ])
        
        st.dataframe(df_positions, use_container_width=True, height=400)
        
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Posições", len(df_positions))
        with col2:
            wins = len([p for p in pnls_list if p > 0])
            st.metric("Posições em Lucro", f"{wins}/{len(pnls_list)}")
        with col3:
            avg_pnl = sum(pnls_list) / len(pnls_list) if pnls_list else 0
            st.metric("PnL Médio", f"${avg_pnl:.2f}")
    
    # ======= TAB 3: ANÁLISE POR BOT =======
    with tab3:
        st.subheader("🤖 Performance por Bot")
        
        # Agrupar por bot
        bots_stats = {}
        for i, bot in enumerate(bots_list):
            if bot not in bots_stats:
                bots_stats[bot] = {
                    'posicoes': 0,
                    'pnl': 0,
                    'capital': 0,
                    'cryptos': []
                }
            bots_stats[bot]['posicoes'] += 1
            bots_stats[bot]['pnl'] += pnls_list[i]
            bots_stats[bot]['capital'] += valores_list[i]
            bots_stats[bot]['cryptos'].append(cryptos_list[i])
        
        # Gráfico - PnL por Bot (Linha)
        fig_bots = px.line(
            x=list(bots_stats.keys()),
            y=[data['pnl'] for data in bots_stats.values()],
            title="🤖 PnL por Bot",
            labels={'x': 'Bot', 'y': 'PnL Total (USDT)'},
            markers=True
        )
        fig_bots.update_traces(marker=dict(size=10), text=[f"${data['pnl']:.2f}" for data in bots_stats.values()], textposition='top center')
        fig_bots.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_bots, use_container_width=True)
        
        # Tabela detalhada por bot
        st.subheader("📊 Resumo Detalhado")
        df_bots = pd.DataFrame([
            {
                'Bot': bot,
                'Posições': data['posicoes'],
                'PnL Total': f"${data['pnl']:.2f}",
                'Capital': f"${data['capital']:.2f}",
                'PnL Médio': f"${data['pnl']/data['posicoes']:.2f}",
                'Cryptos': ', '.join(data['cryptos'])
            }
            for bot, data in bots_stats.items()
        ])
        st.dataframe(df_bots, use_container_width=True)
    
    # ======= TAB 4: PERFORMANCE =======
    with tab4:
        st.subheader("💹 Análise de Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico: PnL Acumulado
            pnl_sorted = sorted(pnls_list, reverse=True)
            fig_cumsum = go.Figure(data=[
                go.Scatter(
                    x=cryptos_list,
                    y=pnls_list,
                    mode='markers+lines',
                    marker=dict(size=12, color=pnls_list, colorscale='RdYlGn', showscale=True),
                    line=dict(color='rgba(100,100,100,0.2)'),
                    text=[f"${v:.2f}" for v in pnls_list],
                    textposition='top center'
                )
            ])
            fig_cumsum.update_layout(
                title="Tendência de PnL",
                xaxis_title="Posição",
                yaxis_title="PnL (USDT)",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig_cumsum, use_container_width=True)
        
        with col2:
            # Box plot: Distribuição de PnL
            fig_box = go.Figure(data=[
                go.Box(
                    y=pnls_list,
                    name='PnL',
                    boxmean='sd',
                    marker_color='lightblue',
                    jitter=0.3,
                    pointpos=-1.8
                )
            ])
            fig_box.update_layout(
                title="Distribuição de PnL",
                yaxis_title="PnL (USDT)",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_box, use_container_width=True)
        
        # Estatísticas resumidas
        st.subheader("📊 Estatísticas Resumidas")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("PnL Máximo", f"${max(pnls_list):.2f}" if pnls_list else "$0.00")
        with col2:
            st.metric("PnL Mínimo", f"${min(pnls_list):.2f}" if pnls_list else "$0.00")
        with col3:
            median_pnl = sorted(pnls_list)[len(pnls_list)//2] if pnls_list else 0
            st.metric("PnL Mediano", f"${median_pnl:.2f}")
        with col4:
            std_pnl = (sum([(p - sum(pnls_list)/len(pnls_list))**2 for p in pnls_list]) / len(pnls_list)) ** 0.5 if pnls_list else 0
            st.metric("Desvio Padrão", f"${std_pnl:.2f}")

else:
    st.warning("⚠️ Nenhuma posição aberta no momento")
    st.info("Os dados serão carregados quando houver posições ativas nos bots")

st.divider()

# Footer
st.markdown("""
---
**R7 Trading Bot v2.0** | Dashboard de Posições
- 🔄 Atualizado a cada 3 segundos
- 📍 Todas as posições monitoradas em tempo real
- 💰 Distribuição automática de capital
- 🤖 4 bots especializados em operação
""")
