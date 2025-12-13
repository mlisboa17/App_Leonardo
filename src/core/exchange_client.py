"""
Módulo de Conexão com Exchanges via CCXT
"""
import ccxt
import logging
import os
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ExchangeClient:
    """Cliente para conexão com exchanges"""
    
    def __init__(self, exchange_name: str, api_key: str, api_secret: str):
        self.exchange_name = exchange_name
        self.testnet = False
        
        # Inicializa exchange via CCXT
        exchange_class = getattr(ccxt, exchange_name)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': 30000,  # 30 segundos de timeout
            'options': {
                'defaultType': 'spot',  # spot, future, swap
                'adjustForTimeDifference': True,  # ✅ Ajusta diferença de tempo automaticamente
                'recvWindow': 60000,  # ✅ Janela de tempo maior (60 segundos)
            }
        })
        
        # ✅ Carrega mercados para sincronizar tempo
        try:
            self.exchange.load_markets()
            logger.info(f"✅ Mercados carregados e tempo sincronizado")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar mercados: {e}")
                
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
        """Obtém saldo da conta (com correção para Testnet)"""
        try:
            balance = self.exchange.fetch_balance()
            
            # Aplica correção de saldo para Testnet
            if self.testnet and TESTNET_BALANCE_CORRECTION > 1:
                corrected_balance = {}
                for key, value in balance.items():
                    if isinstance(value, dict):
                        # Corrige dicionários (free, used, total por moeda)
                        corrected_balance[key] = {}
                        for subkey, subvalue in value.items():
                            if isinstance(subvalue, (int, float)):
                                corrected_balance[key][subkey] = subvalue / TESTNET_BALANCE_CORRECTION
                            else:
                                corrected_balance[key][subkey] = subvalue
                    elif isinstance(value, (int, float)):
                        corrected_balance[key] = value / TESTNET_BALANCE_CORRECTION
                    else:
                        corrected_balance[key] = value
                
                logger.debug(f"💰 Saldo corrigido (Testnet ÷{TESTNET_BALANCE_CORRECTION:.0f})")
                return corrected_balance
            
            return balance
        except Exception as e:
            logger.error(f"❌ Erro ao buscar saldo: {e}")
            return None
    
    def create_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict]:
        """
        Cria ordem a mercado com ajuste automático de saldo
        side: 'buy' ou 'sell'
        """
        try:
            # Primeira tentativa com valor original
            order = self.exchange.create_market_order(symbol, side, amount)
            logger.info(f"📝 Ordem MARKET {side.upper()}: {amount} {symbol} - ID: {order['id']}")
            return order
        except Exception as e:
            error_msg = str(e).lower()
            
            # Se erro de saldo insuficiente, tentar com valor menor
            if 'insufficient balance' in error_msg or 'insufficient funds' in error_msg:
                try:
                    # Buscar saldo atual
                    balance = self.fetch_balance()
                    if not balance:
                        logger.error(f"❌ Não foi possível obter saldo para ajustar ordem")
                        return None
                    
                    if side.lower() == 'buy':
                        # Para compra, usar 90% do USDT disponível
                        available_usdt = balance.get('USDT', {}).get('free', 0)
                        if available_usdt > 1.0:  # Mínimo $1
                            # Obter preço atual para calcular quantidade
                            ticker = self.exchange.fetch_ticker(symbol)
                            current_price = ticker['last']
                            max_amount_usdt = available_usdt * 0.9  # 90% do saldo
                            adjusted_amount = max_amount_usdt / current_price
                            
                            logger.warning(f"⚠️ Ajustando compra: {amount} -> {adjusted_amount:.6f} ({max_amount_usdt:.2f} USDT)")
                            
                            order = self.exchange.create_market_order(symbol, side, adjusted_amount)
                            logger.info(f"📝 Ordem AJUSTADA MARKET {side.upper()}: {adjusted_amount:.6f} {symbol} - ID: {order['id']}")
                            return order
                    
                    else:  # sell
                        # Para venda, usar 90% da crypto disponível
                        base_currency = symbol.split('/')[0]
                        available_crypto = balance.get(base_currency, {}).get('free', 0)
                        if available_crypto > 0:
                            adjusted_amount = available_crypto * 0.9  # 90% da crypto
                            
                            logger.warning(f"⚠️ Ajustando venda: {amount} -> {adjusted_amount:.6f}")
                            
                            order = self.exchange.create_market_order(symbol, side, adjusted_amount)
                            logger.info(f"📝 Ordem AJUSTADA MARKET {side.upper()}: {adjusted_amount:.6f} {symbol} - ID: {order['id']}")
                            return order
                
                except Exception as adjust_error:
                    logger.error(f"❌ Erro ao ajustar ordem: {adjust_error}")
            
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
