#!/usr/bin/env python3
"""
Script para sincronizar posições com o saldo real da Binance
Remove posições fantasmas do arquivo multibot_positions.json
"""
import json
from pathlib import Path

# Posições que existem de verdade na Binance (baseado no dashboard_balances.json)
REAL_POSITIONS = {
    "BTCUSDT": {"bot_type": "bot_estavel", "entry_price": 88996.48, "amount": 0.00056, "amount_usd": 50, "time": "2025-12-05T19:02:00.317018", "order_id": "53454795747"},
    "ETHUSDT": {"bot_type": "bot_estavel", "entry_price": 3015.63, "amount": 0.0165, "amount_usd": 50, "time": "2025-12-05T19:02:03.148682", "order_id": "40161509175"},
    "UNIUSDT": {"bot_type": "bot_estavel", "entry_price": 5.499, "amount": 9.09, "amount_usd": 50, "time": "2025-12-05T19:17:19.698365", "order_id": "4784689024"},
    "AAVEUSDT": {"bot_type": "bot_estavel", "entry_price": 183.46, "amount": 0.272, "amount_usd": 50, "time": "2025-12-05T19:17:22.766325", "order_id": "4904293172"},
    "SOLUSDT": {"bot_type": "bot_medio", "entry_price": 132.32, "amount": 0.302, "amount_usd": 40, "time": "2025-12-05T19:17:26.450944", "order_id": "15674748438"},
    "BNBUSDT": {"bot_type": "bot_medio", "entry_price": 880.3, "amount": 0.045, "amount_usd": 40, "time": "2025-12-05T19:17:29.625465", "order_id": "10422001360"},
    "DOTUSDT": {"bot_type": "bot_medio", "entry_price": 2.122, "amount": 30.63, "amount_usd": 65, "time": "2025-12-07T08:07:06.672002", "order_id": "5915729076"},
}

def main():
    positions_file = Path("data/multibot_positions.json")
    
    # Backup
    if positions_file.exists():
        backup = positions_file.read_text()
        Path("data/multibot_positions.json.backup").write_text(backup)
        print("✅ Backup criado")
    
    # Salva posições corretas
    with open(positions_file, 'w') as f:
        json.dump(REAL_POSITIONS, f, indent=2)
    
    print(f"✅ Salvo {len(REAL_POSITIONS)} posições reais")
    print("Posições:")
    for symbol in REAL_POSITIONS:
        print(f"   - {symbol}")

if __name__ == "__main__":
    main()
