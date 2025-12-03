"""
🎨 Dashboard Plotly Dash v2.0 - App Leonardo
Dashboard com mini-gráficos para cada cripto e estatísticas completas
"""
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime
import pandas as pd

# ========================================
# CONFIGURAÇÃO
# ========================================

BACKEND_URL = "http://localhost:8001"

# Cores
COLORS = {
    'background': '#0f1419',
    'card': '#1a1f29',
    'text': '#e7e9ea',
    'positive': '#00ba7c',
    'negative': '#f91880',
    'neutral': '#8b98a5',
    'accent': '#1d9bf0'
}

# ========================================
# APP DASH
# ========================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

app.title = "App Leonardo v2.0 | Trading Dashboard"


# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def get_api_data(endpoint):
    """Busca dados da API"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def create_mini_chart(symbol):
    """Cria mini gráfico de candlestick para uma cripto"""
    data = get_api_data(f"crypto/{symbol}/chart?timeframe=5m&limit=50")
    
    if not data or 'candles' not in data:
        # Gráfico vazio
        fig = go.Figure()
        fig.update_layout(
            height=150,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor=COLORS['card'],
            plot_bgcolor=COLORS['card'],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    df = pd.DataFrame(data['candles'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Candlestick mini
    fig = go.Figure(data=[
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            increasing_line_color=COLORS['positive'],
            decreasing_line_color=COLORS['negative'],
            showlegend=False
        )
    ])
    
    fig.update_layout(
        height=150,
        margin=dict(l=0, r=0, t=5, b=0),
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['card'],
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            showticklabels=True,
            tickfont=dict(size=10, color=COLORS['neutral']),
            zeroline=False
        ),
        hovermode='x unified',
        dragmode=False
    )
    
    fig.update_xaxes(rangeslider_visible=False)
    
    return fig


def create_crypto_card(crypto_data):
    """Cria card para cada criptomoeda"""
    symbol = crypto_data['symbol']
    
    # Cor do PnL
    pnl_color = COLORS['positive'] if crypto_data['pnl_usd'] >= 0 else COLORS['negative']
    pnl_icon = "▲" if crypto_data['pnl_usd'] >= 0 else "▼"
    
    # Tendência
    trend_icons = {
        'BULLISH': '📈',
        'BEARISH': '📉',
        'NEUTRAL': '➡️'
    }
    trend_icon = trend_icons.get(crypto_data['trend'], '➡️')
    
    card = dbc.Card([
        dbc.CardBody([
            # Header
            html.Div([
                html.H4(
                    [symbol, " ", trend_icon],
                    className="mb-1",
                    style={'color': COLORS['text'], 'fontWeight': 'bold'}
                ),
                html.P(
                    f"${crypto_data.get('last_price', 0):,.2f}",
                    className="mb-2",
                    style={'color': COLORS['neutral'], 'fontSize': '14px'}
                )
            ]),
            
            # Mini gráfico
            html.Div([
                dcc.Graph(
                    figure=create_mini_chart(f"{symbol}/USDT"),
                    config={'displayModeBar': False},
                    style={'height': '150px'}
                )
            ], className="mb-2"),
            
            # Estatísticas
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.P("Investido", className="mb-0", 
                               style={'fontSize': '11px', 'color': COLORS['neutral']}),
                        html.H6(
                            f"${crypto_data['invested_usd']:.2f}",
                            className="mb-0",
                            style={'color': COLORS['text'], 'fontWeight': 'bold'}
                        )
                    ], width=6),
                    dbc.Col([
                        html.P("Valor Atual", className="mb-0",
                               style={'fontSize': '11px', 'color': COLORS['neutral']}),
                        html.H6(
                            f"${crypto_data['current_value_usd']:.2f}",
                            className="mb-0",
                            style={'color': COLORS['text'], 'fontWeight': 'bold'}
                        )
                    ], width=6)
                ], className="mb-2"),
                
                dbc.Row([
                    dbc.Col([
                        html.P("PnL", className="mb-0",
                               style={'fontSize': '11px', 'color': COLORS['neutral']}),
                        html.H6(
                            f"{pnl_icon} ${abs(crypto_data['pnl_usd']):.2f}",
                            className="mb-0",
                            style={'color': pnl_color, 'fontWeight': 'bold'}
                        )
                    ], width=6),
                    dbc.Col([
                        html.P("PnL %", className="mb-0",
                               style={'fontSize': '11px', 'color': COLORS['neutral']}),
                        html.H6(
                            f"{crypto_data['pnl_pct']:+.2f}%",
                            className="mb-0",
                            style={'color': pnl_color, 'fontWeight': 'bold'}
                        )
                    ], width=6)
                ], className="mb-2"),
                
                dbc.Row([
                    dbc.Col([
                        html.P("Win Rate", className="mb-0",
                               style={'fontSize': '11px', 'color': COLORS['neutral']}),
                        html.H6(
                            f"{crypto_data.get('win_rate', 0):.1f}%",
                            className="mb-0",
                            style={'color': COLORS['text'], 'fontWeight': 'bold'}
                        )
                    ], width=6),
                    dbc.Col([
                        html.P("Tendência", className="mb-0",
                               style={'fontSize': '11px', 'color': COLORS['neutral']}),
                        html.H6(
                            crypto_data['trend'],
                            className="mb-0",
                            style={'color': COLORS['accent'], 'fontSize': '12px'}
                        )
                    ], width=6)
                ])
            ])
        ])
    ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
    
    return card


# ========================================
# LAYOUT
# ========================================

app.layout = dbc.Container([
    dcc.Interval(id='interval-update', interval=5000, n_intervals=0),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1(
                "🚀 App Leonardo Trading Bot v2.0",
                className="mb-3",
                style={'color': COLORS['text'], 'fontWeight': 'bold'}
            )
        ])
    ], className="mt-4 mb-4"),
    
    # Cards de Estatísticas Principais
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("💰 Saldo USD", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H3(id='balance-usd', children="$0.00",
                            style={'color': COLORS['text'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("💎 Valor Total", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H3(id='total-value', children="$0.00",
                            style={'color': COLORS['text'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("📊 Trades Hoje", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H3(id='trades-today', children="0",
                            style={'color': COLORS['text'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("🎯 Posições Abertas", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H3(id='open-positions', children="0",
                            style={'color': COLORS['text'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3)
    ], className="mb-4"),
    
    # Estatísticas Adicionais
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("📈 PnL Total", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H4(id='total-pnl', children="$0.00",
                            style={'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("📉 PnL Hoje", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H4(id='daily-pnl', children="$0.00",
                            style={'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("✅ Win Rate", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H4(id='win-rate', children="0%",
                            style={'color': COLORS['positive'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("🔄 Total Trades", className="mb-1",
                           style={'color': COLORS['neutral'], 'fontSize': '14px'}),
                    html.H4(id='total-trades', children="0",
                            style={'color': COLORS['text'], 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3)
    ], className="mb-4"),
    
    # Título das Criptomoedas
    dbc.Row([
        dbc.Col([
            html.H3(
                "🪙 Portfólio de Criptomoedas",
                className="mb-3",
                style={'color': COLORS['text'], 'fontWeight': 'bold'}
            )
        ])
    ]),
    
    # Grid de Cards das Criptomoedas (8 cards)
    html.Div(id='crypto-cards-grid', className="mb-4"),
    
    # Trades Recentes
    dbc.Row([
        dbc.Col([
            html.H3(
                "📋 Trades Recentes",
                className="mb-3",
                style={'color': COLORS['text'], 'fontWeight': 'bold'}
            ),
            html.Div(id='recent-trades-table')
        ])
    ])
    
], fluid=True, style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})


# ========================================
# CALLBACKS
# ========================================

@app.callback(
    [
        Output('balance-usd', 'children'),
        Output('total-value', 'children'),
        Output('trades-today', 'children'),
        Output('open-positions', 'children'),
        Output('total-pnl', 'children'),
        Output('total-pnl', 'style'),
        Output('daily-pnl', 'children'),
        Output('daily-pnl', 'style'),
        Output('win-rate', 'children'),
        Output('total-trades', 'children'),
        Output('crypto-cards-grid', 'children'),
        Output('recent-trades-table', 'children')
    ],
    [Input('interval-update', 'n_intervals')]
)
def update_dashboard(n):
    """Atualiza todo o dashboard"""
    
    # Busca dados da API
    summary = get_api_data('summary')
    status = get_api_data('status')
    recent_trades = get_api_data('trades/recent?limit=10')
    
    if not summary or not status:
        return ["$0.00"] * 10 + [html.Div(), html.Div()]
    
    # Cards principais
    balance_usd = f"${summary['balance_usd']:,.2f}"
    total_value = f"${summary['total_value_usd']:,.2f}"
    trades_today = str(summary['total_trades_today'])
    open_pos = str(summary['open_positions'])
    
    # PnL
    total_pnl_val = summary['total_pnl']
    total_pnl_text = f"${abs(total_pnl_val):,.2f}"
    total_pnl_style = {
        'color': COLORS['positive'] if total_pnl_val >= 0 else COLORS['negative'],
        'fontWeight': 'bold'
    }
    if total_pnl_val >= 0:
        total_pnl_text = f"+{total_pnl_text}"
    else:
        total_pnl_text = f"-{total_pnl_text}"
    
    daily_pnl_val = summary['daily_pnl']
    daily_pnl_text = f"${abs(daily_pnl_val):,.2f}"
    daily_pnl_style = {
        'color': COLORS['positive'] if daily_pnl_val >= 0 else COLORS['negative'],
        'fontWeight': 'bold'
    }
    if daily_pnl_val >= 0:
        daily_pnl_text = f"+{daily_pnl_text}"
    else:
        daily_pnl_text = f"-{daily_pnl_text}"
    
    win_rate = f"{summary['win_rate']:.1f}%"
    total_trades = str(summary['total_trades'])
    
    # Grid de criptomoedas (2 linhas x 4 colunas)
    crypto_cards = []
    cryptos = summary.get('cryptos', [])
    
    # Primeira linha (4 criptos)
    row1 = dbc.Row([
        dbc.Col(create_crypto_card(crypto), width=3)
        for crypto in cryptos[:4]
    ], className="mb-3")
    
    # Segunda linha (4 criptos)
    row2 = dbc.Row([
        dbc.Col(create_crypto_card(crypto), width=3)
        for crypto in cryptos[4:8]
    ])
    
    crypto_grid = html.Div([row1, row2])
    
    # Tabela de trades recentes
    if recent_trades:
        table_rows = []
        for trade in recent_trades[:10]:
            pnl_color = COLORS['positive'] if trade['pnl'] >= 0 else COLORS['negative']
            
            table_rows.append(
                html.Tr([
                    html.Td(trade['symbol'], style={'color': COLORS['text']}),
                    html.Td(trade['side'], style={'color': COLORS['accent']}),
                    html.Td(f"${trade['entry_price']:,.2f}", style={'color': COLORS['neutral']}),
                    html.Td(f"${trade['exit_price']:,.2f}", style={'color': COLORS['neutral']}),
                    html.Td(
                        f"${trade['pnl']:,.2f}",
                        style={'color': pnl_color, 'fontWeight': 'bold'}
                    ),
                    html.Td(
                        f"{trade['pnl_pct']:+.2f}%",
                        style={'color': pnl_color, 'fontWeight': 'bold'}
                    ),
                    html.Td(
                        datetime.fromisoformat(trade['timestamp']).strftime('%H:%M:%S'),
                        style={'color': COLORS['neutral'], 'fontSize': '12px'}
                    )
                ])
            )
        
        trades_table = dbc.Table([
            html.Thead(
                html.Tr([
                    html.Th("Símbolo"),
                    html.Th("Lado"),
                    html.Th("Entrada"),
                    html.Th("Saída"),
                    html.Th("PnL USD"),
                    html.Th("PnL %"),
                    html.Th("Hora")
                ])
            ),
            html.Tbody(table_rows)
        ], dark=True, striped=True, bordered=True, hover=True)
    else:
        trades_table = html.P("Nenhum trade ainda", style={'color': COLORS['neutral']})
    
    return (
        balance_usd,
        total_value,
        trades_today,
        open_pos,
        total_pnl_text,
        total_pnl_style,
        daily_pnl_text,
        daily_pnl_style,
        win_rate,
        total_trades,
        crypto_grid,
        trades_table
    )


# ========================================
# RUN
# ========================================

if __name__ == '__main__':
    print("="*60)
    print("🎨 Iniciando Dashboard Plotly Dash v2.0")
    print("="*60)
    print("📊 Dashboard: http://localhost:8050")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=8050)
