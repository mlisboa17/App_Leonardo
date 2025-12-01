"""
💰 Dashboard de Saldo - App Leonardo
Dashboard minimalista focado no saldo e estatísticas básicas
"""
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import json
import os
from datetime import datetime
from pathlib import Path

# ========================================
# CONFIGURAÇÕES
# ========================================

COLORS = {
    'background': '#0a0e1a',
    'card': '#1a1f2e',
    'text': '#ffffff',
    'positive': '#00ff88',
    'negative': '#ff4757',
    'neutral': '#747d8c',
    'accent': '#3742fa'
}

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'

# ========================================
# FUNÇÕES
# ========================================

def get_balance_info():
    """Obtém informações de saldo dos arquivos"""
    try:
        # Tenta ler daily_stats.json
        daily_stats_file = DATA_DIR / 'daily_stats.json'
        if daily_stats_file.exists():
            with open(daily_stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {
                'balance': data.get('balance_usd', 14.12),
                'trades': data.get('total_trades', 503),
                'wins': data.get('winning_trades', 349),
                'losses': data.get('losing_trades', 104),
                'pnl_daily': data.get('daily_pnl', 4.20),
                'pnl_total': data.get('total_pnl', 4.20)
            }
    except Exception as e:
        print(f"Erro ao ler daily_stats.json: {e}")
    
    # Valores padrão baseados na última execução
    return {
        'balance': 14.12,
        'trades': 503,
        'wins': 349,
        'losses': 104,
        'pnl_daily': 4.20,
        'pnl_total': 4.20
    }

def check_bot_running():
    """Verifica se o bot está rodando baseado em arquivos recentes"""
    try:
        # Verifica se existe arquivo de log recente
        logs_dir = BASE_DIR / 'logs'
        if logs_dir.exists():
            log_files = list(logs_dir.glob('*.log'))
            if log_files:
                latest_log = max(log_files, key=os.path.getctime)
                # Se arquivo foi modificado nas últimas 2 horas
                if (datetime.now().timestamp() - os.path.getctime(latest_log)) < 7200:
                    return True
        
        # Verifica arquivos de history recentes
        history_dir = DATA_DIR / 'history'
        if history_dir.exists():
            history_files = list(history_dir.glob('*.json'))
            if history_files:
                latest_history = max(history_files, key=os.path.getctime)
                # Se arquivo foi criado nas últimas 30 minutos
                if (datetime.now().timestamp() - os.path.getctime(latest_history)) < 1800:
                    return True
        
        return False
    except:
        return False

# ========================================
# APP DASH
# ========================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY]
)

app.title = "App Leonardo - Saldo"

# ========================================
# LAYOUT
# ========================================

app.layout = dbc.Container([
    dcc.Interval(id='interval', interval=5000, n_intervals=0),  # Atualiza a cada 5s
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("💰 App Leonardo - Monitor de Saldo", 
                   style={'color': COLORS['text'], 'textAlign': 'center', 'fontWeight': 'bold'}),
            html.Hr(style={'borderColor': COLORS['neutral']})
        ])
    ], className="mt-3 mb-4"),
    
    # Status do Bot
    dbc.Row([
        dbc.Col([
            dbc.Alert(id='bot-status-alert', className="text-center")
        ])
    ], className="mb-3"),
    
    # Saldo Principal - GRANDE
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H1("SALDO ATUAL", 
                           style={'color': COLORS['neutral'], 'textAlign': 'center', 'fontSize': '24px'}),
                    html.H1(id='main-balance', 
                           style={'color': COLORS['positive'], 'textAlign': 'center', 'fontSize': '60px', 'fontWeight': 'bold'}),
                    html.P(id='balance-change',
                          style={'textAlign': 'center', 'fontSize': '18px'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': f'3px solid {COLORS["accent"]}', 'height': '200px'})
        ])
    ], className="mb-4"),
    
    # Cards de Estatísticas
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("📊", className="text-center mb-2"),
                    html.H2(id='total-trades', className="text-center",
                           style={'color': COLORS['accent'], 'fontWeight': 'bold'}),
                    html.P("TOTAL TRADES", className="text-center", 
                          style={'color': COLORS['neutral'], 'margin': '0'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("🎯", className="text-center mb-2"),
                    html.H2(id='win-rate', className="text-center",
                           style={'color': COLORS['positive'], 'fontWeight': 'bold'}),
                    html.P("WIN RATE", className="text-center",
                          style={'color': COLORS['neutral'], 'margin': '0'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("💎", className="text-center mb-2"),
                    html.H2(id='pnl-daily', className="text-center", style={'fontWeight': 'bold'}),
                    html.P("PnL DIÁRIO", className="text-center",
                          style={'color': COLORS['neutral'], 'margin': '0'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("🏆", className="text-center mb-2"),
                    html.H2(id='pnl-total', className="text-center", style={'fontWeight': 'bold'}),
                    html.P("PnL TOTAL", className="text-center",
                          style={'color': COLORS['neutral'], 'margin': '0'})
                ])
            ], style={'backgroundColor': COLORS['card'], 'border': 'none'})
        ], width=3)
    ], className="mb-4"),
    
    # Gráfico Simples de Trades
    dbc.Row([
        dbc.Col([
            html.H3("📈 Estatísticas de Trades", 
                   style={'color': COLORS['text'], 'textAlign': 'center'}),
            dcc.Graph(id='trades-chart')
        ])
    ], className="mb-4"),
    
    # Informações do Sistema
    dbc.Row([
        dbc.Col([
            html.H4("ℹ️ Informações do Sistema", style={'color': COLORS['text']}),
            html.Div(id='system-info')
        ])
    ])
    
], fluid=True, style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})

# ========================================
# CALLBACKS
# ========================================

