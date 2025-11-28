"""
Views para o dashboard do bot
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os
import sys
import time
import random

# Adiciona o diretório raiz ao path para importar módulos do bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import load_config, load_env_credentials


def add_cors_headers(response):
    """Adiciona headers CORS para permitir requisições"""
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


def index(request):
    """Página principal do dashboard"""
    config = load_config()
    
    # Carrega dados do bot se disponível
    try:
        state_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot_state.json')
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                bot_data = json.load(f)
        else:
            bot_data = {
                'balance': 0,
                'current_price': 0,
                'daily_pnl': 0,
                'total_pnl': 0,
                'rsi': 0,
                'position': 'AGUARDANDO',
                'status': 'Parado',
                'last_signal': 'Bot não iniciado'
            }
        
        # Carrega histórico persistente
        history_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot_history.json')
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history_data = json.load(f)
                # Mescla dados de histórico (trades) com estado atual (preços)
                bot_data['total_trades'] = history_data.get('total_trades', bot_data.get('total_trades', 0))
                bot_data['winning_trades'] = history_data.get('winning_trades', bot_data.get('winning_trades', 0))
                bot_data['losing_trades'] = history_data.get('losing_trades', bot_data.get('losing_trades', 0))
                bot_data['daily_pnl'] = history_data.get('daily_pnl', bot_data.get('daily_pnl', 0))
                bot_data['recent_trades'] = history_data.get('recent_trades', bot_data.get('recent_trades', []))
                bot_data['trades_by_symbol'] = history_data.get('trades_by_symbol', bot_data.get('trades_by_symbol', {}))
                bot_data['history_loaded'] = True
    except:
        bot_data = {
            'balance': 0,
            'current_price': 0,
            'daily_pnl': 0,
            'total_pnl': 0,
            'rsi': 0,
            'position': 'AGUARDANDO',
            'status': 'Erro',
            'last_signal': 'Erro ao carregar dados',
            'history_loaded': False
        }
    
    context = {
        'symbol': config.get('trading', {}).get('symbol', 'BTC/USDT'),
        'timeframe': config.get('trading', {}).get('timeframe', '1h'),
        'testnet': config.get('exchange', {}).get('testnet', True),
        'dry_run': config.get('execution', {}).get('dry_run', False),
        'bot_data': bot_data,
    }
    
    return render(request, 'bot_dashboard/simple.html', context)


def dashboard_old(request):
    """Dashboard antigo (complexo)"""
    config = load_config()
    
    try:
        state_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot_state.json')
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                bot_data = json.load(f)
        else:
            bot_data = {
                'balance': 0,
                'current_price': 0,
                'daily_pnl': 0,
                'total_pnl': 0,
                'rsi': 0,
                'position': 'AGUARDANDO',
                'status': 'Parado',
                'last_signal': 'Bot não iniciado'
            }
    except:
        bot_data = {
            'balance': 0,
            'current_price': 0,
            'daily_pnl': 0,
            'total_pnl': 0,
            'rsi': 0,
            'position': 'AGUARDANDO',
            'status': 'Erro',
            'last_signal': 'Erro ao carregar dados'
        }
    
    context = {
        'symbol': config.get('trading', {}).get('symbol', 'BTC/USDT'),
        'timeframe': config.get('trading', {}).get('timeframe', '1h'),
        'testnet': config.get('exchange', {}).get('testnet', True),
        'dry_run': config.get('execution', {}).get('dry_run', False),
        'bot_data': bot_data,
    }
    
    return render(request, 'bot_dashboard/index.html', context)


def test(request):
    """Página de teste simples"""
    return render(request, 'bot_dashboard/test.html')


def live(request):
    """Dashboard ao vivo simplificado"""
    return render(request, 'bot_dashboard/live.html')


@csrf_exempt
def get_bot_status(request):
    """API endpoint para obter status do bot"""
    try:
        # Tenta ler estado real do bot
        state_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot_state.json')
        
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                data = json.load(f)
                response = JsonResponse(data)
                return add_cors_headers(response)
        else:
            # Bot não está rodando - carrega histórico se disponível
            history_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot_history.json')
            
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    # Usa dados do histórico, mas marca como bot parado
                    data = {
                        'status': 'Parado',
                        'balance': 0,
                        'current_price': 0,  # Preço desatualizado
                        'position': 'AGUARDANDO',
                        'last_signal': 'Bot parado - dados do histórico',
                        'rsi': 0,
                        'kill_switch_active': False,
                        'timestamp': int(time.time() * 1000),
                        'is_running': False,
                        'history_loaded': True,
                        # Dados do histórico
                        'total_trades': history_data.get('total_trades', 0),
                        'winning_trades': history_data.get('winning_trades', 0),
                        'losing_trades': history_data.get('losing_trades', 0),
                        'daily_pnl': history_data.get('daily_pnl', 0),
                        'recent_trades': history_data.get('recent_trades', []),
                        'trades_by_symbol': history_data.get('trades_by_symbol', {}),
                        'last_buy_price': history_data.get('last_buy_price', 0),
                        'last_sell_price': history_data.get('last_sell_price', 0),
                    }
                    response = JsonResponse(data)
                    return add_cors_headers(response)
            
            # Nem bot nem histórico disponível
            data = {
                'status': 'Parado',
                'balance': 0,
                'daily_pnl': 0,
                'total_pnl': 0,
                'current_price': 0,
                'position': 'AGUARDANDO',
                'trades_count': 0,
                'wins': 0,
                'losses': 0,
                'last_signal': 'Bot não está rodando',
                'rsi': 0,
                'macd': 0,
                'macd_signal': 0,
                'sma_20': 0,
                'sma_50': 0,
                'sma_200': 0,
                'kill_switch_active': False,
                'timestamp': int(time.time() * 1000),
                'is_running': False,
                'history_loaded': False
            }
            response = JsonResponse(data)
            return add_cors_headers(response)
    except Exception as e:
        # Erro ao ler arquivo - retorna dados simulados com variação
        base_price = 91500
        variation = random.uniform(-200, 200)
        current_price = base_price + variation
        
        data = {
            'status': 'Simulação',
            'balance': 10050.50 + random.uniform(-10, 10),
            'daily_pnl': 50.50 + random.uniform(-5, 5),
            'total_pnl': 550.50,
            'current_price': current_price,
            'position': random.choice(['LONG', 'AGUARDANDO', 'SHORT']),
            'trades_count': 15,
            'wins': 10,
            'losses': 5,
            'last_signal': 'COMPRA: RSI em sobrevenda (28.5)',
            'rsi': 30 + random.uniform(0, 40),
            'macd': 150.23 + random.uniform(-20, 20),
            'macd_signal': 145.10 + random.uniform(-20, 20),
            'sma_20': current_price - 500,
            'sma_50': current_price - 1000,
            'sma_200': current_price - 3000,
            'kill_switch_active': False,
            'timestamp': int(time.time() * 1000),
        }
        
        response = JsonResponse(data)
        return add_cors_headers(response)


def get_config(request):
    """API endpoint para obter configurações"""
    config = load_config()
    return JsonResponse(config)


@csrf_exempt
def update_config(request):
    """API endpoint para atualizar configurações"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # TODO: Salvar configurações
            return JsonResponse({'success': True, 'message': 'Configuração atualizada'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


def get_price_history(request):
    """API endpoint para obter histórico de preços para gráfico"""
    try:
        # Tenta ler dados reais do bot se disponível
        state_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot_state.json')
        
        base_price = 91500  # Preço padrão
        
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
                base_price = state.get('current_price', 91500)
        
        # Gera dados simulados de candlesticks baseado no preço atual
        # ÚLTIMOS 10 MINUTOS (10 candles de 1 minuto)
        now = int(time.time())
        interval = 60  # 1 minuto
        
        candles = []
        
        for i in range(10, 0, -1):
            timestamp = now - (i * interval)
            
            # Simula movimento de preço
            open_price = base_price + random.uniform(-100, 100)
            close_price = open_price + random.uniform(-50, 50)
            high_price = max(open_price, close_price) + random.uniform(0, 30)
            low_price = min(open_price, close_price) - random.uniform(0, 30)
            
            candles.append({
                'time': timestamp,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
            })
            
            base_price = close_price  # Próximo candle começa onde o anterior terminou
        
        return JsonResponse({'candles': candles})
    except Exception as e:
        # Fallback para dados simulados
        now = int(time.time())
        interval = 60
        candles = []
        base_price = 91500
        
        for i in range(10, 0, -1):
            timestamp = now - (i * interval)
            open_price = base_price + random.uniform(-100, 100)
            close_price = open_price + random.uniform(-50, 50)
            high_price = max(open_price, close_price) + random.uniform(0, 30)
            low_price = min(open_price, close_price) - random.uniform(0, 30)
            
            candles.append({
                'time': timestamp,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
            })
            
            base_price = close_price
        
        return JsonResponse({'candles': candles})
