#!/usr/bin/env python3
"""
Script para verificar e vender cryptos fora do portfolio
"""
import ccxt
import json
import time
import os
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

# Portfolio da Opcao A
PORTFOLIO_NOVO = ['BTC', 'ETH', 'BNB', 'SOL', 'DOT', 'UNI', 'AAVE', 'XRP', 'DOGE']
IGNORAR = ['USDT', 'USD', 'BRL', 'BUSD']

def main():
    # Conecta Binance usando variaveis de ambiente
    exchange = ccxt.binance({
        'apiKey': os.getenv('BINANCE_API_KEY'),
        'secret': os.getenv('BINANCE_API_SECRET')
    })
    
    print("\n" + "="*50)
    print("   VERIFICACAO DE SALDOS BINANCE")
    print("="*50)
    
    # Busca saldos
    balance = exchange.fetch_balance()
    
    manter = []
    vender = []
    
    for coin, amount in balance['total'].items():
        if amount > 0.0001 and coin not in IGNORAR:
            try:
                ticker = exchange.fetch_ticker(f'{coin}/USDT')
                valor_usd = amount * ticker['last']
                
                if valor_usd > 1:  # Mais que $1
                    info = {
                        'coin': coin,
                        'amount': amount,
                        'price': ticker['last'],
                        'valor_usd': valor_usd
                    }
                    
                    if coin in PORTFOLIO_NOVO:
                        manter.append(info)
                    else:
                        vender.append(info)
            except:
                pass
    
    print("\n✅ MANTER (no portfolio):")
    total_manter = 0
    for c in manter:
        print(f"   {c['coin']}: {c['amount']:.6f} = ${c['valor_usd']:.2f}")
        total_manter += c['valor_usd']
    print(f"   TOTAL: ${total_manter:.2f}")
    
    print("\n🔴 VENDER (fora do portfolio):")
    total_vender = 0
    for c in vender:
        print(f"   {c['coin']}: {c['amount']:.6f} = ${c['valor_usd']:.2f}")
        total_vender += c['valor_usd']
    print(f"   TOTAL: ${total_vender:.2f}")
    
    # Pergunta se quer vender
    if vender:
        print("\n" + "="*50)
        resposta = input("Deseja VENDER todas as cryptos fora do portfolio? (s/n): ")
        
        if resposta.lower() == 's':
            print("\n🚀 Vendendo...")
            for c in vender:
                try:
                    symbol = f"{c['coin']}/USDT"
                    market = exchange.market(symbol)
                    qty = exchange.amount_to_precision(symbol, c['amount'] * 0.999)
                    
                    if float(qty) > 0:
                        order = exchange.create_market_sell_order(symbol, qty)
                        print(f"   ✅ VENDIDO: {c['coin']} - {qty} = ~${c['valor_usd']:.2f}")
                        time.sleep(0.5)
                except Exception as e:
                    print(f"   ❌ Erro {c['coin']}: {e}")
            
            print("\n✅ Vendas concluidas!")
            
            # Atualiza arquivo de posicoes
            print("\n📝 Atualizando arquivo de posicoes...")
            with open('data/multibot_positions.json', 'r') as f:
                positions = json.load(f)
            
            # Remove posicoes vendidas
            coins_vendidas = [c['coin'] + 'USDT' for c in vender]
            positions_new = {k: v for k, v in positions.items() if k not in coins_vendidas}
            
            with open('data/multibot_positions.json', 'w') as f:
                json.dump(positions_new, f, indent=2)
            
            print(f"   Posicoes restantes: {len(positions_new)}")
            for k in positions_new.keys():
                print(f"      - {k}")
        else:
            print("\nOperacao cancelada.")
    else:
        print("\n✅ Nenhuma crypto para vender!")
    
    # Mostra USDT disponivel
    usdt = balance['total'].get('USDT', 0)
    print(f"\n💰 USDT disponivel: ${usdt:.2f}")
    print("="*50)

if __name__ == "__main__":
    main()
