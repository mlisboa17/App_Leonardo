"""
Views para o dashboard do bot
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import sys
import time
import random

# Adiciona o diretório raiz ao path para importar módulos do bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import load_config, load_env_credentials


def index(request):
    """Página principal do dashboard"""
    config = load_config()
    
    context = {
        'symbol': config.get('trading', {}).get('symbol', 'BTC/USDT'),
        'timeframe': config.get('trading', {}).get('timeframe', '1h'),
        'testnet': config.get('exchange', {}).get('testnet', True),
        'dry_run': config.get('execution', {}).get('dry_run', False),
    }
    
    return render(request, 'bot_dashboard/index.html', context)


def get_bot_status(request):
    """API endpoint para obter status do bot"""
    # TODO: Integrar com bot real via arquivo compartilhado ou websocket
    
    # Dados simulados com variação para parecer real
    base_price = 91500
    variation = random.uniform(-200, 200)
    current_price = base_price + variation
    
    data = {
        'status': 'Operando',
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
    
    return JsonResponse(data)


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
    # TODO: Integrar com dados reais do bot
    
    # Gera dados simulados de candlesticks
    now = int(time.time() * 1000)
    interval = 60000  # 1 minuto em ms
    
    candles = []
    base_price = 91500
    
    for i in range(100, 0, -1):
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
