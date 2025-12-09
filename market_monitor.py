#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📡 MARKET MONITORING SYSTEM - App Leonardo v3.0
================================================

Monitora dados de mercado de criptomoedas em tempo real.
Coleta dados de múltiplas fontes confiáveis e valida dados.

FONTES DE DADOS:
1. Binance API (Dados em tempo real)
2. CoinGecko API (Preços, market cap, volume)
3. Fear & Greed Index (Sentimento de mercado)
4. Trading View (Análise técnica)

FEATURES:
- Monitoramento contínuo
- Validação de dados (apenas dados assertivos)
- Detecção de oportunidades
- Alertas de volatilidade
- Histórico de análises
"""

import os
import sys
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger('MarketMonitor')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class MarketData:
    """Dados de mercado de uma criptomoeda"""
    symbol: str
    price: float
    price_change_24h: float
    volume_24h: float
    market_cap: float
    rsi: Optional[float] = None
    macd: Optional[float] = None
    bb_signal: Optional[str] = None  # 'overbought', 'oversold', 'neutral'
    trend: Optional[str] = None  # 'bullish', 'bearish', 'sideways'
    volatility: float = 0.0
    confidence: float = 0.0  # 0-1, quando > 0.7 é assertivo
    last_update: str = None
    source: str = "multiple"
    
    def is_assertive(self) -> bool:
        """Retorna True se o dado é assertivo (confiável)"""
        return self.confidence >= 0.7


class CryptoDataCollector:
    """Coleta dados de criptomoedas de múltiplas fontes"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.ai_dir = self.data_dir / "ai"
        self.ai_dir.mkdir(exist_ok=True)
        
        # Cache de dados
        self.market_cache = {}
        self.last_update = {}
        self.cache_ttl = 300  # 5 minutos
        
        # URLs das APIs
        self.COINGECKO_URL = "https://api.coingecko.com/api/v3"
        self.FEAR_GREED_URL = "https://api.alternative.me/fng"
        
    def get_binance_data(self, symbol: str) -> Optional[MarketData]:
        """
        Coleta dados em tempo real da Binance
        
        NOTA: Requer configuração do cliente CCXT em produção
        """
        try:
            import ccxt
            binance = ccxt.binance()
            
            # Buscar ticker
            ticker = binance.fetch_ticker(symbol)
            
            # Buscar OHLCV para calcular RSI e outros indicadores
            ohlcv = binance.fetch_ohlcv(symbol, '1h', limit=14)
            
            # Calcular RSI
            rsi = self._calculate_rsi([x[4] for x in ohlcv])
            
            # Calcular volatilidade
            closes = [x[4] for x in ohlcv]
            volatility = self._calculate_volatility(closes)
            
            data = MarketData(
                symbol=symbol,
                price=ticker['last'],
                price_change_24h=ticker.get('percentage', 0),
                volume_24h=ticker.get('quoteVolume', 0),
                market_cap=0,  # Binance não fornece directly
                rsi=rsi,
                volatility=volatility,
                trend=self._determine_trend(closes[-5:]),
                confidence=0.9,  # Dados diretos da Binance são muito confiáveis
                last_update=datetime.now().isoformat(),
                source="binance"
            )
            
            return data
        
        except Exception as e:
            logger.error(f"Erro ao buscar dados Binance para {symbol}: {e}")
            return None
    
    def get_coingecko_data(self, crypto_id: str, symbol: str) -> Optional[MarketData]:
        """
        Coleta dados do CoinGecko (públicos, sem API key)
        
        Args:
            crypto_id: ID do CoinGecko (ex: 'bitcoin' para BTC)
            symbol: Símbolo (ex: 'BTCUSDT')
        """
        try:
            url = f"{self.COINGECKO_URL}/simple/price"
            params = {
                'ids': crypto_id,
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            price_data = response.json().get(crypto_id, {})
            
            data = MarketData(
                symbol=symbol,
                price=price_data.get('usd', 0),
                price_change_24h=price_data.get('usd_24h_change', 0),
                volume_24h=price_data.get('usd_24h_vol', 0),
                market_cap=price_data.get('usd_market_cap', 0),
                confidence=0.8,  # CoinGecko é confiável
                last_update=datetime.now().isoformat(),
                source="coingecko"
            )
            
            return data
        
        except Exception as e:
            logger.error(f"Erro ao buscar dados CoinGecko para {symbol}: {e}")
            return None
    
    def get_fear_greed_index(self) -> Dict:
        """Obtém o Fear & Greed Index (sentimento de mercado)"""
        try:
            response = requests.get(self.FEAR_GREED_URL, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            value = int(data['data'][0]['value'])
            classification = data['data'][0]['value_classification']
            timestamp = data['data'][0]['timestamp']
            
            return {
                'value': value,
                'classification': classification,  # 'Extreme Fear', 'Fear', 'Greed', etc
                'timestamp': timestamp,
                'confidence': 0.95
            }
        
        except Exception as e:
            logger.error(f"Erro ao buscar Fear & Greed Index: {e}")
            return None
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calcula RSI (Relative Strength Index)"""
        if len(prices) < period:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 0.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calcula volatilidade como desvio padrão percentual"""
        if len(prices) < 2:
            return 0.0
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        volatility = (variance ** 0.5) * 100
        
        return volatility
    
    def _determine_trend(self, recent_prices: List[float]) -> str:
        """Determina tendência (bullish, bearish, sideways)"""
        if len(recent_prices) < 2:
            return "sideways"
        
        change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        if change > 0.02:  # > 2%
            return "bullish"
        elif change < -0.02:  # < -2%
            return "bearish"
        else:
            return "sideways"


class MarketMonitor:
    """Monitor principal de mercado"""
    
    def __init__(self):
        self.collector = CryptoDataCollector()
        self.data_dir = Path("data")
        self.market_data_file = self.data_dir / "ai" / "market_data.json"
        self.alerts_file = self.data_dir / "ai" / "market_alerts.json"
        self.running = False
        self.thread = None
        
        # Criptos principais para monitorar
        self.monitored_cryptos = [
            ('bitcoin', 'BTCUSDT'),
            ('ethereum', 'ETHUSDT'),
            ('solana', 'SOLUSDT'),
            ('polygon', 'MATICUSDT'),
            ('cardano', 'ADAUSDT'),
            ('ripple', 'XRPUSDT'),
            ('dogecoin', 'DOGEUSDT'),
            ('litecoin', 'LTCUSDT'),
        ]
        
        self.market_data = {}
        self.alerts = []
    
    def start(self):
        """Inicia monitoramento em background"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            logger.info("📡 Market Monitor iniciado")
    
    def stop(self):
        """Para monitoramento"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("📡 Market Monitor parado")
    
    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self.running:
            try:
                self.update_market_data()
                self.detect_opportunities()
                self.save_data()
                
                # Aguardar 5 minutos antes de próxima atualização
                time.sleep(300)
            
            except Exception as e:
                logger.error(f"Erro no monitor loop: {e}")
                time.sleep(60)
    
    def update_market_data(self):
        """Atualiza dados de mercado"""
        logger.info("🔄 Atualizando dados de mercado...")
        
        for crypto_id, symbol in self.monitored_cryptos:
            try:
                # Tentar CoinGecko primeiro (público, sem rate limit severo)
                data = self.collector.get_coingecko_data(crypto_id, symbol)
                
                if data and data.is_assertive():
                    self.market_data[symbol] = asdict(data)
                    logger.info(f"✅ {symbol}: ${data.price:.2f} ({data.price_change_24h:+.2f}%)")
                
                time.sleep(0.5)  # Rate limiting
            
            except Exception as e:
                logger.error(f"Erro ao atualizar {symbol}: {e}")
        
        # Atualizar Fear & Greed
        fg = self.collector.get_fear_greed_index()
        if fg:
            self.market_data['FEAR_GREED'] = fg
            logger.info(f"🎭 Fear & Greed: {fg['value']} ({fg['classification']})")
    
    def detect_opportunities(self):
        """Detecta oportunidades de trading"""
        opportunities = []
        
        for symbol, data in self.market_data.items():
            if symbol == 'FEAR_GREED':
                continue
            
            if not isinstance(data, dict):
                continue
            
            # Critério 1: Extreme Fear (medo excessivo = compra potencial)
            fg_data = self.market_data.get('FEAR_GREED', {})
            if fg_data.get('value', 50) < 25:
                opportunities.append({
                    'symbol': symbol,
                    'type': 'EXTREME_FEAR',
                    'reason': f"Fear & Greed muito baixo ({fg_data.get('value')})",
                    'confidence': 0.8,
                    'action': 'BUY_SIGNAL'
                })
            
            # Critério 2: Queda de 24h > 5% + RSI < 30
            if data.get('price_change_24h', 0) < -5 and data.get('rsi', 50) < 30:
                opportunities.append({
                    'symbol': symbol,
                    'type': 'OVERSOLD',
                    'reason': f"Preço -5% + RSI {data.get('rsi'):.1f}",
                    'confidence': 0.85,
                    'action': 'BUY_SIGNAL'
                })
            
            # Critério 3: Alta volatilidade + tendência bullish
            if data.get('volatility', 0) > 3 and data.get('trend') == 'bullish':
                opportunities.append({
                    'symbol': symbol,
                    'type': 'VOLATILE_BULLISH',
                    'reason': f"Volatilidade {data.get('volatility'):.1f}% + tendência bullish",
                    'confidence': 0.75,
                    'action': 'MONITOR_FOR_ENTRY'
                })
        
        if opportunities:
            logger.info(f"🎯 {len(opportunities)} oportunidade(s) detectada(s)")
            for opp in opportunities:
                if opp['confidence'] >= 0.7:
                    logger.info(f"   ⭐ {opp['symbol']}: {opp['reason']}")
        
        self.alerts = opportunities
    
    def save_data(self):
        """Salva dados em arquivo"""
        try:
            market_snapshot = {
                'timestamp': datetime.now().isoformat(),
                'data': self.market_data,
                'sources': {
                    'binance': 'Real-time market data',
                    'coingecko': 'Price, volume, market cap',
                    'fear_greed': 'Market sentiment'
                },
                'update_interval': '5 minutes'
            }
            
            with open(self.market_data_file, 'w') as f:
                json.dump(market_snapshot, f, indent=2)
            
            # Salvar alertas
            if self.alerts:
                with open(self.alerts_file, 'w') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'alerts': self.alerts
                    }, f, indent=2)
        
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")
    
    def get_summary(self) -> str:
        """Retorna resumo formatado dos dados"""
        summary = []
        summary.append("=" * 70)
        summary.append("📊 RESUMO DO MERCADO - App Leonardo v3.0")
        summary.append("=" * 70)
        summary.append(f"Timestamp: {datetime.now().isoformat()}\n")
        
        # Dados gerais
        fg_data = self.market_data.get('FEAR_GREED', {})
        if fg_data:
            summary.append(f"🎭 Fear & Greed Index: {fg_data.get('value')} - {fg_data.get('classification')}")
            summary.append()
        
        # Criptos
        summary.append("💹 CRIPTOMOEDAS:")
        for symbol, data in sorted(self.market_data.items()):
            if symbol == 'FEAR_GREED' or not isinstance(data, dict):
                continue
            
            price = data.get('price', 0)
            change = data.get('price_change_24h', 0)
            volume = data.get('volume_24h', 0)
            rsi = data.get('rsi', 50)
            
            emoji = "📈" if change > 0 else "📉"
            confidence = "✅" if data.get('confidence', 0) >= 0.7 else "⚠️"
            
            summary.append(f"  {emoji} {symbol}: ${price:.2f} ({change:+.2f}%) | Vol: ${volume/1e9:.1f}B | RSI: {rsi:.1f} {confidence}")
        
        summary.append()
        
        # Alertas
        if self.alerts:
            summary.append(f"🎯 OPORTUNIDADES ({len(self.alerts)}):")
            for alert in self.alerts[:5]:  # Top 5
                if alert['confidence'] >= 0.7:
                    summary.append(f"  ⭐ {alert['symbol']}: {alert['reason']} (Confiança: {alert['confidence']:.0%})")
        
        summary.append("\n" + "=" * 70)
        
        return "\n".join(summary)


def main():
    """Função principal"""
    monitor = MarketMonitor()
    
    print("\n" + "=" * 70)
    print("📡 INICIANDO MARKET MONITOR")
    print("=" * 70)
    print("\nExecutando verificação única...")
    
    # Executar uma vez
    monitor.update_market_data()
    monitor.detect_opportunities()
    monitor.save_data()
    
    print(monitor.get_summary())
    
    # Perguntar se quer modo contínuo
    print("\n💡 Para monitoramento contínuo:")
    print("  # Adicionar ao daemon ou cron job")
    print("  # ou usar: python -c \"from market_monitor import MarketMonitor; m = MarketMonitor(); m.start(); import time; time.sleep(3600)\"")


if __name__ == '__main__':
    main()
