"""
📊 Advanced Analytics - Análises Avançadas, Risk Metrics, Exportação
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils.session_manager import get_history, get_config
from frontend.utils.calculators import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_win_rate,
    calculate_avg_win_loss_ratio,
    get_top_symbols,
    get_worst_symbols,
    get_pnl_by_bot
)


def render():
    """Renderiza página de analytics avançado"""
    st.markdown('<div class="main-header">📊 ADVANCED ANALYTICS - App R7</div>', unsafe_allow_html=True)
    
    history = get_history()
    config = get_config()
    
    if not history:
        st.warning("⚠️ Nenhum histórico de trades disponível ainda")
        return
    
    # ===== FILTROS =====
    st.header("🔍 Filtros")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bot_types = ['Todos'] + list(config.keys()) if config else ['Todos']
        selected_bot = st.selectbox("Bot", bot_types)
    
    with col2:
        periods = {
            'Hoje': 0,
            'Últimos 7 dias': 7,
            'Últimos 30 dias': 30,
            'Últimos 90 dias': 90,
            'Tudo': 99999
        }
        selected_period = st.selectbox("Período", list(periods.keys()), index=4)
    
    with col3:
        result_filter = st.selectbox("Resultado", ['Todos', 'Só Wins', 'Só Losses'])
    
    with col4:
        # Extrai symbols únicos
        all_symbols = sorted(list(set(t.get('symbol', '') for t in history if t.get('symbol'))))
        selected_symbol = st.selectbox("Symbol", ['Todos'] + all_symbols)
    
    # Aplica filtros
    filtered_history = history.copy()
    
    # Filtro por bot
    if selected_bot != 'Todos':
        filtered_history = [t for t in filtered_history if t.get('bot_type') == selected_bot]
    
    # Filtro por período
    if periods[selected_period] < 99999:
        cutoff_date = (datetime.now() - timedelta(days=periods[selected_period])).date().isoformat()
        filtered_history = [t for t in filtered_history if t.get('exit_time', '')[:10] >= cutoff_date]
    
    # Filtro por resultado
    if result_filter == 'Só Wins':
        filtered_history = [t for t in filtered_history if t.get('pnl_usd', 0) > 0]
    elif result_filter == 'Só Losses':
        filtered_history = [t for t in filtered_history if t.get('pnl_usd', 0) < 0]
    
    # Filtro por symbol
    if selected_symbol != 'Todos':
        filtered_history = [t for t in filtered_history if t.get('symbol') == selected_symbol]
    
    st.info(f"📊 **{len(filtered_history)} trades** encontrados com os filtros aplicados")
    
    st.markdown("---")
    
    # ===== RISK METRICS =====
    st.header("⚠️ Risk Metrics - Análise de Risco")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sharpe = calculate_sharpe_ratio(filtered_history)
        sharpe_color = "🟢" if sharpe > 1.5 else "🟡" if sharpe > 0.5 else "🔴"
        st.metric(f"{sharpe_color} Sharpe Ratio", f"{sharpe:.2f}")
        st.caption("Retorno ajustado ao risco (>1.5 = bom)")
    
    with col2:
        dd = calculate_max_drawdown(filtered_history)
        dd_color = "🟢" if dd['max_drawdown'] < 10 else "🟡" if dd['max_drawdown'] < 20 else "🔴"
        st.metric(f"{dd_color} Max Drawdown", f"{dd['max_drawdown']:.2f}%")
        st.caption("Maior queda desde o pico")
    
    with col3:
        pf = calculate_profit_factor(filtered_history)
        pf_str = f"{pf:.2f}" if pf != float('inf') else "∞"
        pf_color = "🟢" if pf > 2 else "🟡" if pf > 1 else "🔴"
        st.metric(f"{pf_color} Profit Factor", pf_str)
        st.caption("Total wins / Total losses (>2 = excelente)")
    
    with col4:
        wr = calculate_win_rate(filtered_history)
        wr_color = "🟢" if wr > 60 else "🟡" if wr > 40 else "🔴"
        st.metric(f"{wr_color} Win Rate", f"{wr:.1f}%")
        st.caption("Taxa de vitória")
    
    # Avg Win/Loss
    st.subheader("💰 Média de Ganhos vs Perdas")
    
    wl_ratio = calculate_avg_win_loss_ratio(filtered_history)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📈 Média de Ganhos", f"${wl_ratio['avg_win']:.2f}")
    
    with col2:
        st.metric("📉 Média de Perdas", f"${wl_ratio['avg_loss']:.2f}")
    
    with col3:
        ratio_color = "🟢" if wl_ratio['ratio'] > 1.5 else "🟡" if wl_ratio['ratio'] > 1 else "🔴"
        st.metric(f"{ratio_color} Ratio", f"{wl_ratio['ratio']:.2f}")
    
    st.markdown("---")
    
    # ===== ANÁLISE POR SYMBOL =====
    st.header("🪙 Análise por Symbol")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 5 Mais Lucrativos")
        top_symbols = get_top_symbols(filtered_history, top_n=5)
        
        if top_symbols:
            top_data = []
            for sym in top_symbols:
                top_data.append({
                    'Symbol': sym['symbol'],
                    'PnL Total': f"${sym['total_pnl']:+.2f}",
                    'Trades': sym['trades'],
                    'Win Rate': f"{sym['win_rate']:.1f}%"
                })
            st.dataframe(pd.DataFrame(top_data), use_container_width=True)
        else:
            st.info("Sem dados")
    
    with col2:
        st.subheader("💀 Top 5 Piores")
        worst_symbols = get_worst_symbols(filtered_history, worst_n=5)
        
        if worst_symbols:
            worst_data = []
            for sym in worst_symbols:
                worst_data.append({
                    'Symbol': sym['symbol'],
                    'PnL Total': f"${sym['total_pnl']:+.2f}",
                    'Trades': sym['trades'],
                    'Win Rate': f"{sym['win_rate']:.1f}%"
                })
            st.dataframe(pd.DataFrame(worst_data), use_container_width=True)
        else:
            st.info("Sem dados")
    
    st.markdown("---")
    
    # ===== COMPARAÇÃO TEMPORAL =====
    st.header("📅 Comparação Temporal")
    
    # Esta semana vs semana passada
    today = datetime.now()
    start_this_week = (today - timedelta(days=today.weekday())).date().isoformat()
    start_last_week = (today - timedelta(days=today.weekday() + 7)).date().isoformat()
    end_last_week = (today - timedelta(days=today.weekday() + 1)).date().isoformat()
    
    this_week_trades = [t for t in history if t.get('exit_time', '')[:10] >= start_this_week]
    last_week_trades = [t for t in history if start_last_week <= t.get('exit_time', '')[:10] < end_last_week]
    
    this_week_pnl = sum(t.get('pnl_usd', 0) for t in this_week_trades)
    last_week_pnl = sum(t.get('pnl_usd', 0) for t in last_week_trades)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Esta Semana", f"${this_week_pnl:+.2f}", delta=f"{len(this_week_trades)} trades")
    
    with col2:
        st.metric("📊 Semana Passada", f"${last_week_pnl:+.2f}", delta=f"{len(last_week_trades)} trades")
    
    with col3:
        diff = this_week_pnl - last_week_pnl
        diff_pct = (diff / abs(last_week_pnl) * 100) if last_week_pnl != 0 else 0
        st.metric("📈 Variação", f"${diff:+.2f}", delta=f"{diff_pct:+.1f}%")
    
    st.markdown("---")
    
    # ===== GRÁFICO DE EVOLUÇÃO MENSAL =====
    st.header("📈 Evolução Mensal")
    
    # Agrupa por mês
    monthly_data = {}
    for trade in history:
        month = trade.get('exit_time', '')[:7]  # YYYY-MM
        if month:
            if month not in monthly_data:
                monthly_data[month] = {'pnl': 0, 'trades': 0}
            monthly_data[month]['pnl'] += trade.get('pnl_usd', 0)
            monthly_data[month]['trades'] += 1
    
    if monthly_data:
        months = sorted(monthly_data.keys())
        pnls = [monthly_data[m]['pnl'] for m in months]
        trades = [monthly_data[m]['trades'] for m in months]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=pnls, mode='lines+markers', name='PnL Mensal', line=dict(color='#00ff88')))
        fig.update_layout(title='PnL Mensal', xaxis_title='Mês', yaxis_title='PnL (USD)')
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ===== EXPORTAÇÃO CSV =====
    st.header("💾 Exportar Dados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Exportar Trades Filtrados (CSV)", use_container_width=True):
            if filtered_history:
                df = pd.DataFrame(filtered_history)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                st.success("✅ CSV gerado com sucesso!")
            else:
                st.warning("Nenhum trade para exportar")
    
    with col2:
        if st.button("📥 Exportar Risk Metrics (CSV)", use_container_width=True):
            risk_data = {
                'Métrica': ['Sharpe Ratio', 'Max Drawdown (%)', 'Profit Factor', 'Win Rate (%)', 'Avg Win', 'Avg Loss', 'Win/Loss Ratio'],
                'Valor': [
                    calculate_sharpe_ratio(filtered_history),
                    calculate_max_drawdown(filtered_history)['max_drawdown'],
                    calculate_profit_factor(filtered_history),
                    calculate_win_rate(filtered_history),
                    calculate_avg_win_loss_ratio(filtered_history)['avg_win'],
                    calculate_avg_win_loss_ratio(filtered_history)['avg_loss'],
                    calculate_avg_win_loss_ratio(filtered_history)['ratio']
                ]
            }
            
            df_risk = pd.DataFrame(risk_data)
            csv_risk = df_risk.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Risk CSV",
                data=csv_risk,
                file_name=f"risk_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.success("✅ Risk Metrics CSV gerado!")
    
    with col3:
        if st.button("📥 Exportar Top/Worst Symbols (CSV)", use_container_width=True):
            top = get_top_symbols(filtered_history, top_n=10)
            worst = get_worst_symbols(filtered_history, worst_n=10)
            
            df_symbols = pd.DataFrame({
                'Top Symbols': [s['symbol'] for s in top],
                'Top PnL': [s['total_pnl'] for s in top],
                'Worst Symbols': [s['symbol'] for s in worst],
                'Worst PnL': [s['total_pnl'] for s in worst]
            })
            
            csv_symbols = df_symbols.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Symbols CSV",
                data=csv_symbols,
                file_name=f"symbols_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.success("✅ Symbols CSV gerado!")


if __name__ == "__main__":
    render()
