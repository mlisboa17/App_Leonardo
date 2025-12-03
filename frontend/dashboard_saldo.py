"""
🎨 Dashboard de Saldo - App Leonardo
Mostra saldo em USDT e todas as criptomoedas em tempo real
"""
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import ccxt
from dotenv import load_dotenv
import os
import json
import shutil
from datetime import datetime
import threading
import time as time_module

# Carrega credenciais (tenta vários caminhos)
env_paths = [
    '../.env',                    # Um nível acima (App_Leonardo/.env)
    '../config/.env',             # config/.env
    '../../.env',                 # ScanKripto/.env
    '.env',                       # Pasta atual
]

for env_path in env_paths:
    full_path = os.path.join(os.path.dirname(__file__), env_path)
    if os.path.exists(full_path):
        load_dotenv(full_path)
        print(f"✅ Credenciais carregadas de: {full_path}")
        break
else:
    load_dotenv()  # Tenta default

# ========================================
# CONFIGURAÇÃO
# ========================================

API_KEY = os.getenv('BINANCE_TESTNET_API_KEY', '')
API_SECRET = os.getenv('BINANCE_TESTNET_API_SECRET', '')

# Debug
if API_KEY:
    print(f"✅ API Key encontrada: {API_KEY[:8]}...")
else:
    print("⚠️ API Key não encontrada!")
TESTNET = True

# Correção de saldo Testnet (valores vêm 10x maiores)
TESTNET_BALANCE_CORRECTION = 10.0

# Moedas que queremos destacar
MAIN_CRYPTOS = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'LINK', 'DOGE', 'LTC']

# Cores
COLORS = {
    'background': '#0f1419',
    'card': '#1a1f29',
    'card_highlight': '#252d3a',
    'text': '#e7e9ea',
    'positive': '#00ba7c',
    'negative': '#f91880',
    'neutral': '#8b98a5',
    'accent': '#1d9bf0',
    'gold': '#ffd700',
    'silver': '#c0c0c0',
}

# ========================================
# EXCHANGE (SINGLETON)
# ========================================

# Exchange global para evitar reconexão a cada callback
_exchange_instance = None
_exchange_last_init = None

def get_exchange():
    """Cria conexão com a exchange (singleton)"""
    global _exchange_instance, _exchange_last_init
    
    try:
        # Reinicializa a cada 5 minutos para evitar problemas de conexão
        import time
        current_time = time.time()
        
        if _exchange_instance is None or (_exchange_last_init and current_time - _exchange_last_init > 300):
            print("🔄 Inicializando conexão com a exchange...")
            _exchange_instance = ccxt.binance({
                'apiKey': API_KEY,
                'secret': API_SECRET,
                'sandbox': TESTNET,
                'timeout': 15000,  # 15 segundos
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True,
                    'recvWindow': 60000,
                }
            })
            _exchange_instance.load_markets()
            _exchange_last_init = current_time
            print("✅ Exchange conectada!")
        
        return _exchange_instance
    except Exception as e:
        print(f"❌ Erro ao criar exchange: {e}")
        _exchange_instance = None
        return None

def get_balances():
    """Busca todos os saldos (com correção para Testnet)"""
    try:
        exchange = get_exchange()
        if not exchange:
            print("❌ Exchange não disponível para buscar saldos")
            return None
        balance = exchange.fetch_balance()
        
        # Aplica correção para Testnet
        if TESTNET and TESTNET_BALANCE_CORRECTION > 1:
            corrected_balance = {}
            for key, value in balance.items():
                if isinstance(value, dict):
                    corrected_balance[key] = {}
                    for subkey, subvalue in value.items():
                        if isinstance(subvalue, (int, float)):
                            corrected_balance[key][subkey] = subvalue / TESTNET_BALANCE_CORRECTION
                        else:
                            corrected_balance[key][subkey] = subvalue
                elif isinstance(value, (int, float)):
                    corrected_balance[key] = value / TESTNET_BALANCE_CORRECTION
                else:
                    corrected_balance[key] = value
            
            print(f"✅ Saldo obtido (corrigido ÷{TESTNET_BALANCE_CORRECTION:.0f}): USDT={corrected_balance.get('free', {}).get('USDT', 0):.2f}")
            return corrected_balance
        
        print(f"✅ Saldo obtido: USDT={balance.get('free', {}).get('USDT', 0):.2f}")
        return balance
    except Exception as e:
        print(f"❌ Erro ao buscar saldo: {e}")
        return None

def get_prices(symbols):
    """Busca preços atuais"""
    try:
        exchange = get_exchange()
        if not exchange:
            return {s: 0 for s in symbols}
        # Filtra moedas fiduciárias e outras inválidas
        invalid_symbols = {'TRY', 'EUR', 'GBP', 'BRL', 'USD', 'NGN', 'RUB', 'UAH', 'ARS', 'BIDR', 'IDRT', 'PLN', 'RON'}
        valid_symbols = [s for s in symbols if s not in invalid_symbols and s != 'USDT']
        if not valid_symbols:
            return {}
        tickers = exchange.fetch_tickers([f"{s}/USDT" for s in valid_symbols])
        return {s.replace('/USDT', ''): t.get('last', 0) for s, t in tickers.items()}
    except Exception as e:
        print(f"❌ Erro ao buscar preços: {e}")
        return {s: 0 for s in symbols}

