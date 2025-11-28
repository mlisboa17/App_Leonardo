"""
Módulo de Conexão com Exchanges via CCXT
"""
import ccxt
import logging
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ExchangeClient:
    """Cliente para conexão com exchanges"""
    
    def __init__(self, exchange_name: str, api_key: str, api_secret: str, testnet: bool = True):
        self.exchange_name = exchange_name
        self.testnet = testnet
        
        # Inicializa exchange via CCXT
        exchange_class = getattr(ccxt, exchange_name)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': 30000,  # 30 segundos de timeout
            'options': {
                'defaultType': 'spot',  # spot, future, swap
            }
        })
        
        # Ativa testnet se configurado
        if testnet:
            if hasattr(self.exchange, 'set_sandbox_mode'):
                self.exchange.set_sandbox_mode(True)
                logger.info(f"🧪 Modo TESTNET ativado para {exchange_name}")
            else:
                logger.warning(f"⚠️ {exchange_name} não suporta testnet via ccxt")
                
        logger.info(f"✅ Conectado à {exchange_name}")
        
    def test_connection(self) -> bool:
        """Testa conexão com a exchange"""
        try:
            logger.info("🔄 Testando conexão com exchange...")
            balance = self.exchange.fetch_balance()
            logger.info(f"✅ Conexão OK - Saldo total: {balance.get('total', {})}")
            return True
        except ccxt.NetworkError as e:
            logger.error(f"❌ Erro de rede na conexão: {e}")
            logger.info("⚠️ Tentando continuar sem validação de saldo...")
            return True  # Continua mesmo com erro de rede
        except Exception as e:
            logger.error(f"❌ Erro na conexão: {e}")
            return False
    
    def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """Obtém preço atual de um par"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"❌ Erro ao buscar ticker {symbol}: {e}")
            return None
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[List]:
        """Obtém dados históricos OHLCV"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            logger.info(f"📊 {len(ohlcv)} candles obtidos para {symbol} ({timeframe})")
            return ohlcv
        except Exception as e:
            logger.error(f"❌ Erro ao buscar OHLCV {symbol}: {e}")
            return None
    
    def fetch_balance(self) -> Optional[Dict]:
        """Obtém saldo da conta"""
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"❌ Erro ao buscar saldo: {e}")
            return None
    
    def create_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict]:
        """
        Cria ordem a mercado
        side: 'buy' ou 'sell'
        """
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            logger.info(f"📝 Ordem MARKET {side.upper()}: {amount} {symbol} - ID: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"❌ Erro ao criar ordem market: {e}")
            return None
    
    def create_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict]:
        """
        Cria ordem limitada
        side: 'buy' ou 'sell'
        """
        try:
            order = self.exchange.create_limit_order(symbol, side, amount, price)
            logger.info(f"📝 Ordem LIMIT {side.upper()}: {amount} {symbol} @ {price} - ID: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"❌ Erro ao criar ordem limit: {e}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancela uma ordem"""
        try:
            self.exchange.cancel_order(order_id, symbol)
            logger.info(f"❌ Ordem {order_id} cancelada")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao cancelar ordem {order_id}: {e}")
            return False
    
    def fetch_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        """Verifica status de uma ordem (ANTI-ALUCINAÇÃO)"""
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            logger.info(f"📋 Status ordem {order_id}: {order['status']}")
            return order
        except Exception as e:
            logger.error(f"❌ Erro ao buscar ordem {order_id}: {e}")
            return None
    
    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Obtém todas as ordens abertas"""
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            logger.info(f"📋 {len(orders)} ordens abertas")
            return orders
        except Exception as e:
            logger.error(f"❌ Erro ao buscar ordens abertas: {e}")
            return []
