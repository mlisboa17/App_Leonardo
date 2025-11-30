"""
🤖 App Leonardo - Bot de Trading com WebSocket
Versão que usa dados em tempo real via WebSocket (mais rápido que REST)

Diferenças do main.py:
- Recebe dados instantaneamente via WebSocket
- Não precisa fazer polling a cada X segundos
- Reage imediatamente a mudanças de preço
"""

import os
import sys
import asyncio
import signal
import logging
from datetime import datetime
from typing import Dict, Optional

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.utils import load_config, load_env_credentials, setup_logging
from core.websocket_client import BinanceWebSocket
from core.exchange_client import ExchangeClient
from safety.safety_manager import SafetyManager

# Smart Strategy
try:
    from src.strategies.smart_strategy import SmartStrategy
    SMART_STRATEGY = True
except ImportError:
    from src.strategies.simple_strategies_new import get_strategy
    SMART_STRATEGY = False

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class WebSocketTradingBot:
    """
    Bot de Trading usando WebSocket para dados em tempo real
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        logger.info("="*60)
        logger.info("🤖 APP LEONARDO - MODO WEBSOCKET")
        logger.info("="*60)
        
        # Carrega configurações
        self.config = load_config(config_path)
        self.credentials = load_env_credentials()
        
        # Estado
        self.is_running = False
        self.positions: Dict[str, Optional[Dict]] = {}
        self.last_prices: Dict[str, float] = {}
        
        # Estatísticas
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'daily_pnl': 0.0,
        }
        
        # Configurações
        self.symbols = [s.replace('/', '') for s in self.config['trading']['symbols']]
        self.symbols_original = self.config['trading']['symbols']
        self.timeframe = self.config['trading']['timeframe']
        self.amount_per_trade = self.config['trading']['amount_per_trade']
        self.max_positions = self.config['trading']['max_positions']
        self.testnet = self.config['exchange']['testnet']
        self.dry_run = self.config['execution']['dry_run']
        
        # Inicializa componentes
        self._init_components()
        
        logger.info(f"✅ Bot WebSocket inicializado!")
        logger.info(f"   Símbolos: {', '.join(self.symbols)}")
        logger.info(f"   Modo: {'DRY RUN' if self.dry_run else 'REAL'}")
        logger.info(f"   Testnet: {self.testnet}")
    
    
    def _init_components(self):
        """Inicializa componentes"""
        
        # WebSocket
        self.ws = BinanceWebSocket(testnet=self.testnet)
        
        # Exchange Client (para ordens)
        api_key = self.credentials.get('BINANCE_TESTNET_API_KEY' if self.testnet else 'BINANCE_API_KEY', '')
        api_secret = self.credentials.get('BINANCE_TESTNET_API_SECRET' if self.testnet else 'BINANCE_API_SECRET', '')
        
        self.exchange = ExchangeClient(
            exchange_name='binance',
            api_key=api_key,
            api_secret=api_secret,
            testnet=self.testnet
        )
        
        # Estratégia
        if SMART_STRATEGY:
            self.strategy = SmartStrategy(self.config)
            logger.info(f"🧠 Estratégia: {self.strategy.name}")
        else:
            self.strategy = get_strategy('aggressive', self.config)
            logger.info(f"📊 Estratégia: {self.strategy.name}")
        
        # Safety Manager
        self.safety = SafetyManager(self.config['safety'])
        
        # Inicializa posições
        for symbol in self.symbols_original:
            self.positions[symbol] = None
    
    
    async def on_kline(self, kline: dict):
        """
        Callback chamado quando recebe novo candle
        Este é o coração do bot - processa cada atualização
        """
        
        symbol = kline['symbol']
        symbol_formatted = f"{symbol[:-4]}/{symbol[-4:]}"  # BTCUSDT -> BTC/USDT
        price = kline['close']
        
        # Atualiza último preço
        self.last_prices[symbol_formatted] = price
        
        # Só processa quando candle fecha (evita ruído)
        if not kline['is_closed']:
            return
        
        try:
            # Obtém DataFrame com candles
            df = self.ws.get_candles(symbol)
            
            if df.empty or len(df) < 20:
                # Precisa de pelo menos 20 candles para calcular indicadores
                return
            
            # Verifica posição existente
            position = self.positions.get(symbol_formatted)
            
            if position:
                # Gerencia posição existente
                await self._manage_position(symbol_formatted, position, df, price)
            else:
                # Procura nova entrada
                await self._find_entry(symbol_formatted, df, price)
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar {symbol}: {e}")
    
    
    async def _manage_position(self, symbol: str, position: dict, df, current_price: float):
        """Gerencia posição existente"""
        
        entry_price = position['entry_price']
        entry_time = position['entry_time']
        
        # Usa Smart Strategy se disponível
        if hasattr(self.strategy, 'should_sell'):
            should_close, reason = self.strategy.should_sell(
                symbol=symbol,
                entry_price=entry_price,
                current_price=current_price,
                df=df,
                position_time=entry_time
            )
            
            if should_close:
                await self._close_position(symbol, current_price, reason)
            else:
                # Log status
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                logger.info(f"📊 {symbol}: {reason} ({pnl_pct:+.2f}%)")
        else:
            # Fallback para estratégia antiga
            signal, reason, _ = self.strategy.analyze(df, symbol)
            
            if signal == 'SELL':
                await self._close_position(symbol, current_price, reason)
    
    
    async def _find_entry(self, symbol: str, df, current_price: float):
        """Procura oportunidade de entrada"""
        
        # Verifica se pode abrir mais posições
        open_positions = sum(1 for p in self.positions.values() if p is not None)
        if open_positions >= self.max_positions:
            return
        
        # Usa Smart Strategy se disponível
        if hasattr(self.strategy, 'should_buy'):
            should_buy, reason = self.strategy.should_buy(symbol, df, current_price)
            
            if should_buy:
                await self._open_position(symbol, 'BUY', current_price, reason)
        else:
            # Fallback
            signal, reason, indicators = self.strategy.analyze(df, symbol)
            
            if signal == 'BUY':
                await self._open_position(symbol, signal, current_price, reason)
    
    
    async def _open_position(self, symbol: str, side: str, price: float, reason: str):
        """Abre nova posição"""
        
        # Calcula quantidade
        amount = self.amount_per_trade / price
        
        logger.info(f"""
