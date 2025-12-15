#!/usr/bin/env python3
"""
Script para fechar posições via Binance API
Usa as credenciais do .env
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Carregar .env
load_dotenv('/home/ubuntu/App_Leonardo/.env')

# Tentar importar ccxt
try:
    import ccxt
except:
    print("❌ CCXT não instalado. Instalando...")
    os.system('. /home/ubuntu/App_Leonardo/venv/bin/activate && pip install ccxt -q')
    import ccxt

def fechar_posicoes():
    """Fecha todas as posições abertas"""
    
    print("=" * 70)
    print("🔴 FECHANDO TODAS AS POSIÇÕES ABERTAS")
    print("=" * 70)
    
    # Credenciais
    # API da conta principal (direto no código - para produção, use .env)
    api_key = "ontC9l8pk3yvMEWdX9T7TUXg8j02iM2VLlp34dDp4pUiPvb7xANafPNKuydItiLr"
    api_secret = "efv9oyLoaqVRLe1fwVtJHUADgN10MBdVF5WzrqF8XxAjF8t0xKr187rvMi0f414b"
    if not api_key or not api_secret:
        print("❌ Configure a chave secreta da API da conta principal no script!")
        return False
    
    # Conectar
    print("\n🔗 Conectando à Binance...")
    try:
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    
    print("✅ Conectado à Binance")
    
    # Carregar posições
    positions_file = Path('/home/ubuntu/App_Leonardo/data/multibot_positions.json')
    
    if not positions_file.exists():
        print("❌ Arquivo de posições não encontrado!")
        return False
    
    with open(positions_file, 'r', encoding='utf-8') as f:
        positions = json.load(f)
    
    if not positions:
        print("ℹ️  Nenhuma posição aberta!")
        return True
    
    print(f"\n📍 {len(positions)} posições encontradas:\n")
    
    total_valor = 0
    for symbol, data in positions.items():
        valor = data.get('amount_usd', 0)
        total_valor += valor
        print(f"  • {symbol}: {data['amount']:.4f} units @ ${data['entry_price']:.4f} = ${valor:.2f}")
    
    print(f"\n💰 Valor total bloqueado: ${total_valor:.2f}")
    
    print("\n" + "=" * 70)
    print("⚠️  CONFIRMAÇÃO")
    print("=" * 70)
    print("Isso vai VENDER TODAS as posições acima!")
    print("Digite 'SIM' para confirmar (case-sensitive):")
    
    resp = input("> ").strip()
    
    if resp != "SIM":
        print("❌ Cancelado!")
        return False
    
    print("\n🚀 Iniciando fechamento...\n")
    
    # Fechar cada posição
    closed = 0
    failed = 0
    total_realizado = 0
    
    for symbol, data in positions.items():
        amount = float(data.get('amount', 0))
        entry_price = float(data.get('entry_price', 0))
        
        if amount <= 0:
            print(f"⏭️  {symbol}: Amount 0, ignorando")
            continue
        
        print(f"📤 Vendendo {symbol}...", end=" ")
        sys.stdout.flush()
        
        try:
            # Obter preço atual
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Formatar quantidade (remover zeros)
            amount_rounded = exchange.amount_to_precision(symbol, amount)
            
            # Criar ordem de venda
            order = exchange.create_market_sell_order(
                symbol,
                float(amount_rounded),
                params={}
            )
            
            valor_venda = current_price * float(amount_rounded)
            profit_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            
            print(f"✅")
            print(f"   └─ {float(amount_rounded):.4f} @ ${current_price:.4f} = ${valor_venda:.2f}")
            print(f"   └─ Lucro: {profit_pct:+.2f}% | Order: {order.get('id', 'N/A')}")
            
            closed += 1
            total_realizado += valor_venda
            
        except Exception as e:
            print(f"❌")
            print(f"   └─ Erro: {str(e)[:60]}")
            failed += 1
    
    # Atualizar arquivo
    with open(positions_file, 'w') as f:
        json.dump({}, f)
    
    print("\n" + "=" * 70)
    print("✅ FECHAMENTO CONCLUÍDO!")
    print("=" * 70)
    print(f"📊 Posições fechadas: {closed}")
    print(f"❌ Erros: {failed}")
    print(f"💰 Total realizado: ${total_realizado:.2f}")
    print("=" * 70)
    print("\n🎉 Capital liberado! Bot está pronto para novos trades.\n")
    
    return True

if __name__ == "__main__":
    try:
        fechar_posicoes()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