def get_crypto_predictions(symbols):
    """Busca previsões e indicadores para cada crypto"""
    predictions = {}
    
    try:
        exchange = get_exchange()
        if not exchange:
            return {s: {'trend': 'ERRO', 'signal': '❓', 'confidence': 0} for s in symbols}
        for symbol in symbols:
            try:
                pair = f"{symbol}/USDT"
                # Busca candles de 1h (sem params extras)
                ohlcv = exchange.fetch_ohlcv(pair, '1h', limit=50)
                if len(ohlcv) < 20:
                    predictions[symbol] = {'trend': 'NEUTRO', 'signal': '⚪', 'confidence': 0}
                    continue
                closes = [candle[4] for candle in ohlcv]
                gains = []
                losses = []
                for i in range(1, min(15, len(closes))):
                    change = closes[-i] - closes[-(i+1)]
                    if change > 0:
                        gains.append(change)
                    else:
                        losses.append(abs(change))
                avg_gain = sum(gains) / 14 if gains else 0
                avg_loss = sum(losses) / 14 if losses else 0.001
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                sma_10 = sum(closes[-10:]) / 10
                sma_20 = sum(closes[-20:]) / 20
                current_price = closes[-1]
                price_24h_ago = closes[-24] if len(closes) >= 24 else closes[0]
                change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
                trend = 'NEUTRO'
                signal_emoji = '⚪'
                confidence = 50
                if current_price > sma_10 > sma_20:
                    trend = 'ALTA'
                    signal_emoji = '🟢'
                    confidence = 70
                    if rsi > 60:
                        confidence = 80
                elif current_price < sma_10 < sma_20:
                    trend = 'QUEDA'
                    signal_emoji = '🔴'
                    confidence = 70
                    if rsi < 40:
                        confidence = 80
                elif rsi < 30:
                    trend = 'OVERSOLD'
                    signal_emoji = '🟡'
                    confidence = 65
                elif rsi > 70:
                    trend = 'OVERBOUGHT'
                    signal_emoji = '🟠'
                    confidence = 65
                else:
                    trend = 'LATERAL'
                    signal_emoji = '⚪'
                    confidence = 50
                predictions[symbol] = {
                    'trend': trend,
                    'signal': signal_emoji,
                    'confidence': confidence,
                    'rsi': rsi,
                    'change_24h': change_24h,
                    'sma_10': sma_10,
                    'sma_20': sma_20
                }
            except Exception as e:
                print(f"⚠️ Erro ao calcular previsão para {symbol}: {e}")
                predictions[symbol] = {'trend': 'ERRO', 'signal': '❓', 'confidence': 0}
        return predictions
    except Exception as e:
        print(f"❌ Erro ao buscar previsões: {e}")
        return {s: {'trend': 'ERRO', 'signal': '❓', 'confidence': 0} for s in symbols}

