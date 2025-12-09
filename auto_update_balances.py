"""
Auto-update de Saldos - Monitora mudanças e atualiza automaticamente
"""
import json
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from binance.client import Client
from datetime import datetime

# Credenciais
API_KEY = "R4So8k98GeMLDhNoMmAedjXjYnUBpxCVZKH9bNbMrM6lfbJzFlY9m3okEbXRuJqR"
API_SECRET = "n00KKGAVD7QXbOd3fkCRLXKWFK3PuVS8WUk6wtfpRT0UJG9qRYsay9Qt6LoUKwCN"
CAPITAL_INICIAL = 1000.0

class BalanceUpdater(FileSystemEventHandler):
    """Monitor de arquivos que atualiza saldos automaticamente"""
    
    def __init__(self):
        self.client = None
        self.last_update = 0
        self.cooldown = 2  # segundos entre atualizações
        
    def get_client(self):
        """Lazy loading do cliente Binance"""
        if not self.client:
            try:
                self.client = Client(API_KEY, API_SECRET)
                print("✅ Cliente Binance conectado")
            except Exception as e:
                print(f"⚠️ Erro ao conectar Binance: {e}")
        return self.client
    
    def on_modified(self, event):
        """Chamado quando um arquivo é modificado"""
        if event.is_directory:
            return
        
        # Verifica se é um dos arquivos monitorados
        filename = Path(event.src_path).name
        if filename in ['multibot_positions.json', 'multibot_history.json']:
            # Cooldown para evitar múltiplas atualizações
            now = time.time()
            if now - self.last_update < self.cooldown:
                return
            
            self.last_update = now
            print(f"\n🔄 {filename} modificado - Atualizando saldos...")
            self.update_balances()
    
    def get_current_prices(self, symbols):
        """Pega preços atuais via Binance"""
        client = self.get_client()
        if not client:
            return {}
        
        prices = {}
        for symbol in symbols:
            try:
                ticker = client.get_symbol_ticker(symbol=symbol)
                prices[symbol] = float(ticker['price'])
            except Exception as e:
                print(f"⚠️ Erro ao pegar preço de {symbol}: {e}")
                prices[symbol] = 0
        return prices
    
    def update_balances(self):
        """Atualiza dashboard_balances.json com valores reais"""
        try:
            # Carregar posições
            positions_file = Path("data/multibot_positions.json")
            if not positions_file.exists():
                return
            
            with open(positions_file, 'r') as f:
                positions = json.load(f)
            
            # Carregar histórico para PnL diário
            history_file = Path("data/multibot_history.json")
            history = []
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history = json.load(f)
            
            # Calcular PnL diário
            today = datetime.now().date().isoformat()
            daily_trades = [t for t in history if t.get('exit_time', t.get('timestamp', '')).startswith(today)]
            daily_pnl = sum(t.get('pnl_usd', 0) for t in daily_trades)
            
            if not positions:
                # Sem posições - todo capital em USDT
                balances = {
                    "usdt_balance": CAPITAL_INICIAL,
                    "crypto_balance": 0,
                    "total_balance": CAPITAL_INICIAL,
                    "crypto_positions": {},
                    "poupanca": 0,
                    "daily_target_pct": 1.0,
                    "daily_target_usd": 10.0,
                    "daily_pnl": round(daily_pnl, 2),
                    "daily_progress": (daily_pnl / 10.0 * 100) if daily_pnl > 0 else 0,
                    "initial_capital": CAPITAL_INICIAL,
                    "num_positions": 0,
                    "last_update": datetime.now().isoformat()
                }
            else:
                # Pegar preços atuais
                symbols = list(positions.keys())
                current_prices = self.get_current_prices(symbols)
                
                # Calcular valores
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
                        'current_value': round(current_value, 2),
                        'pnl_usd': round(pnl_usd, 2),
                        'pnl_pct': round(pnl_pct, 2),
                        'bot_type': pos.get('bot_type', 'unknown')
                    }
                
                usdt_balance = CAPITAL_INICIAL - total_invested
                crypto_balance = total_current_value
                total_balance = usdt_balance + crypto_balance
                
                balances = {
                    "usdt_balance": round(usdt_balance, 2),
                    "crypto_balance": round(crypto_balance, 2),
                    "total_balance": round(total_balance, 2),
                    "crypto_positions": crypto_positions_detail,
                    "poupanca": 0,
                    "daily_target_pct": 1.0,
                    "daily_target_usd": 10.0,
                    "daily_pnl": round(daily_pnl, 2),
                    "daily_progress": round((daily_pnl / 10.0 * 100), 2) if daily_pnl > 0 else 0,
                    "initial_capital": CAPITAL_INICIAL,
                    "total_invested": round(total_invested, 2),
                    "num_positions": len(positions),
                    "last_update": datetime.now().isoformat()
                }
                
                print(f"  💰 USDT: ${usdt_balance:.2f} | Cryptos: ${crypto_balance:.2f} | Total: ${total_balance:.2f}")
            
            # Salvar
            balances_file = Path("data/dashboard_balances.json")
            with open(balances_file, 'w', encoding='utf-8') as f:
                json.dump(balances, f, indent=2)
            
            print(f"  ✅ Saldos atualizados às {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"  ❌ Erro ao atualizar saldos: {e}")
            import traceback
            traceback.print_exc()


def start_monitor():
    """Inicia o monitor de arquivos"""
    print("="*60)
    print("🔍 AUTO-UPDATE DE SALDOS - INICIANDO")
    print("="*60)
    print("Monitorando arquivos:")
    print("  • data/multibot_positions.json")
    print("  • data/multibot_history.json")
    print("\nAtualizará automaticamente quando detectar mudanças...")
    print("Pressione Ctrl+C para parar\n")
    
    event_handler = BalanceUpdater()
    observer = Observer()
    
    # Monitorar diretório data/
    data_path = Path("data")
    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
    
    observer.schedule(event_handler, str(data_path), recursive=False)
    observer.start()
    
    # Fazer primeira atualização
    print("🔄 Fazendo primeira atualização...")
    event_handler.update_balances()
    print("\n✅ Monitor ativo! Aguardando mudanças...\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Parando monitor...")
        observer.stop()
    
    observer.join()
    print("✅ Monitor encerrado")


if __name__ == "__main__":
    start_monitor()
