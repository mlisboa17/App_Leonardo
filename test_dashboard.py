import sys
sys.path.insert(0, '.')
from main_multibot import MultiBotEngine
import json
from pathlib import Path

print('Before update:')
path = Path('data/dashboard_balances.json')
if path.exists():
    with open(path, 'r') as f:
        data = json.load(f)
    print(f'Timestamp: {data.get("timestamp")}')
    print(f'Crypto balance: {data.get("crypto_balance")}')

bot = MultiBotEngine()
bot._save_dashboard_data()

print('After update:')
if path.exists():
    with open(path, 'r') as f:
        data = json.load(f)
    print(f'Timestamp: {data.get("timestamp")}')
    print(f'Crypto balance: {data.get("crypto_balance")}')
    print(f'Crypto positions keys: {list(data.get("crypto_positions", {}).keys())}')