@app.callback(
    [
        Output('bot-status-alert', 'children'),
        Output('bot-status-alert', 'color'),
        Output('main-balance', 'children'),
        Output('balance-change', 'children'),
        Output('balance-change', 'style'),
        Output('total-trades', 'children'),
        Output('win-rate', 'children'),
        Output('pnl-daily', 'children'),
        Output('pnl-daily', 'style'),
        Output('pnl-total', 'children'),
        Output('pnl-total', 'style'),
        Output('trades-chart', 'figure'),
        Output('system-info', 'children')
    ],
    [Input('interval', 'n_intervals')]
)
def update_dashboard(n):
    """Atualiza o dashboard"""
    
    # Obtém dados
    balance_info = get_balance_info()
    is_bot_running = check_bot_running()
    
    # Status do bot
    if is_bot_running:
        status_msg = "🟢 Bot está ATIVO e operando"
        status_color = "success"
    else:
        status_msg = "🔴 Bot PARADO ou sem atividade recente"
        status_color = "danger"
    
    # Saldo principal
    main_balance = f"${balance_info['balance']:,.2f}"
    
    # Mudança do saldo (baseada no PnL diário)
    pnl_daily = balance_info['pnl_daily']
    if pnl_daily >= 0:
        balance_change_text = f"📈 +${abs(pnl_daily):.2f} hoje"
        balance_change_color = COLORS['positive']
    else:
        balance_change_text = f"📉 -${abs(pnl_daily):.2f} hoje"
        balance_change_color = COLORS['negative']
    
    balance_change_style = {'textAlign': 'center', 'fontSize': '18px', 'color': balance_change_color}
    
    # Estatísticas
    total_trades = f"{balance_info['trades']:,}"
    
    win_rate = 0
    if balance_info['trades'] > 0:
        win_rate = (balance_info['wins'] / balance_info['trades']) * 100
    win_rate_text = f"{win_rate:.1f}%"
    
    # PnL diário
    pnl_daily_text = f"${abs(pnl_daily):,.2f}"
    if pnl_daily >= 0:
        pnl_daily_text = f"+{pnl_daily_text}"
        pnl_daily_color = COLORS['positive']
    else:
        pnl_daily_text = f"-{pnl_daily_text}"
        pnl_daily_color = COLORS['negative']
    
    pnl_daily_style = {'color': pnl_daily_color, 'fontWeight': 'bold'}
    
    # PnL total
    pnl_total = balance_info['pnl_total']
    pnl_total_text = f"${abs(pnl_total):,.2f}"
    if pnl_total >= 0:
        pnl_total_text = f"+{pnl_total_text}"
        pnl_total_color = COLORS['positive']
    else:
        pnl_total_text = f"-{pnl_total_text}"
        pnl_total_color = COLORS['negative']
    
    pnl_total_style = {'color': pnl_total_color, 'fontWeight': 'bold'}
    
    # Gráfico de pizza - Wins vs Losses
    fig = go.Figure(data=[
        go.Pie(
            labels=['Trades Ganhos', 'Trades Perdidos'],
            values=[balance_info['wins'], balance_info['losses']],
            hole=0.6,
            marker_colors=[COLORS['positive'], COLORS['negative']],
            textinfo='label+percent',
            textfont_size=16
        )
    ])
    
    fig.update_layout(
        title={
            'text': f"Win Rate: {win_rate:.1f}%",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': COLORS['text']}
        },
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text'], size=14),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        height=400
    )
    
    # Adiciona texto no centro do donut
    fig.add_annotation(
        text=f"{balance_info['trades']}<br>TRADES",
        x=0.5, y=0.5,
        font_size=20,
        showarrow=False,
        font_color=COLORS['text']
    )
    
    # Informações do sistema
    now = datetime.now()
    
    system_items = [
        dbc.Row([
            dbc.Col([
                html.P(f"🕒 Atualizado: {now.strftime('%H:%M:%S')}", 
                      style={'color': COLORS['text'], 'margin': '0'}),
                html.P(f"📅 Data: {now.strftime('%d/%m/%Y')}", 
                      style={'color': COLORS['neutral'], 'margin': '0'}),
            ], width=6),
            dbc.Col([
                html.P(f"📁 Pasta de dados: {DATA_DIR.name}", 
                      style={'color': COLORS['neutral'], 'margin': '0'}),
                html.P(f"🔄 Intervalo: 5 segundos", 
                      style={'color': COLORS['neutral'], 'margin': '0'}),
            ], width=6)
        ])
    ]
    
    # Verifica arquivos
    daily_stats_exists = (DATA_DIR / 'daily_stats.json').exists()
    
    if daily_stats_exists:
        system_items.append(
            html.P("✅ Arquivo daily_stats.json encontrado", 
                  style={'color': COLORS['positive'], 'margin': '0'})
        )
    else:
        system_items.append(
            html.P("❌ Arquivo daily_stats.json não encontrado", 
                  style={'color': COLORS['negative'], 'margin': '0'})
        )
    
    system_info = html.Div(system_items)
    
    return (
        status_msg,
        status_color,
        main_balance,
        balance_change_text,
        balance_change_style,
        total_trades,
        win_rate_text,
        pnl_daily_text,
        pnl_daily_style,
        pnl_total_text,
        pnl_total_style,
        fig,
        system_info
    )

# ========================================
# RUN
# ========================================

if __name__ == '__main__':
    print("="*50)
    print("💰 Dashboard de Saldo - App Leonardo")
    print("="*50)
    print("🌐 URL: http://localhost:8051")
    print("📊 Atualização: 5 segundos")
    print("💡 Funciona sem backend!")
    print("="*50)
    
    app.run(debug=True, host='0.0.0.0', port=8051)