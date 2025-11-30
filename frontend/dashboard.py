"""
🎨 Frontend - Plotly Dash Dashboard
Interface web interativa para o bot de trading
"""
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import requests
import pandas as pd
from datetime import datetime

# ========================================
# CONFIGURAÇÃO
# ========================================

API_URL = "http://localhost:8000"
BACKEND_URL = API_URL
WS_URL = "ws://localhost:8000/ws"

# ========================================
# APP DASH
# ========================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="App Leonardo - Trading Bot"
)

# ========================================
# LAYOUT
# ========================================

app.layout = dbc.Container([
    dcc.Interval(id='interval-component', interval=5*1000, n_intervals=0),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🤖 App Leonardo", className="text-primary"),
            html.H5("Sistema Profissional de Trading Automatizado", className="text-muted")
        ], width=8),
        dbc.Col([
            html.Div(id='bot-status-badge', className="text-end")
        ], width=4)
    ], className="mb-4 mt-3"),
    
    # Cards de Estatísticas
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("💰 Saldo", className="text-muted"),
                    html.H3(id='balance-value', className="text-success")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("📈 PnL Total", className="text-muted"),
                    html.H3(id='total-pnl-value')
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("📊 Trades", className="text-muted"),
                    html.H3(id='total-trades-value')
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("🎯 Win Rate", className="text-muted"),
                    html.H3(id='win-rate-value')
                ])
            ])
        ], width=3)
    ], className="mb-4"),
    
    # Controles do Bot
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("⚙️ Controle do Bot"),
                    dbc.ButtonGroup([
                        dbc.Button("▶️ Iniciar", id="start-bot-btn", color="success", className="me-2"),
                        dbc.Button("⏸️ Parar", id="stop-bot-btn", color="danger")
                    ])
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Gráficos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📈 BTC/USDT - Candlestick + Indicadores"),
                    dcc.Graph(id='btc-chart', style={'height': '500px'})
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Tabelas
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📋 Últimos Trades"),
                    html.Div(id='trades-table')
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("💼 Posições Abertas"),
                    html.Div(id='positions-table')
                ])
            ])
        ], width=6)
    ], className="mb-4"),
    
    # Footer
    html.Hr(),
    html.P("🚀 Powered by FastAPI + Plotly Dash + PostgreSQL + Redis", className="text-center text-muted")
    
], fluid=True, style={'backgroundColor': '#1a1a1a', 'minHeight': '100vh', 'padding': '20px'})


# ========================================
# CALLBACKS
# ========================================

@app.callback(
    [
        Output('bot-status-badge', 'children'),
        Output('balance-value', 'children'),
        Output('total-pnl-value', 'children'),
        Output('total-pnl-value', 'className'),
        Output('total-trades-value', 'children'),
        Output('win-rate-value', 'children'),
    ],
    Input('interval-component', 'n_intervals')
)
def update_metrics(n):
    """Atualiza métricas do dashboard"""
    try:
        response = requests.get(f"{API_URL}/api/status", timeout=2)
        data = response.json()
        
        if data.get('is_running'):
            status_badge = dbc.Badge("🟢 Operando", color="success", className="fs-5")
        else:
            status_badge = dbc.Badge("⚫ Parado", color="secondary", className="fs-5")
        
        balance = f"${data.get('balance', 0):,.2f}"
        total_pnl = data.get('total_pnl', 0)
        pnl_text = f"${total_pnl:+,.2f}"
        pnl_class = "text-success" if total_pnl >= 0 else "text-danger"
        
        total_trades = f"{data.get('total_trades', 0)} trades"
        win_rate = f"{data.get('win_rate', 0):.1f}%"
        
        return status_badge, balance, pnl_text, pnl_class, total_trades, win_rate
    
    except:
        return dbc.Badge("❌ Offline", color="danger"), "$0.00", "$0.00", "text-muted", "0", "0%"


