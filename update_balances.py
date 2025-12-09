"""
Atualiza dashboard_balances.json com valores reais das posições
"""
import json
from pathlib import Path
from binance.client import Client

# Credenciais diretas
API_KEY = "R4So8k98GeMLDhNoMmAedjXjYnUBpxCVZKH9bNbMrM6lfbJzFlY9m3okEbXRuJqR"
API_SECRET = "n00KKGAVD7QXbOd3fkCRLXKWFK3PuVS8WUk6wtfpRT0UJG9qRYsay9Qt6LoUKwCN"

CAPITAL_INICIAL = 1000.0

def get_current_prices(client, symbols):
    """Pega preços atuais dos símbolos"""
    prices = {}
    for symbol in symbols:
        try:
            ticker = client.get_symbol_ticker(symbol=symbol)
            prices[symbol] = float(ticker['price'])
        except:
            prices[symbol] = 0
    return prices

def calculate_balances():
    """Calcula saldos reais"""
    print("🔄 Atualizando saldos...")
    
    # Carregar posições
    positions_file = Path("data/multibot_positions.json")
    if not positions_file.exists():
        print("❌ Arquivo de posições não encontrado!")
        return
    
    with open(positions_file, 'r') as f:
        positions = json.load(f)
    
    if not positions:
        print("ℹ️ Nenhuma posição aberta")
        balances = {
            "usdt_balance": CAPITAL_INICIAL,
            "crypto_balance": 0,
            "total_balance": CAPITAL_INICIAL,
            "crypto_positions": {},
            "poupanca": 0,
            "daily_target_pct": 1.0,
            "daily_target_usd": 10.0,
            "daily_pnl": 0,
            "daily_progress": 0,
            "initial_capital": CAPITAL_INICIAL
        }
    else:
        # Conectar Binance para pegar preços atuais
        print("🔗 Conectando com Binance...")
        try:
            client = Client(API_KEY, API_SECRET)
            symbols = list(positions.keys())
            current_prices = get_current_prices(client, symbols)
            print(f"✅ Preços obtidos para {len(current_prices)} símbolos")
        except Exception as e:
            print(f"⚠️ Erro ao conectar Binance, usando preços de entrada: {e}")
            current_prices = {symbol: pos['entry_price'] for symbol, pos in positions.items()}
        
        # Calcular valor total em cryptos
        total_invested = 0
        total_current_value = 0
        crypto_positions_detail = {}
        
        for symbol, pos in positions.items():
            invested = pos.get('amount_usd', 0)
            amount = pos.get('amount', 0)
            entry_price = pos.get('entry_price', 0)
            current_price = current_prices.get(symbol, entry_price)
            
            current_value = amount * current_price
            pnl_usd = current_value - invested
            pnl_pct = (pnl_usd / invested * 100) if invested > 0 else 0
            
            total_invested += invested
            total_current_value += current_value
            
            crypto_positions_detail[symbol] = {
                'amount': amount,
                'entry_price': entry_price,
                'current_price': current_price,
                'invested': invested,
                'current_value': current_value,
                'pnl_usd': pnl_usd,
                'pnl_pct': pnl_pct,
                'bot_type': pos.get('bot_type', 'unknown')
            }
            
            print(f"  • {symbol}: ${invested:.2f} → ${current_value:.2f} ({pnl_pct:+.2f}%)")
        
        # Calcular saldos
        usdt_balance = CAPITAL_INICIAL - total_invested
        crypto_balance = total_current_value
        total_balance = usdt_balance + crypto_balance
        
        print(f"\n💰 RESUMO:")
        print(f"  • USDT Livre: ${usdt_balance:.2f}")
        print(f"  • Valor em Cryptos: ${crypto_balance:.2f}")
        print(f"  • TOTAL: ${total_balance:.2f}")
        print(f"  • PnL: ${total_balance - CAPITAL_INICIAL:+.2f}")
        
        balances = {
            "usdt_balance": round(usdt_balance, 2),
            "crypto_balance": round(crypto_balance, 2),
            "total_balance": round(total_balance, 2),
            "crypto_positions": crypto_positions_detail,
            "poupanca": 0,
            "daily_target_pct": 1.0,
            "daily_target_usd": 10.0,
            "daily_pnl": 0,
            "daily_progress": 0,
            "initial_capital": CAPITAL_INICIAL,
            "total_invested": round(total_invested, 2),
            "num_positions": len(positions)
        }
    
    # Salvar
    balances_file = Path("data/dashboard_balances.json")
    with open(balances_file, 'w', encoding='utf-8') as f:
        json.dump(balances, f, indent=2)
    
    print(f"\n✅ Saldos atualizados em {balances_file}")
    return balances

if __name__ == "__main__":
    calculate_balances()
