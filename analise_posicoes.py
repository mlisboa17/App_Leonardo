"""
Analisa posições e verifica quais estão perto de vender
"""
import json
from datetime import datetime

# Carregar posições
positions = json.load(open('data/multibot_positions.json'))
dashboard = json.load(open('data/dashboard_balances.json'))

# Take Profits por bot
TP = {
    'bot_estavel': 1.8,
    'bot_medio': 2.3,
    'bot_volatil': 3.0,
    'bot_meme': 4.0
}

SL = {
    'bot_estavel': -1.2,
    'bot_medio': -1.5,
    'bot_volatil': -2.0,
    'bot_meme': -2.5
}

print("="*70)
print("📊 ANÁLISE DE POSIÇÕES - DISTÂNCIA DO TAKE PROFIT")
print("="*70)
print()

results = []

for symbol, pos in positions.items():
    bot = pos['bot_type']
    entry = pos['entry_price']
    amount_usd = pos['amount_usd']
    entry_time = datetime.fromisoformat(pos['time'])
    minutes_open = (datetime.now() - entry_time).total_seconds() / 60
    
    # Pegar preço atual
    coin = symbol.replace('USDT', '')
    current_data = dashboard.get('crypto_positions', {}).get(coin, {})
    current_price = current_data.get('price', entry)
    current_value = current_data.get('value_usd', amount_usd)
    
    # Calcular PnL
    pnl_pct = ((current_price - entry) / entry) * 100
    pnl_usd = current_value - amount_usd
    
    # Distância para TP e SL
    tp = TP[bot]
    sl = SL[bot]
    dist_tp = tp - pnl_pct  # Quanto falta para TP
    dist_sl = pnl_pct - sl  # Quanto falta para SL
    
    results.append({
        'symbol': symbol,
        'bot': bot,
        'pnl_pct': pnl_pct,
        'pnl_usd': pnl_usd,
        'dist_tp': dist_tp,
        'tp': tp,
        'sl': sl,
        'minutes': minutes_open,
        'amount_usd': amount_usd
    })

# Ordenar por mais perto do TP
results.sort(key=lambda x: x['dist_tp'])

print(f"{'SYMBOL':<12} {'BOT':<12} {'PnL%':>8} {'PnL$':>8} {'TP':>6} {'Falta':>8} {'Tempo':>8}")
print("-"*70)

perto_vender = []
for r in results:
    status = ""
    if r['dist_tp'] < 0.5:
        status = "🟢 MUITO PERTO!"
        perto_vender.append(r)
    elif r['dist_tp'] < 1.0:
        status = "🟡 Perto"
        perto_vender.append(r)
    elif r['pnl_pct'] < r['sl'] + 0.5:
        status = "🔴 Perto do SL!"
    
    print(f"{r['symbol']:<12} {r['bot'].replace('bot_',''):<12} {r['pnl_pct']:>+7.2f}% ${r['pnl_usd']:>+6.2f} {r['tp']:>5.1f}% {r['dist_tp']:>+7.2f}% {r['minutes']:>6.0f}m {status}")

print()
print("="*70)
print("📋 RESUMO")
print("="*70)

total_pnl = sum(r['pnl_usd'] for r in results)
print(f"\nPnL Total Aberto: ${total_pnl:+.2f}")
print(f"Posições: {len(results)}")

if perto_vender:
    print(f"\n🎯 POSIÇÕES PERTO DE VENDER ({len(perto_vender)}):")
    for r in perto_vender:
        print(f"   {r['symbol']}: PnL {r['pnl_pct']:+.2f}% | Falta {r['dist_tp']:.2f}% para TP {r['tp']}%")
else:
    print("\n⚠️ Nenhuma posição muito perto do Take Profit ainda")
    print("   As posições precisam subir mais para atingir os novos TPs maiores")
