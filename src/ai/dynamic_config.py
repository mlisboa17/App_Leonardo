"""
🧠 CONFIGURADOR DINÂMICO - R7 TRADING BOT API
================================
Sistema que ajusta automaticamente os parâmetros dos bots
baseado nas condições REAIS do mercado em tempo real.

Fontes de dados:
1. Volatilidade atual (ATR, desvio padrão)
2. Tendência do mercado (SMAs, momentum)
3. Volume relativo
4. Fear & Greed Index (se disponível)
5. Correlação BTC
6. Performance recente do bot

Autor: Sistema R7 Trading Bot API
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import json
from pathlib import Path
import numpy as np

logger = logging.getLogger('DynamicConfig')


class MarketRegime:
    """Identifica o regime atual do mercado"""
    STRONG_UPTREND = "strong_uptrend"      # Alta forte
    UPTREND = "uptrend"                     # Alta moderada
    SIDEWAYS = "sideways"                   # Lateral
    DOWNTREND = "downtrend"                 # Baixa moderada
    STRONG_DOWNTREND = "strong_downtrend"  # Baixa forte
    HIGH_VOLATILITY = "high_volatility"    # Vol extrema
    LOW_VOLATILITY = "low_volatility"      # Vol muito baixa


class DynamicConfigManager:
    """
    Gerenciador de configuração dinâmica.
    Ajusta parâmetros dos bots em tempo real baseado no mercado.
    """
    
    def __init__(self, exchange_client, base_config: dict):
        self.exchange = exchange_client
        self.base_config = base_config
        self.current_adjustments = {}
        self.market_cache = {}
        self.cache_expiry = 60  # Cache por 60 segundos
        self.last_cache_time = None
        
        # Histórico de ajustes para não mudar muito rápido
        self.adjustment_history = []
        self.min_adjustment_interval = 300  # 5 minutos entre ajustes
        self.last_adjustment_time = None
        
        # Limites de ajuste (segurança)
        self.ADJUSTMENT_LIMITS = {
            'rsi_buy': {'min': 20, 'max': 45, 'max_change': 5},
            'rsi_sell': {'min': 55, 'max': 80, 'max_change': 5},
            'stop_loss': {'min': -3.0, 'max': -0.3, 'max_change': 0.3},
            'take_profit': {'min': 0.2, 'max': 3.0, 'max_change': 0.3},
            'amount_multiplier': {'min': 0.5, 'max': 1.5, 'max_change': 0.1},
        }
        
        # Estado do mercado
        self.market_state = {
            'regime': MarketRegime.SIDEWAYS,
            'volatility': 'normal',  # low, normal, high, extreme
            'trend_strength': 0,     # -100 a +100
            'volume_ratio': 1.0,     # volume atual / média
            'btc_correlation': 0,    # correlação com BTC
            'fear_greed': 50,        # 0-100
        }
        
        logger.info("🧠 DynamicConfigManager inicializado")
    
    async def analyze_market_conditions(self) -> Dict:
        """
        Analisa condições atuais do mercado.
        Retorna um dicionário com métricas chave.
        """
        try:
            # Obtém dados do BTC como referência principal
            btc_data = await self._get_market_data('BTCUSDT')
            if not btc_data:
                return self.market_state
            
            # Calcula volatilidade
            volatility = self._calculate_volatility(btc_data)
            
            # Calcula tendência
            trend = self._calculate_trend(btc_data)
            
            # Calcula volume relativo
            volume_ratio = self._calculate_volume_ratio(btc_data)
            
            # Determina regime do mercado
            regime = self._determine_market_regime(volatility, trend, volume_ratio)
            
            # Atualiza estado
            self.market_state = {
                'regime': regime,
                'volatility': self._categorize_volatility(volatility),
                'volatility_pct': volatility,
                'trend_strength': trend,
                'volume_ratio': volume_ratio,
                'timestamp': datetime.now().isoformat(),
            }
            
            logger.info(f"📊 Mercado: {regime} | Vol: {volatility:.2f}% | Trend: {trend:.0f} | Vol.Ratio: {volume_ratio:.2f}")
            
            return self.market_state
            
        except Exception as e:
            logger.error(f"Erro ao analisar mercado: {e}")
            return self.market_state
    
    async def _get_market_data(self, symbol: str) -> Optional[list]:
        """Obtém dados OHLCV do mercado"""
        try:
            # Verifica cache
            now = datetime.now()
            if (self.last_cache_time and 
                (now - self.last_cache_time).seconds < self.cache_expiry and
                symbol in self.market_cache):
                return self.market_cache[symbol]
            
            # Busca dados frescos
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=100)
            if ohlcv:
                self.market_cache[symbol] = ohlcv
                self.last_cache_time = now
                return ohlcv
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados de {symbol}: {e}")
            return None
    
    def _calculate_volatility(self, ohlcv: list) -> float:
        """Calcula volatilidade como % do preço"""
        try:
            if len(ohlcv) < 20:
                return 2.0  # Default
            
            # Usa ATR normalizado
            highs = [c[2] for c in ohlcv[-20:]]
            lows = [c[3] for c in ohlcv[-20:]]
            closes = [c[4] for c in ohlcv[-20:]]
            
            # True Range
            trs = []
            for i in range(1, len(closes)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1])
                )
                trs.append(tr)
            
            atr = np.mean(trs)
            current_price = closes[-1]
            
            # Volatilidade como % do preço
            volatility_pct = (atr / current_price) * 100
            
            return volatility_pct
            
        except Exception as e:
            logger.error(f"Erro ao calcular volatilidade: {e}")
            return 2.0
    
    def _calculate_trend(self, ohlcv: list) -> float:
        """
        Calcula força da tendência (-100 a +100)
        Positivo = alta, Negativo = baixa
        """
        try:
            if len(ohlcv) < 50:
                return 0
            
            closes = [c[4] for c in ohlcv]
            
            # SMAs
            sma_20 = np.mean(closes[-20:])
            sma_50 = np.mean(closes[-50:])
            current = closes[-1]
            
            # Momentum (variação % nas últimas 24h)
            momentum_24h = ((current - closes[-24]) / closes[-24]) * 100
            
            # Score de tendência
            trend_score = 0
            
            # Preço vs SMAs
            if current > sma_20:
                trend_score += 25
            else:
                trend_score -= 25
            
            if current > sma_50:
                trend_score += 25
            else:
                trend_score -= 25
            
            # SMA 20 vs SMA 50
            if sma_20 > sma_50:
                trend_score += 25
            else:
                trend_score -= 25
            
            # Momentum
            trend_score += min(25, max(-25, momentum_24h * 5))
            
            return trend_score
            
        except Exception as e:
            logger.error(f"Erro ao calcular tendência: {e}")
            return 0
    
    def _calculate_volume_ratio(self, ohlcv: list) -> float:
        """Calcula volume atual vs média"""
        try:
            if len(ohlcv) < 20:
                return 1.0
            
            volumes = [c[5] for c in ohlcv]
            avg_volume = np.mean(volumes[-20:])
            current_volume = volumes[-1]
            
            if avg_volume > 0:
                return current_volume / avg_volume
            return 1.0
            
        except Exception as e:
            return 1.0
    
    def _categorize_volatility(self, vol_pct: float) -> str:
        """Categoriza nível de volatilidade"""
        if vol_pct < 1.0:
            return 'low'
        elif vol_pct < 2.5:
            return 'normal'
        elif vol_pct < 5.0:
            return 'high'
        else:
            return 'extreme'
    
    def _determine_market_regime(self, volatility: float, trend: float, volume_ratio: float) -> str:
        """Determina o regime atual do mercado"""
        
        # Volatilidade extrema sobrepõe tudo
        if volatility > 6.0:
            return MarketRegime.HIGH_VOLATILITY
        
        if volatility < 0.8:
            return MarketRegime.LOW_VOLATILITY
        
        # Tendências
        if trend > 60:
            return MarketRegime.STRONG_UPTREND
        elif trend > 25:
            return MarketRegime.UPTREND
        elif trend < -60:
            return MarketRegime.STRONG_DOWNTREND
        elif trend < -25:
            return MarketRegime.DOWNTREND
        else:
            return MarketRegime.SIDEWAYS
    
    def get_dynamic_config(self, bot_type: str, base_bot_config: dict) -> dict:
        """
        Retorna configuração ajustada dinamicamente para um bot.
        
        Args:
            bot_type: 'bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme'
            base_bot_config: Configuração base do bot
        
        Returns:
            Configuração ajustada
        """
        # Copia config base
        adjusted = base_bot_config.copy()
        
        regime = self.market_state['regime']
        volatility = self.market_state.get('volatility', 'normal')
        trend = self.market_state.get('trend_strength', 0)
        vol_ratio = self.market_state.get('volume_ratio', 1.0)
        
        # =====================================================
        # AJUSTES POR REGIME DE MERCADO
        # =====================================================
        
        if regime == MarketRegime.STRONG_UPTREND:
            # Mercado em alta forte - ser mais agressivo em compras
            adjusted = self._adjust_for_uptrend(adjusted, bot_type, strong=True)
            
        elif regime == MarketRegime.UPTREND:
            adjusted = self._adjust_for_uptrend(adjusted, bot_type, strong=False)
            
        elif regime == MarketRegime.STRONG_DOWNTREND:
            # Mercado em baixa forte - ser muito conservador
            adjusted = self._adjust_for_downtrend(adjusted, bot_type, strong=True)
            
        elif regime == MarketRegime.DOWNTREND:
            adjusted = self._adjust_for_downtrend(adjusted, bot_type, strong=False)
            
        elif regime == MarketRegime.HIGH_VOLATILITY:
            # Volatilidade extrema - alargar stops, diminuir posições
            adjusted = self._adjust_for_high_volatility(adjusted, bot_type)
            
        elif regime == MarketRegime.LOW_VOLATILITY:
            # Volatilidade baixa - apertar ranges
            adjusted = self._adjust_for_low_volatility(adjusted, bot_type)
            
        else:  # SIDEWAYS
            # Mercado lateral - RSI funciona bem aqui
            adjusted = self._adjust_for_sideways(adjusted, bot_type)
        
        # =====================================================
        # AJUSTES POR VOLUME
        # =====================================================
        if vol_ratio > 2.0:
            # Volume muito alto - possível movimento forte
            adjusted['risk']['take_profit'] *= 1.2
            adjusted['risk']['stop_loss'] *= 1.1
            
        elif vol_ratio < 0.5:
            # Volume muito baixo - cuidado com liquidez
            adjusted['trading']['amount_per_trade'] *= 0.8
        
        # =====================================================
        # VALIDAÇÃO DE LIMITES
        # =====================================================
        adjusted = self._validate_limits(adjusted)
        
        # Loga ajustes
        self._log_adjustments(bot_type, base_bot_config, adjusted)
        
        return adjusted
    
    def _adjust_for_uptrend(self, config: dict, bot_type: str, strong: bool) -> dict:
        """Ajustes para mercado em alta"""
        config = config.copy()
        
        # RSI: Comprar em níveis mais altos (pullbacks menores)
        rsi_adjustment = 5 if strong else 3
        config['rsi']['oversold'] = min(45, config['rsi']['oversold'] + rsi_adjustment)
        
        # Take profit maior em tendência de alta
        tp_multiplier = 1.3 if strong else 1.15
        config['risk']['take_profit'] *= tp_multiplier
        
        # Stop loss pode ser um pouco mais apertado
        config['risk']['stop_loss'] *= 0.9
        
        # Pode aumentar posição em alta forte
        if strong and bot_type in ['bot_estavel', 'bot_medio']:
            config['trading']['amount_per_trade'] *= 1.1
        
        return config
    
    def _adjust_for_downtrend(self, config: dict, bot_type: str, strong: bool) -> dict:
        """Ajustes para mercado em baixa"""
        config = config.copy()
        
        # RSI: Esperar níveis mais baixos para comprar
        rsi_adjustment = 8 if strong else 4
        config['rsi']['oversold'] = max(20, config['rsi']['oversold'] - rsi_adjustment)
        
        # Vender mais rápido (RSI mais baixo)
        config['rsi']['overbought'] = max(55, config['rsi']['overbought'] - rsi_adjustment)
        
        # Stop loss mais largo (mercado pode cair mais)
        sl_multiplier = 1.3 if strong else 1.15
        config['risk']['stop_loss'] *= sl_multiplier
        
        # Take profit menor (pegar o que conseguir)
        config['risk']['take_profit'] *= 0.85
        
        # Reduzir tamanho das posições
        reduction = 0.6 if strong else 0.8
        config['trading']['amount_per_trade'] *= reduction
        
        # Em baixa forte, desabilitar bots mais arriscados
        if strong and bot_type == 'bot_meme':
            config['trading']['max_positions'] = 1
        
        return config
    
    def _adjust_for_high_volatility(self, config: dict, bot_type: str) -> dict:
        """Ajustes para volatilidade extrema"""
        config = config.copy()
        
        # Stops e takes muito mais largos
        config['risk']['stop_loss'] *= 1.5
        config['risk']['take_profit'] *= 1.5
        
        # RSI em extremos
        config['rsi']['oversold'] = max(20, config['rsi']['oversold'] - 8)
        config['rsi']['overbought'] = min(80, config['rsi']['overbought'] + 8)
        
        # Reduzir posições significativamente
        config['trading']['amount_per_trade'] *= 0.5
        config['trading']['max_positions'] = max(1, config['trading']['max_positions'] - 1)
        
        # Tempo de hold mais curto
        config['risk']['max_hold_minutes'] = int(config['risk']['max_hold_minutes'] * 0.5)
        
        return config
    
    def _adjust_for_low_volatility(self, config: dict, bot_type: str) -> dict:
        """Ajustes para volatilidade muito baixa"""
        config = config.copy()
        
        # Stops e takes mais apertados
        config['risk']['stop_loss'] *= 0.7
        config['risk']['take_profit'] *= 0.7
        
        # RSI menos extremo (mercado range-bound)
        config['rsi']['oversold'] = min(42, config['rsi']['oversold'] + 5)
        config['rsi']['overbought'] = max(58, config['rsi']['overbought'] - 5)
        
        # Pode aumentar posições (risco menor)
        if bot_type in ['bot_estavel', 'bot_medio']:
            config['trading']['amount_per_trade'] *= 1.2
        
        return config
    
    def _adjust_for_sideways(self, config: dict, bot_type: str) -> dict:
        """Ajustes para mercado lateral - RSI funciona melhor aqui"""
        config = config.copy()
        
        # Configuração quase padrão - RSI é bom em sideways
        # Pequenos ajustes para otimizar
        
        # RSI clássico funciona bem
        # Mantém próximo do default
        
        # Pode aumentar um pouco as posições
        if bot_type == 'bot_estavel':
            config['trading']['amount_per_trade'] *= 1.1
        
        return config
    
    def _validate_limits(self, config: dict) -> dict:
        """Valida e aplica limites de segurança"""
        
        # RSI limits
        config['rsi']['oversold'] = max(20, min(45, config['rsi']['oversold']))
        config['rsi']['overbought'] = max(55, min(80, config['rsi']['overbought']))
        
        # Stop loss limits (valores negativos)
        config['risk']['stop_loss'] = max(-3.0, min(-0.3, config['risk']['stop_loss']))
        
        # Take profit limits
        config['risk']['take_profit'] = max(0.2, min(3.0, config['risk']['take_profit']))
        
        # Amount limits (não pode ser menor que $10)
        config['trading']['amount_per_trade'] = max(10, config['trading']['amount_per_trade'])
        
        # Max positions
        config['trading']['max_positions'] = max(1, min(5, config['trading']['max_positions']))
        
        # Hold time
        config['risk']['max_hold_minutes'] = max(15, min(480, config['risk']['max_hold_minutes']))
        
        return config
    
    def _log_adjustments(self, bot_type: str, original: dict, adjusted: dict) -> None:
        """Loga mudanças significativas"""
        changes = []
        
        # Compara RSI
        if original.get('rsi', {}).get('oversold') != adjusted['rsi']['oversold']:
            changes.append(f"RSI_buy: {original['rsi']['oversold']} → {adjusted['rsi']['oversold']}")
        
        if original.get('rsi', {}).get('overbought') != adjusted['rsi']['overbought']:
            changes.append(f"RSI_sell: {original['rsi']['overbought']} → {adjusted['rsi']['overbought']}")
        
        # Compara Risk
        if original.get('risk', {}).get('stop_loss') != adjusted['risk']['stop_loss']:
            changes.append(f"SL: {original['risk']['stop_loss']}% → {adjusted['risk']['stop_loss']:.2f}%")
        
        if original.get('risk', {}).get('take_profit') != adjusted['risk']['take_profit']:
            changes.append(f"TP: {original['risk']['take_profit']}% → {adjusted['risk']['take_profit']:.2f}%")
        
        if changes:
            logger.info(f"🔧 [{bot_type}] Ajustes dinâmicos: {', '.join(changes)}")
    
    def get_status_report(self) -> str:
        """Retorna relatório de status do sistema dinâmico"""
        report = f"""
