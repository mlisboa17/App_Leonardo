"""
📊 Dashboard Simples - App Leonardo
Dashboard que funciona SEM backend, lendo dados diretamente dos arquivos do bot
"""
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import json
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path

# ========================================
# CONFIGURAÇÕES
# ========================================

# Cores tema escuro
COLORS = {
    'background': '#0f1419',
    'card': '#1a1f29',
    'text': '#e7e9ea',
    'positive': '#00ba7c',
    'negative': '#f91880',
    'neutral': '#8b98a5',
    'accent': '#1d9bf0'
}

# Paths dos arquivos
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'

# ========================================
# FUNÇÕES DE LEITURA DE DADOS
# ========================================

def load_bot_stats():
    """Carrega estatísticas do bot dos arquivos JSON"""
    try:
        # Arquivo de estatísticas diárias
        daily_stats_file = DATA_DIR / 'daily_stats.json'
        if daily_stats_file.exists():
            with open(daily_stats_file, 'r') as f:
                stats = json.load(f)
        else:
            stats = {
                'balance': 14.12,
                'total_trades': 503,
                'winning_trades': 349,
                'losing_trades': 104,
                'daily_pnl': 4.20,
                'total_pnl': 4.20,
                'open_positions': 0
            }
        
        return stats
    except Exception as e:
        print(f"❌ Erro ao carregar stats: {e}")
        return {
            'balance': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'daily_pnl': 0,
            'total_pnl': 0,
            'open_positions': 0
        }

def load_crypto_profiles():
    """Carrega perfis das criptomoedas"""
    try:
        profiles_file = DATA_DIR / 'crypto_profiles.json'
        if profiles_file.exists():
            with open(profiles_file, 'r') as f:
                profiles = json.load(f)
        else:
            profiles = {}
        
        # Símbolos principais
        symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'LINK', 'DOGE', 'LTC']
        
        crypto_data = []
        for symbol in symbols:
            profile = profiles.get(f'{symbol}/USDT', {})
            
            crypto_data.append({
                'symbol': symbol,
                'volume_24h': profile.get('volume_24h', 1000000),
                'volatility': profile.get('volatility', 2.5),
                'trend_strength': profile.get('trend_strength', 0.5),
                'rsi_oversold': profile.get('rsi_oversold', 35),
                'rsi_overbought': profile.get('rsi_overbought', 65)
            })
        
        return crypto_data
    except Exception as e:
        print(f"❌ Erro ao carregar perfis: {e}")
        return []

def load_recent_trades():
    """Carrega histórico recente de trades"""
    try:
        history_files = list((DATA_DIR / 'history').glob('complete_history_*.json'))
        
        if not history_files:
            return []
        
        # Pega o arquivo mais recente
        latest_file = max(history_files, key=os.path.getctime)
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        trades = data.get('trades', [])
        
        # Pega os últimos 20 trades
        recent_trades = trades[-20:] if len(trades) > 20 else trades
        
        return recent_trades
    except Exception as e:
        print(f"❌ Erro ao carregar trades: {e}")
        return []

# ========================================
# APP DASH
# ========================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

app.title = "App Leonardo - Dashboard Simples"

# ========================================
# LAYOUT
# ========================================