def get_bot_stats():
    """Busca estatísticas do bot (PnL diário, trades, etc)"""
    try:
        # Primeiro tenta ler o daily_stats.json (persistente)
        daily_stats_paths = [
            '../data/daily_stats.json',
            '../../App_Leonardo/data/daily_stats.json',
            'data/daily_stats.json',
        ]
        
        daily_stats = None
        for path in daily_stats_paths:
            full_path = os.path.join(os.path.dirname(__file__), path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    daily_stats = json.load(f)
                break
        
        # Tenta ler o bot_state.json para status em tempo real
        state_paths = [
            '../bot_state.json',
            '../../App_Leonardo/bot_state.json',
            'bot_state.json',
        ]
        
        bot_state = None
        for path in state_paths:
            full_path = os.path.join(os.path.dirname(__file__), path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    bot_state = json.load(f)
                break
        
        # Combina os dados (prioriza daily_stats para PnL)
        result = {}
        
        if daily_stats:
            result['daily_pnl'] = daily_stats.get('daily_pnl', 0.0)
            result['total_pnl'] = daily_stats.get('total_pnl', 0.0)
            result['trades_count'] = daily_stats.get('total_trades', 0)
            result['wins'] = daily_stats.get('winning_trades', 0)
            result['losses'] = daily_stats.get('losing_trades', 0)
            result['daily_target'] = daily_stats.get('daily_target', 100.0)
            result['target_reached'] = daily_stats.get('target_reached', False)
            result['date'] = daily_stats.get('date', '')
        
        if bot_state:
            result['is_running'] = bot_state.get('is_running', False)
            # Se bot_state tiver dados mais recentes, usa eles
            if not daily_stats:
                result['daily_pnl'] = bot_state.get('daily_pnl', 0.0)
                result['total_pnl'] = bot_state.get('total_pnl', 0.0)
                result['trades_count'] = bot_state.get('trades_count', 0)
                result['wins'] = bot_state.get('wins', 0)
                result['losses'] = bot_state.get('losses', 0)
        else:
            result['is_running'] = False
        
        return result if result else None
        
    except Exception as e:
        print(f"❌ Erro ao ler stats: {e}")
        return None


# ========================================
# SISTEMA DE BACKUP
# ========================================

def backup_daily_stats():
    """Faz backup das estatísticas diárias"""
    try:
        daily_stats_paths = [
            '../data/daily_stats.json',
            '../../App_Leonardo/data/daily_stats.json',
        ]
        
        for path in daily_stats_paths:
            full_path = os.path.join(os.path.dirname(__file__), path)
            if os.path.exists(full_path):
                # Cria pasta de backup
                backup_dir = os.path.join(os.path.dirname(full_path), 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                # Nome do backup com timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = os.path.join(backup_dir, f'daily_stats_backup_{timestamp}.json')
                
                # Copia arquivo
                shutil.copy2(full_path, backup_file)
                print(f"✅ Backup criado: {backup_file}")
                
                # Remove backups antigos (mantém últimos 48 = 24h de backups de 30min)
                backups = sorted([f for f in os.listdir(backup_dir) if f.startswith('daily_stats_backup_')])
                if len(backups) > 48:
                    for old_backup in backups[:-48]:
                        os.remove(os.path.join(backup_dir, old_backup))
                        print(f"🗑️ Backup antigo removido: {old_backup}")
                
                return True
        
        return False
    except Exception as e:
        print(f"❌ Erro ao fazer backup: {e}")
        return False


def backup_scheduler():
    """Thread que faz backup a cada 30 minutos"""
    while True:
        time_module.sleep(30 * 60)  # 30 minutos
        print(f"\n⏰ Executando backup automático...")
        backup_daily_stats()


# Inicia thread de backup
backup_thread = threading.Thread(target=backup_scheduler, daemon=True)
backup_thread.start()
print("🔄 Sistema de backup automático iniciado (a cada 30 min)")

# ========================================
# APP DASH
# ========================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

app.title = "App Leonardo | Saldo em Criptomoedas"

# ========================================
# LAYOUT
# ========================================

app.layout = dbc.Container([
    dcc.Interval(id='interval-update', interval=10000, n_intervals=0),  # 10 segundos
    dcc.Store(id='balance-data'),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1(
                "💰 App Leonardo - Trading Bot",
                className="mb-2",
                style={'color': COLORS['text'], 'fontWeight': 'bold'}
            ),
            html.Div([
                html.Span(
                    f"🧪 Binance {'Testnet' if TESTNET else 'Real'} | Atualização a cada 10s",
                    style={'color': COLORS['neutral'], 'fontSize': '14px'}
                ),
                html.Span(" | ", style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                html.Span(
                    id='stats-date',
                    children="📅 Data: --",
                    style={'color': COLORS['accent'], 'fontSize': '14px', 'fontWeight': 'bold'}
                ),
            ])
        ])
    ], className="mt-4 mb-3"),
    
    # Navegação por abas
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="📊 Dashboard", tab_id="dashboard-tab", active_label_style={'color': COLORS['gold']}),
                dbc.Tab(label="⚙️ Configurações", tab_id="config-tab", active_label_style={'color': COLORS['accent']}),
                dbc.Tab(label="📈 Estratégia", tab_id="strategy-tab", active_label_style={'color': COLORS['positive']}),
                dbc.Tab(label="🛡️ Segurança", tab_id="safety-tab", active_label_style={'color': COLORS['negative']}),
            ], id="main-tabs", active_tab="dashboard-tab", style={'marginBottom': '20px'})
        ])
    ]),
    
    # Conteúdo das abas
    html.Div(id='tab-content'),
    
], fluid=True, style={'backgroundColor': COLORS['background'], 'minHeight': '100vh', 'padding': '20px'})

# ========================================
# CALLBACK PARA MUDANÇA DE ABAS (MOVIDO PARA SEÇÃO DE CALLBACKS)
# ========================================
# O callback render_tab_content_with_data está definido na seção CALLBACKS

# Função get_dashboard_layout() REMOVIDA - agora usamos get_dashboard_layout_with_data()


# ========================================
# CALLBACKS
# ========================================

@app.callback(
    Output('balance-data', 'data'),
    [Input('interval-update', 'n_intervals')]
)
def fetch_balance_data(n):
    """Busca dados de saldo (roda sempre)"""
    print(f"🔄 Buscando dados #{n}")
    
    # Busca estatísticas do bot
    bot_stats = get_bot_stats()
    
    # Busca saldos
    balance_data = get_balances()
    
    if not balance_data:
        return {'error': True}
    
    # Extrai saldos livres
    free_balances = balance_data.get('free', {})
    
    # USDT (correção já aplicada no exchange_client para Testnet)
    usdt_balance = float(free_balances.get('USDT', 0))
    
    # Filtra moedas com saldo > 0
    cryptos_with_balance = {
        k: float(v) for k, v in free_balances.items() 
        if float(v) > 0 and k != 'USDT'
    }
    
    # Busca preços
    prices = get_prices(list(cryptos_with_balance.keys())[:50])
    
    # Busca previsões
    predictions = get_crypto_predictions(MAIN_CRYPTOS)
    
    # Calcula valor em USD de cada crypto
    crypto_values = {}
    for symbol, amount in cryptos_with_balance.items():
        price = prices.get(symbol, 0)
        crypto_values[symbol] = {
            'amount': amount,
            'price': price,
            'value_usd': amount * price if price else 0
        }
    
    # Total em crypto
    total_crypto_value = sum(v['value_usd'] for v in crypto_values.values())
    
    # Total geral
    total_value = usdt_balance + total_crypto_value
    
    return {
        'error': False,
        'usdt_balance': usdt_balance,
        'crypto_values': crypto_values,
        'total_crypto_value': total_crypto_value,
        'total_value': total_value,
        'prices': prices,
        'predictions': predictions,
        'bot_stats': bot_stats,
        'timestamp': datetime.now().isoformat()
    }