╔══════════════════════════════════════════════════════╗
║  🟢 ABRINDO POSIÇÃO                                  ║
╠══════════════════════════════════════════════════════╣
║  Símbolo: {symbol:<20}                         ║
║  Lado: {side:<23}                         ║
║  Preço: ${price:<20.2f}                      ║
║  Quantidade: {amount:<15.6f}                      ║
║  Valor: ${self.amount_per_trade:<20.2f}                      ║
║  Razão: {reason[:40]:<40} ║
╚══════════════════════════════════════════════════════╝
""")
        
        if not self.dry_run:
            try:
                order = self.exchange.create_order(
                    symbol=symbol,
                    order_type='market',
                    side=side.lower(),
                    amount=amount
                )
                logger.info(f"✅ Ordem executada: {order.get('id', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ Erro ao executar ordem: {e}")
                return
        
        # Registra posição
        self.positions[symbol] = {
            'side': side,
            'entry_price': price,
            'amount': amount,
            'entry_time': datetime.now(),
            'reason': reason,
        }
        
        self.stats['total_trades'] += 1
    
    
    async def _close_position(self, symbol: str, price: float, reason: str):
        """Fecha posição existente"""
        
        position = self.positions[symbol]
        if not position:
            return
        
        # Calcula PnL
        if position['side'] == 'BUY':
            pnl = (price - position['entry_price']) * position['amount']
            pnl_pct = ((price - position['entry_price']) / position['entry_price']) * 100
        else:
            pnl = (position['entry_price'] - price) * position['amount']
            pnl_pct = ((position['entry_price'] - price) / position['entry_price']) * 100
        
        # Atualiza estatísticas
        self.stats['daily_pnl'] += pnl
        if pnl > 0:
            self.stats['winning_trades'] += 1
        else:
            self.stats['losing_trades'] += 1
        
        emoji = "🟢" if pnl > 0 else "🔴"
        
        logger.info(f"""
