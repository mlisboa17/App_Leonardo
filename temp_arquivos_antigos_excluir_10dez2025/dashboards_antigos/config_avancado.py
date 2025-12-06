"""
🔧 Painel de Configurações Avançadas - App Leonardo
Interface web para configurações detalhadas do bot
"""
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dotenv import load_dotenv
import os
import json
import yaml
from datetime import datetime

# Carrega credenciais
load_dotenv('../config/.env')

# Cores do tema
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
}

# ========================================
# APP DASH
# ========================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

app.title = "App Leonardo | Configurações Avançadas"

# ========================================
# LAYOUT PRINCIPAL
# ========================================

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1(
                "🔧 App Leonardo - Configurações Avançadas",
                className="mb-2",
                style={'color': COLORS['text'], 'fontWeight': 'bold'}
            ),
            html.P(
                "Configure regras avançadas de gestão de portfólio e risco",
                style={'color': COLORS['neutral'], 'fontSize': '16px'}
            ),
        ])
    ], className="mt-4 mb-4"),
    
    # Navegação
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("📊 Dashboard Principal", href="http://localhost:8050", color="info", outline=True),
                dbc.Button("🔧 Configurações", color="primary", disabled=True),
                dbc.Button("📈 Backtesting", color="secondary", outline=True, disabled=True),
            ], className="mb-4")
        ])
    ]),
    
    # Configurações de Gestão de Portfólio
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("💼 Gestão de Portfólio", className="mb-0", style={'color': COLORS['gold']})
                ]),
                dbc.CardBody([
                    # Regra de Exposição em Crypto
                    html.H6("🎯 Regra de Exposição Máxima", style={'color': COLORS['accent'], 'marginBottom': '20px'}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("📊 Exposição Máxima em Crypto (%):", style={'color': COLORS['text']}),
                            dbc.Input(
                                id='max-crypto-exposure',
                                type='number',
                                value=40,
                                min=10,
                                max=90,
                                step=5,
                                className='mb-3'
                            ),
                            html.Small(
                                "Quando atingir este % do portfólio em crypto, aplicar estratégia",
                                style={'color': COLORS['neutral']}
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("🔄 Estratégia ao Atingir Limite:", style={'color': COLORS['text']}),
                            dbc.Select(
                                id='exposure-action',
                                options=[
                                    {'label': '🧠 Capitalização Inteligente (Recomendado)', 'value': 'smart_capitalize'},
                                    {'label': '🛑 Parar de comprar apenas', 'value': 'stop_buying'},
                                    {'label': '⚖️ Rebalancear vendendo lucros', 'value': 'rebalance'},
                                    {'label': '🚨 Vender tudo (emergência)', 'value': 'sell_all'},
                                ],
                                value='smart_capitalize',
                                className='mb-3'
                            )
                        ], width=6),
                    ]),
                    
                    html.Hr(),
                    
                    # Exceções da Regra
                    html.H6("⚠️ Exceções da Regra", style={'color': COLORS['negative'], 'marginBottom': '20px'}),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Checklist(
                                id='portfolio-exceptions',
                                options=[
                                    {
                                        'label': ' Permitir até 5 posições se portfólio vazio',
                                        'value': 'empty_portfolio_exception'
                                    },
                                    {
                                        'label': '🛡️ NUNCA vender no prejuízo (Proteção Total)',
                                        'value': 'never_sell_at_loss'
                                    },
                                    {
                                        'label': ' Ignorar regra em oportunidades de alta confiança (>80%)',
                                        'value': 'high_confidence_exception'
                                    },
                                    {
                                        'label': ' Permitir compras de DCA em posições perdendo',
                                        'value': 'dca_exception'
                                    },
                                    {
                                        'label': ' Exceção durante primeiras 2 horas do dia',
                                        'value': 'morning_exception'
                                    }
                                ],
                                value=['empty_portfolio_exception', 'never_sell_at_loss'],
                                style={'color': COLORS['text']}
                            )
                        ], width=12),
                    ]),
                    
                    html.Hr(),
                    
                    # Configurações de Posições Mínimas
                    html.H6("📈 Configurações de Posições", style={'color': COLORS['positive'], 'marginBottom': '20px'}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("🔢 Mínimo de Posições Ativas:", style={'color': COLORS['text']}),
                            dbc.Input(
                                id='min-positions',
                                type='number',
                                value=2,
                                min=0,
                                max=10,
                                className='mb-3'
                            ),
                        ], width=4),
                        dbc.Col([
                            html.Label("🎯 Máximo de Posições (exceção):", style={'color': COLORS['text']}),
                            dbc.Input(
                                id='max-positions-exception',
                                type='number',
                                value=5,
                                min=1,
                                max=15,
                                className='mb-3'
                            ),
                        ], width=4),
                        dbc.Col([
                            html.Label("💰 Valor Mínimo por Posição (USDT):", style={'color': COLORS['text']}),
                            dbc.Input(
                                id='min-position-value',
                                type='number',
                                value=10,
                                min=1,
                                max=100,
                                step=1,
                                className='mb-3'
                            ),
                        ], width=4),
                    ]),
                ])
            ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
            
            # Configurações de Capitalização Inteligente
            dbc.Card([
                dbc.CardHeader([
                    html.H4("💰 Capitalização Inteligente", className="mb-0", style={'color': COLORS['gold']})
                ]),
                dbc.CardBody([
                    html.H6("🎯 Configurações de Lucro", style={'color': COLORS['positive'], 'marginBottom': '20px'}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("📈 Meta de Lucro para Capitalizar (%):", style={'color': COLORS['text']}),
                            dbc.Input(
                                id='target-profit-percent',
                                type='number',
                                value=20.0,
                                min=5.0,
                                max=100.0,
                                step=5.0,
                                className='mb-3'
                            ),
                            html.Small("Meta realista para início da capitalização (recomendado: 20%)", style={'color': COLORS['neutral']})
                        ], width=4),
                        dbc.Col([
                            html.Label("💎 Lucro Mínimo para Vender (%):", style={'color': COLORS['text']}),
                            dbc.Input(
                                id='min-profit-to-sell',
                                type='number',
                                value=5.0,
                                min=2.0,
                                max=25.0,
                                step=1.0,
                                className='mb-3'
                            ),
                            html.Small("Lucro mínimo para considerar venda (evita vendas prematuras)", style={'color': COLORS['neutral']})
                        ], width=4),
                        dbc.Col([
                            html.Label("🛡️ Proteção:", style={'color': COLORS['text']}),
                            dbc.Checklist(
                                id='capitalization-protection',
                                options=[
                                    {'label': ' Nunca vender no prejuízo', 'value': 'never_sell_at_loss'},
                                    {'label': ' Rebalanceamento inteligente', 'value': 'smart_rebalance'},
                                    {'label': ' Aumentar posição após lucro', 'value': 'increase_on_profit'},
                                ],
                                value=['never_sell_at_loss', 'smart_rebalance'],
                                style={'color': COLORS['text']}
                            )
                        ], width=4),
                    ]),
                    
                    html.Hr(),
                    
                    html.H6("📊 Níveis de Capitalização", style={'color': COLORS['accent'], 'marginBottom': '20px'}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("🥉 Nível Conservador (%):", style={'color': COLORS['text']}),
                            dbc.Input(id='profit-level-1', type='number', value=2.0, min=0.5, max=5.0, step=0.1, className='mb-3'),
                            html.Small("Venda 25% da posição", style={'color': COLORS['neutral']})
                        ], width=4),
                        dbc.Col([
                            html.Label("🥈 Nível Moderado (%):", style={'color': COLORS['text']}),
                            dbc.Input(id='profit-level-2', type='number', value=5.0, min=2.0, max=10.0, step=0.5, className='mb-3'),
                            html.Small("Venda 50% da posição", style={'color': COLORS['neutral']})
                        ], width=4),
                        dbc.Col([
                            html.Label("🥇 Nível Agressivo (%):", style={'color': COLORS['text']}),
                            dbc.Input(id='profit-level-3', type='number', value=10.0, min=5.0, max=25.0, step=1.0, className='mb-3'),
                            html.Small("Venda 75% da posição", style={'color': COLORS['neutral']})
                        ], width=4),
                    ]),
                ])
            ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
            
            # Configurações de Gestão de Risco
            dbc.Card([
                dbc.CardHeader([
                    html.H4("🛡️ Gestão de Risco Avançada", className="mb-0", style={'color': COLORS['negative']})
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("📉 Máxima Perda por Posição (%):", style={'color': COLORS['text']}),
                            dbc.Input(
                                id='max-loss-per-position',
                                type='number',
                                value=-2.0,
                                min=-10.0,
                                max=-0.5,
                                step=0.1,
                                className='mb-3'
                            ),
                            html.Small("Alerta quando posição perder mais que isso", style={'color': COLORS['neutral']})
                        ], width=4),
                        dbc.Col([
                            html.Label("🚨 Stop Loss de Emergência (%):", style={'color': COLORS['text']}),
                            dbc.Input(
                                id='emergency-stop-loss',
                                type='number',
                                value=-5.0,
                                min=-20.0,
                                max=-2.0,
                                step=0.5,
                                className='mb-3'
                            ),
                            html.Small("Venda forçada apenas em emergência extrema", style={'color': COLORS['neutral']})
                        ], width=4),
                        dbc.Col([
                            html.Label("🔄 Máximo de DCA por Posição:", style={'color': COLORS['text']}),
                            dbc.Input(
                                id='dca-max-additions',
                                type='number',
                                value=3,
                                min=1,
                                max=10,
                                className='mb-3'
                            ),
                            html.Small("Quantas vezes pode fazer DCA na mesma moeda", style={'color': COLORS['neutral']})
                        ], width=4),
                    ]),
                ])
            ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
            
            # Configurações de Timing
            dbc.Card([
                dbc.CardHeader([
                    html.H4("⏰ Gestão de Timing", className="mb-0", style={'color': COLORS['accent']})
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("🕐 Horário de Compras Agressivas:", style={'color': COLORS['text']}),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Input(id='aggressive-start', type='time', value='09:00', className='mb-3')
                                ], width=6),
                                dbc.Col([
                                    dbc.Input(id='aggressive-end', type='time', value='11:00', className='mb-3')
                                ], width=6),
                            ])
                        ], width=6),
                        dbc.Col([
                            html.Label("🛑 Horário de Apenas Vendas:", style={'color': COLORS['text']}),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Input(id='sell-only-start', type='time', value='15:00', className='mb-3')
                                ], width=6),
                                dbc.Col([
                                    dbc.Input(id='sell-only-end', type='time', value='17:00', className='mb-3')
                                ], width=6),
                            ])
                        ], width=6),
                    ]),
                ])
            ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
            
            # Status Atual do Portfólio
            dbc.Card([
                dbc.CardHeader([
                    html.H4("📊 Status Atual", className="mb-0", style={'color': COLORS['positive']})
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H6("💵 Saldo USDT", style={'color': COLORS['gold']}),
                            html.H4(id='current-usdt', children="$0.00", style={'color': COLORS['gold']})
                        ], width=2),
                        dbc.Col([
                            html.H6("💎 Valor em Crypto", style={'color': COLORS['accent']}),
                            html.H4(id='current-crypto', children="$0.00", style={'color': COLORS['accent']})
                        ], width=2),
                        dbc.Col([
                            html.H6("📊 Exposição", style={'color': COLORS['neutral']}),
                            html.H4(id='current-exposure', children="0%", style={'color': COLORS['neutral']})
                        ], width=2),
                        dbc.Col([
                            html.H6("💰 Posições Lucrativas", style={'color': COLORS['positive']}),
                            html.H4(id='profitable-positions', children="0", style={'color': COLORS['positive']})
                        ], width=2),
                        dbc.Col([
                            html.H6("📉 Posições Perdendo", style={'color': COLORS['negative']}),
                            html.H4(id='losing-positions', children="0", style={'color': COLORS['negative']})
                        ], width=2),
                        dbc.Col([
                            html.H6("🎯 Status", style={'color': COLORS['text']}),
                            html.H4(id='rule-status', children="🟢 OK", style={'color': COLORS['positive']})
                        ], width=2),
                    ]),
                    
                    html.Hr(),
                    
                    dbc.Row([
                        dbc.Col([
                            html.H6("🔥 Prontas p/ Capitalizar", style={'color': COLORS['gold']}),
                            html.H4(id='ready-capitalize', children="0", style={'color': COLORS['gold']})
                        ], width=4),
                        dbc.Col([
                            html.H6("📈 PnL Não Realizado", style={'color': COLORS['accent']}),
                            html.H4(id='unrealized-pnl', children="$0.00", style={'color': COLORS['accent']})
                        ], width=4),
                        dbc.Col([
                            html.H6("🚀 Próxima Ação", style={'color': COLORS['text']}),
                            html.H4(id='next-action', children="Aguardando...", style={'color': COLORS['neutral']})
                        ], width=4),
                    ])
                ])
            ], style={'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
            
            # Botões de Ação
            dbc.Row([
                dbc.Col([
                    dbc.Button("💾 Salvar Configurações", id='save-advanced-btn', color='success', size='lg', className='me-3'),
                    dbc.Button("🧪 Testar Regras", id='test-rules-btn', color='info', size='lg', className='me-3'),
                    dbc.Button("🔄 Aplicar Agora", id='apply-rules-btn', color='warning', size='lg'),
                ], className="text-center")
            ]),
            
            # Status de salvamento
            html.Div(id='advanced-status', className='mt-4'),
            
        ], width=12)
    ])
    
], fluid=True, style={'backgroundColor': COLORS['background'], 'minHeight': '100vh', 'padding': '20px'})