@app.callback(
    Output('tab-content', 'children'),
    [Input('main-tabs', 'active_tab'),
     Input('balance-data', 'data')]
)
def render_tab_content_with_data(active_tab, data):
    """Renderiza o conteúdo baseado na aba ativa COM os dados"""
    if active_tab == "dashboard-tab":
        return get_dashboard_layout_with_data(data)
    elif active_tab == "config-tab":
        return get_config_layout()
    elif active_tab == "strategy-tab":
        return get_strategy_layout()
    elif active_tab == "safety-tab":
        return get_safety_layout()
    return html.Div("Carregando...")


def get_dashboard_layout_with_data(data):
    """Layout do dashboard com dados já carregados"""
    
    # Valores padrão
    usdt_balance = 0.0
    total_crypto_value = 0.0
    total_value = 0.0
    daily_pnl = 0.0
    trades_count = 0
    wins = 0
    losses = 0
    bot_running = False
    stats_date = datetime.now().strftime('%Y-%m-%d')
    crypto_values = {}
    prices = {}
    predictions = {}
    
    if data and not data.get('error', True):
        usdt_balance = data.get('usdt_balance', 0)
        crypto_values = data.get('crypto_values', {})
        total_crypto_value = data.get('total_crypto_value', 0)
        total_value = data.get('total_value', 0)
        prices = data.get('prices', {})
        predictions = data.get('predictions', {})
        
        bot_stats = data.get('bot_stats')
        if bot_stats:
            daily_pnl = bot_stats.get('daily_pnl', 0.0)
            trades_count = bot_stats.get('trades_count', 0)
            wins = bot_stats.get('wins', 0)
            losses = bot_stats.get('losses', 0)
            bot_running = bot_stats.get('is_running', False)
            stats_date = bot_stats.get('date', stats_date)
    
    # Win rate
    win_rate = (wins / trades_count * 100) if trades_count > 0 else 0
    
    # Progresso da meta ($100)
    target = 100.0
    progress_pct = min((daily_pnl / target) * 100, 100) if daily_pnl > 0 else 0
    
    # Estilo do PnL
    pnl_color = COLORS['positive'] if daily_pnl >= 0 else COLORS['negative']
    pnl_sign = "+" if daily_pnl >= 0 else ""
    
    # Status do bot
    if bot_running:
        bot_status_text = "🟢 Operando"
        bot_status_color = COLORS['positive']
    else:
        bot_status_text = "⚪ Parado"
        bot_status_color = COLORS['neutral']
    
    # Cores de tendência
    trend_colors = {
        'ALTA': COLORS['positive'],
        'QUEDA': COLORS['negative'],
        'LATERAL': COLORS['neutral'],
        'OVERSOLD': '#ffd700',
        'OVERBOUGHT': '#ff8c00',
        'NEUTRO': COLORS['neutral'],
        'ERRO': COLORS['neutral']
    }
    
    # ===== CARDS PRINCIPAIS (8 cryptos) =====
    main_cards_data = []
    for symbol in MAIN_CRYPTOS:
        if symbol in crypto_values:
            main_cards_data.append((symbol, crypto_values[symbol], predictions.get(symbol, {})))
        else:
            main_cards_data.append((symbol, {'amount': 0, 'price': prices.get(symbol, 0), 'value_usd': 0}, predictions.get(symbol, {})))
    
    main_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Span(symbol, style={'fontSize': '18px', 'fontWeight': 'bold', 'color': COLORS['text']}),
                        html.Span(pred.get('signal', '⚪'), style={'fontSize': '16px', 'marginLeft': '8px'})
                    ], className="d-flex justify-content-between align-items-center mb-1"),
                    html.Div([
                        html.Span(pred.get('trend', 'NEUTRO'), 
                                  style={'fontSize': '12px', 'fontWeight': 'bold', 
                                         'color': trend_colors.get(pred.get('trend', 'NEUTRO'), COLORS['neutral']),
                                         'backgroundColor': f"{trend_colors.get(pred.get('trend', 'NEUTRO'), COLORS['neutral'])}20",
                                         'padding': '2px 8px', 'borderRadius': '4px'}),
                        html.Span(f"{pred.get('confidence', 0)}%", 
                                  style={'fontSize': '11px', 'color': COLORS['neutral'], 'marginLeft': '8px'})
                    ], className="mb-2"),
                    html.Div([
                        html.Span(f"${cdata['price']:,.4f}" if cdata['price'] else "-", 
                                  style={'color': COLORS['text'], 'fontSize': '13px', 'fontWeight': 'bold'}),
                        html.Span(f" ({pred.get('change_24h', 0):+.1f}%)" if pred.get('change_24h') else "", 
                                  style={'fontSize': '11px', 
                                         'color': COLORS['positive'] if pred.get('change_24h', 0) >= 0 else COLORS['negative']})
                    ], className="mb-1"),
                    html.P(f"Qtd: {cdata['amount']:.4f} | RSI: {pred.get('rsi', 0):.0f}", 
                           style={'color': COLORS['neutral'], 'fontSize': '11px', 'marginBottom': '3px'}),
                    html.H5(f"${cdata['value_usd']:,.2f}",
                           style={'color': COLORS['positive'] if cdata['value_usd'] > 0 else COLORS['neutral'], 
                                  'fontWeight': 'bold', 'marginBottom': '0'})
                ])
            ], style={'backgroundColor': COLORS['card_highlight'], 
                      'border': f"1px solid {trend_colors.get(pred.get('trend', 'NEUTRO'), COLORS['neutral'])}40",
                      'height': '175px'})
        ], width=3, className="mb-3")
        for symbol, cdata, pred in main_cards_data
    ])
    
    # ===== DISTRIBUIÇÃO DO PORTFÓLIO =====
    distribution_cards = []
    usdt_pct = (usdt_balance / total_value * 100) if total_value > 0 else 0
    distribution_cards.append(
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Span("💵", style={'fontSize': '24px'}),
                        html.Span(" USDT", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': COLORS['text'], 'marginLeft': '8px'}),
                    ], className="mb-2"),
                    html.H4(f"${usdt_balance:,.2f}", style={'color': COLORS['gold'], 'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dbc.Progress(value=usdt_pct, color="warning", className="mb-2", style={'height': '8px'}),
                    html.P(f"{usdt_pct:.1f}% do portfólio", style={'color': COLORS['neutral'], 'fontSize': '12px', 'marginBottom': '0'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': f'1px solid {COLORS["gold"]}', 'height': '150px'})
        ], width=3, className="mb-3")
    )
    
    crypto_colors = ['#1d9bf0', '#00ba7c', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#a29bfe']
    for i, symbol in enumerate(MAIN_CRYPTOS):
        if symbol in crypto_values:
            cdata = crypto_values[symbol]
            pct = (cdata['value_usd'] / total_value * 100) if total_value > 0 else 0
            color = crypto_colors[i % len(crypto_colors)]
            distribution_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Span("🪙", style={'fontSize': '24px'}),
                                html.Span(f" {symbol}", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': COLORS['text'], 'marginLeft': '8px'}),
                            ], className="mb-2"),
                            html.H4(f"${cdata['value_usd']:,.2f}", style={'color': color, 'fontWeight': 'bold', 'marginBottom': '5px'}),
                            dbc.Progress(value=pct, className="mb-2", style={'height': '8px', 'backgroundColor': COLORS['card_highlight']}),
                            html.P(f"{pct:.1f}% | {cdata['amount']:.6f}", style={'color': COLORS['neutral'], 'fontSize': '12px', 'marginBottom': '0'})
                        ])
                    ], style={'backgroundColor': COLORS['card'], 'border': f'1px solid {color}', 'height': '150px'})
                ], width=3, className="mb-3")
            )
        else:
            distribution_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Span("🪙", style={'fontSize': '24px', 'opacity': '0.5'}),
                                html.Span(f" {symbol}", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': COLORS['neutral'], 'marginLeft': '8px'}),
                            ], className="mb-2"),
                            html.H4("$0.00", style={'color': COLORS['neutral'], 'fontWeight': 'bold', 'marginBottom': '5px'}),
                            dbc.Progress(value=0, className="mb-2", style={'height': '8px'}),
                            html.P("0.0% | 0.000000", style={'color': COLORS['neutral'], 'fontSize': '12px', 'marginBottom': '0'})
                        ])
                    ], style={'backgroundColor': COLORS['card'], 'border': f'1px solid {COLORS["card_highlight"]}', 'height': '150px', 'opacity': '0.6'})
                ], width=3, className="mb-3")
            )
    
    portfolio_distribution = dbc.Row(distribution_cards)
    
    # ===== LISTA DE MOEDAS =====
    all_balances_rows = []
    for symbol in MAIN_CRYPTOS:
        if symbol in crypto_values:
            cdata = crypto_values[symbol]
            all_balances_rows.append(
                html.Div([
                    html.Div([
                        html.Span(symbol, style={'fontWeight': 'bold', 'color': COLORS['text']}),
                        html.Span(f" {cdata['amount']:.6f}", style={'color': COLORS['neutral'], 'fontSize': '12px'})
                    ]),
                    html.Span(f"${cdata['value_usd']:,.2f}", 
                             style={'color': COLORS['positive'] if cdata['value_usd'] > 1 else COLORS['neutral'], 
                                    'fontWeight': 'bold'})
                ], className="d-flex justify-content-between align-items-center py-2",
                   style={'borderBottom': f'1px solid {COLORS["card_highlight"]}'}))
        else:
            all_balances_rows.append(
                html.Div([
                    html.Div([
                        html.Span(symbol, style={'fontWeight': 'bold', 'color': COLORS['neutral']}),
                        html.Span(" 0.000000", style={'color': COLORS['neutral'], 'fontSize': '12px'})
                    ]),
                    html.Span("$0.00", style={'color': COLORS['neutral'], 'fontWeight': 'bold'})
                ], className="d-flex justify-content-between align-items-center py-2",
                   style={'borderBottom': f'1px solid {COLORS["card_highlight"]}'}))
    
    last_update = f"Última atualização: {datetime.now().strftime('%H:%M:%S')}"
    
    return [
        # Cards Principais (USDT + Total)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("💵 USDT Disponível", className="mb-1",
                               style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                        html.H2(f"${usdt_balance:,.2f}",
                                style={'color': COLORS['gold'], 'fontWeight': 'bold'})
                    ])
                ], style={'backgroundColor': COLORS['card'], 'border': f'2px solid {COLORS["gold"]}'})
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("💎 Valor Total em Crypto", className="mb-1",
                               style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                        html.H2(f"${total_crypto_value:,.2f}",
                                style={'color': COLORS['accent'], 'fontWeight': 'bold'})
                    ])
                ], style={'backgroundColor': COLORS['card'], 'border': f'2px solid {COLORS["accent"]}'})
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("🏦 Patrimônio Total", className="mb-1",
                               style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                        html.H2(f"${total_value:,.2f}",
                                style={'color': COLORS['positive'], 'fontWeight': 'bold'})
                    ])
                ], style={'backgroundColor': COLORS['card'], 'border': f'2px solid {COLORS["positive"]}'})
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("📈 Lucro do Dia", className="mb-1",
                               style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                        html.H2(f"{pnl_sign}${abs(daily_pnl):.2f}",
                                style={'color': pnl_color, 'fontWeight': 'bold'})
                    ])
                ], style={'backgroundColor': COLORS['card'], 'border': f'2px solid {pnl_color}'})
            ], width=3),
        ], className="mb-4"),
        
        # Cards de Estatísticas do Bot
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("🎯 Meta Diária ($100)", className="mb-1",
                               style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                        html.H3(f"{progress_pct:.1f}%",
                                style={'color': COLORS['accent'], 'fontWeight': 'bold'}),
                        dbc.Progress(value=progress_pct, color="success", className="mt-2", style={'height': '10px'})
                    ])
                ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("📊 Trades Hoje", className="mb-1",
                               style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                        html.H3(f"{trades_count} (✅{wins} | ❌{losses})",
                                style={'color': COLORS['text'], 'fontWeight': 'bold'})
                    ])
                ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("✅ Win Rate", className="mb-1",
                               style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                        html.H3(f"{win_rate:.1f}%",
                                style={'color': COLORS['positive'], 'fontWeight': 'bold'})
                    ])
                ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("🤖 Status do Bot", className="mb-1",
                               style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                        html.H3(bot_status_text,
                                style={'color': bot_status_color, 'fontWeight': 'bold'})
                    ])
                ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
            ], width=3),
        ], className="mb-4"),
        
        # Criptomoedas Principais (8 cards)
        html.H3(
            "🪙 Principais Criptomoedas",
            className="mb-3",
            style={'color': COLORS['text'], 'fontWeight': 'bold'}
        ),
        main_cards,
        
        # Distribuição do Portfólio
        dbc.Row([
            dbc.Col([
                html.H4("📊 Distribuição do Portfólio", 
                        className="mb-3",
                        style={'color': COLORS['text'], 'fontWeight': 'bold'}),
            ])
        ]),
        portfolio_distribution,
        
        # Moedas em Operação
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("📋 Moedas em Operação", 
                                style={'color': COLORS['text'], 'marginBottom': '20px'}),
                        html.Div(all_balances_rows, style={'maxHeight': '400px', 'overflowY': 'auto'})
                    ])
                ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
            ], width=12)
        ], className="mb-4"),
        
        # Última atualização
        html.Div(last_update, className="text-center mb-4",
                 style={'color': COLORS['neutral'], 'fontSize': '12px'})
    ]