╔══════════════════════════════════════════════════════════╗
║          🧠 CONFIGURADOR DINÂMICO - STATUS               ║
╠══════════════════════════════════════════════════════════╣
║  Regime Atual: {self.market_state['regime']:<40} ║
║  Volatilidade: {self.market_state.get('volatility', 'N/A'):<40} ║
║  Vol. %:       {self.market_state.get('volatility_pct', 0):<40.2f} ║
║  Tendência:    {self.market_state.get('trend_strength', 0):<40} ║
║  Volume Ratio: {self.market_state.get('volume_ratio', 1.0):<40.2f} ║
║  Última Atualização: {self.market_state.get('timestamp', 'N/A'):<29} ║
╚══════════════════════════════════════════════════════════╝
"""
        return report


class PerformanceBasedAdjuster:
    """
    Ajusta configurações baseado na performance recente do bot.
    Se bot está perdendo, fica mais conservador.
    Se bot está ganhando, pode ser mais agressivo.
    """
    
    def __init__(self):
        self.trade_history = []
        self.max_history = 50  # Últimos 50 trades
        
    def add_trade_result(self, bot_type: str, profit_pct: float, won: bool):
        """Registra resultado de um trade"""
        self.trade_history.append({
            'bot': bot_type,
            'profit_pct': profit_pct,
            'won': won,
            'timestamp': datetime.now()
        })
        
        # Mantém apenas últimos N
        if len(self.trade_history) > self.max_history:
            self.trade_history = self.trade_history[-self.max_history:]
    
    def get_performance_multiplier(self, bot_type: str) -> float:
        """
        Retorna multiplicador baseado em performance recente.
        < 1.0 = ser mais conservador
        > 1.0 = pode ser mais agressivo
        """
        # Filtra trades do bot nos últimos 24h
        cutoff = datetime.now() - timedelta(hours=24)
        recent = [t for t in self.trade_history 
                  if t['bot'] == bot_type and t['timestamp'] > cutoff]
        
        if len(recent) < 5:
            return 1.0  # Dados insuficientes
        
        # Calcula win rate
        wins = sum(1 for t in recent if t['won'])
        win_rate = wins / len(recent)
        
        # Calcula profit médio
        avg_profit = np.mean([t['profit_pct'] for t in recent])
        
        # Score de performance
        if win_rate >= 0.7 and avg_profit > 0.3:
            return 1.2  # Performance excelente
        elif win_rate >= 0.55 and avg_profit > 0:
            return 1.1  # Performance boa
        elif win_rate < 0.4 or avg_profit < -0.5:
            return 0.7  # Performance ruim - ser conservador
        elif win_rate < 0.5:
            return 0.85  # Performance abaixo da média
        else:
            return 1.0  # Normal
    
    def should_pause_bot(self, bot_type: str) -> Tuple[bool, str]:
        """
        Verifica se bot deve ser pausado por performance muito ruim.
        Retorna (deve_pausar, motivo)
        """
        # Últimos 10 trades
        recent = [t for t in self.trade_history if t['bot'] == bot_type][-10:]
        
        if len(recent) < 5:
            return False, ""
        
        # Verifica losing streak
        last_5 = recent[-5:]
        if all(not t['won'] for t in last_5):
            return True, "5 losses consecutivos"
        
        # Verifica loss total
        total_loss = sum(t['profit_pct'] for t in recent if t['profit_pct'] < 0)
        if total_loss < -5.0:  # -5% nos últimos 10 trades
            return True, f"Perdas acumuladas: {total_loss:.2f}%"
        
        return False, ""


# Singleton para acesso global
_dynamic_config_instance = None

def get_dynamic_config_manager(exchange_client=None, base_config=None) -> DynamicConfigManager:
    """Retorna instância singleton do gerenciador"""
    global _dynamic_config_instance
    
    if _dynamic_config_instance is None:
        if exchange_client is None or base_config is None:
            raise ValueError("Primeira chamada requer exchange_client e base_config")
        _dynamic_config_instance = DynamicConfigManager(exchange_client, base_config)
    
    return _dynamic_config_instance