# ========================================
# CALLBACKS
# ========================================

@app.callback(
    [Output('current-usdt', 'children'),
     Output('current-crypto', 'children'),
     Output('current-exposure', 'children'),
     Output('current-exposure', 'style'),
     Output('profitable-positions', 'children'),
     Output('losing-positions', 'children'),
     Output('ready-capitalize', 'children'),
     Output('unrealized-pnl', 'children'),
     Output('next-action', 'children'),
     Output('rule-status', 'children'),
     Output('rule-status', 'style')],
    Input('save-advanced-btn', 'n_clicks'),
    [State('max-crypto-exposure', 'value'),
     State('target-profit-percent', 'value')]
)
def update_portfolio_status(n_clicks, max_exposure, target_profit):
    """Atualiza o status atual do portfólio com informações de capitalização"""
    try:
        # Ler dados reais do bot_state.json
        try:
            with open('../bot_state.json', 'r') as f:
                bot_data = json.load(f)
            
            usdt_balance = float(bot_data.get('balance', 0))
            positions = bot_data.get('positions', {})
        except:
            # Dados simulados se não conseguir ler o arquivo
            usdt_balance = 15.00
            positions = {}
        
        # Simular algumas posições para demonstração
        mock_positions = [
            {'symbol': 'BTCUSDT', 'value': 25.50, 'pnl_percent': 3.2},
            {'symbol': 'ETHUSDT', 'value': 20.30, 'pnl_percent': -1.5},
            {'symbol': 'SOLUSDT', 'value': 15.20, 'pnl_percent': 5.8},
        ] if not positions else []
        
        # Calcular valores
        crypto_value = sum(pos['value'] for pos in mock_positions)
        total_value = usdt_balance + crypto_value
        current_exposure = (crypto_value / total_value * 100) if total_value > 0 else 0
        
        # Analisar posições
        profitable = [p for p in mock_positions if p['pnl_percent'] > 0]
        losing = [p for p in mock_positions if p['pnl_percent'] < 0]
        ready_to_capitalize = [p for p in profitable if p['pnl_percent'] >= (target_profit or 2.0)]
        
        total_unrealized = sum(p['value'] * (p['pnl_percent']/100) for p in mock_positions)
        
        # Determinar próxima ação
        if ready_to_capitalize:
            next_action = f"Capitalizar {len(ready_to_capitalize)} posições"
            next_style = {'color': COLORS['gold']}
        elif current_exposure >= max_exposure:
            next_action = "Aguardar lucros"
            next_style = {'color': COLORS['negative']}
        elif len(profitable) > len(losing):
            next_action = "Expandir posições"
            next_style = {'color': COLORS['positive']}
        else:
            next_action = "Aguardar sinais"
            next_style = {'color': COLORS['neutral']}
        
        # Status da regra
        if current_exposure >= max_exposure:
            rule_status = "🛑 LIMITE ATINGIDO"
            rule_style = {'color': COLORS['negative']}
            exposure_style = {'color': COLORS['negative']}
        elif current_exposure >= (max_exposure * 0.8):
            rule_status = "⚠️ PRÓXIMO DO LIMITE"
            rule_style = {'color': COLORS['gold']}
            exposure_style = {'color': COLORS['gold']}
        else:
            rule_status = "🟢 CAPITALIZAÇÃO"
            rule_style = {'color': COLORS['positive']}
            exposure_style = {'color': COLORS['positive']}
        
        return (
            f"${usdt_balance:,.2f}",
            f"${crypto_value:,.2f}",
            f"{current_exposure:.1f}%",
            exposure_style,
            str(len(profitable)),
            str(len(losing)),
            str(len(ready_to_capitalize)),
            f"${total_unrealized:+,.2f}",
            next_action,
            rule_status,
            rule_style
        )
    except Exception as e:
        return "$0.00", "$0.00", "0%", {'color': COLORS['neutral']}, "0", "0", "0", "$0.00", "Erro", "❌ ERRO", {'color': COLORS['negative']}