╔══════════════════════════════════════════════════════╗
║  {emoji} FECHANDO POSIÇÃO                               ║
╠══════════════════════════════════════════════════════╣
║  Símbolo: {symbol:<20}                         ║
║  Entrada: ${position['entry_price']:<20.2f}                      ║
║  Saída: ${price:<22.2f}                      ║
║  PnL: ${pnl:<21.2f} ({pnl_pct:+.2f}%)             ║
║  Razão: {reason[:40]:<40} ║
║  PnL Diário: ${self.stats['daily_pnl']:<18.2f}                      ║
╚══════════════════════════════════════════════════════╝
""")
        
        if not self.dry_run:
            try:
                close_side = 'sell' if position['side'] == 'BUY' else 'buy'
                order = self.exchange.create_order(
                    symbol=symbol,
                    order_type='market',
                    side=close_side,
                    amount=position['amount']
                )
                logger.info(f"✅ Ordem de fechamento executada: {order.get('id', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ Erro ao fechar posição: {e}")
        
        # Atualiza estratégia
        if hasattr(self.strategy, 'update_trade_stats'):
            self.strategy.update_trade_stats(symbol, pnl)
        
        # Limpa posição
        self.positions[symbol] = None
    
    
    async def start(self):
        """Inicia o bot"""
        
        logger.info("🚀 Iniciando bot WebSocket...")
        self.is_running = True
        
        # Inscreve em klines de todos os símbolos
        await self.ws.subscribe_klines(
            symbols=self.symbols,
            interval=self.timeframe.replace('m', 'm').replace('h', 'h'),
            callback=self.on_kline
        )
        
        logger.info("👂 Escutando dados em tempo real...")
        logger.info("   Pressione Ctrl+C para parar\n")
        
        # Loop principal
        try:
            await self.ws.start()
        except asyncio.CancelledError:
            logger.info("🛑 Bot cancelado")
        finally:
            await self.stop()
    
    
    async def stop(self):
        """Para o bot"""
        
        logger.info("🛑 Parando bot...")
        self.is_running = False
        
        await self.ws.stop()
        
        # Mostra resumo
        win_rate = (self.stats['winning_trades'] / self.stats['total_trades'] * 100) if self.stats['total_trades'] > 0 else 0
        
        logger.info(f"""
╔══════════════════════════════════════════════════════╗
║  📊 RESUMO DA SESSÃO                                 ║
╠══════════════════════════════════════════════════════╣
║  Total de Trades: {self.stats['total_trades']:<20}              ║
║  Trades Vencedores: {self.stats['winning_trades']:<18}              ║
║  Trades Perdedores: {self.stats['losing_trades']:<18}              ║
║  Win Rate: {win_rate:<20.1f}%             ║
║  PnL Diário: ${self.stats['daily_pnl']:<18.2f}              ║
╚══════════════════════════════════════════════════════╝
""")


async def main():
    """Função principal"""
    
    bot = WebSocketTradingBot()
    
    # Handler para Ctrl+C
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        asyncio.create_task(bot.stop())
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows não suporta add_signal_handler
            pass
    
    await bot.start()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════╗
║  🤖 APP LEONARDO - MODO WEBSOCKET                    ║
║  Dados em tempo real da Binance                      ║
╚══════════════════════════════════════════════════════╝
""")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Até logo!")
