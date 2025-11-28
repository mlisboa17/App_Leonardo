"""
Bot de Trading Leonardo - Main
Arquivo principal de execução
"""
import sys
import time
import logging
import pandas as pd
import json
import os
from datetime import datetime
from rich.live import Live

# Imports do projeto
from src.core import ExchangeClient, load_config, load_env_credentials, setup_logging
from src.core.dashboard import TradingDashboard
from src.safety import SafetyManager
from src.indicators import TechnicalIndicators
from src.strategies import SimpleRSIStrategy

logger = logging.getLogger(__name__)


class TradingBot:
    """Bot de Trading Principal"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        # Carrega configurações
        self.config = load_config(config_path)
        self.credentials = load_env_credentials()
        
        # Setup de logs
        setup_logging(
            log_level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=self.config.get('logging', {}).get('file', 'logs/trading_bot.log')
        )
        
        # Parâmetros de trading
        self.symbols = self.config['trading'].get('symbols', [self.config['trading'].get('symbol', 'BTC/USDT')])
        if isinstance(self.symbols, str):
            self.symbols = [self.symbols]
        self.timeframe = self.config['trading']['timeframe']
        self.amount_per_trade = self.config['trading']['amount_per_trade']
        
        # Parâmetros de execução
        self.interval_seconds = self.config.get('execution', {}).get('interval_seconds', 60)
        self.dry_run = self.config.get('execution', {}).get('dry_run', False)
        
        # Inicializa componentes
        self._init_exchange()
        self._init_safety()
        self._init_strategy()
        
        # Estado
        self.running = False
        self.current_balance = 0.0
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # Histórico de trades recentes (últimos 10 minutos)
        self.recent_trades = []
        self.last_buy_price = 0.0
        self.last_sell_price = 0.0
        
        # Histórico de compras por símbolo (para múltiplas compras)
        # Estrutura: {'BTC/USDT': [{'price': 91500, 'amount': 0.0001, 'timestamp': '...'}, ...]}
        self.purchase_history = {
            'BTC/USDT': [],
            'ETH/USDT': [],
            'SOL/USDT': [],
            'POL/USDT': []
        }
        
        # Preço médio de compra calculado
        self.avg_buy_prices = {
            'BTC/USDT': 0.0,
            'ETH/USDT': 0.0,
            'SOL/USDT': 0.0,
            'POL/USDT': 0.0
        }
        
        # Trades por símbolo
        self.trades_by_symbol = {
            'BTC/USDT': [],
            'ETH/USDT': [],
            'SOL/USDT': [],
            'POL/USDT': []
        }
        
        # Dashboard visual
        self.dashboard = TradingDashboard()
        self.dashboard.update_data(
            symbol=', '.join(self.symbols),
            timeframe=self.timeframe,
            testnet=self.config['exchange']['testnet'],
            dry_run=self.dry_run,
            max_daily_loss=self.config['safety']['max_daily_loss'],
            max_drawdown=self.config['safety']['max_drawdown'],
            interval=self.interval_seconds
        )
        
        # Carrega histórico salvo
        self.load_bot_history()
        
    def _init_exchange(self):
        """Inicializa conexão com exchange"""
        exchange_config = self.config['exchange']
        
        # Seleciona credenciais corretas (testnet ou real)
        if exchange_config['testnet']:
            api_key = self.credentials['binance_testnet_api_key']
            api_secret = self.credentials['binance_testnet_api_secret']
        else:
            api_key = self.credentials['binance_api_key']
            api_secret = self.credentials['binance_api_secret']
        
        self.exchange = ExchangeClient(
            exchange_name=exchange_config['name'],
            api_key=api_key,
            api_secret=api_secret,
            testnet=exchange_config['testnet']
        )
        
        # Pula teste de conexão inicial para evitar timeout
        logger.info("⏭️ Conexão será validada durante operações")
    
    def _init_safety(self):
        """Inicializa sistema de segurança"""
        safety_config = self.config['safety']
        self.safety_manager = SafetyManager(safety_config)
        logger.info("🛡️ Sistema de segurança inicializado")
    
    def _init_strategy(self):
        """Inicializa estratégia de trading"""
        rsi_config = self.config['indicators']['rsi']
        self.strategy = SimpleRSIStrategy(
            rsi_period=rsi_config['period'],
            oversold=rsi_config['oversold'],
            overbought=rsi_config['overbought']
        )
        logger.info("📊 Estratégia RSI inicializada")
    
    def fetch_market_data(self, symbol: str = None) -> pd.DataFrame:
        """Obtém dados de mercado e calcula indicadores"""
        if symbol is None:
            symbol = self.symbols[0]
        # Busca OHLCV
        ohlcv = self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=200)
        
        if not ohlcv:
            logger.error("❌ Falha ao obter dados de mercado")
            return pd.DataFrame()
        
        # Converte para DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calcula indicadores
        df = TechnicalIndicators.calculate_all_indicators(df, self.config['indicators'])
        
        return df
    
    def execute_trade(self, signal: str, reason: str, symbol: str = None):
        """Executa operação de compra/venda"""
        if symbol is None:
            symbol = self.symbols[0]
            
        logger.info(f"🎯 Sinal recebido para {symbol}: {signal.upper()} - {reason}")
        
        # Atualiza dashboard
        self.dashboard.update_data(last_signal=f"{symbol} {signal.upper()}: {reason}")
        
        # Modo DRY RUN - apenas simula
        if self.dry_run:
            logger.info(f"🔸 MODO DRY RUN - Simulando {signal.upper()} {symbol}")
            logger.info(f"   Valor: ${self.amount_per_trade} USDT")
            self.total_trades += 1
            # Adiciona trade simulado ao histórico
            current_price = self.get_current_price(symbol)
            amount = self.amount_per_trade / current_price
            self.add_trade('COMPRA' if signal == 'buy' else 'VENDA', current_price, amount, symbol)
            self.dashboard.update_data(
                trades_count=self.total_trades,
                last_signal=f"🔸 DRY RUN - {symbol} {signal.upper()}: {reason}"
            )
            return
        
        # Verifica saldo
        balance = self.exchange.fetch_balance()
        if not balance:
            logger.error("❌ Não foi possível obter saldo")
            return
        
        # Obtém preço atual
        current_price = self.get_current_price(symbol)
        
        # Validação de saldo
        if signal == 'buy':
            available = balance['free'].get('USDT', 0)
            if not self.safety_manager.order_validator.validate_balance(
                self.amount_per_trade, available
            ):
                logger.warning(f"⚠️ Saldo insuficiente para comprar {symbol}")
                return
            
            # Calcula quantidade a comprar
            amount = self.amount_per_trade / current_price
            
            logger.info(f"💰 EXECUTANDO COMPRA: {amount:.6f} {symbol.split('/')[0]} @ ${current_price:.2f}")
            
            # Executa compra
            order = self.exchange.create_market_order(symbol, 'buy', amount)
            
            if order:
                # Registra compra no histórico
                purchase = {
                    'price': current_price,
                    'amount': amount,
                    'timestamp': datetime.now().isoformat(),
                    'cost': self.amount_per_trade
                }
                self.purchase_history[symbol].append(purchase)
        elif signal == 'sell':
            # Obtém moeda base (ex: BTC de BTC/USDT)
            base_currency = symbol.split('/')[0]
            available = balance['free'].get(base_currency, 0)
            
            if available <= 0:
                logger.warning(f"⚠️ Nenhum {base_currency} disponível para vender")
                return
            
            # Obtém histórico de compras
            purchases = self.purchase_history.get(symbol, [])
            
            if not purchases:
                logger.warning(f"⚠️ Nenhuma compra registrada para {symbol}")
                return
            
            # 🛡️ SEMPRE USA PREÇO MÉDIO (total ou parcial)
            avg_buy_price = self.avg_buy_prices.get(symbol, 0.0)
            
            if avg_buy_price > 0 and current_price <= avg_buy_price:
                profit_pct = ((current_price - avg_buy_price) / avg_buy_price) * 100
                logger.warning(
                    f"🛡️ VENDA BLOQUEADA - Preço abaixo da média: {profit_pct:.2f}% "
                    f"(Média de {len(purchases)} compras: ${avg_buy_price:.2f} → Atual: ${current_price:.2f})"
                )
                return
            
            # Calcula lucro
            total_cost = sum(p['cost'] for p in purchases)
            total_value = current_price * available
            profit_usd = total_value - total_cost
            profit_pct = ((current_price - avg_buy_price) / avg_buy_price * 100) if avg_buy_price > 0 else 0
            
            logger.info(
                f"💰 VENDA: {available:.6f} {base_currency} @ ${current_price:.2f} "
                f"(Média: ${avg_buy_price:.2f} | +{profit_pct:.2f}% | +${profit_usd:.2f} | {len(purchases)} compras)"
            )
            
            # Executa venda
            order = self.exchange.create_market_order(symbol, 'sell', available)
            
            if order:
                # Calcula lucro total da venda
                purchases = self.purchase_history.get(symbol, [])
                total_purchased = sum(p['amount'] for p in purchases)
                sell_all = abs(available - total_purchased) < 0.00001
                
                if sell_all:
                    # Vendeu tudo - calcula lucro total
                    total_cost = sum(p['cost'] for p in purchases)
                    total_value = current_price * available
                    profit = total_value - total_cost
                    
                    logger.info(f"✅ VENDA TOTAL executada: +${profit:.2f}")
                    
                    # Detalha cada compra vendida
                    for i, purchase in enumerate(purchases, 1):
                        individual_profit = (current_price - purchase['price']) * purchase['amount']
                        profit_pct = ((current_price - purchase['price']) / purchase['price']) * 100
                        logger.info(
                            f"   ✓ Compra #{i}: ${purchase['price']:.2f} → ${current_price:.2f} "
                            f"(+{profit_pct:.2f}% | +${individual_profit:.2f})"
                        )
                    
                    # Limpa histórico completo
                    self.purchase_history[symbol] = []
                    self.avg_buy_prices[symbol] = 0.0
                    logger.info(f"🧹 Todas as {len(purchases)} compras de {symbol} zeradas")
                    
                else:
                    # Vendeu parcialmente - remove compras vendidas (FIFO)
                    amount_to_sell = available
                    amount_sold = 0
                    sold_purchases = []
                    
                    for purchase in purchases[:]:  # Cópia da lista
                        if amount_sold >= amount_to_sell:
                            break
                        sold_purchases.append(purchase)
                        amount_sold += purchase['amount']
                    
                    # Calcula lucro das compras vendidas
                    total_cost = sum(p['cost'] for p in sold_purchases)
                    total_value = current_price * amount_to_sell
            if order:
                # Calcula lucro usando preço médio
                purchases = self.purchase_history.get(symbol, [])
                avg_buy_price = self.avg_buy_prices.get(symbol, 0.0)
                total_cost = sum(p['cost'] for p in purchases)
                total_value = current_price * available
                profit = total_value - total_cost
                
                logger.info(f"✅ VENDA executada: +${profit:.2f}")
                
                # Detalha cada compra vendida
                for i, purchase in enumerate(purchases, 1):
                    individual_profit = (current_price - purchase['price']) * purchase['amount']
                    profit_pct = ((current_price - purchase['price']) / purchase['price']) * 100
                    logger.info(
                        f"   ✓ Compra #{i}: ${purchase['price']:.2f} → ${current_price:.2f} "
                        f"(+{profit_pct:.2f}% | +${individual_profit:.2f})"
                    )
                
                # Limpa TODAS as compras (sempre vende tudo usando preço médio)
                num_purchases = len(purchases)
                self.purchase_history[symbol] = []
                self.avg_buy_prices[symbol] = 0.0
                
                self.add_trade('VENDA', current_price, available, symbol)
                self.winning_trades += 1
                self.daily_pnl += profit
                
                logger.info(f"🧹 {num_purchases} compra(s) de {symbol} zeradas")
        
        else:
            return
        
        # Valida execução da ordem
        if order:
            if self.safety_manager.order_validator.validate_order_response(order):
                # Confirma status na exchange (ANTI-ALUCINAÇÃO)
                time.sleep(1)  # Aguarda processamento
                confirmed_order = self.exchange.fetch_order_status(order['id'], symbol)
                
                if confirmed_order:
                    logger.info(f"✅ Ordem confirmada na exchange: {confirmed_order['status']}")
                    self.strategy.update_position('long' if signal == 'buy' else None)
                    
                    # Atualiza estatísticas
                    self.total_trades += 1
                    self.dashboard.update_data(
                        trades_count=self.total_trades,
                        position='LONG' if signal == 'buy' else 'SHORT',
                        wins=self.winning_trades,
                        losses=self.losing_trades
                    )
    
    def get_current_price(self, symbol: str = None) -> float:
        """Obtém preço atual"""
        if symbol is None:
            symbol = self.symbols[0]
        ticker = self.exchange.fetch_ticker(symbol)
        return ticker['last'] if ticker else 0.0
    
    def add_trade(self, trade_type: str, price: float, amount: float, symbol: str = None):
        """Adiciona trade ao histórico recente"""
        if symbol is None:
            symbol = self.symbols[0]
            
        trade = {
            'type': trade_type,  # 'COMPRA' ou 'VENDA'
            'price': price,
            'amount': amount,
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'time_ago': 0  # será calculado no front
        }
        
        if trade_type == 'COMPRA':
            self.last_buy_price = price
        else:
            self.last_sell_price = price
            
        self.recent_trades.insert(0, trade)  # Adiciona no início
        
        # Adiciona ao histórico do símbolo específico
        if symbol in self.trades_by_symbol:
            self.trades_by_symbol[symbol].insert(0, trade)
            # Mantém apenas últimas 10 trades por símbolo
            if len(self.trades_by_symbol[symbol]) > 10:
                self.trades_by_symbol[symbol] = self.trades_by_symbol[symbol][:10]
        
        # Mantém apenas últimas 50 trades no geral
        if len(self.recent_trades) > 50:
            self.recent_trades = self.recent_trades[:50]
        
        # Salva trade permanentemente em arquivo CSV
        self.save_trade_to_csv(trade)
    
    def save_trade_to_csv(self, trade: dict):
        """Salva trade em arquivo CSV permanente"""
        try:
            import csv
            from pathlib import Path
            
            # Cria diretório de relatórios se não existir
            reports_dir = Path('data/reports')
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Nome do arquivo com data
            today = datetime.now().strftime('%Y-%m-%d')
            csv_file = reports_dir / f'trades_{today}.csv'
            
            # Verifica se arquivo existe para criar cabeçalho
            file_exists = csv_file.exists()
            
            # Abre em modo append
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                fieldnames = ['timestamp', 'symbol', 'type', 'price', 'amount', 'value_usd']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Escreve cabeçalho se arquivo é novo
                if not file_exists:
                    writer.writeheader()
                
                # Calcula valor total em USD
                value_usd = trade['price'] * trade['amount']
                
                # Escreve linha do trade
                writer.writerow({
                    'timestamp': trade['timestamp'],
                    'symbol': trade['symbol'],
                    'type': trade['type'],
                    'price': f"{trade['price']:.2f}",
                    'amount': f"{trade['amount']:.8f}",
                    'value_usd': f"{value_usd:.2f}"
                })
                
            logger.info(f"💾 Trade salvo em {csv_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar trade em CSV: {e}")
    
    def calculate_avg_buy_price(self, symbol: str):
        """Calcula preço médio de compra baseado em múltiplas compras"""
        purchases = self.purchase_history.get(symbol, [])
        
        if not purchases:
            self.avg_buy_prices[symbol] = 0.0
            return
        
        total_cost = sum(p['cost'] for p in purchases)
        total_amount = sum(p['amount'] for p in purchases)
        
        if total_amount > 0:
            avg_price = total_cost / total_amount
            self.avg_buy_prices[symbol] = avg_price
            logger.info(
                f"📊 Preço médio de {symbol}: ${avg_price:.2f} "
                f"({len(purchases)} compras, {total_amount:.6f} total)"
            )
        else:
            self.avg_buy_prices[symbol] = 0.0
    
    def save_bot_state(self, data: dict):
        """Salva estado do bot para o dashboard"""
        try:
            # Adiciona trades recentes ao estado
            data['recent_trades'] = self.recent_trades
            data['last_buy_price'] = self.last_buy_price
            data['last_sell_price'] = self.last_sell_price
            data['trades_by_symbol'] = self.trades_by_symbol
            
            # Salva estado atual (volátil)
            state_file = 'bot_state.json'
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Salva histórico permanente
            history_file = 'bot_history.json'
            history_data = {
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'daily_pnl': self.daily_pnl,
                'recent_trades': self.recent_trades[:50],  # Últimos 50
                'trades_by_symbol': self.trades_by_symbol,
                'last_buy_price': self.last_buy_price,
                'last_sell_price': self.last_sell_price,
                'purchase_history': self.purchase_history,  # Histórico de múltiplas compras
                'avg_buy_prices': self.avg_buy_prices,  # Preços médios calculados
                'last_update': datetime.now().isoformat()
            }
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Erro ao salvar estado do bot: {e}")
    
    def load_bot_history(self):
        """Carrega histórico salvo ao iniciar"""
        try:
            history_file = 'bot_history.json'
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
                
                self.total_trades = history.get('total_trades', 0)
                self.winning_trades = history.get('winning_trades', 0)
                self.losing_trades = history.get('losing_trades', 0)
                self.daily_pnl = history.get('daily_pnl', 0.0)
                self.recent_trades = history.get('recent_trades', [])
                self.trades_by_symbol = history.get('trades_by_symbol', {
                    'BTC/USDT': [],
                    'ETH/USDT': [],
                    'SOL/USDT': [],
                    'POL/USDT': []
                })
                self.last_buy_price = history.get('last_buy_price', 0.0)
                self.last_sell_price = history.get('last_sell_price', 0.0)
                
                # Carrega histórico de compras e preços médios
                self.purchase_history = history.get('purchase_history', {
                    'BTC/USDT': [],
                    'ETH/USDT': [],
                    'SOL/USDT': [],
                    'POL/USDT': []
                })
                self.avg_buy_prices = history.get('avg_buy_prices', {
                    'BTC/USDT': 0.0,
                    'ETH/USDT': 0.0,
                    'SOL/USDT': 0.0,
                    'POL/USDT': 0.0
                })
                
                # Mostra resumo de posições em aberto
                for symbol, purchases in self.purchase_history.items():
                    if purchases:
                        avg = self.avg_buy_prices.get(symbol, 0.0)
                        logger.info(
                            f"💰 {symbol}: {len(purchases)} compras em aberto "
                            f"(Preço médio: ${avg:.2f})"
                        )
                
                logger.info(f"📂 Histórico carregado: {self.total_trades} trades, PnL: ${self.daily_pnl:.2f}")
        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {e}")
    
    def run_cycle(self):
        """Executa um ciclo de análise"""
        try:
            logger.info(f"🔄 Ciclo iniciado - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Atualiza status
            self.dashboard.update_data(status='Analisando...')
            
            # Atualiza saldo
            balance = self.exchange.fetch_balance()
            crypto_balances = {}
            if balance:
                self.current_balance = balance['total'].get('USDT', 0)
                self.dashboard.update_data(balance=self.current_balance)
                
                # Obtém saldo de cada cripto
                for symbol in self.symbols:
                    base_currency = symbol.split('/')[0]
                    crypto_balances[symbol] = {
                        'free': balance['free'].get(base_currency, 0),
                        'total': balance['total'].get(base_currency, 0)
                    }
            
            # Verifica segurança
            is_safe = self.safety_manager.is_safe_to_trade(self.current_balance, self.daily_pnl)
            
            if not is_safe:
                logger.critical("🛑 TRADING BLOQUEADO - Kill Switch ativo!")
                self.safety_manager.emergency_stop(self.exchange.exchange)
                self.dashboard.update_data(
                    status='PARADO - Kill Switch',
                    kill_switch_active=True
                )
                return False
            
            self.dashboard.update_data(kill_switch_active=False)
            
            # Verifica se tem alguma cripto para negociar
            total_crypto_balance = 0
            if balance:
                for symbol in self.symbols:
                    base_currency = symbol.split('/')[0]
                    total_crypto_balance += balance['total'].get(base_currency, 0)
            
            has_crypto = total_crypto_balance > 0
            
            # Ajusta threshold de compra dinamicamente
            self.strategy.adjust_oversold_threshold(has_crypto)
            
            # Analisa cada criptomoeda
            all_data = {}
            for symbol in self.symbols:
                logger.info(f"📊 Analisando {symbol}...")
                
                # Obtém dados de mercado
                df = self.fetch_market_data(symbol)
                if df.empty:
                    logger.warning(f"⚠️ Dados insuficientes para {symbol}")
                    continue
                
                # Valida preço
                current_price = df['close'].iloc[-1]
                
                if not self.safety_manager.price_validator.validate_price(current_price, symbol):
                    logger.warning(f"⚠️ Preço suspeito detectado em {symbol} - pulando")
                    continue
                
                # Armazena dados
                all_data[symbol] = {
                    'price': current_price,
                    'rsi': df['rsi'].iloc[-1] if 'rsi' in df.columns else None,
                    'macd': df.get('MACD_12_26_9', pd.Series([None])).iloc[-1],
                    'macd_signal': df.get('MACDs_12_26_9', pd.Series([None])).iloc[-1],
                    'sma_20': df.get('sma_20', pd.Series([None])).iloc[-1],
                    'sma_50': df.get('sma_50', pd.Series([None])).iloc[-1],
                    'sma_200': df.get('sma_200', pd.Series([None])).iloc[-1],
                    'df': df
                }
                
                rsi_value = all_data[symbol]['rsi'] if all_data[symbol]['rsi'] else 0
                logger.info(f"   {symbol}: ${current_price:.2f} | RSI: {rsi_value:.1f}")
            
            # Analisa todas as criptomoedas e executa trades
            signals_found = []
            
            for symbol, data in all_data.items():
                df = data['df']
                current_price = data['price']
                
                # Verifica se tem cripto deste símbolo
                base_currency = symbol.split('/')[0]
                has_crypto = crypto_balances.get(symbol, {}).get('total', 0) > 0
                
                # Calcula idade da compra mais antiga (em minutos)
                purchase_age_minutes = 0.0
                if has_crypto and symbol in self.purchase_history:
                    purchases = self.purchase_history[symbol]
                    if purchases:
                        from datetime import datetime
                        oldest_purchase = purchases[0]  # Primeira compra (mais antiga)
                        purchase_time = datetime.fromisoformat(oldest_purchase['timestamp'])
                        purchase_age_minutes = (datetime.now() - purchase_time).total_seconds() / 60.0
                
                # Analisa estratégia para cada cripto (passa se tem cripto e idade da compra)
                analysis = self.strategy.analyze(df, has_crypto=has_crypto, purchase_age_minutes=purchase_age_minutes)
                logger.info(f"📊 {symbol} - Análise: {analysis['signal']} - {analysis['reason']}")
                
                # Executa trade se houver sinal
                if analysis['signal'] in ['buy', 'sell']:
                    signals_found.append(f"{symbol}: {analysis['signal'].upper()}")
                    self.execute_trade(analysis['signal'], analysis['reason'], symbol)
            
            # Atualiza dashboard com dados do primeiro símbolo (compatibilidade)
            if self.symbols[0] in all_data:
                main_data = all_data[self.symbols[0]]
                self.dashboard.update_data(
                    current_price=main_data['price'],
                    rsi=main_data['rsi'],
                    macd=main_data['macd'],
                    macd_signal=main_data['macd_signal'],
                    sma_20=main_data['sma_20'],
                    sma_50=main_data['sma_50'],
                    sma_200=main_data['sma_200']
                )
                analysis = self.strategy.analyze(main_data['df'])
            else:
                logger.warning("⚠️ Nenhum dado válido obtido")
                return True
            
            # Atualiza dashboard
            signal_summary = ' | '.join(signals_found) if signals_found else f"{analysis['signal'].upper()}: {analysis['reason']}"
            self.dashboard.update_data(
                status='Operando',
                last_signal=signal_summary,
                daily_pnl=self.daily_pnl
            )
            
            # Salva estado para dashboard web
            bot_state = {
                'status': 'Operando',
                'balance': self.current_balance,
                'daily_pnl': self.daily_pnl,
                'total_pnl': self.daily_pnl,
                'current_price': current_price,
                'position': self.strategy.position.upper() if self.strategy.position else 'AGUARDANDO',
                'trades_count': self.total_trades,
                'wins': self.winning_trades,
                'losses': self.losing_trades,
                'last_signal': f"{analysis['signal'].upper()}: {analysis['reason']}",
                'rsi': float(df['rsi'].iloc[-1]) if 'rsi' in df.columns else 0,
                'macd': float(df.get('MACD_12_26_9', pd.Series([0])).iloc[-1]),
                'macd_signal': float(df.get('MACDs_12_26_9', pd.Series([0])).iloc[-1]),
                'sma_20': float(df.get('sma_20', pd.Series([0])).iloc[-1]),
                'sma_50': float(df.get('sma_50', pd.Series([0])).iloc[-1]),
                'sma_200': float(df.get('sma_200', pd.Series([0])).iloc[-1]),
                'kill_switch_active': False,
                'timestamp': int(time.time() * 1000),
                'crypto_balances': crypto_balances,
                'all_symbols_data': all_data
            }
            self.save_bot_state(bot_state)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo: {e}", exc_info=True)
            return True
    
    def start(self, interval_seconds: int = None):
        """Inicia o bot"""
        if interval_seconds is None:
            interval_seconds = self.interval_seconds
            
        logger.info("🚀 Iniciando Trading Bot...")
        logger.info(f"📈 Pares: {', '.join(self.symbols)} | Timeframe: {self.timeframe}")
        logger.info(f"💰 Valor por trade: {self.amount_per_trade} USDT")
        
        if self.dry_run:
            logger.warning("🔸 MODO DRY RUN ATIVO - Apenas simulação, nenhuma ordem será executada!")
        
        self.running = True
        
        # Inicia dashboard em tempo real
        with Live(self.dashboard.render(), refresh_per_second=1, screen=True) as live:
            try:
                while self.running:
                    continue_running = self.run_cycle()
                    
                    if not continue_running:
                        logger.critical("🛑 Bot parado por sistema de segurança")
                        self.dashboard.update_data(status='PARADO - Segurança')
                        break
                    
                    # Atualiza dashboard
                    live.update(self.dashboard.render())
                    
                    logger.info(f"⏳ Aguardando {interval_seconds}s para próximo ciclo...\n")
                    
                    # Sleep com atualização do dashboard
                    for _ in range(interval_seconds):
                        if not self.running:
                            break
                        time.sleep(1)
                        live.update(self.dashboard.render())
                    
            except KeyboardInterrupt:
                logger.info("\n⚠️ Interrupção manual detectada (Ctrl+C)")
                self.stop()
            except Exception as e:
                logger.critical(f"❌ Erro crítico: {e}", exc_info=True)
                self.stop()
    
    def stop(self):
        """Para o bot"""
        logger.info("🛑 Parando Trading Bot...")
        self.running = False
        
        # Cancela ordens abertas por segurança
        self.safety_manager.emergency_stop(self.exchange.exchange)
        
        logger.info("✅ Bot encerrado com segurança")


def main():
    """Função principal"""
    bot = TradingBot()
    bot.start()  # Usa intervalo do config


if __name__ == "__main__":
    main()
