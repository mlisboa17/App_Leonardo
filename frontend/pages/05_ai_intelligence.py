"""
🤖 AI Intelligence Page - Análise de Mercado INTELIGENTE
INTEGRADA com sistema existente + APRENDIZADO DIÁRIO
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from binance.client import Client

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils.session_manager import (
    get_ai_data, 
    get_config_changes, 
    get_autotuner_state, 
    get_positions,
    get_history,
    get_balances
)

# ============================================================
# CONFIGURAÇÕES
# ============================================================
API_KEY = "R4So8k98GeMLDhNoMmAedjXjYnUBpxCVZKH9bNbMrM6lfbJzFlY9m3okEbXRuJqR"
API_SECRET = "n00KKGAVD7QXbOd3fkCRLXKWFK3PuVS8WUk6wtfpRT0UJG9qRYsay9Qt6LoUKwCN"

# Diretórios para salvar dados
AI_DATA_DIR = Path("data/ai")
MARKET_PATTERNS_FILE = AI_DATA_DIR / "market_patterns.json"
DAILY_SNAPSHOTS_FILE = AI_DATA_DIR / "daily_snapshots.json"
STRATEGY_RULES_FILE = AI_DATA_DIR / "strategy_rules.json"

# Criar diretórios se não existem
AI_DATA_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="🤖 AI Intelligence", layout="wide")

# Session State
if 'binance_client' not in st.session_state:
    st.session_state.binance_client = None
if 'last_ai_update' not in st.session_state:
    st.session_state.last_ai_update = None
if 'last_daily_save' not in st.session_state:
    st.session_state.last_daily_save = None

# ============================================================
# FUNÇÕES DE APRENDIZADO
# ============================================================

def load_market_patterns():
    """Carrega padrões de mercado salvos"""
    if MARKET_PATTERNS_FILE.exists():
        with open(MARKET_PATTERNS_FILE, 'r') as f:
            return json.load(f)
    return {
        'patterns': [],
        'correlations': {},
        'success_rates': {},
        'best_entry_conditions': [],
        'worst_exit_conditions': []
    }

def load_daily_snapshots():
    """Carrega snapshots diários"""
    if DAILY_SNAPSHOTS_FILE.exists():
        with open(DAILY_SNAPSHOTS_FILE, 'r') as f:
            return json.load(f)
    return []

def load_strategy_rules():
    """Carrega regras de estratégia aprendidas"""
    if STRATEGY_RULES_FILE.exists():
        with open(STRATEGY_RULES_FILE, 'r') as f:
            return json.load(f)
    return {
        'buy_rules': [],
        'sell_rules': [],
        'risk_rules': [],
        'learned_at': None
    }

def save_daily_snapshot(market_data, positions, history, balances):
    """Salva snapshot diário para aprendizado"""
    snapshots = load_daily_snapshots()
    
    today = datetime.now().date().isoformat()
    
    # Verifica se já salvou hoje
    if snapshots and snapshots[-1].get('date') == today:
        return
    
    # Calcula métricas do dia
    daily_trades = [t for t in history if t.get('exit_time', '').startswith(today)]
    daily_pnl = sum(t.get('pnl_usd', 0) for t in daily_trades)
    wins = sum(1 for t in daily_trades if t.get('pnl_usd', 0) > 0)
    losses = sum(1 for t in daily_trades if t.get('pnl_usd', 0) < 0)
    
    snapshot = {
        'date': today,
        'timestamp': datetime.now().isoformat(),
        'market': {
            'btc_price': market_data.get('btc', {}).get('price', 0),
            'btc_change': market_data.get('btc', {}).get('change_24h', 0),
            'volatility': market_data.get('btc', {}).get('volatility', 0),
            'rsi': market_data.get('indicators', {}).get('rsi', 50),
            'trend': market_data.get('analysis', {}).get('trend', 'NEUTRAL')
        },
        'trading': {
            'total_trades': len(daily_trades),
            'wins': wins,
            'losses': losses,
            'win_rate': (wins / len(daily_trades) * 100) if daily_trades else 0,
            'pnl': daily_pnl,
            'positions_open': len(positions) if isinstance(positions, dict) else 0
        },
        'balance': {
            'total': balances.get('total_balance', 0),
            'usdt': balances.get('usdt_balance', 0),
            'crypto': balances.get('crypto_balance', 0)
        }
    }
    
    snapshots.append(snapshot)
    
    # Mantém últimos 365 dias
    if len(snapshots) > 365:
        snapshots = snapshots[-365:]
    
    with open(DAILY_SNAPSHOTS_FILE, 'w') as f:
        json.dump(snapshots, f, indent=2)
    
    st.session_state.last_daily_save = datetime.now()
    
    return snapshot

def analyze_patterns(snapshots):
    """Analisa padrões nos dados históricos"""
    if len(snapshots) < 7:
        return None
    
    df = pd.DataFrame(snapshots)
    
    patterns = {
        'best_rsi_for_entry': None,
        'best_volatility_range': None,
        'best_trend_for_trading': None,
        'optimal_positions_count': None,
        'correlations': {}
    }
    
    # Melhor RSI para entrada (quando tivemos mais sucesso)
    profitable_days = df[df['trading'].apply(lambda x: x.get('pnl', 0) > 0)]
    if len(profitable_days) > 0:
        avg_rsi_profit = profitable_days['market'].apply(lambda x: x.get('rsi', 50)).mean()
        patterns['best_rsi_for_entry'] = avg_rsi_profit
    
    # Melhor range de volatilidade
    high_winrate_days = df[df['trading'].apply(lambda x: x.get('win_rate', 0) > 60)]
    if len(high_winrate_days) > 0:
        avg_vol = high_winrate_days['market'].apply(lambda x: x.get('volatility', 0)).mean()
        patterns['best_volatility_range'] = avg_vol
    
    # Tendência mais lucrativa
    trend_pnl = {}
    for trend in ['BULLISH', 'BEARISH', 'NEUTRAL']:
        trend_days = df[df['market'].apply(lambda x: x.get('trend') == trend)]
        if len(trend_days) > 0:
            avg_pnl = trend_days['trading'].apply(lambda x: x.get('pnl', 0)).mean()
            trend_pnl[trend] = avg_pnl
    
    if trend_pnl:
        patterns['best_trend_for_trading'] = max(trend_pnl, key=trend_pnl.get)
    
    # Número ótimo de posições
    position_performance = {}
    for _, row in df.iterrows():
        pos_count = row['trading'].get('positions_open', 0)
        pnl = row['trading'].get('pnl', 0)
        if pos_count not in position_performance:
            position_performance[pos_count] = []
        position_performance[pos_count].append(pnl)
    
    if position_performance:
        avg_pnl_by_positions = {k: sum(v)/len(v) for k, v in position_performance.items()}
        patterns['optimal_positions_count'] = max(avg_pnl_by_positions, key=avg_pnl_by_positions.get)
    
    return patterns

def generate_strategy_rules(patterns, snapshots):
    """Gera regras de estratégia baseadas nos padrões"""
    rules = {
        'buy_rules': [],
        'sell_rules': [],
        'risk_rules': [],
        'learned_at': datetime.now().isoformat()
    }
    
    if not patterns:
        return rules
    
    # Regras de COMPRA
    best_rsi = patterns.get('best_rsi_for_entry')
    if best_rsi:
        if best_rsi < 40:
            rules['buy_rules'].append({
                'rule': 'BUY_LOW_RSI',
                'description': f'Comprar quando RSI < {best_rsi:.0f}',
                'confidence': 'HIGH',
                'reason': 'Padrão histórico mostra sucesso em oversold'
            })
        elif best_rsi > 50:
            rules['buy_rules'].append({
                'rule': 'BUY_MOMENTUM',
                'description': f'Comprar em momentum (RSI ~{best_rsi:.0f})',
                'confidence': 'MEDIUM',
                'reason': 'Histórico mostra lucro seguindo tendência'
            })
    
    best_trend = patterns.get('best_trend_for_trading')
    if best_trend:
        rules['buy_rules'].append({
            'rule': f'PREFER_{best_trend}',
            'description': f'Priorizar trades em mercado {best_trend}',
            'confidence': 'HIGH',
            'reason': f'Melhor performance histórica em {best_trend}'
        })
    
    # Regras de VENDA
    best_vol = patterns.get('best_volatility_range')
    if best_vol and best_vol > 3:
        rules['sell_rules'].append({
            'rule': 'SELL_HIGH_VOL',
            'description': f'Vender quando volatilidade > {best_vol:.1f}%',
            'confidence': 'MEDIUM',
            'reason': 'Alta volatilidade precede correções'
        })
    
    # Regras de RISCO
    optimal_pos = patterns.get('optimal_positions_count')
    if optimal_pos:
        rules['risk_rules'].append({
            'rule': 'OPTIMAL_POSITIONS',
            'description': f'Manter ~{optimal_pos} posições abertas',
            'confidence': 'HIGH',
            'reason': f'Melhor performance com {optimal_pos} posições simultâneas'
        })
    
    # Salvar regras
    with open(STRATEGY_RULES_FILE, 'w') as f:
        json.dump(rules, f, indent=2)
    
    return rules

def get_binance_client():
    """Cliente Binance"""
    if st.session_state.binance_client is None:
        try:
            st.session_state.binance_client = Client(API_KEY, API_SECRET)
        except:
            pass
    return st.session_state.binance_client

def get_advanced_market_data():
    """Análise de mercado COMPLETA"""
    client = get_binance_client()
    if not client:
        return {}
    
    try:
        # BTC
        btc_ticker = client.get_ticker(symbol='BTCUSDT')
        btc_price = float(btc_ticker['lastPrice'])
        btc_change = float(btc_ticker['priceChangePercent'])
        btc_volume = float(btc_ticker['volume'])
        btc_high = float(btc_ticker['highPrice'])
        btc_low = float(btc_ticker['lowPrice'])
        
        # Klines para análise
        klines = client.get_klines(symbol='BTCUSDT', interval='1h', limit=50)
        closes = [float(k[4]) for k in klines]
        
        # RSI
        rsi = calculate_rsi(closes)
        
        # Tendência
        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50
        trend = "BULLISH" if btc_price > sma_20 > sma_50 else "BEARISH" if btc_price < sma_20 < sma_50 else "NEUTRAL"
        
        # Volatilidade
        volatility = ((btc_high - btc_low) / btc_low) * 100
        
        return {
            'btc': {
                'price': btc_price,
                'change_24h': btc_change,
                'volume': btc_volume,
                'high_24h': btc_high,
                'low_24h': btc_low,
                'volatility': volatility
            },
            'indicators': {
                'rsi': rsi,
                'sma_20': sma_20,
                'sma_50': sma_50
            },
            'analysis': {
                'trend': trend
            },
            'historical': {
                'closes': closes
            }
        }
    except Exception as e:
        return {}

def calculate_rsi(closes, period=14):
    """Calcula RSI"""
    if len(closes) < period:
        return 50
    
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ============================================================
# INTERFACE PRINCIPAL
# ============================================================

st.markdown('<div class="main-header">🤖 AI INTELLIGENCE - App R7</div>', unsafe_allow_html=True)

# Carregar dados existentes
ai_data = get_ai_data()
config_changes = get_config_changes()
autotuner_state = get_autotuner_state()
positions = get_positions()
history = get_history()
balances = get_balances()

# Carregar dados de aprendizado
patterns = load_market_patterns()
snapshots = load_daily_snapshots()
strategy_rules = load_strategy_rules()

st.markdown("---")

# ============================================================
# SEÇÃO 1: STATUS INTEGRADO
# ============================================================
st.header("📊 Status do Sistema de IA")

col1, col2, col3, col4, col5 = st.columns(5)

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
    days_learning = len(snapshots)
    st.metric("📚 Dias Aprendendo", days_learning)

with col4:
    patterns_found = len(patterns.get('patterns', []))
    st.metric("🔍 Padrões Encontrados", patterns_found)

with col5:
    rules_learned = len(strategy_rules.get('buy_rules', [])) + len(strategy_rules.get('sell_rules', []))
    st.metric("🎯 Regras Aprendidas", rules_learned)

st.markdown("---")

# ============================================================
# SEÇÃO 2: MERCADO EM TEMPO REAL
# ============================================================
st.header("💹 Análise de Mercado em Tempo Real")

# Buscar dados do mercado
market_data = get_advanced_market_data()

if market_data:
    btc = market_data.get('btc', {})
    indicators = market_data.get('indicators', {})
    analysis = market_data.get('analysis', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        btc_color = "🟢" if btc.get('change_24h', 0) >= 0 else "🔴"
        st.metric(f"{btc_color} **BTC**", 
                 f"${btc.get('price', 0):,.2f}",
                 f"{btc.get('change_24h', 0):+.2f}%")
    
    with col2:
        rsi = indicators.get('rsi', 50)
        rsi_status = "🟢 OVERSOLD" if rsi < 30 else "🔴 OVERBOUGHT" if rsi > 70 else "🟡 NEUTRO"
        st.metric("RSI", f"{rsi:.1f}", rsi_status)
    
    with col3:
        trend = analysis.get('trend', 'NEUTRAL')
        trend_emoji = "🟢" if trend == "BULLISH" else "🔴" if trend == "BEARISH" else "🟡"
        st.metric(f"{trend_emoji} Tendência", trend)
    
    with col4:
        vol = btc.get('volatility', 0)
        vol_color = "🟢" if vol < 2 else "🟡" if vol < 4 else "🔴"
        st.metric(f"{vol_color} Volatilidade", f"{vol:.2f}%")
    
    # Salvar snapshot diário
    current_hour = datetime.now().hour
    if current_hour == 23 or st.session_state.last_daily_save is None:  # Salva às 23h ou primeira vez
        snapshot = save_daily_snapshot(market_data, positions, history, balances)
        if snapshot:
            st.success(f"✅ Snapshot diário salvo! Total: {len(snapshots)} dias de aprendizado")
    
    st.markdown("---")
    
    # ============================================================
    # SEÇÃO 3: PADRÕES APRENDIDOS
    # ============================================================
    st.header("🧠 Padrões Aprendidos com o Mercado")
    
    if len(snapshots) >= 7:
        analyzed_patterns = analyze_patterns(snapshots)
        
        if analyzed_patterns:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Condições Ideais Identificadas")
                
                best_rsi = analyzed_patterns.get('best_rsi_for_entry')
                if best_rsi:
                    st.metric("🎯 Melhor RSI para Entrada", f"{best_rsi:.1f}")
                    st.write(f"*Baseado em {len(snapshots)} dias de análise*")
                
                best_vol = analyzed_patterns.get('best_volatility_range')
                if best_vol:
                    st.metric("📈 Volatilidade Ideal", f"{best_vol:.2f}%")
                
                optimal_pos = analyzed_patterns.get('optimal_positions_count')
                if optimal_pos:
                    st.metric("💼 Nº Ótimo de Posições", f"{optimal_pos}")
            
            with col2:
                st.subheader("📈 Performance por Tendência")
                
                best_trend = analyzed_patterns.get('best_trend_for_trading')
                if best_trend:
                    st.success(f"✅ Melhor performance em: **{best_trend}**")
                
                # Gráfico de performance
                if snapshots:
                    df = pd.DataFrame(snapshots)
                    daily_pnls = df['trading'].apply(lambda x: x.get('pnl', 0)).tolist()
                    dates = df['date'].tolist()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=daily_pnls,
                        mode='lines+markers',
                        name='PnL Diário',
                        line=dict(color='#00ff88', width=2)
                    ))
                    fig.update_layout(
                        title="PnL Diário - Últimos Dias",
                        height=300,
                        template='plotly_dark'
                    )
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"📚 Coletando dados... {len(snapshots)}/7 dias necessários para análise de padrões")
    
    st.markdown("---")
    
    # ============================================================
    # SEÇÃO 4: REGRAS DE ESTRATÉGIA
    # ============================================================
    st.header("🎯 Regras de Estratégia Aprendidas")
    
    if len(snapshots) >= 7:
        # Gerar regras baseadas nos padrões
        generated_rules = generate_strategy_rules(analyzed_patterns, snapshots)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🟢 Regras de COMPRA")
            buy_rules = generated_rules.get('buy_rules', [])
            if buy_rules:
                for rule in buy_rules:
                    with st.expander(f"✅ {rule['rule']}"):
                        st.write(f"**Descrição:** {rule['description']}")
                        st.write(f"**Confiança:** {rule['confidence']}")
                        st.write(f"**Razão:** {rule['reason']}")
            else:
                st.info("Aprendendo...")
        
        with col2:
            st.subheader("🔴 Regras de VENDA")
            sell_rules = generated_rules.get('sell_rules', [])
            if sell_rules:
                for rule in sell_rules:
                    with st.expander(f"⚠️ {rule['rule']}"):
                        st.write(f"**Descrição:** {rule['description']}")
                        st.write(f"**Confiança:** {rule['confidence']}")
                        st.write(f"**Razão:** {rule['reason']}")
            else:
                st.info("Aprendendo...")
        
        with col3:
            st.subheader("🛡️ Regras de RISCO")
            risk_rules = generated_rules.get('risk_rules', [])
            if risk_rules:
                for rule in risk_rules:
                    with st.expander(f"🔒 {rule['rule']}"):
                        st.write(f"**Descrição:** {rule['description']}")
                        st.write(f"**Confiança:** {rule['confidence']}")
                        st.write(f"**Razão:** {rule['reason']}")
            else:
                st.info("Aprendendo...")
    else:
        st.info("🎓 IA está aprendendo... Aguarde 7 dias de dados para gerar estratégias")
    
    st.markdown("---")
    
    # ============================================================
    # SEÇÃO 5: TABELA DE APRENDIZADO
    # ============================================================
    st.header("📚 Histórico de Aprendizado Diário")
    
    if snapshots:
        df_snapshots = []
        for snap in snapshots[-30:]:  # Últimos 30 dias
            df_snapshots.append({
                'Data': snap['date'],
                'BTC': f"${snap['market']['btc_price']:,.0f}",
                'Variação': f"{snap['market']['btc_change']:+.2f}%",
                'RSI': f"{snap['market']['rsi']:.1f}",
                'Tendência': snap['market']['trend'],
                'Trades': snap['trading']['total_trades'],
                'Win Rate': f"{snap['trading']['win_rate']:.1f}%",
                'PnL': f"${snap['trading']['pnl']:+.2f}",
                'Posições': snap['trading']['positions_open'],
                'Saldo': f"${snap['balance']['total']:.2f}"
            })
        
        df = pd.DataFrame(df_snapshots)
        st.dataframe(df, use_container_width=True, height=400)
        
        # Download dos dados
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Baixar Dados de Aprendizado",
            data=csv,
            file_name=f"ai_learning_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum dado histórico ainda. A IA começará a aprender a partir de hoje!")

else:
    st.warning("⚠️ Aguardando conexão com Binance...")

st.markdown("---")

# ============================================================
# SEÇÃO 6: AUTO-TUNER EXISTENTE
# ============================================================
st.header("🎛️ Auto-Tuner - Integração com Sistema Existente")

current = autotuner_state.get('current', {})
market_cond = current.get('market_conditions', {})

col1, col2, col3, col4 = st.columns(4)

with col1:
    trend = market_cond.get('trend', 'unknown')
    st.metric("Tendência Auto-Tuner", trend.upper())

with col2:
    vol_level = market_cond.get('volatility_level', 'unknown')
    st.metric("Volatilidade", vol_level.upper())

with col3:
    vol_ratio = market_cond.get('volume_ratio', 1.0)
    st.metric("Volume", f"{vol_ratio:.2f}x")

with col4:
    action = market_cond.get('recommended_action', 'hold')
    st.metric("Ação Recomendada", action.upper())

st.markdown("---")

# Histórico de mudanças
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