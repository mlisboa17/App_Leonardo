"""
🚀 Dashboard Streamlit - App Leonardo
Dashboard moderno com atualização em tempo real
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ccxt
from dotenv import load_dotenv
import os
import json
import yaml
from datetime import datetime, timedelta
import time
import subprocess

# ========================================
# CONFIGURAÇÃO DA PÁGINA
# ========================================

st.set_page_config(
    page_title="App Leonardo | Trading Bot_v2",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado
st.markdown("""
<style>
    /* Tema escuro */
    .stApp {
        background-color: #0f1419;
    }
    
    /* Cards de métricas */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: bold;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #e7e9ea !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1f29;
    }
    
    /* Métrica positiva */
    .positive {
        color: #00ba7c !important;
    }
    
    /* Métrica negativa */
    .negative {
        color: #f91880 !important;
    }
    
    /* Card container */
    .metric-card {
        background-color: #1a1f29;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #252d3a;
    }
    
    /* Status badge */
    .status-online {
        background-color: #00ba7c20;
        color: #00ba7c;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .status-offline {
        background-color: #8b98a520;
        color: #8b98a5;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# CONFIGURAÇÃO
# ========================================

# Carrega credenciais
env_paths = [
    '../.env',
    '../config/.env',
    '../../.env',
    '.env',
    'config/.env',
]

for env_path in env_paths:
    full_path = os.path.join(os.path.dirname(__file__), env_path)
    if os.path.exists(full_path):
        load_dotenv(full_path)
        break
else:
    load_dotenv()

API_KEY = os.getenv('BINANCE_TESTNET_API_KEY', '')
API_SECRET = os.getenv('BINANCE_TESTNET_API_SECRET', '')
TESTNET = True
TESTNET_BALANCE_CORRECTION = 10.0

MAIN_CRYPTOS = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'LINK', 'DOGE', 'LTC']

# ========================================
# FUNÇÕES DE DADOS
# ========================================

@st.cache_resource
def get_exchange():
    """Cria conexão com a exchange (cached)"""
    try:
        exchange = ccxt.binance({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'sandbox': TESTNET,
            'timeout': 30000,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True,
                'recvWindow': 60000,
            }
        })
        exchange.load_markets()
        return exchange
    except Exception as e:
        st.error(f"❌ Erro ao conectar: {e}")
        return None

@st.cache_data(ttl=10)
def get_balances():
    """Busca saldos (cache 10s)"""
    try:
        exchange = get_exchange()
        if not exchange:
            return None
        
        balance = exchange.fetch_balance()
        
        if TESTNET and TESTNET_BALANCE_CORRECTION > 1:
            corrected = {}
            for key, value in balance.items():
                if isinstance(value, dict):
                    corrected[key] = {k: v / TESTNET_BALANCE_CORRECTION if isinstance(v, (int, float)) else v 
                                      for k, v in value.items()}
                elif isinstance(value, (int, float)):
                    corrected[key] = value / TESTNET_BALANCE_CORRECTION
                else:
                    corrected[key] = value
            return corrected
        
        return balance
    except Exception as e:
        st.error(f"❌ Erro ao buscar saldo: {e}")
        return None

@st.cache_data(ttl=5)
def get_prices(symbols):
    """Busca preços (cache 5s)"""
    try:
        exchange = get_exchange()
        if not exchange:
            return {}
        
        invalid = {'TRY', 'EUR', 'GBP', 'BRL', 'USD', 'USDT', 'USDC', 'DAI', 'FDUSD', 
                   'JPY', 'MXN', 'COP', 'PLN', 'ZAR', 'UAH', 'ARS', 'CZK', 'RON'}
        valid = [s for s in symbols if s not in invalid]
        
        if not valid:
            return {}
        
        tickers = exchange.fetch_tickers()
        prices = {}
        for symbol in valid:
            pair = f"{symbol}/USDT"
            if pair in tickers:
                prices[symbol] = {
                    'price': tickers[pair].get('last', 0) or 0,
                    'change': tickers[pair].get('percentage', 0) or 0
                }
        
        return prices
    except Exception as e:
        return {}

