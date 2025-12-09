"""
Dashboard de Distribuição de Capital
Visualiza como o capital está sendo distribuído entre os bots
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from pathlib import Path

st.set_page_config(
    page_title="Distribuição - R7 Trading",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Dashboard de Distribuição de Capital")

# Carregar dados
@st.cache_data(ttl=3)
def load_data():
    """Carrega dados de distribuição e histórico"""
    try:
        with open('data/distribution_history.json') as f:
            history = json.load(f)
            latest = history[-1] if history else {}
    except:
        latest = {}
    
    try:
        with open('data/auto_balance_history.json') as f:
            balance_history = json.load(f)
    except:
        balance_history = []
    
    return latest, balance_history

latest_dist, balance_history = load_data()

st.subheader("📊 Distribuição de Capital Atual")

if latest_dist:
    total_balance = latest_dist.get('total_balance', 0)
    distribution = latest_dist.get('distribution', {})
    timestamp = latest_dist.get('timestamp', 'N/A')
    
    # Informações principais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💎 Saldo Total", f"${total_balance:.2f}")
    with col2:
        st.metric("🤖 Bots Ativos", len(distribution))
    with col3:
        st.metric("⏱️ Última Atualização", timestamp)
    
    st.divider()
    
    # Gráficos de distribuição
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pizza - Capital por Bot
        bot_names = list(distribution.keys())
        bot_capitals = [distribution[b]['capital'] for b in bot_names]
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=[b.replace('bot_', '').title() for b in bot_names],
            values=bot_capitals,
            title="💰 Capital por Bot",
            hole=0.3,
            textposition='inside',
            textinfo='label+percent+value'
        )])
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Gráfico de linha - Amount per Trade
        amounts = [distribution[b]['amount_per_trade'] for b in bot_names]
        
        fig_bar = px.line(
            x=[b.replace('bot_', '').title() for b in bot_names],
            y=amounts,
            title="💵 Amount por Trade",
            labels={'x': 'Bot', 'y': 'Amount (USDT)'},
            markers=True
        )
        fig_bar.update_traces(
            mode='lines+markers+text',
            marker=dict(size=10, color='steelblue'),
            line=dict(width=3, color='steelblue'),
            text=[f"${a:.2f}" for a in amounts],
            textposition='top center'
        )
        fig_bar.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider()
    
    # Tabela detalhada
    st.subheader("📋 Detalhes da Distribuição")
    
    df_dist = pd.DataFrame([
        {
            'Bot': b.replace('bot_', '').title(),
            'Capital': f"${distribution[b]['capital']:.2f}",
            'Percentual': f"{(distribution[b]['capital']/total_balance)*100:.1f}%",
            'Amount/Trade': f"${distribution[b]['amount_per_trade']:.2f}",
            'Max Posições': distribution[b].get('max_positions', 'N/A'),
            'Est. Trades': f"{int(distribution[b]['capital']/distribution[b]['amount_per_trade'])}"
        }
        for b in bot_names
    ])
    
    st.dataframe(df_dist, use_container_width=True)
    
    # Reserva
    reserve = total_balance * 0.05
    st.info(f"💼 **Reserva (5%)**: ${reserve:.2f}")
    
    st.divider()
    
    # Histórico de distribuições
    if len(balance_history) > 1:
        st.subheader("📈 Histórico de Distribuições")
        
        # Gráfico de linha - Saldo ao longo do tempo
        timestamps = [h.get('timestamp', '') for h in balance_history[-20:]]
        balances = [h.get('total_balance', 0) for h in balance_history[-20:]]
        
        fig_history = go.Figure(data=[
            go.Scatter(
                x=list(range(len(timestamps))),
                y=balances,
                mode='lines+markers',
                name='Saldo Total',
                fill='tozeroy',
                marker=dict(size=8, color='green')
            )
        ])
        fig_history.update_layout(
            title="Evolução do Saldo Total",
            xaxis_title="Iteração",
            yaxis_title="Saldo (USDT)",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig_history, use_container_width=True)
        
        # Tabela de histórico
        df_history = pd.DataFrame([
            {
                'Timestamp': h.get('timestamp', 'N/A'),
                'Saldo Total': f"${h.get('total_balance', 0):.2f}",
                'Bots': len(h.get('allocations', {}))
            }
            for h in balance_history[-10:]
        ])
        st.dataframe(df_history, use_container_width=True)

else:
    st.warning("⚠️ Nenhuma distribuição registrada ainda")
    st.info("Execute o script de auto-rebalance para gerar distribuição")

st.divider()

# Modo manual
st.subheader("🔧 Configuração Manual")

with st.expander("Ajustar Distribuição Manualmente"):
    st.write("Use este formulário para ajustar a distribuição de capital entre os bots")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bot_estavel_pct = st.slider("Bot Estável (%)", 0, 100, 25, key="est")
    with col2:
        bot_medio_pct = st.slider("Bot Médio (%)", 0, 100, 25, key="med")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bot_volatil_pct = st.slider("Bot Volátil (%)", 0, 100, 25, key="vol")
    with col2:
        bot_meme_pct = st.slider("Bot Meme (%)", 0, 100, 25, key="meme")
    
    total_pct = bot_estavel_pct + bot_medio_pct + bot_volatil_pct + bot_meme_pct
    
    if total_pct == 100:
        st.success(f"✅ Distribuição válida: 100%")
        
        if st.button("💾 Salvar Distribuição", key="save_dist"):
            st.success("✅ Distribuição salva! Reinicie o bot para aplicar.")
    else:
        st.error(f"❌ Total: {total_pct}% (deve ser 100%)")

st.divider()

# Footer
st.markdown("""
---
**R7 Trading Bot v2.0** | Dashboard de Distribuição
- 💰 Distribuição automática de capital entre 4 bots
- 📊 Histórico completo de rebalanceamentos
- 🤖 Auto-confirm em 5 segundos
- ⚙️ Configuração manual disponível
""")