@app.callback(
    Output('btc-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_chart(n):
    """Atualiza gráfico de candlestick"""
    try:
        response = requests.get(f"{API_URL}/api/market-data/BTC/USDT?limit=100", timeout=2)
        data = response.json()
        
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Cria subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=('Preço', 'RSI', 'MACD')
        )
        
        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='BTC/USDT'
            ),
            row=1, col=1
        )
        
        # RSI
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['rsi'],
                name='RSI',
                line=dict(color='#FFA500', width=2)
            ),
            row=2, col=1
        )
        
        # Linhas RSI
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        # MACD
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['macd'],
                name='MACD',
                line=dict(color='#00BFFF', width=2)
            ),
            row=3, col=1
        )
        
        # Layout
        fig.update_layout(
            template='plotly_dark',
            showlegend=True,
            height=500,
            margin=dict(l=50, r=50, t=50, b=50),
            xaxis_rangeslider_visible=False
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#333')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#333')
        
        return fig
    
    except:
        return go.Figure()


@app.callback(
    Output('trades-table', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_trades_table(n):
    """Atualiza tabela de trades"""
    try:
        response = requests.get(f"{API_URL}/api/trades?limit=10", timeout=2)
        trades = response.json()
        
        if not trades:
            return html.P("Nenhum trade registrado", className="text-muted")
        
        rows = []
        for trade in trades:
            pnl_color = "success" if trade['pnl'] > 0 else "danger"
            rows.append(
                html.Tr([
                    html.Td(trade['symbol']),
                    html.Td(trade['side'], className=f"text-{'success' if trade['side'] == 'BUY' else 'danger'}"),
                    html.Td(f"${trade['entry_price']:.2f}"),
                    html.Td(f"${trade['exit_price']:.2f}"),
                    html.Td(f"${trade['pnl']:+.2f}", className=f"text-{pnl_color}"),
                    html.Td(f"{trade['pnl_pct']:+.2f}%", className=f"text-{pnl_color}"),
                ])
            )
        
        table = dbc.Table([
            html.Thead(html.Tr([
                html.Th("Símbolo"),
                html.Th("Lado"),
                html.Th("Entrada"),
                html.Th("Saída"),
                html.Th("PnL $"),
                html.Th("PnL %")
            ])),
            html.Tbody(rows)
        ], bordered=True, dark=True, hover=True, responsive=True, size='sm')
        
        return table
    
    except:
        return html.P("Erro ao carregar trades", className="text-danger")


@app.callback(
    Output('positions-table', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_positions_table(n):
    """Atualiza tabela de posições"""
    try:
        response = requests.get(f"{API_URL}/api/positions", timeout=2)
        positions = response.json()
        
        if not positions:
            return html.P("Nenhuma posição aberta", className="text-muted")
        
        rows = []
        for pos in positions:
            rows.append(
                html.Tr([
                    html.Td(pos['symbol']),
                    html.Td(pos['side'], className=f"text-{'success' if pos['side'] == 'BUY' else 'danger'}"),
                    html.Td(f"${pos['entry_price']:.2f}"),
                    html.Td(f"{pos['amount']:.6f}"),
                    html.Td(pos['entry_reason']),
                ])
            )
        
        table = dbc.Table([
            html.Thead(html.Tr([
                html.Th("Símbolo"),
                html.Th("Lado"),
                html.Th("Preço"),
                html.Th("Quantidade"),
                html.Th("Razão")
            ])),
            html.Tbody(rows)
        ], bordered=True, dark=True, hover=True, responsive=True, size='sm')
        
        return table
    
    except:
        return html.P("Erro ao carregar posições", className="text-danger")


@app.callback(
    Output('start-bot-btn', 'disabled'),
    Input('start-bot-btn', 'n_clicks'),
    prevent_initial_call=True
)
def start_bot(n_clicks):
    """Inicia o bot"""
    if n_clicks:
        try:
            requests.post(f"{API_URL}/api/bot/start")
            return True
        except:
            return False
    return False


@app.callback(
    Output('stop-bot-btn', 'disabled'),
    Input('stop-bot-btn', 'n_clicks'),
    prevent_initial_call=True
)
def stop_bot(n_clicks):
    """Para o bot"""
    if n_clicks:
        try:
            requests.post(f"{API_URL}/api/bot/stop")
            return True
        except:
            return False
    return False


# ========================================
# RUN
# ========================================

if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
