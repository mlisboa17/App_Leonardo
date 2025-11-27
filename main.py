"""
Bot de Trading Leonardo - Main
Arquivo principal de execução
"""
import sys
import time
import logging
import pandas as pd
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
        self.symbol = self.config['trading']['symbol']
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
        
        # Dashboard visual
        self.dashboard = TradingDashboard()
        self.dashboard.update_data(
            symbol=self.symbol,
            timeframe=self.timeframe,
            testnet=config['exchange']['testnet'],
            dry_run=self.dry_run,
            max_daily_loss=config['safety']['max_daily_loss'],
            max_drawdown=config['safety']['max_drawdown'],
            interval=self.interval_seconds
        )
        
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
        
        # Testa conexão
        if not self.exchange.test_connection():
            logger.critical("❌ Falha na conexão com exchange. Encerrando...")
            sys.exit(1)
    
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
    
    def fetch_market_data(self) -> pd.DataFrame:
        """Obtém dados de mercado e calcula indicadores"""
        # Busca OHLCV
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=200)
        
        if not ohlcv:
            logger.error("❌ Falha ao obter dados de mercado")
            return pd.DataFrame()
        
        # Converte para DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calcula indicadores
        df = TechnicalIndicators.calculate_all_indicators(df, self.config['indicators'])
        
        return df
    
    def execute_trade(self, signal: str, reason: str):
        """Executa operação de compra/venda"""
        logger.info(f"🎯 Sinal recebido: {signal.upper()} - {reason}")
        
        # Atualiza dashboard
        self.dashboard.update_data(last_signal=f"{signal.upper()}: {reason}")
        
        # Modo DRY RUN - apenas simula
        if self.dry_run:
            logger.info(f"🔸 MODO DRY RUN - Simulando {signal.upper()}")
            logger.info(f"   Par: {self.symbol} | Valor: ${self.amount_per_trade} USDT")
            self.total_trades += 1
            self.dashboard.update_data(
                trades_count=self.total_trades,
                last_signal=f"🔸 DRY RUN - {signal.upper()}: {reason}"
            )
            return
        
        # Verifica saldo
        balance = self.exchange.fetch_balance()
        if not balance:
            logger.error("❌ Não foi possível obter saldo")
            return
        
        # Validação de saldo
        if signal == 'buy':
            available = balance['free'].get('USDT', 0)
            if not self.safety_manager.order_validator.validate_balance(
                self.amount_per_trade, available
            ):
                return
            
            # Executa compra
            order = self.exchange.create_market_order(
                self.symbol, 
                'buy', 
                self.amount_per_trade / self.get_current_price()
            )
            
        elif signal == 'sell':
            available = balance['free'].get('BTC', 0)  # Adaptar conforme moeda base
            
            # Executa venda
            order = self.exchange.create_market_order(
                self.symbol,
                'sell',
                available  # Vende tudo
            )
        
        else:
            return
        
        # Valida execução da ordem
        if order:
            if self.safety_manager.order_validator.validate_order_response(order):
                # Confirma status na exchange (ANTI-ALUCINAÇÃO)
                time.sleep(1)  # Aguarda processamento
                confirmed_order = self.exchange.fetch_order_status(order['id'], self.symbol)
                
                if confirmed_order:
                    logger.info(f"✅ Ordem confirmada: {confirmed_order['status']}")
                    self.strategy.update_position('long' if signal == 'buy' else None)
                    
                    # Atualiza estatísticas
                    self.total_trades += 1
                    self.dashboard.update_data(
                        trades_count=self.total_trades,
                        position='LONG' if signal == 'buy' else None
                    )
    
    def get_current_price(self) -> float:
        """Obtém preço atual"""
        ticker = self.exchange.fetch_ticker(self.symbol)
        return ticker['last'] if ticker else 0.0
    
    def run_cycle(self):
        """Executa um ciclo de análise"""
        try:
            logger.info(f"🔄 Ciclo iniciado - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Atualiza status
            self.dashboard.update_data(status='Analisando...')
            
            # Atualiza saldo
            balance = self.exchange.fetch_balance()
            if balance:
                self.current_balance = balance['total'].get('USDT', 0)
                self.dashboard.update_data(balance=self.current_balance)
            
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
            
            # Obtém dados de mercado
            df = self.fetch_market_data()
            if df.empty:
                logger.warning("⚠️ Dados insuficientes neste ciclo")
                return True
            
            # Valida preço
            current_price = df['close'].iloc[-1]
            
            # Atualiza dashboard com preço
            self.dashboard.update_data(current_price=current_price)
            
            if not self.safety_manager.price_validator.validate_price(current_price, self.symbol):
                logger.warning("⚠️ Preço suspeito detectado - pulando ciclo")
                self.dashboard.update_data(
                    status='Aguardando',
                    last_signal='⚠️ Preço suspeito - ciclo pulado'
                )
                return True
            
            # Atualiza indicadores no dashboard
            self.dashboard.update_data(
                rsi=df['rsi'].iloc[-1] if 'rsi' in df.columns else None,
                macd=df.get('MACD_12_26_9', pd.Series([None])).iloc[-1],
                macd_signal=df.get('MACDs_12_26_9', pd.Series([None])).iloc[-1],
                sma_20=df.get('sma_20', pd.Series([None])).iloc[-1],
                sma_50=df.get('sma_50', pd.Series([None])).iloc[-1],
                sma_200=df.get('sma_200', pd.Series([None])).iloc[-1]
            )
            
            # Analisa estratégia
            analysis = self.strategy.analyze(df)
            logger.info(f"📊 Análise: {analysis['signal']} - {analysis['reason']}")
            
            # Atualiza dashboard
            self.dashboard.update_data(
                status='Operando',
                last_signal=f"{analysis['signal'].upper()}: {analysis['reason']}",
                daily_pnl=self.daily_pnl
            )
            
            # Executa trades
            if analysis['signal'] in ['buy', 'sell']:
                self.execute_trade(analysis['signal'], analysis['reason'])
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo: {e}", exc_info=True)
            return True
    
    def start(self, interval_seconds: int = None):
        """Inicia o bot"""
        if interval_seconds is None:
            interval_seconds = self.interval_seconds
            
        logger.info("🚀 Iniciando Trading Bot...")
        logger.info(f"📈 Par: {self.symbol} | Timeframe: {self.timeframe}")
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
