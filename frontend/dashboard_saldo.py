"""
🎨 Dashboard de Saldo - App Leonardo
Mostra saldo em USDT e todas as criptomoedas em tempo real
"""
import dash
from dash import dcc, html, Input, Output
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
    """Busca todos os saldos"""
    try:
        exchange = get_exchange()
        if not exchange:
            print("❌ Exchange não disponível para buscar saldos")
            return None
        balance = exchange.fetch_balance()
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
        tickers = exchange.fetch_tickers([f"{s}/USDT" for s in symbols if s != 'USDT'])
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
                "💰 App Leonardo - Saldo em Criptomoedas",
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
    ], className="mt-4 mb-4"),
    
    # Cards Principais (USDT + Total)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("💵 USDT Disponível", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H2(id='usdt-balance', children="$0.00",
                            style={'color': COLORS['gold'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': f'2px solid {COLORS["gold"]}'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("💎 Valor Total em Crypto", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H2(id='crypto-value', children="$0.00",
                            style={'color': COLORS['accent'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': f'2px solid {COLORS["accent"]}'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("🏦 Patrimônio Total", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H2(id='total-value', children="$0.00",
                            style={'color': COLORS['positive'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': f'2px solid {COLORS["positive"]}'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("📈 Lucro do Dia", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H2(id='daily-pnl', children="$0.00",
                            style={'color': COLORS['positive'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': f'2px solid {COLORS["positive"]}'}, id='daily-pnl-card')
        ], width=3),
    ], className="mb-4"),
    
    # Cards de Estatísticas do Bot
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("🎯 Meta Diária ($100)", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H3(id='daily-progress', children="0%",
                            style={'color': COLORS['accent'], 'fontWeight': 'bold'}),
                    dbc.Progress(id='progress-bar', value=0, color="success", className="mt-2", style={'height': '10px'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("📊 Trades Hoje", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H3(id='trades-count', children="0",
                            style={'color': COLORS['text'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("✅ Win Rate", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H3(id='win-rate', children="0%",
                            style={'color': COLORS['positive'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("🤖 Status do Bot", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H3(id='bot-status', children="⚪ Offline",
                            style={'color': COLORS['neutral'], 'fontWeight': 'bold'})
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
    
    html.Div(id='main-crypto-cards', className="mb-4"),
    
    # Distribuição do Portfólio (Cards)
    dbc.Row([
        dbc.Col([
            html.H4("📊 Distribuição do Portfólio", 
                    className="mb-3",
                    style={'color': COLORS['text'], 'fontWeight': 'bold'}),
        ])
    ]),
    
    html.Div(id='portfolio-distribution', className="mb-4"),
    
    # Moedas em Operação
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📋 Moedas em Operação", 
                            style={'color': COLORS['text'], 'marginBottom': '20px'}),
                    html.Div(id='all-balances-list', style={'maxHeight': '400px', 'overflowY': 'auto'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=12)
    ], className="mb-4"),
    
    # Última atualização
    html.Div(id='last-update', className="text-center mb-4",
             style={'color': COLORS['neutral'], 'fontSize': '12px'})
    
], fluid=True, style={'backgroundColor': COLORS['background'], 'minHeight': '100vh', 'padding': '20px'})


# ========================================
# CALLBACKS
# ========================================

@app.callback(
    [
        Output('usdt-balance', 'children'),
        Output('crypto-value', 'children'),
        Output('total-value', 'children'),
        Output('daily-pnl', 'children'),
        Output('daily-pnl', 'style'),
        Output('daily-progress', 'children'),
        Output('progress-bar', 'value'),
        Output('trades-count', 'children'),
        Output('win-rate', 'children'),
        Output('bot-status', 'children'),
        Output('bot-status', 'style'),
        Output('stats-date', 'children'),
        Output('main-crypto-cards', 'children'),
        Output('portfolio-distribution', 'children'),
        Output('all-balances-list', 'children'),
        Output('last-update', 'children')
    ],
    [Input('interval-update', 'n_intervals')]
)
def update_dashboard(n):
    """Atualiza todo o dashboard"""
    print(f"🔄 Callback executado #{n}")
    
    # Busca estatísticas do bot
    bot_stats = get_bot_stats()
    print(f"📊 Bot stats: {bot_stats is not None}")
    
    # Valores padrão para estatísticas do bot
    daily_pnl = 0.0
    total_pnl = 0.0
    trades_count = 0
    wins = 0
    losses = 0
    bot_running = False
    stats_date = datetime.now().strftime('%Y-%m-%d')
    
    if bot_stats:
        daily_pnl = bot_stats.get('daily_pnl', 0.0)
        total_pnl = bot_stats.get('total_pnl', 0.0)
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
    
    # Estilo do PnL (verde se positivo, vermelho se negativo)
    pnl_color = COLORS['positive'] if daily_pnl >= 0 else COLORS['negative']
    pnl_style = {'color': pnl_color, 'fontWeight': 'bold'}
    
    # Status do bot
    if bot_running:
        bot_status = "🟢 Operando"
        bot_status_style = {'color': COLORS['positive'], 'fontWeight': 'bold'}
    else:
        bot_status = "⚪ Parado"
        bot_status_style = {'color': COLORS['neutral'], 'fontWeight': 'bold'}
    
    # Busca saldos
    balance_data = get_balances()
    
    if not balance_data:
        return (
            "Erro", "Erro", "Erro",  # saldos
            "$0.00", pnl_style,  # daily pnl
            "0%", 0,  # progresso
            "0", "0%",  # trades, win rate
            bot_status, bot_status_style,  # status
            f"📅 Data: {stats_date}",  # data
            [], [],  # cards principais, distribuição
            [],  # lista
            "Erro ao conectar"
        )
    
    # Extrai saldos livres
    free_balances = balance_data.get('free', {})
    
    # USDT
    usdt_balance = float(free_balances.get('USDT', 0))
    
    # Filtra moedas com saldo > 0
    cryptos_with_balance = {
        k: float(v) for k, v in free_balances.items() 
        if float(v) > 0 and k != 'USDT'
    }
    
    # Busca preços
    prices = get_prices(list(cryptos_with_balance.keys())[:50])  # Limite de 50
    
    # Busca previsões para as 8 cryptos principais
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
    
    # Ordena por valor USD
    sorted_cryptos = sorted(
        crypto_values.items(), 
        key=lambda x: x[1]['value_usd'], 
        reverse=True
    )
    
    # Total em crypto
    total_crypto_value = sum(v['value_usd'] for v in crypto_values.values())
    
    # Total geral
    total_value = usdt_balance + total_crypto_value
    
    # ===== CARDS PRINCIPAIS (8 cryptos) com previsões =====
    main_cards_data = []
    for symbol in MAIN_CRYPTOS:
        if symbol in crypto_values:
            main_cards_data.append((symbol, crypto_values[symbol], predictions.get(symbol, {})))
        else:
            main_cards_data.append((symbol, {'amount': 0, 'price': prices.get(symbol, 0), 'value_usd': 0}, predictions.get(symbol, {})))
    
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
    
    main_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    # Header com símbolo e emoji de tendência
                    html.Div([
                        html.Span(symbol, style={'fontSize': '18px', 'fontWeight': 'bold', 'color': COLORS['text']}),
                        html.Span(pred.get('signal', '⚪'), style={'fontSize': '16px', 'marginLeft': '8px'})
                    ], className="d-flex justify-content-between align-items-center mb-1"),
                    
                    # Tendência e confiança
                    html.Div([
                        html.Span(pred.get('trend', 'NEUTRO'), 
                                  style={'fontSize': '12px', 'fontWeight': 'bold', 
                                         'color': trend_colors.get(pred.get('trend', 'NEUTRO'), COLORS['neutral']),
                                         'backgroundColor': f"{trend_colors.get(pred.get('trend', 'NEUTRO'), COLORS['neutral'])}20",
                                         'padding': '2px 8px', 'borderRadius': '4px'}),
                        html.Span(f"{pred.get('confidence', 0)}%", 
                                  style={'fontSize': '11px', 'color': COLORS['neutral'], 'marginLeft': '8px'})
                    ], className="mb-2"),
                    
                    # Preço e variação 24h
                    html.Div([
                        html.Span(f"${data['price']:,.4f}" if data['price'] else "-", 
                                  style={'color': COLORS['text'], 'fontSize': '13px', 'fontWeight': 'bold'}),
                        html.Span(f" ({pred.get('change_24h', 0):+.1f}%)" if pred.get('change_24h') else "", 
                                  style={'fontSize': '11px', 
                                         'color': COLORS['positive'] if pred.get('change_24h', 0) >= 0 else COLORS['negative']})
                    ], className="mb-1"),
                    
                    # Quantidade e RSI
                    html.P(f"Qtd: {data['amount']:.4f} | RSI: {pred.get('rsi', 0):.0f}", 
                           style={'color': COLORS['neutral'], 'fontSize': '11px', 'marginBottom': '3px'}),
                    
                    # Valor em USD
                    html.H5(f"${data['value_usd']:,.2f}",
                           style={'color': COLORS['positive'] if data['value_usd'] > 0 else COLORS['neutral'], 
                                  'fontWeight': 'bold', 'marginBottom': '0'})
                ])
            ], style={'backgroundColor': COLORS['card_highlight'], 
                      'border': f"1px solid {trend_colors.get(pred.get('trend', 'NEUTRO'), COLORS['neutral'])}40",
                      'height': '175px'})
        ], width=3, className="mb-3")
        for symbol, data, pred in main_cards_data
    ])
    
    # ===== CARDS DE DISTRIBUIÇÃO DO PORTFÓLIO =====
    # Calcula porcentagem de cada ativo
    distribution_cards = []
    
    # USDT primeiro
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
    
    # Cryptos em operação
    crypto_colors = ['#1d9bf0', '#00ba7c', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#a29bfe']
    for i, symbol in enumerate(MAIN_CRYPTOS):
        if symbol in crypto_values:
            data = crypto_values[symbol]
            pct = (data['value_usd'] / total_value * 100) if total_value > 0 else 0
            color = crypto_colors[i % len(crypto_colors)]
            
            distribution_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Span("🪙", style={'fontSize': '24px'}),
                                html.Span(f" {symbol}", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': COLORS['text'], 'marginLeft': '8px'}),
                            ], className="mb-2"),
                            html.H4(f"${data['value_usd']:,.2f}", style={'color': color, 'fontWeight': 'bold', 'marginBottom': '5px'}),
                            dbc.Progress(value=pct, className="mb-2", style={'height': '8px', 'backgroundColor': COLORS['card_highlight']}),
                            html.P(f"{pct:.1f}% | {data['amount']:.6f}", style={'color': COLORS['neutral'], 'fontSize': '12px', 'marginBottom': '0'})
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
    
    # ===== LISTA DE TODAS AS MOEDAS =====
    # Mostra apenas as moedas que estão sendo operadas pelo bot
    all_balances_rows = []
    for symbol in MAIN_CRYPTOS:
        if symbol in crypto_values:
            data = crypto_values[symbol]
            all_balances_rows.append(
                html.Div([
                    html.Div([
                        html.Span(symbol, style={'fontWeight': 'bold', 'color': COLORS['text']}),
                        html.Span(f" {data['amount']:.6f}", style={'color': COLORS['neutral'], 'fontSize': '12px'})
                    ]),
                    html.Span(f"${data['value_usd']:,.2f}", 
                             style={'color': COLORS['positive'] if data['value_usd'] > 1 else COLORS['neutral'], 
                                    'fontWeight': 'bold'})
                ], className="d-flex justify-content-between align-items-center py-2",
                   style={'borderBottom': f'1px solid {COLORS["card_highlight"]}'})
            )
        else:
            # Moeda sem saldo
            all_balances_rows.append(
                html.Div([
                    html.Div([
                        html.Span(symbol, style={'fontWeight': 'bold', 'color': COLORS['neutral']}),
                        html.Span(" 0.000000", style={'color': COLORS['neutral'], 'fontSize': '12px'})
                    ]),
                    html.Span("$0.00", 
                             style={'color': COLORS['neutral'], 'fontWeight': 'bold'})
                ], className="d-flex justify-content-between align-items-center py-2",
                   style={'borderBottom': f'1px solid {COLORS["card_highlight"]}'})
            )
    
    # Última atualização
    last_update = f"Última atualização: {datetime.now().strftime('%H:%M:%S')}"
    
    # Formata PnL diário
    pnl_sign = "+" if daily_pnl >= 0 else ""
    daily_pnl_text = f"{pnl_sign}${daily_pnl:.2f}"
    
    # Formata data
    date_display = f"📅 Data: {stats_date}"
    
    print(f"✅ Dashboard atualizado: USDT=${usdt_balance:,.2f}, Total=${total_value:,.2f}")
    
    return (
        f"${usdt_balance:,.2f}",
        f"${total_crypto_value:,.2f}",
        f"${total_value:,.2f}",
        daily_pnl_text,
        pnl_style,
        f"{progress_pct:.1f}%",
        progress_pct,
        f"{trades_count} (✅{wins} | ❌{losses})",
        f"{win_rate:.1f}%",
        bot_status,
        bot_status_style,
        date_display,
        main_cards,
        portfolio_distribution,
        html.Div(all_balances_rows),
        last_update
    )


# ========================================
# RUN
# ========================================

if __name__ == '__main__':
    print("="*60)
    print("💰 Dashboard de Saldo - App Leonardo")
    print("="*60)
    print(f"🧪 Modo: {'Testnet' if TESTNET else 'Real'}")
    print("📊 Dashboard: http://localhost:8050")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=8050)
