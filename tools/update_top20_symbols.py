"""Fetch top 20 symbols by 24h quote volume from Binance and update config/config.yaml symbols list."""
import os
import sys
import yaml
from pathlib import Path

# Make project importable
proj_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(proj_root))

from src.core.exchange_client import ExchangeClient

CONFIG_PATH = Path('config/config.yaml')

client = ExchangeClient()  # will use config/.env credentials if needed
try:
    tickers = client.fetch_tickers()  # expects a mapping
except Exception as e:
    print('Failed to fetch tickers:', e)
    tickers = {}

# Compute top20 by quoteVolume (USD/USDT quote)
vols = []
for sym, t in (tickers or {}).items():
    try:
        qv = float(t.get('quoteVolume') or t.get('quoteVolume24h') or 0)
        if sym.endswith('USDT'):
            vols.append((sym.replace('/', '') if '/' in sym else sym, qv))
    except Exception:
        continue

vols = sorted(vols, key=lambda x: x[1], reverse=True)[:20]
# Convert to CCXT symbol format 'BTC/USDT'
top20 = [s[:-4] + '/USDT' if s.endswith('USDT') else s for s, _ in vols]

if not top20:
    print('No top20 detected, aborting')
    sys.exit(1)

print('Top 20 detected:', top20)
# Load config and update symbols
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

cfg.setdefault('trading', {})
cfg['trading']['symbols'] = top20

with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)

print('config/config.yaml updated with top20 symbols')
