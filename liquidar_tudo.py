"""
🔴 LIQUIDAR TODAS AS POSIÇÕES
==============================

Script para vender TODAS as criptomoedas e ficar apenas com USDT.
Execute apenas quando quiser começar do zero.

Uso:
    python liquidar_tudo.py

"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Carrega variáveis do .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

from src.core.exchange_client import ExchangeClient


def load_credentials():
    """Carrega credenciais do .env"""
    return {
        'api_key': os.getenv('BINANCE_TESTNET_API_KEY', ''),
        'api_secret': os.getenv('BINANCE_TESTNET_API_SECRET', '')
    }


def liquidar_tudo():
    """Vende todas as posições abertas"""
    
    print("\n" + "="*60)
    print("🔴 LIQUIDAÇÃO TOTAL - App Leonardo")
    print("="*60)
    
    # Confirmação
    print("\n⚠️  ATENÇÃO: Isso vai VENDER TODAS as criptomoedas!")
    resposta = input("   Digite 'SIM' para confirmar: ")
    
    if resposta.upper() != 'SIM':
        print("\n❌ Cancelado pelo usuário")
        return
    
    # Conecta à exchange
    print("\n📡 Conectando à Binance Testnet...")
    creds = load_credentials()
    exchange = ExchangeClient(
        exchange_name='binance', 
        api_key=creds['api_key'],
        api_secret=creds['api_secret'],
        testnet=True
    )
    
    # Obtém saldo
    print("💰 Obtendo saldos...")
    balance = exchange.fetch_balance()
    
    if not balance:
        print("❌ Erro ao obter saldo")
        return
    
    # Lista cryptos para vender
    cryptos_to_sell = []
    for asset, data in balance.items():
        # Ignora chaves especiais do ccxt
        if asset in ['info', 'free', 'used', 'total', 'timestamp', 'datetime']:
            continue
        
        if asset == 'USDT':
            if isinstance(data, dict):
                print(f"   💵 USDT: ${data.get('free', 0):.2f}")
            else:
                print(f"   💵 USDT: ${data:.2f}")
            continue
        
        # Obtém quantidade disponível
        if isinstance(data, dict):
            free = float(data.get('free', 0))
        elif isinstance(data, (int, float)):
            free = float(data)
        else:
            continue
        
        if free > 0.0001:  # Ignora valores muito pequenos
            cryptos_to_sell.append({
                'asset': asset,
                'symbol': f"{asset}USDT",
                'amount': free
            })
    
    if not cryptos_to_sell:
        print("\n✅ Nenhuma posição para liquidar!")
        return
    
    print(f"\n📊 {len(cryptos_to_sell)} posições encontradas:")
    
    total_vendido = 0
    
    for crypto in cryptos_to_sell:
        symbol = crypto['symbol']
        amount = crypto['amount']
        
        try:
            # Obtém preço atual
            ticker = exchange.fetch_ticker(symbol)
            if not ticker:
                print(f"   ⚠️ {symbol}: Não conseguiu obter preço")
                continue
            
            price = ticker.get('last', ticker.get('close', 0))
            value = amount * price
            
            print(f"\n   💰 {symbol}:")
            print(f"      Quantidade: {amount:.6f}")
            print(f"      Preço: ${price:.4f}")
            print(f"      Valor: ${value:.2f}")
            
            # Executa venda
            order = exchange.create_market_order(
                symbol=symbol,
                side='sell',
                amount=amount
            )
            
            if order:
                print(f"      ✅ VENDIDO!")
                total_vendido += value
            else:
                print(f"      ❌ Falha na venda")
                
        except Exception as e:
            print(f"   ❌ {symbol}: Erro - {e}")
    
    # Resultado final
    print("\n" + "="*60)
    print("📊 RESULTADO DA LIQUIDAÇÃO")
    print("="*60)
    print(f"   Total vendido: ${total_vendido:.2f}")
    
    # Saldo final
    balance_final = exchange.fetch_balance()
    if balance_final:
        usdt = balance_final.get('USDT', {}).get('free', 0)
        print(f"   Saldo USDT final: ${usdt:.2f}")
    
    print("\n✅ Liquidação concluída!")
    print("="*60)


if __name__ == "__main__":
    liquidar_tudo()