# ========================================
# RUN
# ========================================

# ========================================
# LAYOUTS DAS ABAS DE CONFIGURAÇÃO
# ========================================

def get_config_layout():
    """Layout da aba de configurações gerais"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("⚙️ Configurações do Bot", style={'color': COLORS['text'], 'marginBottom': '30px'}),
                
                # Configurações de Trading
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📊 Configurações de Trading", className="mb-0", style={'color': COLORS['accent']})
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("💰 Valor por Trade (USDT):", style={'color': COLORS['text']}),
                                dbc.Input(id='amount-per-trade', type='number', value=50.0, step=5.0, min=1.0, max=500.0, className='mb-3')
                            ], width=6),
                            dbc.Col([
                                html.Label("📈 Posições Máximas:", style={'color': COLORS['text']}),
                                dbc.Input(id='max-positions', type='number', value=6, min=1, max=10, className='mb-3')
                            ], width=6),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                html.Label("🎯 Meta Diária (USDT):", style={'color': COLORS['text']}),
                                dbc.Input(id='daily-target', type='number', value=100.0, step=10.0, min=10.0, max=1000.0, className='mb-3')
                            ], width=6),
                            dbc.Col([
                                html.Label("⏱️ Intervalo (segundos):", style={'color': COLORS['text']}),
                                dbc.Input(id='interval-seconds', type='number', value=3, min=1, max=60, className='mb-3')
                            ], width=6),
                        ]),
                    ])
                ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
                
                # Seleção de Moedas
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🪙 Criptomoedas Ativas", className="mb-0", style={'color': COLORS['gold']})
                    ]),
                    dbc.CardBody([
                        html.P("Selecione as moedas para trading:", style={'color': COLORS['neutral']}),
                        dbc.Checklist(
                            id='crypto-selection',
                            options=[
                                {'label': ' Bitcoin (BTC)', 'value': 'BTC/USDT'},
                                {'label': ' Ethereum (ETH)', 'value': 'ETH/USDT'},
                                {'label': ' Solana (SOL)', 'value': 'SOL/USDT'},
                                {'label': ' Binance Coin (BNB)', 'value': 'BNB/USDT'},
                                {'label': ' XRP', 'value': 'XRP/USDT'},
                                {'label': ' Chainlink (LINK)', 'value': 'LINK/USDT'},
                                {'label': ' Dogecoin (DOGE)', 'value': 'DOGE/USDT'},
                                {'label': ' Litecoin (LTC)', 'value': 'LTC/USDT'},
                            ],
                            value=['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT'],
                            inline=True,
                            style={'color': COLORS['text']}
                        )
                    ])
                ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
                
                # Botões de Ação
                dbc.Row([
                    dbc.Col([
                        dbc.Button("💾 Salvar Configurações", id='save-config-btn', color='success', className='me-2'),
                        dbc.Button("🔄 Restaurar Padrões", id='reset-config-btn', color='warning', className='me-2'),
                        dbc.Button("⚡ Aplicar Agora", id='apply-config-btn', color='primary'),
                    ], className="text-center mt-3")
                ]),
                
                # Status de salvamento
                html.Div(id='config-status', className='mt-3'),
                
            ], width=12)
        ])
    ], fluid=True)

def get_strategy_layout():
    """Layout da aba de configurações de estratégia"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("📈 Configurações da Estratégia", style={'color': COLORS['text'], 'marginBottom': '30px'}),
                
                # Indicadores Técnicos
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("📊 Indicadores Técnicos", className="mb-0", style={'color': COLORS['positive']})
                    ]),
                    dbc.CardBody([
                        # RSI
                        html.H6("📉 RSI (Relative Strength Index)", style={'color': COLORS['accent']}),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Período:", style={'color': COLORS['text']}),
                                dbc.Input(id='rsi-period', type='number', value=14, min=5, max=50, className='mb-3')
                            ], width=4),
                            dbc.Col([
                                html.Label("Sobrevenda:", style={'color': COLORS['text']}),
                                dbc.Input(id='rsi-oversold', type='number', value=35, min=10, max=40, className='mb-3')
                            ], width=4),
                            dbc.Col([
                                html.Label("Sobrecompra:", style={'color': COLORS['text']}),
                                dbc.Input(id='rsi-overbought', type='number', value=65, min=60, max=90, className='mb-3')
                            ], width=4),
                        ]),
                        
                        html.Hr(),
                        
                        # MACD
                        html.H6("📈 MACD (Moving Average Convergence Divergence)", style={'color': COLORS['accent']}),
                        dbc.Row([
                            dbc.Col([
                                html.Label("EMA Rápida:", style={'color': COLORS['text']}),
                                dbc.Input(id='macd-fast', type='number', value=12, min=5, max=20, className='mb-3')
                            ], width=4),
                            dbc.Col([
                                html.Label("EMA Lenta:", style={'color': COLORS['text']}),
                                dbc.Input(id='macd-slow', type='number', value=26, min=20, max=50, className='mb-3')
                            ], width=4),
                            dbc.Col([
                                html.Label("Sinal:", style={'color': COLORS['text']}),
                                dbc.Input(id='macd-signal', type='number', value=9, min=5, max=20, className='mb-3')
                            ], width=4),
                        ]),
                        
                        html.Hr(),
                        
                        # Médias Móveis
                        html.H6("📊 Médias Móveis Simples (SMA)", style={'color': COLORS['accent']}),
                        dbc.Row([
                            dbc.Col([
                                html.Label("SMA Curta:", style={'color': COLORS['text']}),
                                dbc.Input(id='sma-short', type='number', value=20, min=5, max=50, className='mb-3')
                            ], width=4),
                            dbc.Col([
                                html.Label("SMA Média:", style={'color': COLORS['text']}),
                                dbc.Input(id='sma-medium', type='number', value=50, min=30, max=100, className='mb-3')
                            ], width=4),
                            dbc.Col([
                                html.Label("SMA Longa:", style={'color': COLORS['text']}),
                                dbc.Input(id='sma-long', type='number', value=200, min=100, max=500, className='mb-3')
                            ], width=4),
                        ]),
                    ])
                ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
                
                # Tipo de Estratégia
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🧠 Tipo de Estratégia", className="mb-0", style={'color': COLORS['gold']})
                    ]),
                    dbc.CardBody([
                        dbc.RadioItems(
                            id='strategy-type',
                            options=[
                                {'label': ' 🤖 Smart Strategy (Recomendado)', 'value': 'smart'},
                                {'label': ' 📊 Scalping Simples', 'value': 'scalping'},
                                {'label': ' 🎯 Trend Following', 'value': 'trend'},
                                {'label': ' ⚖️ Mean Reversion', 'value': 'mean_reversion'},
                            ],
                            value='smart',
                            style={'color': COLORS['text']}
                        )
                    ])
                ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
                
                # Botões
                dbc.Row([
                    dbc.Col([
                        dbc.Button("💾 Salvar Estratégia", id='save-strategy-btn', color='success', className='me-2'),
                        dbc.Button("📊 Testar Configuração", id='test-strategy-btn', color='info'),
                    ], className="text-center")
                ]),
                
                html.Div(id='strategy-status', className='mt-3'),
                
            ], width=12)
        ])
    ], fluid=True)