app.layout = dbc.Container([
    dcc.Interval(id='interval-update', interval=10000, n_intervals=0),  # Atualiza a cada 10s
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1(
                "🚀 App Leonardo Trading Bot - Dashboard Simples",
                className="mb-3",
                style={'color': COLORS['text'], 'fontWeight': 'bold'}
            ),
            html.P(
                "Dashboard funcionando SEM backend - Lendo dados diretamente dos arquivos",
                style={'color': COLORS['neutral'], 'fontSize': '16px'}
            )
        ])
    ], className="mt-4 mb-4"),
    
    # Cards principais de estatísticas
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("💰", className="mb-1"),
                    html.H4(id='balance', children="$0.00", 
                            style={'color': COLORS['text'], 'fontWeight': 'bold'}),
                    html.P("Saldo USDT", style={'color': COLORS['neutral'], 'margin': '0'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none', 'textAlign': 'center'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("📊", className="mb-1"),
                    html.H4(id='total-trades', children="0",
                            style={'color': COLORS['accent'], 'fontWeight': 'bold'}),
                    html.P("Total Trades", style={'color': COLORS['neutral'], 'margin': '0'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none', 'textAlign': 'center'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("🎯", className="mb-1"),
                    html.H4(id='win-rate', children="0%",
                            style={'color': COLORS['positive'], 'fontWeight': 'bold'}),
                    html.P("Win Rate", style={'color': COLORS['neutral'], 'margin': '0'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none', 'textAlign': 'center'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("💎", className="mb-1"),
                    html.H4(id='daily-pnl', children="$0.00",
                            style={'fontWeight': 'bold'}),
                    html.P("PnL Diário", style={'color': COLORS['neutral'], 'margin': '0'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none', 'textAlign': 'center'})
        ], width=3)
    ], className="mb-4"),
    
    # Gráfico de PnL e Estatísticas dos Símbolos
    dbc.Row([
        dbc.Col([
            html.H3("📈 Estatísticas por Símbolo", 
                    style={'color': COLORS['text'], 'fontWeight': 'bold'}),
            dcc.Graph(id='crypto-stats-chart')
        ], width=8),
        
        dbc.Col([
            html.H3("🏆 Top Performers", 
                    style={'color': COLORS['text'], 'fontWeight': 'bold'}),
            html.Div(id='top-performers')
        ], width=4)
    ], className="mb-4"),
    
    # Trades Recentes
    dbc.Row([
        dbc.Col([
            html.H3("📋 Trades Recentes", 
                    style={'color': COLORS['text'], 'fontWeight': 'bold'}),
            html.Div(id='recent-trades-table')
        ])
    ], className="mb-4"),
    
    # Status do Sistema
    dbc.Row([
        dbc.Col([
            html.H3("⚙️ Status do Sistema",
                    style={'color': COLORS['text'], 'fontWeight': 'bold'}),
            html.Div(id='system-status')
        ])
    ])
    
], fluid=True, style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})

# ========================================
# CALLBACKS
# ========================================

@app.callback(
    [
        Output('balance', 'children'),
        Output('total-trades', 'children'),
        Output('win-rate', 'children'),
        Output('daily-pnl', 'children'),
        Output('daily-pnl', 'style'),
        Output('crypto-stats-chart', 'figure'),
        Output('top-performers', 'children'),
        Output('recent-trades-table', 'children'),
        Output('system-status', 'children')
    ],
    [Input('interval-update', 'n_intervals')]
)
def update_dashboard(n):
    """Atualiza todo o dashboard"""
    
    # Carrega dados
    stats = load_bot_stats()
    crypto_profiles = load_crypto_profiles()
    recent_trades = load_recent_trades()
    
    # Cards principais
    balance = f"${stats['balance']:,.2f}"
    total_trades = f"{stats['total_trades']:,}"
    
    win_rate = 0
    if stats['total_trades'] > 0:
        win_rate = (stats['winning_trades'] / stats['total_trades']) * 100
    win_rate_text = f"{win_rate:.1f}%"
    
    # PnL diário com cor
    daily_pnl_val = stats['daily_pnl']
    daily_pnl_text = f"${abs(daily_pnl_val):,.2f}"
    daily_pnl_color = COLORS['positive'] if daily_pnl_val >= 0 else COLORS['negative']
    
    if daily_pnl_val >= 0:
        daily_pnl_text = f"+{daily_pnl_text}"
    else:
        daily_pnl_text = f"-{daily_pnl_text}"
    
    daily_pnl_style = {'color': daily_pnl_color, 'fontWeight': 'bold'}
    
    # Gráfico de estatísticas dos símbolos
    if crypto_profiles:
        symbols = [crypto['symbol'] for crypto in crypto_profiles]
        volumes = [crypto['volume_24h'] for crypto in crypto_profiles]
        volatilities = [crypto['volatility'] for crypto in crypto_profiles]
        
        fig = go.Figure()
        
        # Volume (barras)
        fig.add_trace(go.Bar(
            name='Volume 24h',
            x=symbols,
            y=volumes,
            yaxis='y',
            marker_color=COLORS['accent'],
            opacity=0.7
        ))
        
        # Volatilidade (linha)
        fig.add_trace(go.Scatter(
            name='Volatilidade %',
            x=symbols,
            y=volatilities,
            yaxis='y2',
            mode='lines+markers',
            line=dict(color=COLORS['positive'], width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='Volume 24h vs Volatilidade por Símbolo',
            xaxis=dict(title='Símbolos', color=COLORS['text']),
            yaxis=dict(
                title='Volume 24h',
                side='left',
                color=COLORS['accent']
            ),
            yaxis2=dict(
                title='Volatilidade %',
                overlaying='y',
                side='right',
                color=COLORS['positive']
            ),
            paper_bgcolor=COLORS['background'],
            plot_bgcolor=COLORS['card'],
            font=dict(color=COLORS['text']),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
    else:
        fig = go.Figure()
        fig.update_layout(
            title='Aguardando dados...',
            paper_bgcolor=COLORS['background'],
            plot_bgcolor=COLORS['card'],
            font=dict(color=COLORS['text'])
        )
    
    # Top Performers
    if crypto_profiles:
        sorted_cryptos = sorted(crypto_profiles, key=lambda x: x['volume_24h'], reverse=True)
        
        top_cards = []
        for i, crypto in enumerate(sorted_cryptos[:4]):
            color = COLORS['positive'] if i < 2 else COLORS['neutral']
            
            card = dbc.Card([
                dbc.CardBody([
                    html.H4(f"#{i+1} {crypto['symbol']}", 
                            style={'color': color, 'margin': '0'}),
                    html.P(f"Vol: ${crypto['volume_24h']:,.0f}", 
                           style={'color': COLORS['text'], 'fontSize': '12px', 'margin': '0'}),
                    html.P(f"Volat: {crypto['volatility']:.1f}%", 
                           style={'color': COLORS['neutral'], 'fontSize': '12px', 'margin': '0'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none', 'marginBottom': '10px'})
            
            top_cards.append(card)
        
        top_performers = html.Div(top_cards)
    else:
        top_performers = html.P("Aguardando dados...", style={'color': COLORS['neutral']})
    
    # Tabela de trades recentes
    if recent_trades:
        table_rows = []
        
        for trade in recent_trades[-10:]:  # Últimos 10 trades
            pnl = trade.get('pnl', 0)
            pnl_color = COLORS['positive'] if pnl >= 0 else COLORS['negative']
            
            timestamp = trade.get('timestamp', '')
            if isinstance(timestamp, str) and timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = timestamp[:8]
            else:
                time_str = 'N/A'
            
            table_rows.append(
                html.Tr([
                    html.Td(trade.get('symbol', 'N/A'), style={'color': COLORS['text']}),
                    html.Td(trade.get('side', 'N/A'), style={'color': COLORS['accent']}),
                    html.Td(f"${trade.get('entry_price', 0):,.2f}", 
                           style={'color': COLORS['neutral']}),
                    html.Td(f"${trade.get('exit_price', 0):,.2f}", 
                           style={'color': COLORS['neutral']}),
                    html.Td(f"${pnl:,.2f}", 
                           style={'color': pnl_color, 'fontWeight': 'bold'}),
                    html.Td(time_str, style={'color': COLORS['neutral'], 'fontSize': '12px'})
                ])
            )
        
        trades_table = dbc.Table([
            html.Thead(
                html.Tr([
                    html.Th("Símbolo"),
                    html.Th("Lado"),
                    html.Th("Entrada"),
                    html.Th("Saída"),
                    html.Th("PnL"),
                    html.Th("Hora")
                ])
            ),
            html.Tbody(table_rows)
        ], dark=True, striped=True, bordered=True, hover=True)
    else:
        trades_table = html.P("Nenhum trade encontrado nos arquivos", 
                             style={'color': COLORS['neutral']})
    
    # Status do Sistema
    now = datetime.now()
    
    # Verifica se arquivos existem
    daily_stats_exists = (DATA_DIR / 'daily_stats.json').exists()
    profiles_exists = (DATA_DIR / 'crypto_profiles.json').exists()
    history_exists = len(list((DATA_DIR / 'history').glob('*.json'))) > 0 if (DATA_DIR / 'history').exists() else False
    
    status_items = [
        html.P(f"🕒 Última atualização: {now.strftime('%H:%M:%S')}", 
               style={'color': COLORS['text']}),
        html.P(f"📊 Stats diárias: {'✅' if daily_stats_exists else '❌'}", 
               style={'color': COLORS['positive'] if daily_stats_exists else COLORS['negative']}),
        html.P(f"📈 Perfis cripto: {'✅' if profiles_exists else '❌'}", 
               style={'color': COLORS['positive'] if profiles_exists else COLORS['negative']}),
        html.P(f"📋 Histórico: {'✅' if history_exists else '❌'}", 
               style={'color': COLORS['positive'] if history_exists else COLORS['negative']}),
        html.P(f"📁 Pasta data: {DATA_DIR}", 
               style={'color': COLORS['neutral'], 'fontSize': '12px'})
    ]
    
    system_status = html.Div(status_items)
    
    return (
        balance,
        total_trades,
        win_rate_text,
        daily_pnl_text,
        daily_pnl_style,
        fig,
        top_performers,
        trades_table,
        system_status
    )

# ========================================
# RUN
# ========================================

if __name__ == '__main__':
    print("="*60)
    print("📊 Iniciando Dashboard Simples - App Leonardo")
    print("="*60)
    print("🔗 Dashboard: http://localhost:8050")
    print("📁 Lendo dados de:", DATA_DIR)
    print("✅ Funciona SEM backend!")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=8050)