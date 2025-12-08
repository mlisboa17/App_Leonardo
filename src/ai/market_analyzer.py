"""
📊 MARKET ANALYZER - Análise de Mercado em Tempo Real
=====================================================
Analisa condições de mercado e fornece dados para o
DynamicConfigManager ajustar os bots automaticamente.

Fontes de dados:
1. OHLCV do BTC (referência principal)
2. Volatilidade via ATR
3. Volume relativo
4. Correlações entre cryptos
5. Momentum do mercado

Autor: Sistema R7 Trading Bot API
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger('MarketAnalyzer')


@dataclass
class MarketConditions:
    """Estrutura com condições atuais do mercado"""
    timestamp: datetime
    btc_price: float
    btc_change_24h: float
    btc_change_1h: float
    volatility: float  # ATR em %
    volatility_level: str  # 'low', 'normal', 'high', 'extreme'
    trend: str  # 'strong_up', 'up', 'neutral', 'down', 'strong_down'
    trend_strength: float  # -100 a +100
    volume_ratio: float  # Volume atual / média
    market_phase: str  # 'accumulation', 'markup', 'distribution', 'markdown'
    recommended_action: str  # 'aggressive_buy', 'buy', 'hold', 'reduce', 'defensive'


class MarketAnalyzer:
    """
    Analisa o mercado em tempo real e fornece insights
    para ajuste automático dos bots.
    """
    
    def __init__(self, exchange_client):
        self.exchange = exchange_client
        
        # Cache de dados
        self.cache = {}
        self.cache_expiry = 60  # 60 segundos
        self.last_cache_time = None
        
        # Histórico de análises (para detectar mudanças)
        self.analysis_history: List[MarketConditions] = []
        self.max_history = 60  # Últimos 60 análises (1 hora)
        
        # Última análise
        self.current_conditions: Optional[MarketConditions] = None
        
        logger.info("📊 MarketAnalyzer inicializado")
    
    async def analyze(self) -> MarketConditions:
        """
        Analisa condições atuais do mercado.
        Retorna estrutura com todas as métricas.
        """
        try:
            # Busca dados do BTC
            btc_data = await self._fetch_ohlcv('BTCUSDT', '1h', 100)
            if not btc_data:
                return self._get_default_conditions()
            
            # Busca dados de 1 minuto para volatilidade recente
            btc_1m = await self._fetch_ohlcv('BTCUSDT', '1m', 60)
            
            # Calcula métricas
            btc_price = btc_data[-1][4]  # Close
            btc_change_24h = self._calc_change(btc_data, 24)
            btc_change_1h = self._calc_change(btc_data, 1)
            
            volatility = self._calc_volatility(btc_data)
            volatility_level = self._categorize_volatility(volatility)
            
            trend, trend_strength = self._calc_trend(btc_data)
            volume_ratio = self._calc_volume_ratio(btc_data)
            
            market_phase = self._detect_market_phase(btc_data, trend, volatility)
            recommended_action = self._get_recommended_action(
                trend, volatility_level, volume_ratio, btc_change_1h
            )
            
            # Cria estrutura de condições
            conditions = MarketConditions(
                timestamp=datetime.now(),
                btc_price=btc_price,
                btc_change_24h=btc_change_24h,
                btc_change_1h=btc_change_1h,
                volatility=volatility,
                volatility_level=volatility_level,
                trend=trend,
                trend_strength=trend_strength,
                volume_ratio=volume_ratio,
                market_phase=market_phase,
                recommended_action=recommended_action
            )
            
            # Salva no histórico
            self._save_to_history(conditions)
            self.current_conditions = conditions
            
            logger.info(f"📊 Mercado: {trend} | Vol: {volatility_level} | Ação: {recommended_action}")
            
            return conditions
            
        except Exception as e:
            logger.error(f"Erro na análise de mercado: {e}")
            return self._get_default_conditions()
    
    def analyze_sync(self) -> MarketConditions:
        """Versão síncrona do analyze para uso em contextos não-async"""
        try:
            # Busca dados do BTC
            btc_data = self._fetch_ohlcv_sync('BTCUSDT', '1h', 100)
            if not btc_data:
                return self._get_default_conditions()
            
            # Calcula métricas
            btc_price = btc_data[-1][4]
            btc_change_24h = self._calc_change(btc_data, 24)
            btc_change_1h = self._calc_change(btc_data, 1)
            
            volatility = self._calc_volatility(btc_data)
            volatility_level = self._categorize_volatility(volatility)
            
            trend, trend_strength = self._calc_trend(btc_data)
            volume_ratio = self._calc_volume_ratio(btc_data)
            
            market_phase = self._detect_market_phase(btc_data, trend, volatility)
            recommended_action = self._get_recommended_action(
                trend, volatility_level, volume_ratio, btc_change_1h
            )
            
            conditions = MarketConditions(
                timestamp=datetime.now(),
                btc_price=btc_price,
                btc_change_24h=btc_change_24h,
                btc_change_1h=btc_change_1h,
                volatility=volatility,
                volatility_level=volatility_level,
                trend=trend,
                trend_strength=trend_strength,
                volume_ratio=volume_ratio,
                market_phase=market_phase,
                recommended_action=recommended_action
            )
            
            self._save_to_history(conditions)
            self.current_conditions = conditions
            
            return conditions
            
        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return self._get_default_conditions()
    
    async def _fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> Optional[list]:
        """Busca dados OHLCV com cache"""
        cache_key = f"{symbol}_{timeframe}"
        now = datetime.now()
        
        # Verifica cache
        if (self.last_cache_time and 
            (now - self.last_cache_time).seconds < self.cache_expiry and
            cache_key in self.cache):
            return self.cache[cache_key]
        
        try:
            data = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if data:
                self.cache[cache_key] = data
                self.last_cache_time = now
            return data
        except Exception as e:
            logger.error(f"Erro ao buscar {symbol}: {e}")
            return None
    
    def _fetch_ohlcv_sync(self, symbol: str, timeframe: str, limit: int) -> Optional[list]:
        """Versão síncrona do fetch"""
        cache_key = f"{symbol}_{timeframe}"
        now = datetime.now()
        
        if (self.last_cache_time and 
            (now - self.last_cache_time).seconds < self.cache_expiry and
            cache_key in self.cache):
            return self.cache[cache_key]
        
        try:
            data = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if data:
                self.cache[cache_key] = data
                self.last_cache_time = now
            return data
        except Exception as e:
            logger.error(f"Erro ao buscar {symbol}: {e}")
            return None
    
    def _calc_change(self, ohlcv: list, hours: int) -> float:
        """Calcula variação % nas últimas N horas"""
        if len(ohlcv) < hours:
            return 0.0
        
        current = ohlcv[-1][4]  # Close atual
        past = ohlcv[-(hours+1)][4]  # Close de N horas atrás
        
        if past > 0:
            return ((current - past) / past) * 100
        return 0.0
    
    def _calc_volatility(self, ohlcv: list) -> float:
        """Calcula volatilidade como % usando ATR"""
        if len(ohlcv) < 20:
            return 2.0
        
        # ATR - Average True Range
        trs = []
        for i in range(1, min(20, len(ohlcv))):
            high = ohlcv[-i][2]
            low = ohlcv[-i][3]
            prev_close = ohlcv[-(i+1)][4]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            trs.append(tr)
        
        atr = np.mean(trs)
        current_price = ohlcv[-1][4]
        
        return (atr / current_price) * 100
    
    def _categorize_volatility(self, vol_pct: float) -> str:
        """Categoriza nível de volatilidade"""
        if vol_pct < 0.8:
            return 'low'
        elif vol_pct < 2.0:
            return 'normal'
        elif vol_pct < 4.0:
            return 'high'
        else:
            return 'extreme'
    
    def _calc_trend(self, ohlcv: list) -> Tuple[str, float]:
        """
        Calcula tendência e força.
        Retorna (trend_name, strength -100 a +100)
        """
        if len(ohlcv) < 50:
            return 'neutral', 0
        
        closes = [c[4] for c in ohlcv]
        
        # SMAs
        sma_10 = np.mean(closes[-10:])
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-50:])
        current = closes[-1]
        
        # Momentum
        momentum_10 = ((current - closes[-10]) / closes[-10]) * 100 if closes[-10] > 0 else 0
        
        # Score
        score = 0
        
        # Preço vs SMAs (mais peso para SMAs mais curtas)
        if current > sma_10:
            score += 30
        else:
            score -= 30
        
        if current > sma_20:
            score += 25
        else:
            score -= 25
        
        if current > sma_50:
            score += 20
        else:
            score -= 20
        
        # SMA alignment
        if sma_10 > sma_20 > sma_50:
            score += 15  # Alinhamento bullish
        elif sma_10 < sma_20 < sma_50:
            score -= 15  # Alinhamento bearish
        
        # Momentum (limita a contribuição)
        score += min(10, max(-10, momentum_10 * 2))
        
        # Categoriza
        if score > 50:
            trend = 'strong_up'
        elif score > 20:
            trend = 'up'
        elif score > -20:
            trend = 'neutral'
        elif score > -50:
            trend = 'down'
        else:
            trend = 'strong_down'
        
        return trend, score
    
    def _calc_volume_ratio(self, ohlcv: list) -> float:
        """Volume atual / média de 20 períodos"""
        if len(ohlcv) < 20:
            return 1.0
        
        volumes = [c[5] for c in ohlcv]
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        
        if avg_volume > 0:
            return current_volume / avg_volume
        return 1.0
    
    def _detect_market_phase(self, ohlcv: list, trend: str, volatility: float) -> str:
        """
        Detecta fase do mercado (Wyckoff simplificado):
        - accumulation: Preços baixos, volume aumentando, tendência neutra
        - markup: Tendência de alta com volume
        - distribution: Preços altos, volume alto, tendência enfraquecendo
        - markdown: Tendência de baixa
        """
        if len(ohlcv) < 50:
            return 'unknown'
        
        closes = [c[4] for c in ohlcv]
        volumes = [c[5] for c in ohlcv]
        
        # Posição relativa do preço (0-100)
        price_position = ((closes[-1] - min(closes)) / (max(closes) - min(closes) + 0.0001)) * 100
        
        # Volume trend
        vol_early = np.mean(volumes[:25])
        vol_late = np.mean(volumes[-25:])
        vol_increasing = vol_late > vol_early * 1.1
        
        if trend in ['strong_up', 'up'] and price_position > 50:
            return 'markup'
        elif trend in ['strong_down', 'down'] and price_position < 50:
            return 'markdown'
        elif price_position < 30 and vol_increasing:
            return 'accumulation'
        elif price_position > 70 and vol_increasing:
            return 'distribution'
        else:
            return 'consolidation'
    
    def _get_recommended_action(self, trend: str, vol_level: str, vol_ratio: float, change_1h: float) -> str:
        """
        Determina ação recomendada baseado nas condições.
        
        Returns:
            'aggressive_buy': Comprar agressivamente
            'buy': Comprar normalmente
            'hold': Manter posições atuais
            'reduce': Reduzir exposição
            'defensive': Modo defensivo
        """
        # Volatilidade extrema = modo defensivo
        if vol_level == 'extreme':
            return 'defensive'
        
        # Queda forte recente = defensivo ou esperar
        if change_1h < -3.0:
            return 'defensive'
        
        # Alta forte + alta volatilidade = cuidado (pode ser pico)
        if trend == 'strong_up' and vol_level == 'high' and vol_ratio > 2.0:
            return 'reduce'  # Pode estar perto do topo
        
        # Tendência de alta + volatilidade normal = comprar
        if trend in ['strong_up', 'up']:
            if vol_level == 'low':
                return 'buy'  # Subida controlada
            elif vol_level == 'normal':
                return 'aggressive_buy'  # Bom momento
            else:
                return 'buy'  # Alta vol = menor exposição
        
        # Tendência neutra
        if trend == 'neutral':
            if vol_level == 'low':
                return 'hold'  # Esperando breakout
            else:
                return 'buy'  # Range trading
        
        # Tendência de baixa
        if trend == 'down':
            if vol_level in ['low', 'normal']:
                return 'buy'  # Oportunidade de compra
            else:
                return 'hold'  # Esperar estabilizar
        
        # Queda forte
        if trend == 'strong_down':
            if change_1h > 0:  # Mostrando recuperação
                return 'buy'  # Possível fundo
            else:
                return 'defensive'  # Ainda caindo
        
        return 'hold'
    
    def _save_to_history(self, conditions: MarketConditions):
        """Salva análise no histórico"""
        self.analysis_history.append(conditions)
        
        # Mantém apenas últimos N
        if len(self.analysis_history) > self.max_history:
            self.analysis_history = self.analysis_history[-self.max_history:]
    
    def _get_default_conditions(self) -> MarketConditions:
        """Retorna condições default quando não há dados"""
        return MarketConditions(
            timestamp=datetime.now(),
            btc_price=0,
            btc_change_24h=0,
            btc_change_1h=0,
            volatility=2.0,
            volatility_level='normal',
            trend='neutral',
            trend_strength=0,
            volume_ratio=1.0,
            market_phase='unknown',
            recommended_action='hold'
        )
    
    def get_config_adjustments(self) -> Dict:
        """
        Retorna ajustes recomendados para configs dos bots
        baseado nas condições atuais.
        """
        if not self.current_conditions:
            return {}
        
        cond = self.current_conditions
        adjustments = {
            'multipliers': {},
            'recommendations': []
        }
        
        # ==== AJUSTES DE TAMANHO DE POSIÇÃO ====
        if cond.recommended_action == 'aggressive_buy':
            adjustments['multipliers']['position_size'] = 1.2
            adjustments['recommendations'].append("Aumentar tamanho das posições em 20%")
        elif cond.recommended_action == 'defensive':
            adjustments['multipliers']['position_size'] = 0.5
            adjustments['recommendations'].append("Reduzir tamanho das posições em 50%")
        elif cond.recommended_action == 'reduce':
            adjustments['multipliers']['position_size'] = 0.7
            adjustments['recommendations'].append("Reduzir tamanho das posições em 30%")
        
        # ==== AJUSTES DE STOP LOSS ====
        if cond.volatility_level == 'high':
            adjustments['multipliers']['stop_loss'] = 1.3  # Stop mais largo
            adjustments['recommendations'].append("Alargar stop loss em 30% (alta volatilidade)")
        elif cond.volatility_level == 'extreme':
            adjustments['multipliers']['stop_loss'] = 1.5
            adjustments['recommendations'].append("Alargar stop loss em 50% (volatilidade extrema)")
        elif cond.volatility_level == 'low':
            adjustments['multipliers']['stop_loss'] = 0.8
            adjustments['recommendations'].append("Apertar stop loss em 20% (baixa volatilidade)")
        
        # ==== AJUSTES DE TAKE PROFIT ====
        if cond.trend in ['strong_up', 'up']:
            adjustments['multipliers']['take_profit'] = 1.2
            adjustments['recommendations'].append("Aumentar take profit em 20% (tendência de alta)")
        elif cond.trend in ['strong_down', 'down']:
            adjustments['multipliers']['take_profit'] = 0.8
            adjustments['recommendations'].append("Diminuir take profit em 20% (pegar lucro rápido)")
        
        # ==== AJUSTES DE RSI ====
        if cond.trend == 'strong_up':
            adjustments['multipliers']['rsi_buy'] = 1.1  # Comprar em RSI mais alto
            adjustments['recommendations'].append("RSI de compra mais alto (tendência forte)")
        elif cond.trend == 'strong_down':
            adjustments['multipliers']['rsi_buy'] = 0.85  # Esperar RSI mais baixo
            adjustments['recommendations'].append("Esperar RSI mais baixo (mercado em queda)")
        
        return adjustments
    
    def get_status_report(self) -> str:
        """Retorna relatório formatado do status do mercado"""
        if not self.current_conditions:
            return "Sem dados de mercado disponíveis"
        
        cond = self.current_conditions
        
        # Emojis por condição
        trend_emoji = {
            'strong_up': '🚀',
            'up': '📈',
            'neutral': '➡️',
            'down': '📉',
            'strong_down': '💥'
        }
        
        vol_emoji = {
            'low': '😴',
            'normal': '✅',
            'high': '⚡',
            'extreme': '🌋'
        }
        
        action_emoji = {
            'aggressive_buy': '🟢🟢',
            'buy': '🟢',
            'hold': '🟡',
            'reduce': '🟠',
            'defensive': '🔴'
        }
        
        return f"""
╔═══════════════════════════════════════════════════════════╗
║              📊 ANÁLISE DE MERCADO R7 TRADING BOT API    ║
╠═══════════════════════════════════════════════════════════╣
║  BTC: ${cond.btc_price:,.2f}                               
║  24h: {cond.btc_change_24h:+.2f}% | 1h: {cond.btc_change_1h:+.2f}%
║                                                           
║  {trend_emoji.get(cond.trend, '')} Tendência: {cond.trend.upper()} ({cond.trend_strength:+.0f})
║  {vol_emoji.get(cond.volatility_level, '')} Volatilidade: {cond.volatility_level.upper()} ({cond.volatility:.2f}%)
║  📊 Volume: {cond.volume_ratio:.2f}x média
║  🔄 Fase: {cond.market_phase.upper()}
║                                                           
║  {action_emoji.get(cond.recommended_action, '')} AÇÃO: {cond.recommended_action.upper()}
║                                                           
║  Última atualização: {cond.timestamp.strftime('%H:%M:%S')}
╚═══════════════════════════════════════════════════════════╝
"""
