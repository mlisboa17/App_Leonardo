"""
🤖 AI Intelligence Page - Análise de Mercado e Auto-Tuning
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils.session_manager import get_ai_data, get_config_changes, get_autotuner_state


def render():
    """Renderiza página de inteligência artificial"""
    st.markdown('<div class="main-header">🤖 AI INTELLIGENCE - App R7</div>', unsafe_allow_html=True)
    
    # Carrega dados da AI
    ai_data = get_ai_data()
    config_changes = get_config_changes()
    
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
            fg_emoji = "😱"
        elif fg_value <= 45:
            fg_emoji = "😟"
        elif fg_value <= 55:
            fg_emoji = "😐"
        elif fg_value <= 75:
            fg_emoji = "😊"
        else:
            fg_emoji = "🤑"
        
        st.metric(f"{fg_emoji} {fg_class}", f"{fg_value}/100", delta=fg_trend)
        
        interpretation = fear_greed.get('interpretation', '')
        if interpretation:
            st.info(interpretation)
        
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
        
        headlines = news_summary.get('recent_headlines', [])
        if headlines:
            st.write("**📝 Headlines Recentes:**")
            for h in headlines[:5]:
                st.write(f"• {h[:80]}...")
    
    st.markdown("---")
    
    # ===== SEÇÃO 3: AUTO-TUNER =====
    st.header("🎛️ Auto-Tuner - Ajuste Dinâmico em Tempo Real")
    
    autotuner_state = get_autotuner_state()
    current = autotuner_state.get('current', {})
    market_cond = current.get('market_conditions', {})
    
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
    
    btc_price = market_cond.get('btc_price', 0)
    btc_change = market_cond.get('btc_change_24h', 0)
    if btc_price:
        st.info(f"💰 BTC: ${btc_price:,.2f} ({btc_change:+.2f}% 24h)")
    
    st.markdown("---")
    
    # ===== HISTÓRICO DE MUDANÇAS =====
    st.header("📝 Histórico de Ajustes Automáticos")
    
    if config_changes:
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


if __name__ == "__main__":
    render()
