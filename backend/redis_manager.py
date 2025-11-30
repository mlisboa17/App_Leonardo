"""
Redis Manager - Cache e Mensageria
"""
import redis.asyncio as redis
import json
from typing import Optional, Dict
from backend.config import settings


class RedisManager:
    """Gerenciador do Redis para cache e mensagens"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Conecta ao Redis"""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        print("✅ Conectado ao Redis")
    
    async def disconnect(self):
        """Desconecta do Redis"""
        if self.redis:
            await self.redis.close()
            print("✅ Desconectado do Redis")
    
    # ========================================
    # CACHE DE STATUS
    # ========================================
    
    async def set_status(self, status_data: Dict, ttl: int = 5):
        """Cacheia status do bot"""
        await self.redis.setex(
            "bot:status",
            ttl,
            json.dumps(status_data)
        )
    
    async def get_status(self) -> Optional[Dict]:
        """Obtém status do cache"""
        data = await self.redis.get("bot:status")
        return json.loads(data) if data else None
    
    # ========================================
    # CACHE DE PREÇOS
    # ========================================
    
    async def set_price(self, symbol: str, price: float):
        """Cacheia último preço"""
        await self.redis.hset("prices", symbol, price)
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Obtém último preço"""
        price = await self.redis.hget("prices", symbol)
        return float(price) if price else None
    
    async def get_all_prices(self) -> Dict[str, float]:
        """Obtém todos os preços"""
        prices = await self.redis.hgetall("prices")
        return {k: float(v) for k, v in prices.items()}
    
    # ========================================
    # POSIÇÕES
    # ========================================
    
    async def set_position(self, symbol: str, position_data: Dict):
        """Cacheia posição aberta"""
        await self.redis.hset(
            "positions",
            symbol,
            json.dumps(position_data)
        )
    
    async def get_position(self, symbol: str) -> Optional[Dict]:
        """Obtém posição"""
        data = await self.redis.hget("positions", symbol)
        return json.loads(data) if data else None
    
    async def remove_position(self, symbol: str):
        """Remove posição (fechada)"""
        await self.redis.hdel("positions", symbol)
    
    async def get_all_positions(self) -> Dict[str, Dict]:
        """Obtém todas as posições"""
        positions = await self.redis.hgetall("positions")
        return {k: json.loads(v) for k, v in positions.items()}
    
    # ========================================
    # FILA DE MENSAGENS
    # ========================================
    
    async def publish_trade(self, trade_data: Dict):
        """Publica trade na fila"""
        await self.redis.publish(
            "trades",
            json.dumps(trade_data)
        )
    
    async def publish_signal(self, signal_data: Dict):
        """Publica sinal de trading"""
        await self.redis.publish(
            "signals",
            json.dumps(signal_data)
        )