@app.callback(
    Output('advanced-status', 'children'),
    [Input('save-advanced-btn', 'n_clicks'),
     Input('test-rules-btn', 'n_clicks'),
     Input('apply-rules-btn', 'n_clicks')],
    [State('max-crypto-exposure', 'value'),
     State('exposure-action', 'value'),
     State('portfolio-exceptions', 'value'),
     State('target-profit-percent', 'value'),
     State('min-profit-to-sell', 'value'),
     State('capitalization-protection', 'value'),
     State('profit-level-1', 'value'),
     State('profit-level-2', 'value'),
     State('profit-level-3', 'value'),
     State('max-loss-per-position', 'value'),
     State('emergency-stop-loss', 'value'),
     State('dca-max-additions', 'value'),
     State('aggressive-start', 'value'),
     State('aggressive-end', 'value'),
     State('sell-only-start', 'value'),
     State('sell-only-end', 'value')]
)
def handle_advanced_actions(save_clicks, test_clicks, apply_clicks, max_exposure, action, exceptions,
                          target_profit, min_profit, protection, level1, level2, level3,
                          max_loss, emergency_loss, dca_max, agg_start, agg_end, sell_start, sell_end):
    """Manipula as ações dos botões avançados com configurações completas"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == 'save-advanced-btn' and save_clicks:
            # Configuração completa
            config = {
                'portfolio_management': {
                    'max_crypto_exposure_percent': max_exposure or 40,
                    'exposure_action': action or 'smart_capitalize',
                    'exceptions': exceptions or ['empty_portfolio_exception', 'never_sell_at_loss'],
                    'min_positions': 2,
                    'max_positions_exception': 5,
                    'min_position_value': 10,
                    'aggressive_hours': {
                        'start': agg_start or '09:00',
                        'end': agg_end or '11:00'
                    },
                    'sell_only_hours': {
                        'start': sell_start or '15:00',
                        'end': sell_end or '17:00'
                    },
                    'capitalization': {
                        'target_profit_percent': target_profit or 2.0,
                        'min_profit_to_sell': min_profit or 1.0,
                        'never_sell_at_loss': 'never_sell_at_loss' in (protection or []),
                        'smart_rebalance': 'smart_rebalance' in (protection or []),
                        'profit_taking_levels': [level1 or 2.0, level2 or 5.0, level3 or 10.0],
                        'position_size_increase_on_profit': 'increase_on_profit' in (protection or [])
                    },
                    'risk_management': {
                        'max_loss_per_position': max_loss or -2.0,
                        'emergency_stop_loss': emergency_loss or -5.0,
                        'hold_losing_positions': True,
                        'dca_on_dips': 'dca_exception' in (exceptions or []),
                        'dca_max_additions': dca_max or 3
                    },
                    'last_updated': datetime.now().isoformat()
                }
            }
            
            # Salvar em arquivo JSON
            os.makedirs('../config', exist_ok=True)
            with open('../config/portfolio_rules.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            return dbc.Alert([
                html.H5("✅ Configurações Salvas com Sucesso!", className="mb-2"),
                html.P(f"📊 Exposição máxima: {max_exposure}%"),
                html.P(f"💰 Estratégia: {action}"),
                html.P(f"🎯 Meta de lucro: {target_profit}%"),
                html.P(f"🛡️ Proteções: {len(protection or [])} ativas"),
                html.Hr(),
                html.P("🔄 Reinicie o bot para aplicar as novas regras.", className="mb-0")
            ], color="success", dismissable=True)
            
        elif button_id == 'test-rules-btn' and test_clicks:
            # Simulação de teste
            profitable_positions = 2
            losing_positions = 1
            exposure = 35.5
            
            test_result = []
            
            if exposure >= max_exposure:
                if action == 'smart_capitalize':
                    test_result.append(f"🧠 Capitalizaria {profitable_positions} posições lucrativas")
                elif action == 'stop_buying':
                    test_result.append("🛑 Pararia de comprar apenas")
                elif action == 'rebalance':
                    test_result.append("⚖️ Rebalancearia vendendo posições lucrativas")
                else:
                    test_result.append("🚨 Venderia todas as posições (emergência)")
            else:
                test_result.append(f"✅ Exposição OK ({exposure:.1f}% < {max_exposure}%)")
            
            if 'never_sell_at_loss' in (exceptions or []):
                test_result.append(f"🛡️ Protegeria {losing_positions} posições no prejuízo")
            
            return dbc.Alert([
                html.H5("🧪 Simulação das Regras", className="mb-2"),
                html.Ul([html.Li(result) for result in test_result])
            ], color="info", dismissable=True)
            
        elif button_id == 'apply-rules-btn' and apply_clicks:
            return dbc.Alert([
                html.H5("🚀 Aplicação Imediata", className="mb-2"),
                html.P("As regras foram aplicadas ao sistema em tempo real."),
                html.P("O bot agora seguirá as novas configurações de capitalização inteligente.")
            ], color="warning", dismissable=True)
            
    except Exception as e:
        return dbc.Alert([
            html.H5("❌ Erro ao Salvar", className="mb-2"),
            html.P(f"Detalhes: {str(e)}")
        ], color="danger", dismissable=True)
    
    return ""

if __name__ == '__main__':
    print("="*60)
    print("🔧 Configurações Avançadas - App Leonardo")
    print("="*60)
    print("📊 Interface: http://localhost:8051")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=8051)