@st.cache_data(ttl=60)
def get_predictions(symbols):
    """Calcula previsões (cache 60s)"""
    predictions = {}
    try:
        exchange = get_exchange()
        if not exchange:
            return {s: {'trend': 'ERRO', 'signal': '❓', 'confidence': 0, 'rsi': 50} for s in symbols}
        
        for symbol in symbols:
            try:
                pair = f"{symbol}/USDT"
                ohlcv = exchange.fetch_ohlcv(pair, '1h', limit=50)
                
                if len(ohlcv) < 20:
                    predictions[symbol] = {'trend': 'NEUTRO', 'signal': '⚪', 'confidence': 50, 'rsi': 50}
                    continue
                
                closes = [c[4] for c in ohlcv]
                
                # RSI
                gains, losses = [], []
                for i in range(1, min(15, len(closes))):
                    change = closes[-i] - closes[-(i+1)]
                    (gains if change > 0 else losses).append(abs(change))
                
                avg_gain = sum(gains) / 14 if gains else 0
                avg_loss = sum(losses) / 14 if losses else 0.001
                rsi = 100 - (100 / (1 + avg_gain / avg_loss))
                
                # SMAs
                sma_10 = sum(closes[-10:]) / 10
                sma_20 = sum(closes[-20:]) / 20
                current = closes[-1]
                
                # Tendência
                if current > sma_10 > sma_20:
                    trend, signal, conf = 'ALTA', '🟢', 75
                elif current < sma_10 < sma_20:
                    trend, signal, conf = 'QUEDA', '🔴', 75
                elif rsi < 30:
                    trend, signal, conf = 'OVERSOLD', '🟡', 65
                elif rsi > 70:
                    trend, signal, conf = 'OVERBOUGHT', '🟠', 65
                else:
                    trend, signal, conf = 'LATERAL', '⚪', 50
                
                predictions[symbol] = {'trend': trend, 'signal': signal, 'confidence': conf, 'rsi': rsi}
                
            except:
                predictions[symbol] = {'trend': 'ERRO', 'signal': '❓', 'confidence': 0, 'rsi': 50}
        
        return predictions
    except:
        return {s: {'trend': 'ERRO', 'signal': '❓', 'confidence': 0, 'rsi': 50} for s in symbols}

