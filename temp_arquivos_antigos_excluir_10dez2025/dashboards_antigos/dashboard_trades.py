"""
📊 Dashboard de Trades - Planilha Completa
Visualização de todas as operações realizadas
"""
import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output
import pandas as pd
import json
import sqlite3
from datetime import datetime
import os

# Configuração de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'trading_history.db')
JSON_PATH = os.path.join(BASE_DIR, 'data', 'all_trades_history.json')

# Inicializa o app Dash
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "📊 Planilha de Trades - App Leonardo"

def get_trades_from_db():
    """Busca trades do banco de dados SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT 
                id,
                symbol as Símbolo,
                side as Lado,
                entry_price as 'Preço Entrada',
                exit_price as 'Preço Saída',
                amount as Quantidade,
                pnl as 'PnL ($)',
                pnl_pct as 'PnL (%)',
                entry_time as 'Data/Hora Entrada',
                exit_time as 'Data/Hora Saída',
                entry_reason as 'Razão Entrada',
                exit_reason as 'Razão Saída'
            FROM trades
            ORDER BY id DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Erro ao buscar do DB: {e}")
        return pd.DataFrame()

def get_trades_from_json():
    """Busca trades do arquivo JSON"""
    try:
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)
        
        trades = data.get('trades', [])
        if not trades:
            return pd.DataFrame()
        
        df = pd.DataFrame(trades)
        
        # Renomear colunas
        column_map = {
            'symbol': 'Símbolo',
            'side': 'Lado',
            'entry_price': 'Preço Entrada',
            'exit_price': 'Preço Saída',
            'amount': 'Quantidade',
            'pnl': 'PnL ($)',
            'pnl_pct': 'PnL (%)',
            'entry_time': 'Data/Hora Entrada',
            'exit_time': 'Data/Hora Saída',
            'entry_reason': 'Razão Entrada',
            'exit_reason': 'Razão Saída',
            'duration_minutes': 'Duração (min)'
        }
        df = df.rename(columns=column_map)
        
        return df
    except Exception as e:
        print(f"Erro ao buscar do JSON: {e}")
        return pd.DataFrame()

def get_all_trades():
    """Tenta buscar trades do DB, se falhar usa JSON"""
    df = get_trades_from_db()
    if df.empty:
        df = get_trades_from_json()
    return df

def calculate_stats(df):
    """Calcula estatísticas dos trades"""
    if df.empty:
        return {}
    
    total = len(df)
    pnl_col = 'PnL ($)' if 'PnL ($)' in df.columns else 'pnl'
    
    wins = len(df[df[pnl_col] > 0])
    losses = len(df[df[pnl_col] < 0])
    total_pnl = df[pnl_col].sum()
    avg_pnl = df[pnl_col].mean()
    best = df[pnl_col].max()
    worst = df[pnl_col].min()
    win_rate = (wins / total * 100) if total > 0 else 0
    
    return {
        'total': total,
        'wins': wins,
        'losses': losses,
        'total_pnl': total_pnl,
        'avg_pnl': avg_pnl,
        'best': best,
        'worst': worst,
        'win_rate': win_rate
    }

# Layout do dashboard
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("📊 Planilha de Trades - App Leonardo", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
        html.P(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
               style={'textAlign': 'center', 'color': '#7f8c8d'}),
    ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'marginBottom': '20px'}),
    
    # Cards de estatísticas
    html.Div(id='stats-cards', style={
        'display': 'flex', 
        'justifyContent': 'space-around', 
        'flexWrap': 'wrap',
        'marginBottom': '20px',
        'padding': '0 20px'
    }),
    
    # Filtros
    html.Div([
        html.Div([
            html.Label("Filtrar por Símbolo:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='symbol-filter',
                options=[{'label': 'Todos', 'value': 'ALL'}],
                value='ALL',
                style={'width': '200px'}
            ),
        ], style={'display': 'inline-block', 'marginRight': '20px'}),
        
        html.Div([
            html.Label("Filtrar por Resultado:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='result-filter',
                options=[
                    {'label': 'Todos', 'value': 'ALL'},
                    {'label': '🟢 Ganhos', 'value': 'WIN'},
                    {'label': '🔴 Perdas', 'value': 'LOSS'}
                ],
                value='ALL',
                style={'width': '200px'}
            ),
        ], style={'display': 'inline-block', 'marginRight': '20px'}),
        
        html.Button('🔄 Atualizar', id='refresh-btn', n_clicks=0,
                   style={
                       'backgroundColor': '#3498db',
                       'color': 'white',
                       'border': 'none',
                       'padding': '10px 20px',
                       'borderRadius': '5px',
                       'cursor': 'pointer',
                       'marginTop': '20px'
                   }),
        
        html.Button('📥 Exportar CSV', id='export-btn', n_clicks=0,
                   style={
                       'backgroundColor': '#27ae60',
                       'color': 'white',
                       'border': 'none',
                       'padding': '10px 20px',
                       'borderRadius': '5px',
                       'cursor': 'pointer',
                       'marginTop': '20px',
                       'marginLeft': '10px'
                   }),
        dcc.Download(id='download-csv'),
        
    ], style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'marginBottom': '20px'}),
    
    # Tabela de trades
    html.Div([
        dash_table.DataTable(
            id='trades-table',
            columns=[],
            data=[],
            page_size=25,
            page_action='native',
            sort_action='native',
            sort_mode='multi',
            filter_action='native',
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': '#2c3e50',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_cell={
                'textAlign': 'center',
                'padding': '10px',
                'minWidth': '80px',
                'maxWidth': '200px',
                'whiteSpace': 'normal'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f9f9f9'
                },
                {
                    'if': {
                        'filter_query': '{PnL ($)} > 0',
                        'column_id': 'PnL ($)'
                    },
                    'backgroundColor': '#d4edda',
                    'color': '#155724'
                },
                {
                    'if': {
                        'filter_query': '{PnL ($)} < 0',
                        'column_id': 'PnL ($)'
                    },
                    'backgroundColor': '#f8d7da',
                    'color': '#721c24'
                }
            ],
            export_format='xlsx',
            export_headers='display',
        )
    ], style={'padding': '20px'}),
    
    # SOMA TOTAL DO PNL
    html.Div(id='pnl-total-box', style={'padding': '20px'}),
    
    # Intervalo de atualização
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # 30 segundos
        n_intervals=0
    ),
    
    # Links
    html.Div([
        html.Hr(),
        html.P([
            "🔗 Links: ",
            html.A("Dashboard Principal", href="http://localhost:8050", target="_blank"),
            " | ",
            html.A("Planilha de Trades", href="http://localhost:8051", target="_blank"),
        ], style={'textAlign': 'center', 'color': '#7f8c8d'})
    ], style={'padding': '20px'})
    
], style={'fontFamily': 'Arial, sans-serif', 'maxWidth': '1400px', 'margin': '0 auto'})

@app.callback(
    [Output('trades-table', 'columns'),
     Output('trades-table', 'data'),
     Output('stats-cards', 'children'),
     Output('symbol-filter', 'options'),
     Output('pnl-total-box', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('refresh-btn', 'n_clicks'),
     Input('symbol-filter', 'value'),
     Input('result-filter', 'value')]
)
def update_table(n_intervals, n_clicks, symbol_filter, result_filter):
    df = get_all_trades()
    
    if df.empty:
        return [], [], html.P("Nenhum trade encontrado"), [{'label': 'Todos', 'value': 'ALL'}], html.Div()
    
    # Aplicar filtros
    pnl_col = 'PnL ($)' if 'PnL ($)' in df.columns else 'pnl'
    symbol_col = 'Símbolo' if 'Símbolo' in df.columns else 'symbol'
    
    if symbol_filter and symbol_filter != 'ALL':
        df = df[df[symbol_col] == symbol_filter]
    
    if result_filter == 'WIN':
        df = df[df[pnl_col] > 0]
    elif result_filter == 'LOSS':
        df = df[df[pnl_col] < 0]
    
    # Calcular estatísticas
    stats = calculate_stats(df)
    total_pnl = stats.get('total_pnl', 0)
    
    # Criar cards de estatísticas
    cards = [
        create_stat_card("Total de Trades", stats.get('total', 0), "#3498db", "📊"),
        create_stat_card("Ganhos", stats.get('wins', 0), "#27ae60", "✅"),
        create_stat_card("Perdas", stats.get('losses', 0), "#e74c3c", "❌"),
        create_stat_card("Win Rate", f"{stats.get('win_rate', 0):.1f}%", "#9b59b6", "🎯"),
        create_stat_card("PnL Total", f"${stats.get('total_pnl', 0):.2f}", 
                        "#27ae60" if stats.get('total_pnl', 0) >= 0 else "#e74c3c", "💰"),
        create_stat_card("PnL Médio", f"${stats.get('avg_pnl', 0):.4f}", "#f39c12", "📈"),
    ]
    
    # Preparar colunas
    columns = [{"name": col, "id": col} for col in df.columns if col != 'entry_indicators']
    
    # Formatar dados para exibição
    df_display = df.copy()
    if pnl_col in df_display.columns:
        df_display[pnl_col] = df_display[pnl_col].apply(lambda x: round(x, 4) if pd.notnull(x) else x)
    
    # Opções de filtro de símbolo
    symbols = df[symbol_col].unique().tolist() if symbol_col in df.columns else []
    symbol_options = [{'label': 'Todos', 'value': 'ALL'}] + [{'label': s, 'value': s} for s in symbols]
    
    # Box de soma total do PnL
    pnl_color = '#27ae60' if total_pnl >= 0 else '#e74c3c'
    pnl_icon = '📈 LUCRO' if total_pnl >= 0 else '📉 PREJUÍZO'
    pnl_box = html.Div([
        html.Div([
            html.H2(f"{pnl_icon}", style={'margin': '0', 'color': pnl_color}),
            html.H1(f"${total_pnl:.2f}", style={'margin': '10px 0', 'color': pnl_color, 'fontSize': '48px'}),
            html.P(f"Soma total de {stats.get('total', 0)} trades | {stats.get('wins', 0)} ganhos | {stats.get('losses', 0)} perdas", 
                   style={'margin': '0', 'color': '#7f8c8d'}),
            html.P(f"Melhor: ${stats.get('best', 0):.4f} | Pior: ${stats.get('worst', 0):.4f} | Média: ${stats.get('avg_pnl', 0):.4f}",
                   style={'margin': '5px 0', 'color': '#7f8c8d', 'fontSize': '14px'}),
        ], style={
            'backgroundColor': '#fff',
            'padding': '30px',
            'borderRadius': '15px',
            'boxShadow': '0 4px 15px rgba(0,0,0,0.1)',
            'textAlign': 'center',
            'border': f'3px solid {pnl_color}'
        })
    ])
    
    return columns, df_display.to_dict('records'), cards, symbol_options, pnl_box

def create_stat_card(title, value, color, icon):
    """Cria um card de estatística"""
    return html.Div([
        html.Div(icon, style={'fontSize': '30px', 'marginBottom': '5px'}),
        html.H3(str(value), style={'margin': '5px 0', 'color': color}),
        html.P(title, style={'margin': '0', 'color': '#7f8c8d', 'fontSize': '12px'})
    ], style={
        'backgroundColor': 'white',
        'padding': '15px 25px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 5px rgba(0,0,0,0.1)',
        'textAlign': 'center',
        'minWidth': '120px',
        'margin': '5px'
    })

@app.callback(
    Output('download-csv', 'data'),
    Input('export-btn', 'n_clicks'),
    prevent_initial_call=True
)
def export_csv(n_clicks):
    df = get_all_trades()
    if not df.empty:
        return dcc.send_data_frame(df.to_csv, f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
    return None

if __name__ == '__main__':
    print("\n" + "="*60)
    print("📊 Planilha de Trades - App Leonardo")
    print("="*60)
    print("📊 Acesse: http://localhost:8051")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8051, debug=True)