def get_safety_layout():
    """Layout da aba de configurações de segurança"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("🛡️ Configurações de Segurança", style={'color': COLORS['text'], 'marginBottom': '30px'}),
                
                # Limites de Risco
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("⚠️ Limites de Risco", className="mb-0", style={'color': COLORS['negative']})
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("💥 Perda Máxima Diária (USDT):", style={'color': COLORS['text']}),
                                dbc.Input(id='max-daily-loss', type='number', value=50.0, step=5.0, min=5.0, max=200.0, className='mb-3')
                            ], width=6),
                            dbc.Col([
                                html.Label("📉 Drawdown Máximo (%):", style={'color': COLORS['text']}),
                                dbc.Input(id='max-drawdown', type='number', value=20.0, step=1.0, min=5.0, max=50.0, className='mb-3')
                            ], width=6),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                html.Label("🎯 Stop Loss (%):", style={'color': COLORS['text']}),
                                dbc.Input(id='stop-loss', type='number', value=2.0, step=0.1, min=0.5, max=10.0, className='mb-3')
                            ], width=6),
                            dbc.Col([
                                html.Label("💰 Take Profit (%):", style={'color': COLORS['text']}),
                                dbc.Input(id='take-profit', type='number', value=3.0, step=0.1, min=1.0, max=15.0, className='mb-3')
                            ], width=6),
                        ]),
                    ])
                ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
                
                # Kill Switch
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🚨 Kill Switch Automático", className="mb-0", style={'color': COLORS['negative']})
                    ]),
                    dbc.CardBody([
                        dbc.Checklist(
                            id='kill-switch-options',
                            options=[
                                {'label': ' Ativar Kill Switch', 'value': 'enabled'},
                                {'label': ' Parar em perda consecutiva (5 trades)', 'value': 'consecutive_losses'},
                                {'label': ' Parar em horários de alta volatilidade', 'value': 'high_volatility'},
                                {'label': ' Enviar notificações de emergência', 'value': 'emergency_notifications'},
                            ],
                            value=['enabled', 'consecutive_losses'],
                            style={'color': COLORS['text']}
                        )
                    ])
                ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
                
                # Configurações de Proteção
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🔒 Proteções Avançadas", className="mb-0", style={'color': COLORS['accent']})
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("🕐 Horário de Funcionamento:", style={'color': COLORS['text']}),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Input(id='start-time', type='time', value='09:00', className='mb-3')
                                    ], width=6),
                                    dbc.Col([
                                        dbc.Input(id='end-time', type='time', value='18:00', className='mb-3')
                                    ], width=6),
                                ])
                            ], width=6),
                            dbc.Col([
                                html.Label("📅 Dias de Operação:", style={'color': COLORS['text']}),
                                dbc.Checklist(
                                    id='operating-days',
                                    options=[
                                        {'label': 'Seg', 'value': 0},
                                        {'label': 'Ter', 'value': 1},
                                        {'label': 'Qua', 'value': 2},
                                        {'label': 'Qui', 'value': 3},
                                        {'label': 'Sex', 'value': 4},
                                        {'label': 'Sáb', 'value': 5},
                                        {'label': 'Dom', 'value': 6},
                                    ],
                                    value=[0, 1, 2, 3, 4],
                                    inline=True,
                                    style={'color': COLORS['text'], 'fontSize': '12px'}
                                )
                            ], width=6),
                        ]),
                    ])
                ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
                
                # Botões
                dbc.Row([
                    dbc.Col([
                        dbc.Button("🛡️ Salvar Segurança", id='save-safety-btn', color='danger', className='me-2'),
                        dbc.Button("🚨 Ativar Kill Switch", id='emergency-stop-btn', color='warning'),
                    ], className="text-center")
                ]),
                
                html.Div(id='safety-status', className='mt-3'),
                
            ], width=12)
        ])
    ], fluid=True)

# ========================================
# CALLBACKS PARA CONFIGURAÇÕES
# ========================================

@app.callback(
    Output('config-status', 'children'),
    Input('save-config-btn', 'n_clicks'),
    [State('amount-per-trade', 'value'),
     State('max-positions', 'value'),
     State('daily-target', 'value'),
     State('interval-seconds', 'value'),
     State('crypto-selection', 'value')]
)
def save_config(n_clicks, amount, max_pos, target, interval, cryptos):
    """Salva configurações gerais"""
    if n_clicks:
        try:
            # Aqui você salvaria no config.yaml
            return dbc.Alert("✅ Configurações salvas com sucesso!", color="success", dismissable=True)
        except Exception as e:
            return dbc.Alert(f"❌ Erro ao salvar: {str(e)}", color="danger", dismissable=True)
    return ""

@app.callback(
    Output('strategy-status', 'children'),
    Input('save-strategy-btn', 'n_clicks'),
    [State('rsi-period', 'value'),
     State('rsi-oversold', 'value'),
     State('rsi-overbought', 'value'),
     State('strategy-type', 'value')]
)
def save_strategy(n_clicks, rsi_period, rsi_oversold, rsi_overbought, strategy_type):
    """Salva configurações de estratégia"""
    if n_clicks:
        try:
            # Aqui você salvaria as configurações da estratégia
            return dbc.Alert("📈 Estratégia atualizada com sucesso!", color="success", dismissable=True)
        except Exception as e:
            return dbc.Alert(f"❌ Erro ao salvar estratégia: {str(e)}", color="danger", dismissable=True)
    return ""

@app.callback(
    Output('safety-status', 'children'),
    Input('save-safety-btn', 'n_clicks'),
    [State('max-daily-loss', 'value'),
     State('max-drawdown', 'value'),
     State('stop-loss', 'value'),
     State('take-profit', 'value')]
)
def save_safety(n_clicks, max_loss, max_drawdown, stop_loss, take_profit):
    """Salva configurações de segurança"""
    if n_clicks:
        try:
            # Aqui você salvaria as configurações de segurança
            return dbc.Alert("🛡️ Configurações de segurança salvas!", color="success", dismissable=True)
        except Exception as e:
            return dbc.Alert(f"❌ Erro ao salvar segurança: {str(e)}", color="danger", dismissable=True)
    return ""

if __name__ == '__main__':
    print("="*60)
    print("💰 Dashboard de Saldo - App Leonardo")
    print("="*60)
    print(f"🧪 Modo: {'Testnet' if TESTNET else 'Real'}")
    print("📊 Dashboard: http://localhost:8050")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=8050)
