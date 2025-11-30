"""
🔌 WebSocket Client para Binance
Recebe dados em tempo real (muito mais rápido que REST API)

Streams disponíveis:
- kline_1m: Candles de 1 minuto
- trade: Trades individuais
- ticker: Ticker 24h
- depth: Order book
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Callable, Optional, List
import pandas as pd

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    print("⚠️ Instale websockets: pip install websockets")

logger = logging.getLogger(__name__)


class BinanceWebSocket:
    """
    Cliente WebSocket para Binance
    
    Uso:
        ws = BinanceWebSocket(testnet=True)
        await ws.subscribe_klines(['BTCUSDT', 'ETHUSDT'], '1m', callback)
        await ws.start()
    """
    
    # URLs dos WebSockets
    MAINNET_WS = "wss://stream.binance.com:9443/ws"
    MAINNET_COMBINED = "wss://stream.binance.com:9443/stream"
    TESTNET_WS = "wss://testnet.binance.vision/ws"
    TESTNET_COMBINED = "wss://testnet.binance.vision/stream"
    
    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        self.base_url = self.TESTNET_WS if testnet else self.MAINNET_WS
        self.combined_url = self.TESTNET_COMBINED if testnet else self.MAINNET_COMBINED
        
        self.ws = None
        self.is_running = False
        self.subscriptions: Dict[str, Callable] = {}
        
        # Cache de candles para cada símbolo
        self.candles_cache: Dict[str, pd.DataFrame] = {}
        self.max_candles = 100  # Mantém últimos 100 candles
        
        # Callbacks
        self.on_kline: Optional[Callable] = None
        self.on_trade: Optional[Callable] = None
        self.on_ticker: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        logger.info(f"🔌 WebSocket inicializado ({'TESTNET' if testnet else 'MAINNET'})")
    
    
    def _build_stream_url(self, streams: List[str]) -> str:
        """Constrói URL para múltiplos streams"""
        if len(streams) == 1:
            return f"{self.base_url}/{streams[0]}"
        else:
            combined = "/".join(streams)
            return f"{self.combined_url}?streams={combined}"
    
    
    async def connect(self, streams: List[str]):
        """Conecta ao WebSocket com os streams especificados"""
        
        if not HAS_WEBSOCKETS:
            logger.error("❌ Biblioteca websockets não instalada!")
            return
        
        url = self._build_stream_url(streams)
        logger.info(f"🔗 Conectando a: {url}")
        
        try:
            self.ws = await websockets.connect(url, ping_interval=20)
            self.is_running = True
            logger.info("✅ WebSocket conectado!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar WebSocket: {e}")
            self.is_running = False
    
    
    async def subscribe_klines(self, symbols: List[str], interval: str = '1m', 
                                callback: Optional[Callable] = None):
        """
        Inscreve em streams de candles (klines)
        
        Args:
            symbols: Lista de símbolos ['BTCUSDT', 'ETHUSDT']
            interval: Timeframe ('1m', '5m', '15m', '1h', etc)
            callback: Função chamada quando receber novo candle
        """
        
        streams = [f"{s.lower()}@kline_{interval}" for s in symbols]
        
        if callback:
            self.on_kline = callback
        
        await self.connect(streams)
        
        # Inicializa cache de candles
        for symbol in symbols:
            self.candles_cache[symbol.upper()] = pd.DataFrame()
        
        logger.info(f"📊 Inscrito em klines: {symbols} ({interval})")
    
    
    async def subscribe_trades(self, symbols: List[str], callback: Optional[Callable] = None):
        """Inscreve em trades em tempo real"""
        
        streams = [f"{s.lower()}@trade" for s in symbols]
        
        if callback:
            self.on_trade = callback
        
        await self.connect(streams)
        logger.info(f"💹 Inscrito em trades: {symbols}")
    
    
    async def subscribe_tickers(self, symbols: List[str], callback: Optional[Callable] = None):
        """Inscreve em tickers 24h"""
        
        streams = [f"{s.lower()}@ticker" for s in symbols]
        
        if callback:
            self.on_ticker = callback
        
        await self.connect(streams)
        logger.info(f"📈 Inscrito em tickers: {symbols}")
    
    
    async def subscribe_multi(self, symbols: List[str], interval: str = '1m'):
        """
        Inscreve em múltiplos streams de uma vez
        (klines + ticker para cada símbolo)
        """
        
        streams = []
        for s in symbols:
            s_lower = s.lower().replace('/', '')
            streams.append(f"{s_lower}@kline_{interval}")
            streams.append(f"{s_lower}@ticker")
        
        await self.connect(streams)
        
        for symbol in symbols:
            key = symbol.upper().replace('/', '')
            self.candles_cache[key] = pd.DataFrame()
        
        logger.info(f"🔄 Inscrito em multi-stream: {len(symbols)} símbolos")
    
    
    def _parse_kline(self, data: dict) -> dict:
        """Parse dados de kline do WebSocket"""
        k = data.get('k', {})
        
        return {
            'symbol': data.get('s', ''),
            'timestamp': pd.to_datetime(k.get('t', 0), unit='ms'),
            'open': float(k.get('o', 0)),
            'high': float(k.get('h', 0)),
            'low': float(k.get('l', 0)),
            'close': float(k.get('c', 0)),
            'volume': float(k.get('v', 0)),
            'is_closed': k.get('x', False),  # Candle fechado?
            'trades': k.get('n', 0),
        }
    
    
    def _parse_trade(self, data: dict) -> dict:
        """Parse dados de trade"""
        return {
            'symbol': data.get('s', ''),
            'price': float(data.get('p', 0)),
            'quantity': float(data.get('q', 0)),
            'timestamp': pd.to_datetime(data.get('T', 0), unit='ms'),
            'is_buyer_maker': data.get('m', False),
        }
    
    
    def _parse_ticker(self, data: dict) -> dict:
        """Parse dados de ticker 24h"""
        return {
            'symbol': data.get('s', ''),
            'price': float(data.get('c', 0)),  # Último preço
            'price_change': float(data.get('p', 0)),
            'price_change_pct': float(data.get('P', 0)),
            'high_24h': float(data.get('h', 0)),
            'low_24h': float(data.get('l', 0)),
            'volume_24h': float(data.get('v', 0)),
            'trades_24h': int(data.get('n', 0)),
        }
    
    
    def _update_candles_cache(self, kline: dict):
        """Atualiza cache de candles"""
        symbol = kline['symbol']
        
        if symbol not in self.candles_cache:
            self.candles_cache[symbol] = pd.DataFrame()
        
        df = self.candles_cache[symbol]
        
        # Cria novo row
        new_row = pd.DataFrame([{
            'timestamp': kline['timestamp'],
            'open': kline['open'],
            'high': kline['high'],
            'low': kline['low'],
            'close': kline['close'],
            'volume': kline['volume'],
        }])
        
        if kline['is_closed']:
            # Candle fechado - adiciona ao histórico
            self.candles_cache[symbol] = pd.concat([df, new_row], ignore_index=True)
            
            # Limita tamanho do cache
            if len(self.candles_cache[symbol]) > self.max_candles:
                self.candles_cache[symbol] = self.candles_cache[symbol].tail(self.max_candles)
        else:
            # Candle em andamento - atualiza último
            if len(df) > 0:
                self.candles_cache[symbol].iloc[-1] = new_row.iloc[0]
            else:
                self.candles_cache[symbol] = new_row
    
    
    def get_candles(self, symbol: str) -> pd.DataFrame:
        """Retorna DataFrame com candles do símbolo"""
        key = symbol.upper().replace('/', '')
        return self.candles_cache.get(key, pd.DataFrame())
    
    
    async def _handle_message(self, message: str):
        """Processa mensagem recebida do WebSocket"""
        try:
            data = json.loads(message)
            
            # Stream combinado tem wrapper
            if 'stream' in data:
                stream = data['stream']
                data = data['data']
            else:
                stream = None
            
            # Identifica tipo de evento
            event_type = data.get('e', '')
            
            if event_type == 'kline':
                kline = self._parse_kline(data)
                self._update_candles_cache(kline)
                
                if self.on_kline:
                    await self._call_callback(self.on_kline, kline)
                
                # Log apenas quando candle fecha
                if kline['is_closed']:
                    logger.debug(f"📊 {kline['symbol']}: {kline['close']:.2f} (candle fechado)")
            
            elif event_type == 'trade':
                trade = self._parse_trade(data)
                
                if self.on_trade:
                    await self._call_callback(self.on_trade, trade)
            
            elif event_type == '24hrTicker':
                ticker = self._parse_ticker(data)
                
                if self.on_ticker:
                    await self._call_callback(self.on_ticker, ticker)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao decodificar JSON: {e}")
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {e}")
            if self.on_error:
                await self._call_callback(self.on_error, e)
    
    
    async def _call_callback(self, callback: Callable, data):
        """Chama callback (sync ou async)"""
        if asyncio.iscoroutinefunction(callback):
            await callback(data)
        else:
            callback(data)
    
    
    async def listen(self):
        """Loop principal de escuta"""
        
        if not self.ws:
            logger.error("❌ WebSocket não conectado!")
            return
        
        logger.info("👂 Escutando mensagens...")
        
        try:
            async for message in self.ws:
                await self._handle_message(message)
                
                if not self.is_running:
                    break
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"⚠️ Conexão fechada: {e}")
            self.is_running = False
        except Exception as e:
            logger.error(f"❌ Erro no loop de escuta: {e}")
            self.is_running = False
    
    
    async def start(self):
        """Inicia o loop de escuta"""
        await self.listen()
    
    
    async def stop(self):
        """Para o WebSocket"""
        logger.info("🛑 Parando WebSocket...")
        self.is_running = False
        
        if self.ws:
            await self.ws.close()
            self.ws = None
        
        logger.info("✅ WebSocket parado")
    
    
    async def reconnect(self, streams: List[str], max_retries: int = 5):
        """Reconecta automaticamente em caso de desconexão"""
        
        retries = 0
        
        while retries < max_retries:
            try:
                await self.connect(streams)
                await self.listen()
                
            except Exception as e:
                retries += 1
                wait_time = min(30, 2 ** retries)  # Backoff exponencial
                logger.warning(f"⚠️ Reconectando em {wait_time}s... (tentativa {retries}/{max_retries})")
                await asyncio.sleep(wait_time)
        
        logger.error("❌ Máximo de tentativas de reconexão atingido")


# =====================================================
# EXEMPLO DE USO
# =====================================================

async def exemplo_kline_callback(kline: dict):
    """Callback chamado a cada atualização de candle"""
    if kline['is_closed']:
        print(f"🕯️ {kline['symbol']}: O={kline['open']:.2f} H={kline['high']:.2f} L={kline['low']:.2f} C={kline['close']:.2f}")


async def exemplo_uso():
    """Exemplo de como usar o WebSocket"""
    
    # Cria cliente (mainnet para dados públicos - não precisa autenticação)
    ws = BinanceWebSocket(testnet=False)
    
    # Define símbolos
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    
    # Inscreve em klines de 1 minuto
    await ws.subscribe_klines(symbols, '1m', callback=exemplo_kline_callback)
    
    # Escuta por 15 segundos (teste rápido)
    try:
        await asyncio.wait_for(ws.start(), timeout=15)
    except asyncio.TimeoutError:
        print("⏰ Timeout - parando...")
    finally:
        await ws.stop()
        
        # Mostra candles coletados
        for symbol in symbols:
            df = ws.get_candles(symbol)
            print(f"\n{symbol}: {len(df)} candles coletados")
            if not df.empty:
                print(df.tail(3))


if __name__ == "__main__":
    print("🔌 Testando WebSocket...")
    asyncio.run(exemplo_uso())
