"""
🤖 App Leonardo - Bot de Trading de Criptomoedas
Sistema automatizado de trading com múltiplas criptomoedas
"""
import os
import sys
import time
import json
import csv
import sqlite3
import signal
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.utils import load_config, load_env_credentials, setup_logging
from core.exchange_client import ExchangeClient
from indicators.technical_indicators import TechnicalIndicators
from safety.safety_manager import SafetyManager
from src.core.portfolio_manager import PortfolioManager

# Tentar carregar Enhanced Trading Engine
try:
    from enhanced_trading_engine import EnhancedTradingEngine
    ENHANCED_ENGINE_AVAILABLE = True
    print("🚀 Enhanced Trading Engine Disponível!")
except ImportError as e:
    ENHANCED_ENGINE_AVAILABLE = False
    print(f"⚠️ Enhanced Trading Engine não disponível: {e}")

# Tenta usar Smart Strategy, senão usa a antiga
try:
    from src.strategies.smart_strategy import SmartStrategy
    SMART_STRATEGY_AVAILABLE = True
except ImportError:
    SMART_STRATEGY_AVAILABLE = False
    from src.strategies.simple_strategies_new import get_strategy

logger = logging.getLogger(__name__)


class TradingBot:
    """Bot de Trading Principal"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Inicializa o bot"""
        logger.info("="*60)
        logger.info("🤖 INICIANDO APP LEONARDO - BOT DE TRADING")
        logger.info("="*60)
        
        # Carrega configurações
        self.config = load_config(config_path)
        self.credentials = load_env_credentials()
        
        # Estado do bot
        self.is_running = False
        self.start_time = datetime.now()
        self.positions: Dict[str, Optional[Dict]] = {}  # {symbol: position_data}
        self.trades_history: List[Dict] = []
        
        # Estatísticas
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'daily_pnl': 0.0,
            'initial_balance': 0.0,
            'current_balance': 0.0,
            'daily_target': 100.0,  # Meta diária de $100
            'date': datetime.now().strftime('%Y-%m-%d'),
        }
        
        # Arquivo de estatísticas diárias persistentes
        self.daily_stats_file = 'data/daily_stats.json'
        
        # Carrega estatísticas do dia (se existirem)
        self._load_daily_stats()
        
        # Sistema de histórico
        self.history_db_path = 'data/trading_history.db'
        self.all_trades_file = 'data/all_trades_history.json'
        self._init_history_database()
        
        # Configurações de trading
        self.symbols = self.config['trading']['symbols']
        self.timeframe = self.config['trading']['timeframe']
        self.amount_per_trade = self.config['trading']['amount_per_trade']
        self.max_positions = self.config['trading']['max_positions']
        self.interval = self.config['execution']['interval_seconds']
        self.dry_run = self.config['execution']['dry_run']
        
        # Atributos para histórico e metas
        self.trade_amount = self.amount_per_trade  # Valor por trade
        self.daily_goal = self.stats.get('daily_target', 100.0)  # Meta diária de $100
        
        # Inicializa componentes
        self._initialize_components()
        
        # Configura signal handlers para parada graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"✅ Bot inicializado com sucesso!")
        logger.info(f"   Símbolos: {', '.join(self.symbols)}")
        logger.info(f"   Timeframe: {self.timeframe}")
        logger.info(f"   Modo: {'DRY RUN (Simulação)' if self.dry_run else 'REAL'}")
        logger.info(f"   Testnet: {self.config['exchange']['testnet']}")
    
    def _initialize_components(self):
        """Inicializa exchange, estratégia e safety manager"""
        # Exchange Client - usa credenciais corretas baseado em testnet
        testnet = self.config['exchange']['testnet']
        
        if testnet:
            api_key = self.credentials.get('BINANCE_TESTNET_API_KEY', '')
            api_secret = self.credentials.get('BINANCE_TESTNET_API_SECRET', '')
            logger.info("🧪 Usando credenciais da TESTNET")
        else:
            api_key = self.credentials.get('BINANCE_API_KEY', '')
            api_secret = self.credentials.get('BINANCE_API_SECRET', '')
            logger.info("💰 Usando credenciais da Binance REAL")
        
        if not api_key or not api_secret:
            logger.warning("⚠️ Credenciais não encontradas - usando modo API pública")
            api_key = api_secret = ''
        else:
            logger.info(f"✅ Credenciais encontradas (key: {api_key[:8]}...)")
        
        self.exchange = ExchangeClient(
            exchange_name=self.config['exchange']['name'],
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
        
        # Testa conexão
        if not self.exchange.test_connection():
            logger.warning("⚠️ Conexão com exchange falhou - continuando em modo limitado")
        
        # Estratégia de trading (Smart Strategy com perfis por moeda)
        if SMART_STRATEGY_AVAILABLE:
            self.strategy = SmartStrategy(self.config)
            logger.info(f"🧠 Estratégia INTELIGENTE: {self.strategy.name}")
        else:
            strategy_type = self.config.get('strategy', {}).get('type', 'aggressive')
            self.strategy = get_strategy(strategy_type, self.config)
            logger.info(f"📊 Estratégia: {strategy_type.upper()} - {self.strategy.name}")
        
        # Safety Manager
        self.safety = SafetyManager(self.config['safety'])
        
        # Portfolio Manager - Gestão avançada de portfólio
        self.portfolio_manager = PortfolioManager()
        logger.info("💼 Portfolio Manager inicializado - Regras de exposição ativas")
        
        # Inicializa posições
        for symbol in self.symbols:
            self.positions[symbol] = None
        
        # Obtém saldo inicial
        self._update_balance()
    
    def _signal_handler(self, sig, frame):
        """Handler para sinais de interrupção (Ctrl+C)"""
        logger.warning("\n⚠️ Sinal de interrupção recebido!")
        self.stop()
    
    def _load_daily_stats(self):
        """Carrega estatísticas do dia de arquivo persistente"""
        try:
            os.makedirs('data', exist_ok=True)
            
            if os.path.exists(self.daily_stats_file):
                with open(self.daily_stats_file, 'r') as f:
                    saved_stats = json.load(f)
                
                # Verifica se é do mesmo dia
                today = datetime.now().strftime('%Y-%m-%d')
                saved_date = saved_stats.get('date', '')
                
                if saved_date == today:
                    # Mesmo dia - carrega estatísticas salvas
                    self.stats['total_trades'] = saved_stats.get('total_trades', 0)
                    self.stats['winning_trades'] = saved_stats.get('winning_trades', 0)
                    self.stats['losing_trades'] = saved_stats.get('losing_trades', 0)
                    self.stats['total_pnl'] = saved_stats.get('total_pnl', 0.0)
                    self.stats['daily_pnl'] = saved_stats.get('daily_pnl', 0.0)
                    self.stats['date'] = today
                    
                    logger.info(f"📂 Estatísticas do dia carregadas!")
                    logger.info(f"   Trades: {self.stats['total_trades']}")
                    logger.info(f"   PnL diário: ${self.stats['daily_pnl']:.2f}")
                    logger.info(f"   Win/Loss: {self.stats['winning_trades']}/{self.stats['losing_trades']}")
                else:
                    # Novo dia - reseta estatísticas
                    logger.info(f"🌅 Novo dia detectado! Resetando estatísticas...")
                    logger.info(f"   Dia anterior: {saved_date} | PnL: ${saved_stats.get('daily_pnl', 0):.2f}")
                    self.stats['date'] = today
                    self._save_daily_stats()
            else:
                logger.info("📝 Primeiro uso - criando arquivo de estatísticas...")
                self._save_daily_stats()
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar estatísticas: {e}")
    
    def _save_daily_stats(self):
        """Salva estatísticas do dia em arquivo persistente"""
        try:
            os.makedirs('data', exist_ok=True)
            
            stats_to_save = {
                'date': self.stats.get('date', datetime.now().strftime('%Y-%m-%d')),
                'total_trades': self.stats['total_trades'],
                'winning_trades': self.stats['winning_trades'],
                'losing_trades': self.stats['losing_trades'],
                'total_pnl': float(self.stats['total_pnl']),
                'daily_pnl': float(self.stats['daily_pnl']),
                'daily_target': float(self.stats.get('daily_target', 100.0)),
                'last_update': datetime.now().isoformat(),
                'target_reached': bool(self.stats['daily_pnl'] >= self.stats.get('daily_target', 100.0)),
            }
            
            with open(self.daily_stats_file, 'w') as f:
                json.dump(stats_to_save, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar estatísticas: {e}")
    
    def _update_balance(self):
        """Atualiza saldo da conta"""
        try:
            balance_data = self.exchange.fetch_balance()
            if balance_data:
                usdt_balance = balance_data.get('USDT', {})
                self.stats['current_balance'] = usdt_balance.get('free', 0.0)
                
                if self.stats['initial_balance'] == 0:
                    self.stats['initial_balance'] = self.stats['current_balance']
                
                logger.info(f"💰 Saldo: {self.stats['current_balance']:.2f} USDT")
        except Exception as e:
            logger.error(f"❌ Erro ao obter saldo: {e}")
            if self.stats['current_balance'] == 0:
                self.stats['current_balance'] = 10000.0  # Valor padrão para dry run
                self.stats['initial_balance'] = 10000.0
    
    def fetch_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Busca dados de mercado e calcula indicadores"""
        try:
            # Busca dados OHLCV
            ohlcv = self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=200)
            
            if not ohlcv:
                logger.warning(f"⚠️ Sem dados para {symbol}")
                return None
            
            # Converte para DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calcula indicadores técnicos
            df = TechnicalIndicators.calculate_all_indicators(df, self.config['indicators'])
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados de {symbol}: {e}")
            return None
    
    def check_position(self, symbol: str) -> bool:
        """Verifica se há posição aberta para o símbolo"""
        return self.positions.get(symbol) is not None
    
    def open_position(self, symbol: str, signal: str, price: float, reason: str, indicators: Dict):
        """Abre uma nova posição"""
        if self.check_position(symbol):
            logger.warning(f"⚠️ Já existe posição aberta para {symbol}")
            return
        
        # Verifica limite de posições
        open_positions = sum(1 for p in self.positions.values() if p is not None)
        if open_positions >= self.max_positions:
            logger.warning(f"⚠️ Limite de posições atingido ({self.max_positions})")
            return
        
        # Executa ordem
        if self.dry_run:
            logger.info(f"🧪 [DRY RUN] Ordem de {signal}: {self.amount_per_trade} USDT em {symbol} @ {price:.2f}")
            order_result = {
                'id': f"DRY_{int(time.time())}",
                'symbol': symbol,
                'side': signal.lower(),
                'price': price,
                'amount': self.amount_per_trade / price,
                'status': 'filled'
            }
        else:
            # Ordem real
            amount_crypto = self.amount_per_trade / price
            order_result = self.exchange.create_market_order(symbol, signal.lower(), amount_crypto)
            
            if not order_result:
                logger.error(f"❌ Falha ao criar ordem para {symbol}")
                return
        
        # Registra posição
        self.positions[symbol] = {
            'symbol': symbol,
            'side': signal,
            'entry_price': price,
            'amount': order_result['amount'],
            'entry_time': datetime.now(),
            'reason': reason,
            'indicators': indicators,
            'order_id': order_result['id']
        }
        
        self.stats['total_trades'] += 1
        
        logger.info(f"✅ Posição {signal} aberta: {symbol} @ {price:.2f}")
        logger.info(f"   Razão: {reason}")
        self._save_state()
    
    def close_position(self, symbol: str, current_price: float, reason: str):
        """Fecha uma posição aberta"""
        if not self.check_position(symbol):
            logger.warning(f"⚠️ Nenhuma posição aberta para {symbol}")
            return
        
        position = self.positions[symbol]
        
        # Calcula PnL
        if position['side'] == 'BUY':
            pnl = (current_price - position['entry_price']) * position['amount']
        else:
            pnl = (position['entry_price'] - current_price) * position['amount']
        
        pnl_pct = (pnl / self.amount_per_trade) * 100
        
        # Executa ordem de fechamento
        close_side = 'sell' if position['side'] == 'BUY' else 'buy'
        
        if self.dry_run:
            logger.info(f"🧪 [DRY RUN] Fechando posição {symbol}: {close_side.upper()} @ {current_price:.2f}")
        else:
            close_order = self.exchange.create_market_order(symbol, close_side, position['amount'])
            if not close_order:
                logger.error(f"❌ Falha ao fechar posição {symbol}")
                return
        
        # Atualiza estatísticas
        self.stats['total_pnl'] += pnl
        self.stats['daily_pnl'] += pnl
        
        if pnl > 0:
            self.stats['winning_trades'] += 1
            emoji = "🟢"
        else:
            self.stats['losing_trades'] += 1
            emoji = "🔴"
        
        # Registra no histórico
        trade_record = {
            'symbol': symbol,
            'side': position['side'],
            'entry_price': position['entry_price'],
            'exit_price': current_price,
            'amount': position['amount'],
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'entry_time': position['entry_time'].isoformat(),
            'exit_time': datetime.now().isoformat(),
            'entry_reason': position['reason'],
            'exit_reason': reason,
            'duration_minutes': (datetime.now() - position['entry_time']).total_seconds() / 60,
            'entry_indicators': position.get('indicators', {})
        }
        self.trades_history.append(trade_record)
        
        # Salva em múltiplos formatos
        self._save_trade_to_csv(trade_record)
        self._save_trade_to_db(trade_record)
        self._save_all_trades_json()
        self._save_daily_stats()  # Salva estatísticas diárias
        
        # Registra evento de trade
        self._save_bot_event('TRADE_CLOSED', f'{symbol} PnL: ${pnl:.2f}', trade_record)
        
        logger.info(f"{emoji} Posição fechada: {symbol}")
        logger.info(f"   Entrada: {position['entry_price']:.2f} → Saída: {current_price:.2f}")
        logger.info(f"   PnL: {pnl:.2f} USDT ({pnl_pct:+.2f}%)")
        logger.info(f"   Razão: {reason}")
        
        # Verifica meta diária
        target = self.stats.get('daily_target', 100.0)
        progress = (self.stats['daily_pnl'] / target) * 100
        logger.info(f"   📊 Progresso diário: ${self.stats['daily_pnl']:.2f} / ${target:.2f} ({progress:.1f}%)")
        
        if self.stats['daily_pnl'] >= target:
            logger.info(f"   🎉 META DIÁRIA ATINGIDA!")
        
        # Remove posição
        self.positions[symbol] = None
        self._save_state()
    
    def process_symbol(self, symbol: str):
        """Processa um símbolo (análise e execução)"""
        try:
            # Busca dados de mercado
            df = self.fetch_market_data(symbol)
            if df is None or df.empty:
                return
            
            current_price = df.iloc[-1]['close']
            
            # Valida preço
            if not self.safety.price_validator.validate_price(current_price, symbol):
                logger.warning(f"⚠️ Preço suspeito para {symbol}, pulando...")
                return
            
            # Verifica se há posição aberta
            has_position = self.check_position(symbol)
            
            if has_position:
                # Gerencia posição existente
                position = self.positions[symbol]
                
                # Calcula PnL atual
                if position['side'] == 'BUY':
                    unrealized_pnl = (current_price - position['entry_price']) * position['amount']
                else:
                    unrealized_pnl = (position['entry_price'] - current_price) * position['amount']
                
                unrealized_pnl_pct = (unrealized_pnl / self.amount_per_trade) * 100
                
                # Usa Smart Strategy se disponível
                should_close = False
                close_reason = ""
                
                if SMART_STRATEGY_AVAILABLE and hasattr(self.strategy, 'should_sell'):
                    # Verifica se posições estão cheias
                    open_positions = sum(1 for p in self.positions.values() if p is not None)
                    positions_full = (open_positions >= self.max_positions)
                    
                    # Estratégia inteligente: segura até tendência virar
                    # Se posições cheias → modo agressivo de venda (mas nunca no prejuízo!)
                    should_close, close_reason = self.strategy.should_sell(
                        symbol=symbol,
                        entry_price=position['entry_price'],
                        current_price=current_price,
                        df=df,
                        position_time=position['entry_time'],
                        positions_full=positions_full  # NOVO: Ativa modo agressivo!
                    )
                    
                    if not should_close:
                        mode = "🚀CHEIO" if positions_full else ""
                        logger.info(f"📊 {symbol}: {close_reason} {mode}")
                else:
                    # Estratégia antiga (fallback)
                    signal, reason, indicators = self.strategy.analyze(df, symbol)
                    self._save_analysis_to_db(symbol, current_price, signal, reason, indicators)
                    
                    if position['side'] == 'BUY' and signal == 'SELL':
                        should_close = True
                        close_reason = f"Sinal de venda: {reason}"
                    elif position['side'] == 'SELL' and signal == 'BUY':
                        should_close = True
                        close_reason = f"Sinal de compra: {reason}"
                    elif unrealized_pnl_pct <= -1.5:  # Stop loss 1.5%
                        should_close = True
                        close_reason = f"Stop Loss ({unrealized_pnl_pct:.2f}%)"
                    elif unrealized_pnl_pct >= 5:  # Take profit 5%
                        should_close = True
                        close_reason = f"Take Profit ({unrealized_pnl_pct:.2f}%)"
                
                if should_close:
                    self.close_position(symbol, current_price, close_reason)
                    
                    # Atualiza estatísticas da estratégia
                    if SMART_STRATEGY_AVAILABLE and hasattr(self.strategy, 'update_daily_stats'):
                        pnl = unrealized_pnl
                        self.strategy.update_daily_stats(pnl)
                else:
                    logger.debug(f"⚪ {symbol}: Mantendo posição ({unrealized_pnl_pct:+.2f}%)")
            
            else:
                # Procura nova entrada
                signal, reason, indicators = self.strategy.analyze(df, symbol)
                
                # Salva análise no histórico
                self._save_analysis_to_db(symbol, current_price, signal, reason, indicators)
                
                if signal in ['BUY', 'SELL']:
                    self.open_position(symbol, signal, current_price, reason, indicators)
                else:
                    logger.debug(f"⚪ {symbol} @ {current_price:.2f}: {reason}")
        
        except Exception as e:
            logger.error(f"❌ Erro ao processar {symbol}: {e}", exc_info=True)
    
    def trading_loop(self):
        """Loop principal de trading"""
        logger.info("🔄 Iniciando loop de trading...")
        iteration = 0
        
        while self.is_running:
            try:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"📊 Iteração #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                # Atualiza saldo
                self._update_balance()
                
                # Verifica segurança
                if not self.safety.is_safe_to_trade(
                    self.stats['current_balance'],
                    self.stats['daily_pnl']
                ):
                    logger.critical("🛑 CONDIÇÕES DE SEGURANÇA VIOLADAS - Parando bot!")
                    self.stop()
                    break
                
                # Processa cada símbolo
                for symbol in self.symbols:
                    logger.info(f"\n🔍 Analisando {symbol}...")
                    self.process_symbol(symbol)
                    time.sleep(1)  # Pequeno delay entre símbolos
                
                # Exibe resumo
                self._print_summary()
                
                # Salva estado
                self._save_state()
                
                # Salva histórico completo a cada 10 iterações
                if iteration % 10 == 0:
                    self._save_complete_history()
                    self._save_daily_summary()
                
                # Aguarda próxima iteração
                logger.info(f"\n⏳ Aguardando {self.interval} segundos até próxima análise...")
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                logger.warning("\n⚠️ Interrupção detectada!")
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop de trading: {e}", exc_info=True)
                time.sleep(5)
    
    def _print_summary(self):
        """Exibe resumo das operações"""
        open_positions = sum(1 for p in self.positions.values() if p is not None)
        win_rate = (self.stats['winning_trades'] / self.stats['total_trades'] * 100) if self.stats['total_trades'] > 0 else 0
        
        logger.info(f"\n📈 RESUMO:")
        logger.info(f"   Saldo: {self.stats['current_balance']:.2f} USDT")
        logger.info(f"   PnL Total: {self.stats['total_pnl']:+.2f} USDT")
        logger.info(f"   PnL Diário: {self.stats['daily_pnl']:+.2f} USDT")
        logger.info(f"   Trades: {self.stats['total_trades']} (✅ {self.stats['winning_trades']} | ❌ {self.stats['losing_trades']})")
        logger.info(f"   Win Rate: {win_rate:.1f}%")
        logger.info(f"   Posições Abertas: {open_positions}/{self.max_positions}")
    
    def _save_state(self):
        """Salva estado do bot em arquivo JSON"""
        try:
            # Estado atual
            state = {
                'status': 'Operando' if self.is_running else 'Parado',
                'balance': self.stats['current_balance'],
                'daily_pnl': self.stats['daily_pnl'],
                'total_pnl': self.stats['total_pnl'],
                'trades_count': self.stats['total_trades'],
                'wins': self.stats['winning_trades'],
                'losses': self.stats['losing_trades'],
                'positions': {k: v for k, v in self.positions.items() if v is not None},
                'last_update': datetime.now().isoformat(),
                'timestamp': int(time.time() * 1000),
                'is_running': self.is_running,
            }
            
            # Salva estado
            with open('bot_state.json', 'w') as f:
                json.dump(state, f, indent=2, default=str)
            
            # Salva histórico
            history = {
                'total_trades': self.stats['total_trades'],
                'winning_trades': self.stats['winning_trades'],
                'losing_trades': self.stats['losing_trades'],
                'total_pnl': self.stats['total_pnl'],
                'daily_pnl': self.stats['daily_pnl'],
                'recent_trades': self.trades_history[-50:],  # Últimos 50 trades
                'trades_by_symbol': self._get_trades_by_symbol(),
            }
            
            with open('bot_history.json', 'w') as f:
                json.dump(history, f, indent=2, default=str)
            
            # Salva daily stats para o dashboard
            self._save_daily_stats()
            
            # Salva snapshot do portfolio (a cada 5 iterações para não sobrecarregar)
            if not hasattr(self, '_snapshot_counter'):
                self._snapshot_counter = 0
            self._snapshot_counter += 1
            if self._snapshot_counter % 5 == 0:
                self._save_portfolio_snapshot({})
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar estado: {e}")
    
    def _init_history_database(self):
        """Inicializa banco de dados SQLite para histórico completo"""
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(self.history_db_path)
        cursor = conn.cursor()
        
        # Tabela de trades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                amount REAL NOT NULL,
                pnl REAL NOT NULL,
                pnl_pct REAL NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT NOT NULL,
                entry_reason TEXT,
                exit_reason TEXT,
                duration_minutes REAL,
                entry_rsi REAL,
                entry_macd REAL,
                strategy TEXT
            )
        ''')
        
        # Tabela de análises (cada verificação do mercado)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                rsi REAL,
                macd REAL,
                macd_signal REAL,
                sma_20 REAL,
                signal TEXT,
                reason TEXT
            )
        ''')
        
        # Tabela de snapshots do portfolio (a cada ciclo)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_balance_usdt REAL NOT NULL,
                available_usdt REAL NOT NULL,
                positions_value_usdt REAL NOT NULL,
                open_positions INTEGER NOT NULL,
                positions_json TEXT,
                daily_pnl REAL,
                total_pnl REAL
            )
        ''')
        
        # Tabela de resumo diário
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                starting_balance REAL NOT NULL,
                ending_balance REAL NOT NULL,
                daily_pnl REAL NOT NULL,
                total_trades INTEGER NOT NULL,
                winning_trades INTEGER NOT NULL,
                losing_trades INTEGER NOT NULL,
                win_rate REAL NOT NULL,
                best_trade_pnl REAL,
                worst_trade_pnl REAL,
                traded_symbols TEXT,
                daily_goal_reached INTEGER DEFAULT 0
            )
        ''')
        
        # Tabela de eventos do bot
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Banco de dados de histórico inicializado com todas as tabelas")
    
    def _save_trade_to_csv(self, trade_record: Dict):
        """Salva trade em CSV diário"""
        try:
            csv_dir = 'data/reports'
            os.makedirs(csv_dir, exist_ok=True)
            
            today = datetime.now().strftime('%Y-%m-%d')
            csv_file = os.path.join(csv_dir, f'trades_{today}.csv')
            
            file_exists = os.path.isfile(csv_file)
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                fieldnames = ['timestamp', 'symbol', 'side', 'entry_price', 'exit_price', 
                            'amount', 'pnl', 'pnl_pct', 'duration_minutes', 'entry_reason', 'exit_reason']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'timestamp': trade_record['exit_time'],
                    'symbol': trade_record['symbol'],
                    'side': trade_record['side'],
                    'entry_price': trade_record['entry_price'],
                    'exit_price': trade_record['exit_price'],
                    'amount': trade_record['amount'],
                    'pnl': trade_record['pnl'],
                    'pnl_pct': trade_record['pnl_pct'],
                    'duration_minutes': trade_record['duration_minutes'],
                    'entry_reason': trade_record['entry_reason'],
                    'exit_reason': trade_record['exit_reason']
                })
            
            logger.debug(f"✅ Trade salvo em CSV: {csv_file}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar CSV: {e}")
    
    def _save_trade_to_db(self, trade_record: Dict):
        """Salva trade no banco de dados SQLite"""
        try:
            conn = sqlite3.connect(self.history_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (
                    timestamp, symbol, side, entry_price, exit_price, amount,
                    pnl, pnl_pct, entry_time, exit_time, entry_reason, exit_reason,
                    duration_minutes, entry_rsi, entry_macd, strategy
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_record['exit_time'],
                trade_record['symbol'],
                trade_record['side'],
                trade_record['entry_price'],
                trade_record['exit_price'],
                trade_record['amount'],
                trade_record['pnl'],
                trade_record['pnl_pct'],
                trade_record['entry_time'],
                trade_record['exit_time'],
                trade_record['entry_reason'],
                trade_record['exit_reason'],
                trade_record['duration_minutes'],
                trade_record.get('entry_indicators', {}).get('rsi'),
                trade_record.get('entry_indicators', {}).get('macd'),
                self.strategy.name
            ))
            
            conn.commit()
            conn.close()
            logger.debug("✅ Trade salvo no banco de dados")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar no DB: {e}")
    
    def _save_analysis_to_db(self, symbol: str, price: float, signal: str, reason: str, indicators: Dict):
        """Salva cada análise de mercado no banco"""
        try:
            conn = sqlite3.connect(self.history_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO market_analysis (
                    timestamp, symbol, price, rsi, macd, macd_signal, sma_20, signal, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                symbol,
                price,
                indicators.get('rsi'),
                indicators.get('macd'),
                indicators.get('macd_signal'),
                indicators.get('sma_20'),
                signal,
                reason
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Erro ao salvar análise: {e}")
    
    def _save_all_trades_json(self):
        """Salva TODOS os trades em arquivo JSON único"""
        try:
            with open(self.all_trades_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'bot_start_time': self.start_time.isoformat(),
                    'total_trades': len(self.trades_history),
                    'trades': self.trades_history,
                    'statistics': self.stats,
                    'last_update': datetime.now().isoformat()
                }, f, indent=2, default=str)
            logger.debug("✅ Histórico completo salvo em JSON")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar JSON completo: {e}")
    
    def _get_trades_by_symbol(self) -> Dict:
        """Retorna estatísticas por símbolo"""
        stats_by_symbol = {}
        for trade in self.trades_history:
            symbol = trade['symbol']
            if symbol not in stats_by_symbol:
                stats_by_symbol[symbol] = {
                    'total': 0,
                    'wins': 0,
                    'losses': 0,
                    'pnl': 0.0
                }
            
            stats_by_symbol[symbol]['total'] += 1
            stats_by_symbol[symbol]['pnl'] += trade['pnl']
            if trade['pnl'] > 0:
                stats_by_symbol[symbol]['wins'] += 1
            else:
                stats_by_symbol[symbol]['losses'] += 1
        
        return stats_by_symbol
    
    def _save_portfolio_snapshot(self, balances: Dict = None):
        """Salva snapshot do portfolio no banco de dados"""
        try:
            # Usa o saldo atual das estatísticas
            usdt_balance = self.stats.get('current_balance', 0)
            
            # Calcula valor das posições
            positions_value = 0
            for symbol, pos in self.positions.items():
                if pos is not None:
                    positions_value += pos.get('amount', 0) * pos.get('entry_price', 0)
            
            open_positions = sum(1 for p in self.positions.values() if p is not None)
            total_balance = usdt_balance + positions_value
            
            # Posições atuais como JSON
            positions_data = {}
            for k, v in self.positions.items():
                if v is not None:
                    positions_data[k] = {
                        'symbol': v.get('symbol', k),
                        'entry_price': v.get('entry_price', 0),
                        'amount': v.get('amount', 0),
                        'side': v.get('side', 'BUY'),
                        'entry_time': v.get('entry_time', datetime.now()).isoformat() if isinstance(v.get('entry_time'), datetime) else str(v.get('entry_time', ''))
                    }
            
            conn = sqlite3.connect(self.history_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO portfolio_snapshots (
                    timestamp, total_balance_usdt, available_usdt, positions_value_usdt,
                    open_positions, positions_json, daily_pnl, total_pnl
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                total_balance,
                usdt_balance,
                positions_value,
                open_positions,
                json.dumps(positions_data, default=str),
                self.stats['daily_pnl'],
                self.stats['total_pnl']
            ))
            
            conn.commit()
            conn.close()
            logger.debug("📊 Snapshot do portfolio salvo")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar snapshot: {e}")
    
    def _save_daily_summary(self):
        """Salva resumo do dia no banco de dados"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Coleta trades do dia
            today_trades = [t for t in self.trades_history 
                          if t.get('exit_time', '').startswith(today)]
            
            win_rate = (self.stats['winning_trades'] / self.stats['total_trades'] * 100) \
                      if self.stats['total_trades'] > 0 else 0
            
            # Melhor e pior trade do dia
            best_trade = max([t['pnl'] for t in today_trades], default=0)
            worst_trade = min([t['pnl'] for t in today_trades], default=0)
            
            # Símbolos negociados
            traded = list(set(t['symbol'] for t in today_trades))
            
            conn = sqlite3.connect(self.history_db_path)
            cursor = conn.cursor()
            
            # Upsert (insert ou update)
            cursor.execute('''
                INSERT INTO daily_summary (
                    date, starting_balance, ending_balance, daily_pnl,
                    total_trades, winning_trades, losing_trades, win_rate,
                    best_trade_pnl, worst_trade_pnl, traded_symbols, daily_goal_reached
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    ending_balance = excluded.ending_balance,
                    daily_pnl = excluded.daily_pnl,
                    total_trades = excluded.total_trades,
                    winning_trades = excluded.winning_trades,
                    losing_trades = excluded.losing_trades,
                    win_rate = excluded.win_rate,
                    best_trade_pnl = excluded.best_trade_pnl,
                    worst_trade_pnl = excluded.worst_trade_pnl,
                    traded_symbols = excluded.traded_symbols,
                    daily_goal_reached = excluded.daily_goal_reached
            ''', (
                today,
                self.stats.get('starting_balance', self.stats['current_balance']),
                self.stats['current_balance'],
                self.stats['daily_pnl'],
                self.stats['total_trades'],
                self.stats['winning_trades'],
                self.stats['losing_trades'],
                win_rate,
                best_trade,
                worst_trade,
                json.dumps(traded),
                1 if self.stats['daily_pnl'] >= self.daily_goal else 0
            ))
            
            conn.commit()
            conn.close()
            logger.debug("📅 Resumo diário atualizado")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar resumo diário: {e}")
    
    def _save_bot_event(self, event_type: str, description: str, details: Dict = None):
        """Salva evento do bot no histórico"""
        try:
            conn = sqlite3.connect(self.history_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bot_events (timestamp, event_type, description, details)
                VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                event_type,
                description,
                json.dumps(details) if details else None
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"📝 Evento registrado: {event_type}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar evento: {e}")
    
    def _save_complete_history(self):
        """Salva histórico completo em arquivo JSON (backup geral)"""
        try:
            os.makedirs('data/history', exist_ok=True)
            
            history = {
                'export_time': datetime.now().isoformat(),
                'bot_info': {
                    'start_time': self.start_time.isoformat() if self.start_time else None,
                    'strategy': self.strategy.name,
                    'symbols': self.symbols,
                    'max_positions': self.max_positions,
                    'trade_amount': self.trade_amount,
                    'daily_goal': self.daily_goal
                },
                'statistics': {
                    'current_balance': self.stats['current_balance'],
                    'initial_balance': self.stats['initial_balance'],
                    'total_pnl': self.stats['total_pnl'],
                    'daily_pnl': self.stats['daily_pnl'],
                    'total_trades': self.stats['total_trades'],
                    'winning_trades': self.stats['winning_trades'],
                    'losing_trades': self.stats['losing_trades'],
                    'win_rate': (self.stats['winning_trades'] / self.stats['total_trades'] * 100) 
                               if self.stats['total_trades'] > 0 else 0
                },
                'positions': {
                    k: v for k, v in self.positions.items() if v is not None
                },
                'trades_history': self.trades_history,
                'trades_by_symbol': self._get_trades_by_symbol()
            }
            
            # Salva com timestamp
            filename = f"data/history/complete_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, default=str)
            
            # Também salva versão "latest"
            with open('data/history/complete_history_latest.json', 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, default=str)
            
            logger.info(f"💾 Histórico completo salvo: {filename}")
            
            # Limpa históricos antigos (mantém últimos 48)
            self._cleanup_old_history_files()
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar histórico completo: {e}")
    
    def _cleanup_old_history_files(self, max_files: int = 48):
        """Remove arquivos de histórico antigos"""
        try:
            history_dir = 'data/history'
            files = sorted([
                f for f in os.listdir(history_dir) 
                if f.startswith('complete_history_') and f != 'complete_history_latest.json'
            ])
            
            while len(files) > max_files:
                old_file = files.pop(0)
                os.remove(os.path.join(history_dir, old_file))
                logger.debug(f"🗑️ Histórico antigo removido: {old_file}")
        except Exception as e:
            logger.error(f"❌ Erro na limpeza: {e}")
    
    def start(self):
        """Inicia o bot"""
        if self.is_running:
            logger.warning("⚠️ Bot já está rodando!")
            return
        
        logger.info("🚀 Iniciando bot de trading...")
        self.is_running = True
        self.start_time = datetime.now()
        
        # Registra evento de início
        self._save_bot_event('BOT_START', 'Bot iniciado', {
            'strategy': self.strategy.name,
            'symbols': self.symbols,
            'balance': self.stats['current_balance'],
            'max_positions': self.max_positions
        })
        
        try:
            self.trading_loop()
        except Exception as e:
            logger.error(f"❌ Erro fatal: {e}", exc_info=True)
            self._save_bot_event('BOT_ERROR', f'Erro fatal: {str(e)}')
        finally:
            self.stop()
    
    def stop(self):
        """Para o bot"""
        if not self.is_running:
            return
        
        logger.info("🛑 Parando bot...")
        self.is_running = False
        
        # Fecha todas as posições abertas
        for symbol, position in self.positions.items():
            if position is not None:
                logger.info(f"🔒 Fechando posição {symbol}...")
                try:
                    ticker = self.exchange.fetch_ticker(symbol)
                    if ticker:
                        self.close_position(symbol, ticker['last'], "Bot parado")
                except Exception as e:
                    logger.error(f"❌ Erro ao fechar {symbol}: {e}")
        
        # Salva estado final
        self._save_state()
        
        # Salva histórico completo ao parar
        self._save_complete_history()
        self._save_daily_summary()
        
        # Registra evento de parada
        runtime = (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0
        self._save_bot_event('BOT_STOP', 'Bot parado', {
            'runtime_minutes': runtime,
            'final_balance': self.stats['current_balance'],
            'total_pnl': self.stats['total_pnl'],
            'daily_pnl': self.stats['daily_pnl'],
            'total_trades': self.stats['total_trades']
        })
        
        # Exibe resumo final
        logger.info("\n" + "="*60)
        logger.info("📊 RELATÓRIO FINAL")
        logger.info("="*60)
        logger.info(f"⏱️  Tempo de execução: {runtime:.1f} minutos")
        logger.info(f"💰 Saldo final: {self.stats['current_balance']:.2f} USDT")
        logger.info(f"📈 PnL total: {self.stats['total_pnl']:+.2f} USDT")
        logger.info(f"📊 Total de trades: {self.stats['total_trades']}")
        logger.info(f"✅ Ganhos: {self.stats['winning_trades']}")
        logger.info(f"❌ Perdas: {self.stats['losing_trades']}")
        if self.stats['total_trades'] > 0:
            win_rate = (self.stats['winning_trades'] / self.stats['total_trades']) * 100
            logger.info(f"🎯 Win Rate: {win_rate:.1f}%")
        logger.info("="*60)
        logger.info("💾 Histórico completo salvo em data/history/")
        logger.info("✅ Bot encerrado com sucesso!")


def main():
    """Função principal"""
    # Configura logging
    config = load_config()
    setup_logging(
        log_level=config['logging']['level'],
        log_file=config['logging']['file']
    )
    
    # Cria e inicia bot
    bot = TradingBot()
    
    try:
        bot.start()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupção pelo usuário")
        bot.stop()
    except Exception as e:
        logger.critical(f"❌ Erro fatal: {e}", exc_info=True)
        bot.stop()


if __name__ == "__main__":
    main()