def get_bot_stats():
    """Busca estatísticas do bot"""
    stats_paths = [
        '../data/daily_stats.json',
        'data/daily_stats.json',
    ]
    
    for path in stats_paths:
        full_path = os.path.join(os.path.dirname(__file__), path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    return json.load(f)
            except:
                pass
    
    return {
        'daily_pnl': 0,
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'date': datetime.now().strftime('%Y-%m-%d')
    }

def get_trade_history():
    """Busca histórico de trades"""
    history_paths = [
        '../data/all_trades_history.json',
        'data/all_trades_history.json',
    ]
    
    for path in history_paths:
        full_path = os.path.join(os.path.dirname(__file__), path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    data = json.load(f)
                    return data.get('trades', [])[-50:]  # Últimos 50
            except:
                pass
    
    return []

# ========================================
# SIDEBAR
# ========================================

def load_config():
    """Carrega configuração do bot"""
    config_path = os.path.join(os.path.dirname(__file__), '../config/config.yaml')
    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except:
        return None

def save_config(config):
    """Salva configuração do bot"""
    config_path = os.path.join(os.path.dirname(__file__), '../config/config.yaml')
    try:
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

def get_history_files():
    """Lista arquivos de histórico"""
    history_dir = os.path.join(os.path.dirname(__file__), '../data/history')
    if os.path.exists(history_dir):
        files = [f for f in os.listdir(history_dir) if f.endswith('.json')]
        return sorted(files, reverse=True)[:20]  # Últimos 20
    return []

with st.sidebar:
    st.image("https://em-content.zobj.net/source/apple/391/robot_1f916.png", width=80)
    st.title("App Leonardo_v2")
    st.caption("Trading Bot v2.0")
    
    st.divider()
    
    # Status do bot
    bot_state_path = os.path.join(os.path.dirname(__file__), '../bot_state.json')
    bot_running = False
    bot_status = "Offline"
    
    if os.path.exists(bot_state_path):
        try:
            with open(bot_state_path, 'r') as f:
                state = json.load(f)
                bot_running = state.get('is_running', False)
                bot_status = state.get('status', 'Offline')
        except:
            pass
    
    if bot_running:
        st.markdown('<span class="status-online">🟢 Bot Online</span>', unsafe_allow_html=True)
        st.caption(f"Status: {bot_status}")
    else:
        st.markdown('<span class="status-offline">⚪ Bot Offline</span>', unsafe_allow_html=True)
        st.caption(f"Status: {bot_status}")
    
    st.divider()
    
    # ========================================
    # HISTÓRICO
    # ========================================
    st.markdown("### 📜 Histórico de Trades")
    
    history_files = get_history_files()
    if history_files:
        selected_history = st.selectbox(
            "Selecione o arquivo:",
            history_files,
            format_func=lambda x: x.replace('complete_history_', '').replace('.json', '')
        )
        
        if st.button("📊 Abrir Planilha de Histórico", use_container_width=True):
            history_path = os.path.join(os.path.dirname(__file__), f'../data/history/{selected_history}')
            try:
                with open(history_path, 'r') as f:
                    history_data = json.load(f)
                
                # Converte para DataFrame
                trades = history_data.get('trades', [])
                if trades:
                    df_history = pd.DataFrame(trades)
                    
                    # Salva como CSV temporário
                    csv_path = os.path.join(os.path.dirname(__file__), '../data/history_export.csv')
                    df_history.to_csv(csv_path, index=False)
                    
                    # Download button
                    csv_data = df_history.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_data,
                        file_name=f"trades_{selected_history.replace('.json', '.csv')}",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                    st.success(f"✅ {len(trades)} trades carregados!")
                else:
                    st.warning("Arquivo vazio")
            except Exception as e:
                st.error(f"Erro: {e}")
        
        # Botão para abrir no explorador
        if st.button("📁 Abrir Pasta de Histórico", use_container_width=True):
            history_dir = os.path.join(os.path.dirname(__file__), '../data/history')
            os.startfile(os.path.abspath(history_dir))
    else:
        st.info("Nenhum histórico encontrado")
    
    st.divider()
    
    # ========================================
    # CONFIGURAÇÕES
    # ========================================
    st.markdown("### ⚙️ Configurações do Bot")
    
    config = load_config()
    
    if config:
        with st.expander("💰 Trading", expanded=False):
            new_amount = st.number_input(
                "Valor por Trade ($)",
                min_value=100.0,
                max_value=50000.0,
                value=float(config.get('trading', {}).get('amount_per_trade', 5000)),
                step=100.0
            )
            
            new_max_positions = st.slider(
                "Máx. Posições Abertas",
                min_value=1,
                max_value=50,
                value=int(config.get('trading', {}).get('max_positions', 20))
            )
            
            new_daily_target = st.number_input(
                "Meta Diária ($)",
                min_value=10.0,
                max_value=5000.0,
                value=float(config.get('trading', {}).get('daily_profit_target', 500)),
                step=10.0
            )
        
        with st.expander("🛡️ Segurança", expanded=False):
            new_max_loss = st.number_input(
                "Perda Máx. Diária ($)",
                min_value=10.0,
                max_value=1000.0,
                value=float(config.get('safety', {}).get('max_daily_loss', 50)),
                step=10.0
            )
            
            new_max_drawdown = st.slider(
                "Drawdown Máximo (%)",
                min_value=5,
                max_value=50,
                value=int(config.get('safety', {}).get('max_drawdown', 20))
            )
        
        with st.expander("📊 Indicadores", expanded=False):
            new_rsi_oversold = st.slider(
                "RSI Sobrevendido",
                min_value=20,
                max_value=45,
                value=int(config.get('indicators', {}).get('rsi', {}).get('oversold', 45))
            )
            
            new_rsi_overbought = st.slider(
                "RSI Sobrecomprado",
                min_value=55,
                max_value=80,
                value=int(config.get('indicators', {}).get('rsi', {}).get('overbought', 55))
            )
        
        if st.button("💾 Salvar Configurações", use_container_width=True, type="primary"):
            # Atualiza config
            config['trading']['amount_per_trade'] = new_amount
            config['trading']['max_positions'] = new_max_positions
            config['trading']['daily_profit_target'] = new_daily_target
            config['safety']['max_daily_loss'] = new_max_loss
            config['safety']['max_drawdown'] = new_max_drawdown
            config['indicators']['rsi']['oversold'] = new_rsi_oversold
            config['indicators']['rsi']['overbought'] = new_rsi_overbought
            
            if save_config(config):
                st.success("✅ Configurações salvas!")
                st.balloons()
            else:
                st.error("❌ Erro ao salvar")
    else:
        st.warning("Não foi possível carregar config")
    
    st.divider()
    
    # Info atual
    st.markdown("### ℹ️ Info")
    st.info(f"""
    🧪 **Modo:** {'Testnet' if TESTNET else 'Real'}  
    📊 **Moedas:** {len(MAIN_CRYPTOS)}  
    ⏱️ **Refresh:** Auto
    """)
    
    st.divider()
    
    # Auto refresh
    auto_refresh = st.checkbox("🔄 Auto Refresh", value=True)
    if auto_refresh:
        refresh_rate = st.slider("Intervalo (seg)", 5, 60, 10)
        time.sleep(0.1)  # Pequeno delay
        st.rerun() if st.button("🔄 Atualizar Agora") else None

# ========================================
# PÁGINA PRINCIPAL
# ========================================

st.title("🤖 App Leonardo - Trading Bot_v2")
st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | 🧪 Binance Testnet")

# Busca dados
balance_data = get_balances()
bot_stats = get_bot_stats()

if balance_data:
    free = balance_data.get('free', {})
    usdt_balance = float(free.get('USDT', 0))
    
    # Filtra cryptos válidas
    invalid = {'TRY', 'EUR', 'GBP', 'BRL', 'USD', 'USDT', 'USDC', 'DAI', 'FDUSD', 
               'JPY', 'MXN', 'COP', 'PLN', 'ZAR', 'UAH', 'ARS', 'CZK', 'RON'}
    cryptos = {k: float(v) for k, v in free.items() if float(v) > 0.0001 and k not in invalid}
    
    # Busca preços
    prices = get_prices(list(cryptos.keys())[:30])
    
    # Calcula valores
    crypto_values = {}
    for symbol, amount in cryptos.items():
        price_data = prices.get(symbol, {'price': 0, 'change': 0})
        crypto_values[symbol] = {
            'amount': amount,
            'price': price_data['price'],
            'change': price_data['change'],
            'value': amount * price_data['price']
        }
    
    total_crypto = sum(v['value'] for v in crypto_values.values())
    total_value = usdt_balance + total_crypto
    
    # ========================================
    # MÉTRICAS PRINCIPAIS
    # ========================================
    
    st.markdown("### 💰 Visão Geral")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💵 USDT Disponível",
            value=f"${usdt_balance:,.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="💎 Valor em Crypto",
            value=f"${total_crypto:,.2f}",
            delta=None
        )
    
    with col3:
        st.metric(
            label="🏦 Patrimônio Total",
            value=f"${total_value:,.2f}",
            delta=None
        )
    
    daily_pnl = bot_stats.get('daily_pnl', 0)
    with col4:
        st.metric(
            label="📈 Lucro do Dia",
            value=f"${daily_pnl:,.2f}",
            delta=f"{(daily_pnl/total_value*100):.2f}%" if total_value > 0 else "0%"
        )
    
    # ========================================
    # ESTATÍSTICAS DO BOT
    # ========================================
    
    st.markdown("### 📊 Performance do Bot")
    
    col1, col2, col3, col4 = st.columns(4)
    
    trades = bot_stats.get('total_trades', 0)
    wins = bot_stats.get('winning_trades', 0)
    losses = bot_stats.get('losing_trades', 0)
    win_rate = (wins / trades * 100) if trades > 0 else 0
    
    with col1:
        st.metric("📊 Total Trades", f"{trades}")
    
    with col2:
        st.metric("✅ Vitórias", f"{wins}", delta=None)
    
    with col3:
        st.metric("❌ Derrotas", f"{losses}", delta=None)
    
    with col4:
        st.metric("🎯 Win Rate", f"{win_rate:.1f}%")
    
    # Progress bar da meta
    target = 100
    progress = min(daily_pnl / target, 1.0) if daily_pnl > 0 else 0
    st.progress(progress, text=f"🎯 Meta Diária: ${daily_pnl:.2f} / ${target:.2f} ({progress*100:.1f}%)")
    
    # ========================================
    # CRIPTOMOEDAS
    # ========================================
    
    st.markdown("### 🪙 Principais Criptomoedas")
    
    # Busca previsões
    predictions = get_predictions(MAIN_CRYPTOS)
    
    # Cores por tendência
    trend_colors = {
        'ALTA': '#00ba7c',
        'QUEDA': '#f91880',
        'LATERAL': '#8b98a5',
        'OVERSOLD': '#ffd700',
        'OVERBOUGHT': '#ff8c00',
        'NEUTRO': '#8b98a5',
        'ERRO': '#8b98a5'
    }
    
    # Grid de cards
    cols = st.columns(4)
    
    for i, symbol in enumerate(MAIN_CRYPTOS):
        with cols[i % 4]:
            data = crypto_values.get(symbol, {'amount': 0, 'price': 0, 'change': 0, 'value': 0})
            pred = predictions.get(symbol, {'trend': 'NEUTRO', 'signal': '⚪', 'confidence': 50, 'rsi': 50})
            
            # Busca preço se não tiver
            if data['price'] == 0 and symbol in prices:
                data['price'] = prices[symbol]['price']
                data['change'] = prices[symbol]['change']
            
            trend_color = trend_colors.get(pred['trend'], '#8b98a5')
            
            st.markdown(f"""
            <div style="background-color: #1a1f29; padding: 15px; border-radius: 10px; 
                        border-left: 4px solid {trend_color}; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 18px; font-weight: bold; color: #e7e9ea;">{symbol}</span>
                    <span style="font-size: 16px;">{pred['signal']}</span>
                </div>
                <div style="margin: 8px 0;">
                    <span style="background-color: {trend_color}20; color: {trend_color}; 
                                 padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        {pred['trend']}
                    </span>
                    <span style="color: #8b98a5; font-size: 11px; margin-left: 5px;">
                        {pred['confidence']}%
                    </span>
                </div>
                <div style="color: #e7e9ea; font-size: 14px; font-weight: bold;">
                    ${data['price']:,.2f}
                    <span style="color: {'#00ba7c' if data['change'] >= 0 else '#f91880'}; font-size: 12px;">
                        ({data['change']:+.1f}%)
                    </span>
                </div>
                <div style="color: #8b98a5; font-size: 11px;">
                    Qtd: {data['amount']:.6f} | RSI: {pred['rsi']:.0f}
                </div>
                <div style="color: #00ba7c; font-size: 16px; font-weight: bold; margin-top: 5px;">
                    ${data['value']:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # ========================================
    # GRÁFICOS
    # ========================================
    
    st.markdown("### 📈 Gráficos")
    
    tab1, tab2, tab3 = st.tabs(["📊 Distribuição", "💹 Histórico", "🔍 Análise"])
    
    with tab1:
        # Gráfico de Pizza - Distribuição
        col1, col2 = st.columns(2)
        
        with col1:
            # Prepara dados para pizza
            pie_data = [{'symbol': 'USDT', 'value': usdt_balance}]
            for symbol in MAIN_CRYPTOS:
                if symbol in crypto_values and crypto_values[symbol]['value'] > 0:
                    pie_data.append({'symbol': symbol, 'value': crypto_values[symbol]['value']})
            
            df_pie = pd.DataFrame(pie_data)
            
            fig_pie = px.pie(
                df_pie, 
                values='value', 
                names='symbol',
                title='🥧 Distribuição do Portfólio',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#e7e9ea'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Barras - Valor por crypto
            bar_data = []
            for symbol in MAIN_CRYPTOS:
                if symbol in crypto_values:
                    bar_data.append({
                        'symbol': symbol,
                        'value': crypto_values[symbol]['value'],
                        'change': crypto_values[symbol]['change']
                    })
            
            if bar_data:
                df_bar = pd.DataFrame(bar_data)
                
                fig_bar = px.bar(
                    df_bar,
                    x='symbol',
                    y='value',
                    title='📊 Valor por Criptomoeda',
                    color='change',
                    color_continuous_scale=['#f91880', '#8b98a5', '#00ba7c']
                )
                fig_bar.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#e7e9ea',
                    xaxis_title='',
                    yaxis_title='Valor (USD)'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
    
    with tab2:
        # Histórico de trades
        trades_history = get_trade_history()
        
        if trades_history:
            df_trades = pd.DataFrame(trades_history)
            
            if 'pnl' in df_trades.columns:
                # Gráfico de PnL
                fig_pnl = go.Figure()
                
                colors = ['#00ba7c' if x >= 0 else '#f91880' for x in df_trades['pnl']]
                
                fig_pnl.add_trace(go.Bar(
                    x=list(range(len(df_trades))),
                    y=df_trades['pnl'],
                    marker_color=colors,
                    name='PnL'
                ))
                
                fig_pnl.update_layout(
                    title='💹 PnL por Trade',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#e7e9ea',
                    xaxis_title='Trade #',
                    yaxis_title='PnL (USD)'
                )
                
                st.plotly_chart(fig_pnl, use_container_width=True)
            
            # Tabela de trades
            st.dataframe(df_trades.tail(20), use_container_width=True)
        else:
            st.info("📭 Nenhum histórico de trades encontrado.")
    
    with tab3:
        # Análise de RSI
        st.markdown("#### 📉 Indicadores Técnicos")
        
        rsi_data = []
        for symbol in MAIN_CRYPTOS:
            pred = predictions.get(symbol, {'rsi': 50, 'trend': 'NEUTRO'})
            rsi_data.append({
                'symbol': symbol,
                'rsi': pred['rsi'],
                'trend': pred['trend']
            })
        
        df_rsi = pd.DataFrame(rsi_data)
        
        # Barras de RSI (mais simples e sem erro)
        fig_rsi = go.Figure()
        
        colors = []
        for rsi in df_rsi['rsi']:
            if rsi < 30:
                colors.append('#00ba7c')  # Verde - sobrevendido
            elif rsi > 70:
                colors.append('#f91880')  # Vermelho - sobrecomprado
            else:
                colors.append('#1d9bf0')  # Azul - neutro
        
        fig_rsi.add_trace(go.Bar(
            x=df_rsi['symbol'],
            y=df_rsi['rsi'],
            marker_color=colors,
            text=[f"{r:.0f}" for r in df_rsi['rsi']],
            textposition='outside'
        ))
        
        # Linhas de referência
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="#00ba7c", annotation_text="Sobrevendido")
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="#f91880", annotation_text="Sobrecomprado")
        
        fig_rsi.update_layout(
            title="📊 RSI por Criptomoeda",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e7e9ea',
            yaxis=dict(range=[0, 100], title="RSI"),
            xaxis=dict(title=""),
            height=400
        )
        
        st.plotly_chart(fig_rsi, use_container_width=True)
        
        # Legenda
        st.markdown("""
        **Zonas de RSI:**
        - 🟢 **0-30:** Sobrevendido (possível compra)
        - ⚪ **30-70:** Neutro
        - 🔴 **70-100:** Sobrecomprado (possível venda)
        """)

else:
    st.error("❌ Não foi possível conectar à exchange. Verifique suas credenciais.")
    st.info("💡 Dica: Certifique-se que o arquivo `.env` contém as chaves da API.")

# ========================================
# FOOTER
# ========================================

st.divider()
st.caption(f"🤖 App Leonardo v2.0 | Última atualização: {datetime.now().strftime('%H:%M:%S')} | Made with ❤️")

# Auto-refresh
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
