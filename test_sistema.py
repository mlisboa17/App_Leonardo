import json

# Ler saldos
with open('data/dashboard_balances.json', 'r') as f:
    data = json.load(f)

print("="*60)
print("📊 TESTE DO SISTEMA - STATUS ATUAL")
print("="*60)
print()
print("💰 SALDOS:")
print(f"  💵 USDT Livre: ${data['usdt_balance']:.2f}")
print(f"  🪙 Cryptos: ${data['crypto_balance']:.2f}")
print(f"  💎 Total: ${data['total_balance']:.2f}")
print(f"  📈 PnL: ${data['total_balance'] - data['initial_capital']:+.2f}")
print()
print("📦 POSIÇÕES:")
print(f"  🔢 Quantidade: {data.get('num_positions', 0)}")
print(f"  💰 Total Investido: ${data.get('total_invested', 0):.2f}")
print()
print("📅 DAILY:")
print(f"  💵 PnL Diário: ${data.get('daily_pnl', 0):.2f}")
print(f"  🎯 Progresso Meta: {data.get('daily_progress', 0):.1f}%")
print()
print("🕐 ÚLTIMA ATUALIZAÇÃO:")
print(f"  {data.get('last_update', 'N/A')}")
print()

# Mostrar algumas posições
if 'crypto_positions' in data and data['crypto_positions']:
    print("📊 TOP 3 POSIÇÕES:")
    positions = sorted(
        data['crypto_positions'].items(),
        key=lambda x: x[1]['pnl_pct'],
        reverse=True
    )[:3]
    
    for symbol, pos in positions:
        print(f"  {symbol}:")
        print(f"    Investido: ${pos['invested']:.2f}")
        print(f"    Valor Atual: ${pos['current_value']:.2f}")
        print(f"    PnL: ${pos['pnl_usd']:+.2f} ({pos['pnl_pct']:+.2f}%)")
        print()

print("="*60)
print("✅ SISTEMA OPERACIONAL")
print("🌐 Dashboard: http://localhost:8503")
print("="*60)
