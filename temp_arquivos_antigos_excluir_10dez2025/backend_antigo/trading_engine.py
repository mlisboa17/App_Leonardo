"""
Trading Engine - Motor Assíncrono de Trading
"""
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime
from typing import Dict, Optional
from loguru import logger

from backend.config import settings
from backend.database import AsyncSessionLocal, Trade, Position, MarketData, BotStatus, Analysis
from backend.redis_manager import RedisManager
from src.indicators.technical_indicators import TechnicalIndicators

# Importa estratégia inteligente (com perfis por moeda)
try:
    from src.strategies.smart_strategy import SmartStrategy, get_strategy
    SMART_STRATEGY = True
except ImportError:
    from src.strategies.simple_strategies_new import get_strategy
    SMART_STRATEGY = False

import pandas as pd


class TradingEngine:
    """Motor principal de trading assíncrono"""
    
    def __init__(self, redis_manager: RedisManager, websocket_manager):
        self.redis = redis_manager
        self.ws_manager = websocket_manager
        self.is_running = False
        self.exchange: Optional[ccxt.binance] = None
        self.strategy = None
        self.positions: Dict[str, Optional[Dict]] = {}
        
        # Estatísticas
        self.stats = {
            'balance': 0.0,
            'initial_balance': 0.0,
            'daily_pnl': 0.0,
            'total_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0
        }
        
        logger.info("✅ Trading Engine criado")
    
    async def start(self):
        """Inicia o motor de trading"""
        if self.is_running:
            logger.warning("⚠️ Engine já está rodando")
            return
        
        logger.info("🚀 Iniciando Trading Engine...")
        self.is_running = True
        
        # Conecta à exchange
        await self._init_exchange()
        
        # Carrega estratégia
        self._load_strategy()
        
        # Inicializa posições
        for symbol in settings.SYMBOLS:
            self.positions[symbol] = None
        
        # Atualiza saldo
        await self._update_balance()
        
        # Salva status inicial
        await self._save_status()
        
        # Inicia loop de trading
        asyncio.create_task(self._trading_loop())
        
        logger.success("✅ Trading Engine iniciado!")
    
    async def stop(self):
        """Para o motor de trading"""
        if not self.is_running:
            return
        
        logger.info("🛑 Parando Trading Engine...")
        self.is_running = False
        
        # Fecha todas as posições
        for symbol in list(self.positions.keys()):
            if self.positions[symbol]:
                await self._close_position(symbol, "Engine parado")
        
        # Fecha exchange
        if self.exchange:
            await self.exchange.close()
        
        # Salva status final
        await self._save_status()
        
        logger.success("✅ Trading Engine parado!")
    
    async def _init_exchange(self):
        """Inicializa conexão com a exchange"""
        if settings.BINANCE_TESTNET:
            api_key = settings.BINANCE_TESTNET_API_KEY
            api_secret = settings.BINANCE_TESTNET_API_SECRET
        else:
            api_key = settings.BINANCE_API_KEY
            api_secret = settings.BINANCE_API_SECRET
        
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        if settings.BINANCE_TESTNET:
            self.exchange.set_sandbox_mode(True)
            logger.info("🧪 Modo TESTNET ativado")
        
        logger.info("✅ Conectado à Binance")
    
    def _load_strategy(self):
        """Carrega estratégia de trading"""
        config = {
            'indicators': {
                'rsi': {
                    'period': 14,
                    'oversold': settings.RSI_OVERSOLD,
                    'overbought': settings.RSI_OVERBOUGHT
                },
                'macd': {'fast': 12, 'slow': 26, 'signal': 9},
                'sma': {'periods': [20, 50, 200]}
            }
        }
        
        # Usa estratégia inteligente (com perfis por moeda)
        if SMART_STRATEGY:
            self.strategy = SmartStrategy(config)
            logger.info(f"🧠 Estratégia INTELIGENTE carregada: {self.strategy.name}")
        else:
            self.strategy = get_strategy(settings.STRATEGY_TYPE, config)
            logger.info(f"📊 Estratégia carregada: {self.strategy.name}")
    
    async def _update_balance(self):
        """Atualiza saldo"""
        try:
            balance_data = await self.exchange.fetch_balance()
            usdt_balance = balance_data.get('USDT', {})
            self.stats['balance'] = usdt_balance.get('free', 0.0)
            
            if self.stats['initial_balance'] == 0:
                self.stats['initial_balance'] = self.stats['balance']
            
            logger.info(f"💰 Saldo: {self.stats['balance']:.2f} USDT")
        except Exception as e:
            logger.error(f"❌ Erro ao obter saldo: {e}")
    
    async def _trading_loop(self):
        """Loop principal de trading"""
        iteration = 0
        
        while self.is_running:
            try:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"📊 Iteração #{iteration}")
                logger.info(f"{'='*60}")
                
                # Atualiza saldo
                await self._update_balance()
                
                # Processa cada símbolo
                tasks = [self._process_symbol(symbol) for symbol in settings.SYMBOLS]
                await asyncio.gather(*tasks)
                
                # Salva status
                await self._save_status()
                
                # Broadcast via WebSocket
                await self.ws_manager.broadcast({
                    "type": "status_update",
                    "data": self.stats
                })
                
                # Aguarda próxima iteração
                await asyncio.sleep(10)  # 10 segundos
                
            except Exception as e:
                logger.error(f"❌ Erro no loop: {e}")
                await asyncio.sleep(5)
    
    async def _process_symbol(self, symbol: str):
        """Processa um símbolo"""
        try:
            # Busca dados de mercado
            ohlcv = await self.exchange.fetch_ohlcv(symbol, settings.TIMEFRAME, limit=200)
            
            if not ohlcv:
                return
            
            # Converte para DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calcula indicadores
            config = {'indicators': {
                'rsi': {'period': 14, 'oversold': settings.RSI_OVERSOLD, 'overbought': settings.RSI_OVERBOUGHT},
                'macd': {'fast': 12, 'slow': 26, 'signal': 9},
                'sma': {'periods': [20, 50, 200]}
            }}
            df = TechnicalIndicators.calculate_all_indicators(df, config['indicators'])
            
            current_price = df.iloc[-1]['close']
            
            # Cacheia preço no Redis
            await self.redis.set_price(symbol, current_price)
            
            # Salva dados de mercado no DB
            await self._save_market_data(symbol, df.iloc[-1])
            
            # Verifica posição
            if self.positions[symbol]:
                # Gerencia posição existente
                await self._manage_position(symbol, df, current_price)
            else:
                # Procura nova entrada
                await self._check_entry(symbol, df, current_price)
        
        except Exception as e:
            logger.error(f"❌ Erro ao processar {symbol}: {e}")
    
    async def _check_entry(self, symbol: str, df: pd.DataFrame, current_price: float):
        """Verifica entrada em nova posição"""
        # Analisa mercado
        signal, reason, indicators = self.strategy.analyze(df, symbol)
        
        # Salva análise
        await self._save_analysis(symbol, current_price, signal, reason, indicators)
        
        if signal in ['BUY', 'SELL']:
            await self._open_position(symbol, signal, current_price, reason, indicators)
    
    async def _manage_position(self, symbol: str, df: pd.DataFrame, current_price: float):
        """Gerencia posição existente usando estratégia inteligente"""
        position = self.positions[symbol]
        
        # Calcula PnL
        if position['side'] == 'BUY':
            unrealized_pnl = (current_price - position['entry_price']) * position['amount']
        else:
            unrealized_pnl = (position['entry_price'] - current_price) * position['amount']
        
        unrealized_pnl_pct = (unrealized_pnl / settings.AMOUNT_PER_TRADE) * 100
        
        should_close = False
        close_reason = ""
        
        # Usa estratégia inteligente se disponível
        if SMART_STRATEGY and hasattr(self.strategy, 'should_sell'):
            # Pega tempo de abertura da posição
            entry_time = datetime.fromisoformat(position['entry_time'])
            
            # Verifica se deve vender usando lógica inteligente
            should_close, close_reason = self.strategy.should_sell(
                symbol=symbol,
                entry_price=position['entry_price'],
                current_price=current_price,
                df=df,
                position_time=entry_time
            )
            
            # Log status
            if not should_close:
                logger.info(f"📊 {symbol}: {close_reason}")
        else:
            # Lógica antiga (fallback)
            signal, reason, indicators = self.strategy.analyze(df, symbol)
            
            # Sinal contrário
            if position['side'] == 'BUY' and signal == 'SELL':
                should_close = True
                close_reason = f"Sinal de venda: {reason}"
            elif position['side'] == 'SELL' and signal == 'BUY':
                should_close = True
                close_reason = f"Sinal de compra: {reason}"
            # Stop Loss
            elif unrealized_pnl_pct <= settings.STOP_LOSS_PCT:
                should_close = True
                close_reason = f"Stop Loss ({unrealized_pnl_pct:.2f}%)"
            # Take Profit
            elif unrealized_pnl_pct >= settings.TAKE_PROFIT_PCT:
                should_close = True
                close_reason = f"Take Profit ({unrealized_pnl_pct:.2f}%)"
        
        if should_close:
            await self._close_position(symbol, close_reason, current_price)
    
    async def _calculate_crypto_holdings(self) -> float:
        """Calcula o valor total em crypto (não USDT)"""
        try:
            balance_data = await self.exchange.fetch_balance()
            total_crypto_value = 0.0
            
            for symbol in settings.SYMBOLS:
                # Extrai o nome da moeda (ex: BTC de BTC/USDT)
                crypto = symbol.split('/')[0]
                crypto_amount = balance_data.get(crypto, {}).get('free', 0.0)
                
                if crypto_amount > 0:
                    try:
                        ticker = await self.exchange.fetch_ticker(symbol)
                        crypto_price = ticker.get('last', 0)
                        total_crypto_value += crypto_amount * crypto_price
                    except:
                        pass
            
            return total_crypto_value
        except Exception as e:
            logger.error(f"❌ Erro ao calcular holdings: {e}")
            return 0.0
    
    async def _can_open_position(self, amount_usdt: float) -> tuple[bool, str]:
        """
        Verifica se pode abrir nova posição baseado nas regras de negócio:
        1. Não pode comprar mais crypto do que tem em USDT
        2. Se não tem nenhuma crypto, pode usar até 15% do USDT
        """
        try:
            # Atualiza saldo USDT
            await self._update_balance()
            usdt_balance = self.stats['balance']
            
            # Calcula valor total em crypto
            crypto_value = await self._calculate_crypto_holdings()
            
            # Conta posições abertas (pelo bot)
            open_positions = sum(1 for p in self.positions.values() if p is not None)
            
            logger.info(f"💰 Verificação de capital: USDT={usdt_balance:.2f}, Crypto={crypto_value:.2f}, Posições={open_positions}")
            
            # REGRA 1: Se não tem nenhuma crypto, pode usar até 15% do USDT
            if crypto_value < 1.0 and open_positions == 0:
                max_allowed = usdt_balance * 0.15  # 15% do saldo
                if amount_usdt <= max_allowed:
                    logger.info(f"✅ Sem crypto - Permitido usar até 15%: ${amount_usdt:.2f} <= ${max_allowed:.2f}")
                    return True, f"Primeira compra (até 15%): ${amount_usdt:.2f}"
                else:
                    logger.warning(f"⚠️ Sem crypto mas tentando usar mais de 15%: ${amount_usdt:.2f} > ${max_allowed:.2f}")
                    return False, f"Limite de 15% para primeira compra: ${amount_usdt:.2f} > ${max_allowed:.2f}"
            
            # REGRA 2: Não pode comprar mais crypto do que tem em USDT disponível
            if amount_usdt > usdt_balance:
                logger.warning(f"⚠️ Saldo insuficiente: tentando usar ${amount_usdt:.2f} mas só tem ${usdt_balance:.2f}")
                return False, f"Saldo insuficiente: ${amount_usdt:.2f} > ${usdt_balance:.2f}"
            
            # REGRA 3: Valor total em crypto não pode exceder USDT disponível
            future_crypto_value = crypto_value + amount_usdt
            if future_crypto_value > usdt_balance:
                logger.warning(f"⚠️ Crypto excederia USDT: ${future_crypto_value:.2f} > ${usdt_balance:.2f}")
                return False, f"Crypto excederia USDT disponível: ${future_crypto_value:.2f} > ${usdt_balance:.2f}"
            
            logger.info(f"✅ Compra permitida: ${amount_usdt:.2f}")
            return True, "Compra dentro dos limites"
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação de capital: {e}")
            return False, f"Erro na verificação: {e}"
    
    async def _open_position(self, symbol: str, signal: str, price: float, reason: str, indicators: Dict):
        """Abre nova posição"""
        amount_usdt = settings.AMOUNT_PER_TRADE
        
        # ========================================
        # REGRAS DE NEGÓCIO - VERIFICAÇÃO DE CAPITAL
        # ========================================
        can_open, capital_reason = await self._can_open_position(amount_usdt)
        
        if not can_open:
            logger.warning(f"🚫 Posição BLOQUEADA em {symbol}: {capital_reason}")
            return
        
        logger.info(f"🟢 Abrindo posição {signal} em {symbol} @ {price:.2f}")
        logger.info(f"   💵 Capital: {capital_reason}")
        
        amount = amount_usdt / price
        
        # Registra posição
        position_data = {
            'symbol': symbol,
            'side': signal,
            'entry_price': price,
            'amount': amount,
            'entry_time': datetime.now().isoformat(),
            'reason': reason,
            'indicators': indicators
        }
        
        self.positions[symbol] = position_data
        
        # Cacheia no Redis
        await self.redis.set_position(symbol, position_data)
        
        # Salva no DB
        await self._save_position_db(position_data)
        
        self.stats['total_trades'] += 1
    
    async def _close_position(self, symbol: str, reason: str, current_price: float = None):
        """Fecha posição"""
        position = self.positions[symbol]
        
        if not current_price:
            ticker = await self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
        
        # Calcula PnL
        if position['side'] == 'BUY':
            pnl = (current_price - position['entry_price']) * position['amount']
        else:
            pnl = (position['entry_price'] - current_price) * position['amount']
        
        pnl_pct = (pnl / settings.AMOUNT_PER_TRADE) * 100
        
        # Atualiza estatísticas
        self.stats['total_pnl'] += pnl
        self.stats['daily_pnl'] += pnl
        
        if pnl > 0:
            self.stats['winning_trades'] += 1
            emoji = "🟢"
        else:
            self.stats['losing_trades'] += 1
            emoji = "🔴"
        
        logger.info(f"{emoji} Fechando posição {symbol}: PnL {pnl:.2f} USDT ({pnl_pct:+.2f}%)")
        logger.info(f"   Motivo: {reason}")
        
        # Atualiza estatísticas da estratégia inteligente
        if SMART_STRATEGY and hasattr(self.strategy, 'update_daily_stats'):
            self.strategy.update_daily_stats(pnl)
        
        # Salva trade no DB
        await self._save_trade_db(position, current_price, pnl, pnl_pct, reason)
        
        # Remove posição
        self.positions[symbol] = None
        await self.redis.remove_position(symbol)
        
        # Broadcast
        await self.ws_manager.broadcast({
            "type": "trade_closed",
            "data": {"symbol": symbol, "pnl": pnl, "pnl_pct": pnl_pct, "reason": reason}
        })
    
    async def _save_market_data(self, symbol: str, candle_data):
        """Salva dados de mercado no DB"""
        async with AsyncSessionLocal() as session:
            market_data = MarketData(
                timestamp=candle_data['timestamp'],
                symbol=symbol,
                open=candle_data['open'],
                high=candle_data['high'],
                low=candle_data['low'],
                close=candle_data['close'],
                volume=candle_data['volume'],
                rsi=candle_data.get('rsi'),
                macd=candle_data.get('MACD_12_26_9'),
                macd_signal=candle_data.get('MACDs_12_26_9'),
                sma_20=candle_data.get('sma_20'),
                sma_50=candle_data.get('sma_50')
            )
            session.add(market_data)
            await session.commit()
    
    async def _save_analysis(self, symbol: str, price: float, signal: str, reason: str, indicators: Dict):
        """Salva análise no DB"""
        async with AsyncSessionLocal() as session:
            analysis = Analysis(
                symbol=symbol,
                price=price,
                rsi=indicators.get('rsi'),
                macd=indicators.get('macd'),
                macd_signal=indicators.get('macd_signal'),
                sma_20=indicators.get('sma_20'),
                signal=signal,
                reason=reason
            )
            session.add(analysis)
            await session.commit()
    
    async def _save_position_db(self, position_data: Dict):
        """Salva posição no DB"""
        async with AsyncSessionLocal() as session:
            position = Position(
                symbol=position_data['symbol'],
                side=position_data['side'],
                entry_price=position_data['entry_price'],
                amount=position_data['amount'],
                entry_time=datetime.fromisoformat(position_data['entry_time']),
                entry_reason=position_data['reason'],
                entry_rsi=position_data['indicators'].get('rsi'),
                entry_macd=position_data['indicators'].get('macd')
            )
            session.add(position)
            await session.commit()
    
    async def _save_trade_db(self, position: Dict, exit_price: float, pnl: float, pnl_pct: float, exit_reason: str):
        """Salva trade no DB"""
        async with AsyncSessionLocal() as session:
            entry_time = datetime.fromisoformat(position['entry_time'])
            exit_time = datetime.now()
            
            trade = Trade(
                symbol=position['symbol'],
                side=position['side'],
                entry_price=position['entry_price'],
                exit_price=exit_price,
                amount=position['amount'],
                pnl=pnl,
                pnl_pct=pnl_pct,
                entry_time=entry_time,
                exit_time=exit_time,
                duration_minutes=(exit_time - entry_time).total_seconds() / 60,
                entry_reason=position['reason'],
                exit_reason=exit_reason,
                entry_rsi=position['indicators'].get('rsi'),
                entry_macd=position['indicators'].get('macd'),
                strategy=self.strategy.name
            )
            session.add(trade)
            await session.commit()
    
    async def _save_status(self):
        """Salva status do bot no DB e Redis"""
        async with AsyncSessionLocal() as session:
            # Busca ou cria status
            from sqlalchemy import select
            result = await session.execute(select(BotStatus).limit(1))
            bot_status = result.scalar_one_or_none()
            
            if not bot_status:
                bot_status = BotStatus()
                session.add(bot_status)
            
            # Atualiza
            bot_status.is_running = self.is_running
            bot_status.last_update = datetime.now()
            bot_status.balance = self.stats['balance']
            bot_status.initial_balance = self.stats['initial_balance']
            bot_status.daily_pnl = self.stats['daily_pnl']
            bot_status.total_pnl = self.stats['total_pnl']
            bot_status.total_trades = self.stats['total_trades']
            bot_status.winning_trades = self.stats['winning_trades']
            bot_status.losing_trades = self.stats['losing_trades']
            bot_status.current_strategy = self.strategy.name
            
            await session.commit()
        
        # Cacheia no Redis
        await self.redis.set_status(self.stats)
