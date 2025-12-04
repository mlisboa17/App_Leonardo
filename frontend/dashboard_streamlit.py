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
    """Calcula previsões (cache 60s) com sistema de temperatura"""
    predictions = {}
    try:
        exchange = get_exchange()
        if not exchange:
            return {s: {'trend': 'ERRO', 'signal': '❓', 'confidence': 0, 'rsi': 50, 'temp': 'NEUTRO', 'temp_emoji': '⚪'} for s in symbols}
        
        for symbol in symbols:
            try:
                pair = f"{symbol}/USDT"
                ohlcv = exchange.fetch_ohlcv(pair, '1h', limit=50)
                
                if len(ohlcv) < 20:
                    predictions[symbol] = {'trend': 'NEUTRO', 'signal': '⚪', 'confidence': 50, 'rsi': 50, 'temp': 'MORNO', 'temp_emoji': '🌡️'}
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
                
                # Variação percentual
                price_change = ((current - closes[-24]) / closes[-24] * 100) if len(closes) >= 24 else 0
                
                # Sistema de Temperatura (Quente = Alta, Frio = Baixa)
                # QUENTE: 🔥 FERVENDO > 🌶️ SUPER QUENTE > ☀️ QUENTE > 🌡️ MORNO
                # FRIO: ❄️ CONGELANDO < 🥶 SUPER FRIO < 🌬️ FRIO < 🌡️ MORNO
                
                if current > sma_10 > sma_20 and rsi > 60 and price_change > 3:
                    trend, signal, conf = 'ALTA FORTE', '🟢', 85
                    temp, temp_emoji = 'FERVENDO', '🔥'
                elif current > sma_10 > sma_20 and rsi > 55:
                    trend, signal, conf = 'ALTA', '🟢', 75
                    temp, temp_emoji = 'SUPER QUENTE', '🌶️'
                elif current > sma_10 and price_change > 1:
                    trend, signal, conf = 'SUBINDO', '🟡', 65
                    temp, temp_emoji = 'QUENTE', '☀️'
                elif current < sma_10 < sma_20 and rsi < 40 and price_change < -3:
                    trend, signal, conf = 'QUEDA FORTE', '🔴', 85
                    temp, temp_emoji = 'CONGELANDO', '❄️'
                elif current < sma_10 < sma_20 and rsi < 45:
                    trend, signal, conf = 'QUEDA', '🔴', 75
                    temp, temp_emoji = 'SUPER FRIO', '🥶'
                elif current < sma_10 and price_change < -1:
                    trend, signal, conf = 'CAINDO', '🟠', 65
                    temp, temp_emoji = 'FRIO', '🌬️'
                elif rsi < 30:
                    trend, signal, conf = 'OVERSOLD', '🟡', 70
                    temp, temp_emoji = 'CONGELANDO', '❄️'
                elif rsi > 70:
                    trend, signal, conf = 'OVERBOUGHT', '🟠', 70
                    temp, temp_emoji = 'FERVENDO', '🔥'
                else:
                    trend, signal, conf = 'LATERAL', '⚪', 50
                    temp, temp_emoji = 'MORNO', '🌡️'
                
                predictions[symbol] = {
                    'trend': trend, 
                    'signal': signal, 
                    'confidence': conf, 
                    'rsi': rsi,
                    'temp': temp,
                    'temp_emoji': temp_emoji,
                    'price_change': price_change
                }
                
            except:
                predictions[symbol] = {'trend': 'ERRO', 'signal': '❓', 'confidence': 0, 'rsi': 50, 'temp': 'NEUTRO', 'temp_emoji': '⚪', 'price_change': 0}
        
        return predictions
    except:
        return {s: {'trend': 'ERRO', 'signal': '❓', 'confidence': 0, 'rsi': 50, 'temp': 'NEUTRO', 'temp_emoji': '⚪', 'price_change': 0} for s in symbols}

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
        
        with st.expander("🪙 Moedas Ativas", expanded=False):
            st.markdown("Selecione as moedas para operar:")
            
            # As 8 moedas principais - TODAS MARCADAS POR PADRÃO
            moedas_config = config.get('trading', {}).get('symbols', 
                ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'LINK/USDT', 'DOGE/USDT', 'LTC/USDT'])
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                btc_active = st.checkbox("₿ BTC", value='BTC/USDT' in moedas_config)
                eth_active = st.checkbox("Ξ ETH", value='ETH/USDT' in moedas_config)
                sol_active = st.checkbox("◎ SOL", value='SOL/USDT' in moedas_config)
                bnb_active = st.checkbox("🔶 BNB", value='BNB/USDT' in moedas_config)
            with col_m2:
                xrp_active = st.checkbox("✕ XRP", value='XRP/USDT' in moedas_config)
                link_active = st.checkbox("⬡ LINK", value='LINK/USDT' in moedas_config)
                doge_active = st.checkbox("🐕 DOGE", value='DOGE/USDT' in moedas_config)
                ltc_active = st.checkbox("Ł LTC", value='LTC/USDT' in moedas_config)
        
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
    
    # Botão de atualizar
    if st.button("🔄 Atualizar Agora", use_container_width=True):
        st.rerun()
    
    auto_refresh = False
    refresh_rate = 30

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
    # 🚨 PAINEL DE ALERTAS E CONTROLES RÁPIDOS
    # ========================================
    
    st.markdown("### 🚨 Alertas e Controles Rápidos")
    
    # Carrega configuração atual
    import yaml
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        amount_per_trade = config_data.get('trading', {}).get('amount_per_trade', 2000.0)
    except:
        amount_per_trade = 2000.0
    
    max_hold_minutes = 10  # Tempo máximo configurado na estratégia
    
    # ---- ALERTAS ----
    alerts = []
    
    # Alerta de saldo insuficiente
    if usdt_balance < amount_per_trade:
        alerts.append({
            'type': 'error',
            'icon': '🔴',
            'title': 'SALDO INSUFICIENTE',
            'msg': f'USDT disponível (${usdt_balance:.2f}) é menor que o valor por trade (${amount_per_trade:.2f}). Bot NÃO conseguirá abrir novas posições!',
            'action_needed': True
        })
    elif usdt_balance < amount_per_trade * 1.5:
        alerts.append({
            'type': 'warning',
            'icon': '🟡',
            'title': 'Saldo Baixo',
            'msg': f'USDT disponível (${usdt_balance:.2f}) está ficando baixo. Considere reduzir o valor por trade.',
            'action_needed': False
        })
    else:
        alerts.append({
            'type': 'success',
            'icon': '🟢',
            'title': 'Saldo OK',
            'msg': f'USDT disponível: ${usdt_balance:.2f} | Pode abrir {int(usdt_balance / amount_per_trade)} trades',
            'action_needed': False
        })
    
    # Alerta de posições abertas
    open_positions = len([c for c in cryptos if cryptos[c] > 0.001])
    if open_positions > 5:
        alerts.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'Muitas Posições',
            'msg': f'{open_positions} posições abertas. Risco aumentado!',
            'action_needed': False
        })
    elif open_positions > 0:
        alerts.append({
            'type': 'info',
            'icon': 'ℹ️',
            'title': 'Posições Ativas',
            'msg': f'{open_positions} posições abertas no momento',
            'action_needed': False
        })
    
    # Exibir alertas
    for alert in alerts:
        if alert['type'] == 'error':
            st.error(f"{alert['icon']} **{alert['title']}**: {alert['msg']}")
        elif alert['type'] == 'warning':
            st.warning(f"{alert['icon']} **{alert['title']}**: {alert['msg']}")
        elif alert['type'] == 'success':
            st.success(f"{alert['icon']} **{alert['title']}**: {alert['msg']}")
        else:
            st.info(f"{alert['icon']} **{alert['title']}**: {alert['msg']}")
    
    # ---- CORREÇÃO DE SALDO INSUFICIENTE ----
    if usdt_balance < amount_per_trade:
        st.markdown("---")
        st.markdown("### 🔧 CORRIGIR SALDO INSUFICIENTE")
        st.markdown(f"**Problema:** Você tem **${usdt_balance:.2f}** mas o bot precisa de **${amount_per_trade:.2f}** por trade.")
        
        # Calcula valor sugerido (80% do saldo disponível)
        suggested_value = int(usdt_balance * 0.8 / 100) * 100  # Arredonda para centenas
        if suggested_value < 100:
            suggested_value = int(usdt_balance * 0.8)
        
        fix_col1, fix_col2 = st.columns([2, 1])
        
        with fix_col1:
            new_amount = st.number_input(
                "💰 Novo valor por trade ($)",
                min_value=50.0,
                max_value=float(usdt_balance),
                value=float(suggested_value),
                step=50.0,
                help=f"Máximo recomendado: ${usdt_balance * 0.8:.0f} (80% do saldo)"
            )
        
        with fix_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ APLICAR E CONTINUAR", type="primary", use_container_width=True):
                try:
                    # Atualiza o config.yaml
                    config_data['trading']['amount_per_trade'] = float(new_amount)
                    with open(config_path, 'w') as f:
                        yaml.dump(config_data, f, default_flow_style=False)
                    
                    st.success(f"✅ Configuração atualizada! Novo valor: ${new_amount:.2f}")
                    st.toast("🎉 Bot pode continuar operando!", icon="✅")
                    st.balloons()
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {e}")
        
        # Opções rápidas
        st.markdown("**⚡ Opções rápidas:**")
        quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
        
        with quick_col1:
            if st.button(f"${int(usdt_balance * 0.5)}", help="50% do saldo"):
                config_data['trading']['amount_per_trade'] = float(int(usdt_balance * 0.5))
                with open(config_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
                st.toast(f"✅ Alterado para ${int(usdt_balance * 0.5)}", icon="✅")
                st.cache_data.clear()
                st.rerun()
        
        with quick_col2:
            if st.button(f"${int(usdt_balance * 0.6)}", help="60% do saldo"):
                config_data['trading']['amount_per_trade'] = float(int(usdt_balance * 0.6))
                with open(config_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
                st.toast(f"✅ Alterado para ${int(usdt_balance * 0.6)}", icon="✅")
                st.cache_data.clear()
                st.rerun()
        
        with quick_col3:
            if st.button(f"${int(usdt_balance * 0.7)}", help="70% do saldo"):
                config_data['trading']['amount_per_trade'] = float(int(usdt_balance * 0.7))
                with open(config_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
                st.toast(f"✅ Alterado para ${int(usdt_balance * 0.7)}", icon="✅")
                st.cache_data.clear()
                st.rerun()
        
        with quick_col4:
            if st.button(f"${int(usdt_balance * 0.8)}", help="80% do saldo (recomendado)"):
                config_data['trading']['amount_per_trade'] = float(int(usdt_balance * 0.8))
                with open(config_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
                st.toast(f"✅ Alterado para ${int(usdt_balance * 0.8)}", icon="✅")
                st.cache_data.clear()
                st.rerun()
        
        st.markdown("---")
    
    # ---- CONTROLES RÁPIDOS ----
    st.markdown("#### ⚡ Configuração Atual")
    
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)
    
    with ctrl_col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ff6b6b20, #ff6b6b40); 
                    padding: 15px; border-radius: 10px; text-align: center;
                    border: 2px solid #ff6b6b;">
            <div style="font-size: 24px;">⏱️</div>
            <div style="font-size: 12px; color: #8b98a5;">Tempo Máximo</div>
            <div style="font-size: 18px; font-weight: bold; color: #e7e9ea;">{} min</div>
            <div style="font-size: 10px; color: #ff6b6b;">Vende após esse tempo</div>
        </div>
        """.format(max_hold_minutes), unsafe_allow_html=True)
    
    with ctrl_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4ecdc420, #4ecdc440); 
                    padding: 15px; border-radius: 10px; text-align: center;
                    border: 2px solid #4ecdc4;">
            <div style="font-size: 24px;">💰</div>
            <div style="font-size: 12px; color: #8b98a5;">Valor/Trade</div>
            <div style="font-size: 18px; font-weight: bold; color: #e7e9ea;">${:.0f}</div>
            <div style="font-size: 10px; color: #4ecdc4;">Por operação</div>
        </div>
        """.format(amount_per_trade), unsafe_allow_html=True)
    
    with ctrl_col3:
        stop_loss_pct = -0.8  # Configurado na estratégia
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f9188020, #f9188040); 
                    padding: 15px; border-radius: 10px; text-align: center;
                    border: 2px solid #f91880;">
            <div style="font-size: 24px;">🛑</div>
            <div style="font-size: 12px; color: #8b98a5;">Stop Loss</div>
            <div style="font-size: 18px; font-weight: bold; color: #e7e9ea;">{}%</div>
            <div style="font-size: 10px; color: #f91880;">Proteção automática</div>
        </div>
        """.format(stop_loss_pct), unsafe_allow_html=True)
    
    with ctrl_col4:
        take_profit_pct = 3.0  # Configurado na estratégia
        st.markdown("""
        <div style="background: linear-gradient(135deg, #00ba7c20, #00ba7c40); 
                    padding: 15px; border-radius: 10px; text-align: center;
                    border: 2px solid #00ba7c;">
            <div style="font-size: 24px;">🎯</div>
            <div style="font-size: 12px; color: #8b98a5;">Take Profit</div>
            <div style="font-size: 18px; font-weight: bold; color: #e7e9ea;">+{}%</div>
            <div style="font-size: 10px; color: #00ba7c;">Meta de lucro</div>
        </div>
        """.format(take_profit_pct), unsafe_allow_html=True)
    
    # ---- AJUSTAR CONFIGURAÇÕES ----
    with st.expander("⚙️ Ajustar Configurações do Bot", expanded=False):
        st.markdown("**Altere as configurações abaixo e clique em Salvar:**")
        
        adj_col1, adj_col2 = st.columns(2)
        
        with adj_col1:
            new_trade_amount = st.slider(
                "💰 Valor por Trade ($)",
                min_value=100,
                max_value=5000,
                value=int(amount_per_trade),
                step=100,
                help="Quanto investir em cada operação"
            )
            
            new_max_positions = st.slider(
                "📊 Máximo de Posições",
                min_value=1,
                max_value=20,
                value=config_data.get('trading', {}).get('max_positions', 8),
                step=1,
                help="Quantas moedas diferentes pode ter ao mesmo tempo"
            )
        
        with adj_col2:
            st.markdown("**⏱️ Estratégias de Tempo:**")
            time_strategy = st.radio(
                "Selecione o modo",
                options=["🚀 Agressivo (5 min)", "⚡ Rápido (10 min)", "🐢 Conservador (15 min)"],
                index=1,
                help="Tempo máximo para segurar uma posição"
            )
            
            st.markdown("**🛡️ Proteção:**")
            risk_level = st.radio(
                "Nível de risco",
                options=["🟢 Baixo (SL: -0.5%)", "🟡 Médio (SL: -0.8%)", "🔴 Alto (SL: -1.2%)"],
                index=1,
                help="Stop Loss automático"
            )
        
        if st.button("💾 SALVAR CONFIGURAÇÕES", type="primary", use_container_width=True):
            try:
                # Atualiza config
                config_data['trading']['amount_per_trade'] = float(new_trade_amount)
                config_data['trading']['max_positions'] = new_max_positions
                
                with open(config_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
                
                st.success(f"✅ Configurações salvas!")
                st.toast("💾 Configurações atualizadas! Reinicie o bot para aplicar todas.", icon="✅")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro: {e}")
        
        st.info("💡 **Nota:** Alterações no tempo e stop loss requerem edição da estratégia (smart_strategy.py)")
    
    # ---- AÇÕES RÁPIDAS ----
    st.markdown("#### 🎮 Ações Rápidas")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("⚡ MODO TURBO", help="$1000 por trade, mais operações", use_container_width=True):
            config_data['trading']['amount_per_trade'] = 1000.0
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            st.toast("⚡ Modo Turbo! $1000 por trade", icon="⚡")
            st.cache_data.clear()
            st.rerun()
    
    with action_col2:
        if st.button("💪 MODO POWER", help="$2000 por trade, equilibrado", use_container_width=True):
            config_data['trading']['amount_per_trade'] = 2000.0
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            st.toast("💪 Modo Power! $2000 por trade", icon="💪")
            st.cache_data.clear()
            st.rerun()
    
    with action_col3:
        if st.button("🔄 REFRESH", help="Atualiza dados", use_container_width=True):
            st.cache_data.clear()
            st.toast("🔄 Dados atualizados!", icon="✅")
            st.rerun()
    
    # Status atual
    status_color = "#00ba7c" if usdt_balance >= amount_per_trade else "#f91880"
    status_text = "OPERANDO" if usdt_balance >= amount_per_trade else "BLOQUEADO"
    
    st.markdown(f"""
    <div style="background-color: #1a1f29; padding: 10px; border-radius: 8px; margin-top: 10px;">
        <span style="color: #8b98a5;">📋 Status:</span>
        <span style="color: {status_color}; font-weight: bold;"> {status_text}</span> |
        <span style="color: #8b98a5;"> Tempo Máx:</span>
        <span style="color: #ff6b6b;">{max_hold_minutes} min</span> |
        <span style="color: #8b98a5;"> Venda Forçada:</span>
        <span style="color: #00ba7c;">SIM</span> |
        <span style="color: #8b98a5;"> Valor:</span>
        <span style="color: #ffd700;">${amount_per_trade:.0f}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
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
    
    # Cores por temperatura (Quente = tons de vermelho/laranja, Frio = tons de azul)
    trend_colors = {
        # QUENTES (Alta)
        'ALTA FORTE': '#ff0000',    # Vermelho intenso - FERVENDO
        'ALTA': '#ff4500',          # Laranja avermelhado - SUPER QUENTE
        'SUBINDO': '#ff8c00',       # Laranja - QUENTE
        'OVERBOUGHT': '#ff6347',    # Tomate - FERVENDO
        # FRIOS (Baixa)
        'QUEDA FORTE': '#00bfff',   # Azul claro intenso - CONGELANDO
        'QUEDA': '#1e90ff',         # Azul dodger - SUPER FRIO
        'CAINDO': '#4169e1',        # Azul royal - FRIO
        'OVERSOLD': '#00ced1',      # Turquesa - CONGELANDO
        # NEUTROS
        'LATERAL': '#8b98a5',       # Cinza - MORNO
        'NEUTRO': '#8b98a5',
        'ERRO': '#8b98a5'
    }
    
    # Cores de temperatura
    temp_colors = {
        'FERVENDO': '#ff0000',      # Vermelho intenso
        'SUPER QUENTE': '#ff4500',  # Laranja avermelhado
        'QUENTE': '#ff8c00',        # Laranja
        'MORNO': '#ffd700',         # Amarelo/Dourado
        'FRIO': '#4169e1',          # Azul royal
        'SUPER FRIO': '#1e90ff',    # Azul dodger
        'CONGELANDO': '#00bfff',    # Azul claro intenso
        'NEUTRO': '#8b98a5'
    }
    
    # Grid de cards
    cols = st.columns(4)
    
    for i, symbol in enumerate(MAIN_CRYPTOS):
        with cols[i % 4]:
            data = crypto_values.get(symbol, {'amount': 0, 'price': 0, 'change': 0, 'value': 0})
            pred = predictions.get(symbol, {'trend': 'NEUTRO', 'signal': '⚪', 'confidence': 50, 'rsi': 50, 'temp': 'MORNO', 'temp_emoji': '🌡️', 'price_change': 0})
            
            # Busca preço se não tiver
            if data['price'] == 0 and symbol in prices:
                data['price'] = prices[symbol]['price']
                data['change'] = prices[symbol]['change']
            
            trend_color = trend_colors.get(pred['trend'], '#8b98a5')
            temp_color = temp_colors.get(pred.get('temp', 'MORNO'), '#8b98a5')
            temp_emoji = pred.get('temp_emoji', '🌡️')
            temp_text = pred.get('temp', 'MORNO')
            
            st.markdown(f"""
            <div style="background-color: #1a1f29; padding: 15px; border-radius: 10px; 
                        border-left: 4px solid {temp_color}; margin-bottom: 10px;
                        box-shadow: 0 0 10px {temp_color}40;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 18px; font-weight: bold; color: #e7e9ea;">{symbol}</span>
                    <span style="font-size: 20px;">{temp_emoji}</span>
                </div>
                <div style="margin: 8px 0;">
                    <span style="background-color: {temp_color}30; color: {temp_color}; 
                                 padding: 3px 10px; border-radius: 4px; font-size: 13px; font-weight: bold;">
                        {temp_text}
                    </span>
                    <span style="color: #8b98a5; font-size: 11px; margin-left: 5px;">
                        {pred['confidence']}%
                    </span>
                </div>
                <div style="color: {temp_color}; font-size: 11px; margin: 5px 0;">
                    {pred['trend']} {pred['signal']}
                </div>
                <div style="color: #e7e9ea; font-size: 14px; font-weight: bold;">
                    ${data['price']:,.2f}
                    <span style="color: {temp_color}; font-size: 12px;">
                        ({data['change']:+.1f}%)
                    </span>
                </div>
                <div style="color: #8b98a5; font-size: 11px;">
                    Qtd: {data['amount']:.6f} | RSI: {pred['rsi']:.0f}
                </div>
                <div style="color: {temp_color}; font-size: 16px; font-weight: bold; margin-top: 5px;">
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
        # Análise de Temperatura do Mercado
        st.markdown("### 🌡️ Termômetro do Mercado")
        st.markdown("**Sistema de cores:** 🔥 Quente = Alta | ❄️ Frio = Baixa")
        
        # Cards de temperatura por moeda
        temp_cols = st.columns(4)
        for i, symbol in enumerate(MAIN_CRYPTOS):
            with temp_cols[i % 4]:
                pred = predictions.get(symbol, {'rsi': 50, 'trend': 'NEUTRO', 'temp': 'MORNO', 'temp_emoji': '🌡️', 'price_change': 0})
                temp = pred.get('temp', 'MORNO')
                temp_emoji = pred.get('temp_emoji', '🌡️')
                temp_color = temp_colors.get(temp, '#8b98a5')
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {temp_color}20, {temp_color}40); 
                            padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px;
                            border: 2px solid {temp_color};">
                    <div style="font-size: 30px;">{temp_emoji}</div>
                    <div style="font-size: 16px; font-weight: bold; color: #e7e9ea;">{symbol}</div>
                    <div style="font-size: 14px; font-weight: bold; color: {temp_color};">{temp}</div>
                    <div style="font-size: 12px; color: #8b98a5;">RSI: {pred['rsi']:.0f}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        # Gráfico de Temperatura (Barras com gradiente)
        st.markdown("#### 📊 Análise de Tendências")
        
        temp_data = []
        for symbol in MAIN_CRYPTOS:
            pred = predictions.get(symbol, {'rsi': 50, 'trend': 'NEUTRO', 'temp': 'MORNO', 'price_change': 0})
            temp_data.append({
                'symbol': symbol,
                'rsi': pred['rsi'],
                'trend': pred['trend'],
                'temp': pred.get('temp', 'MORNO'),
                'price_change': pred.get('price_change', 0)
            })
        
        df_temp = pd.DataFrame(temp_data)
        
        # Barras de RSI com cores de temperatura
        fig_temp = go.Figure()
        
        # Define cores baseadas na temperatura
        bar_colors = []
        for _, row in df_temp.iterrows():
            temp = row['temp']
            if temp == 'FERVENDO':
                bar_colors.append('#ff0000')
            elif temp == 'SUPER QUENTE':
                bar_colors.append('#ff4500')
            elif temp == 'QUENTE':
                bar_colors.append('#ff8c00')
            elif temp == 'MORNO':
                bar_colors.append('#ffd700')
            elif temp == 'FRIO':
                bar_colors.append('#4169e1')
            elif temp == 'SUPER FRIO':
                bar_colors.append('#1e90ff')
            elif temp == 'CONGELANDO':
                bar_colors.append('#00bfff')
            else:
                bar_colors.append('#8b98a5')
        
        fig_temp.add_trace(go.Bar(
            x=df_temp['symbol'],
            y=df_temp['rsi'],
            marker_color=bar_colors,
            text=[f"{r['temp']}" for _, r in df_temp.iterrows()],
            textposition='outside',
            name='Temperatura'
        ))
        
        # Linhas de referência
        fig_temp.add_hline(y=30, line_dash="dash", line_color="#00bfff", annotation_text="❄️ Zona Fria")
        fig_temp.add_hline(y=50, line_dash="dot", line_color="#ffd700", annotation_text="🌡️ Neutro")
        fig_temp.add_hline(y=70, line_dash="dash", line_color="#ff4500", annotation_text="🔥 Zona Quente")
        
        fig_temp.update_layout(
            title="🌡️ Termômetro RSI por Criptomoeda",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e7e9ea',
            yaxis=dict(range=[0, 100], title="RSI (Intensidade)"),
            xaxis=dict(title=""),
            height=450
        )
        
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Legenda de Temperaturas
        st.markdown("""
        ---
        ### 🌡️ Escala de Temperatura do Mercado
        
        | Emoji | Temperatura | Significado | Cor | Ação Sugerida |
        |-------|-------------|-------------|-----|---------------|
        | 🔥 | **FERVENDO** | Alta muito forte, RSI > 70 | 🔴 Vermelho Intenso | ⚠️ Cuidado, pode reverter |
        | 🌶️ | **SUPER QUENTE** | Alta forte, tendência de subida | 🟠 Laranja Vermelho | 📈 Momento de alta |
        | ☀️ | **QUENTE** | Subindo, tendência positiva | 🟡 Laranja | ✅ Bom momento |
        | 🌡️ | **MORNO** | Lateral, sem tendência clara | ⚪ Amarelo/Dourado | ⏳ Aguardar |
        | 🌬️ | **FRIO** | Caindo, tendência negativa | 🔵 Azul Royal | ⚠️ Cautela |
        | 🥶 | **SUPER FRIO** | Queda forte, tendência de baixa | 🔵 Azul Dodger | 📉 Momento de baixa |
        | ❄️ | **CONGELANDO** | Queda muito forte, RSI < 30 | 🔵 Azul Claro | 🛒 Possível oportunidade |
        
        ---
        **Dica:** Temperaturas extremas (🔥 FERVENDO ou ❄️ CONGELANDO) geralmente indicam reversão próxima!
        """)

else:
    st.error("❌ Não foi possível conectar à exchange. Verifique suas credenciais.")
    st.info("💡 Dica: Certifique-se que o arquivo `.env` contém as chaves da API.")

# ========================================
# FOOTER
# ========================================

st.divider()
st.caption(f"🤖 App Leonardo v2.0 | Última atualização: {datetime.now().strftime('%H:%M:%S')} | Made with ❤️")
