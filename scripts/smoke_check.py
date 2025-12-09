"""Smoke check script for R7 project.
Verifies presence of key data/config files and minimal fields in trade history.
Run: python scripts/smoke_check.py
"""
import json
from pathlib import Path
import sys

FILES = [
    Path('data/all_trades_history.json'),
    Path('data/dashboard_balances.json'),
    Path('data/coordinator_stats.json'),
    Path('config/bots_config.yaml')
]

REQ_TRADE_KEYS = [
    ('side', 'type'),
    ('price', 'exit_price'),
    ('qty', 'quantity'),
    ('fee', 'exchange_fee'),
    ('pnl_usd', 'profit_loss'),
    ('timestamp', 'time', 'date')
]


def check_files():
    ok = True
    print('Checking presence of key files:')
    for p in FILES:
        exists = p.exists()
        print(f' - {p}: {'FOUND' if exists else 'MISSING'}')
        if not exists:
            ok = False
    return ok


def check_trades_file(path: Path):
    if not path.exists():
        print('Trades file not found, skipping trade content checks.')
        return False
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f'Error loading {path}: {e}')
        return False

    if not isinstance(data, list):
        print(f'Unexpected format: {path} is not a list (found {type(data).__name__})')
        return False

    total = len(data)
    print(f'Loaded {total} trade records from {path}')
    sample = data[-20:] if total >= 20 else data

    missing_counts = {k: 0 for k in range(len(REQ_TRADE_KEYS))}
    for i, t in enumerate(sample):
        for idx, key_group in enumerate(REQ_TRADE_KEYS):
            if not any(k in t for k in key_group):
                missing_counts[idx] += 1

    print('\nSample field presence check (last {} records):'.format(len(sample)))
    for idx, key_group in enumerate(REQ_TRADE_KEYS):
        keys = '/'.join(key_group)
        miss = missing_counts[idx]
        print(f' - {keys}: missing in {miss}/{len(sample)} sample records')

    # Show first sample record for inspection
    if sample:
        print('\nFirst sample record (truncated):')
        rec = sample[-1]
        out = {k: rec.get(k) for group in REQ_TRADE_KEYS for k in group if k in rec}
        print(json.dumps(out, indent=2, ensure_ascii=False)[:2000])
    return True


if __name__ == '__main__':
    print('SMOKE CHECK - R7 Project')
    files_ok = check_files()
    trades_ok = check_trades_file(Path('data/all_trades_history.json'))

    if files_ok and trades_ok:
        print('\nSmoke check: PASSED')
        sys.exit(0)
    else:
        print('\nSmoke check: WARN/FAILED (see messages above)')
        sys.exit(2)
