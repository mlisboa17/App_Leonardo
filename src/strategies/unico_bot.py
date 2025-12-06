"""
🤖 UnicoBot - Bot Unificado com Smart Strategy
============================================

Bot que assume TODAS as carteiras com estratégia única
Baseado na Smart Strategy do App_Leonardo original

Características:
- RSI adaptativo por moeda (baseado em histórico)
- Segura enquanto tendência for de ALTA
- Vende apenas quando tendência VIRAR para QUEDA
- Sistema de urgência se ficar sem trades
- Meta: $100/dia comprando barato e vendendo na virada

⚠️ DESATIVADO POR PADRÃO - Este bot deve ser ativado manualmente
"""

import os
import json
import yaml
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Tentar importar biblioteca TA
try:
    import ta
    HAS_TA = True
except ImportError:
    HAS_TA = False

logger = logging.getLogger(__name__)


class SmartStrategy:
    """
    Estratégia Inteligente do UnicoBot:
    1. Carrega perfis de RSI de cada moeda
    2. Compra quando RSI está baixo para AQUELA moeda
    3. Segura enquanto tendência for de ALTA
    4. Vende APENAS quando tendência virar de QUEDA
    """
    
    name = "Smart Strategy v2.0"
    
    def __init__(self, config: dict):
        self.config = config
        self.smart_config = config.get('smart_strategy', {})
        
        # Carrega perfis das moedas
        self.profiles = config.get('crypto_profiles', {})
        
        # Estado de cada moeda
        self.last_trade_time: Dict[str, datetime] = {}
        self.positions_open_time: Dict[str, datetime] = {}
        
        # Configurações de Stop/Take
        self.stop_loss_pct = self.smart_config.get('stop_loss_pct', -0.6)
        self.stop_loss_tight = self.smart_config.get('stop_loss_tight', -0.3)
        self.max_take_pct = self.smart_config.get('max_take_pct', 2.0)
        self.trailing_stop_pct = self.smart_config.get('trailing_stop_pct', 0.15)
        self.max_hold_minutes = self.smart_config.get('max_hold_minutes', 5)
        self.min_profit_to_hold = config.get('targets', {}).get('min_trade_profit', 0.05)
        
        # Controle de picos de preço
        self.price_peaks: Dict[str, float] = {}
        
        # Estatísticas do dia
        self.daily_stats = {
            'trades': 0,
            'profit': 0.0,
            'wins': 0,
            'losses': 0,
            'target': config.get('targets', {}).get('daily_profit', 100.0),
            'last_reset': datetime.now().date()
        }
        
        logger.info(f"✅ {self.name} inicializada")
        logger.info(f"   Biblioteca TA: {'SIM' if HAS_TA else 'NÃO'}")
        logger.info(f"   Moedas com perfil: {len(self.profiles)}")
    
    def get_profile(self, symbol: str) -> dict:
        """Retorna perfil de uma moeda"""
        # Normaliza símbolo (BTC/USDT -> BTCUSDT)
        key = symbol.replace('/', '')
        
        if key in self.profiles:
            return self.profiles[key]
        
        # Perfil padrão
        return {'buy_rsi': 38, 'sell_rsi': 62, 'rsi_mean': 50}
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula todos os indicadores técnicos"""
        
        if HAS_TA:
            # ===== BIBLIOTECA TA (PROFISSIONAL) =====
            
            # RSI
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_hist'] = macd.macd_diff()
            
            # Médias Móveis
            df['sma20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
            df['sma50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
            df['ema9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
            df['ema21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['close'], window=20)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            
            # ATR (Volatilidade)
            df['atr'] = ta.volatility.AverageTrueRange(
                df['high'], df['low'], df['close']
            ).average_true_range()
            
        else:
            # ===== CÁLCULOS MANUAIS (FALLBACK) =====
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Médias
            df['sma20'] = df['close'].rolling(window=20).mean()
            df['sma50'] = df['close'].rolling(window=50).mean()
            df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
            
            # MACD
            exp12 = df['close'].ewm(span=12, adjust=False).mean()
            exp26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = exp12 - exp26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def detect_trend(self, df: pd.DataFrame) -> Tuple[str, int, list]:
        """
        Detecta tendência atual
        Retorna: ('ALTA', 'QUEDA', 'LATERAL'), força (0-4), razões
        """
        
        current = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else current
        
        alta_signals = 0
        queda_signals = 0
        reasons = []
        
        # 1. MACD acima do sinal?
        if pd.notna(current.get('macd')) and pd.notna(current.get('macd_signal')):
            if current['macd'] > current['macd_signal']:
                alta_signals += 1
                reasons.append("MACD↑")
            else:
                queda_signals += 1
                reasons.append("MACD↓")
        
        # 2. Preço acima da SMA20?
        if pd.notna(current.get('sma20')):
            if current['close'] > current['sma20']:
                alta_signals += 1
                reasons.append("P>SMA20")
            else:
                queda_signals += 1
                reasons.append("P<SMA20")
        
        # 3. RSI subindo ou descendo?
        if pd.notna(current.get('rsi')) and pd.notna(previous.get('rsi')):
            if current['rsi'] > previous['rsi']:
                alta_signals += 1
                reasons.append("RSI↑")
            else:
                queda_signals += 1
                reasons.append("RSI↓")
        
        # 4. EMA9 acima da EMA21?
        if pd.notna(current.get('ema9')) and pd.notna(current.get('ema21')):
            if current['ema9'] > current['ema21']:
                alta_signals += 1
                reasons.append("EMA↑")
            else:
                queda_signals += 1
                reasons.append("EMA↓")
        
        # Determina tendência
        if alta_signals >= 3:
            return 'ALTA', alta_signals, reasons
        elif queda_signals >= 3:
            return 'QUEDA', queda_signals, reasons
        else:
            return 'LATERAL', max(alta_signals, queda_signals), reasons
    
    def get_adjusted_buy_rsi(self, symbol: str) -> float:
        """
        Retorna RSI de compra ajustado com base no tempo sem trades
        (Sistema de Urgência)
        """
        profile = self.get_profile(symbol)
        base_rsi = profile.get('buy_rsi', 38)
        mean_rsi = profile.get('rsi_mean', 50)
        
        # Quanto tempo sem trade nessa moeda?
        last_time = self.last_trade_time.get(symbol)
        
        if not last_time:
            minutes_idle = 999
        else:
            minutes_idle = (datetime.now() - last_time).total_seconds() / 60
        
        # Sistema de urgência
        urgency = self.smart_config.get('urgency_system', {})
        if not urgency.get('enabled', True):
            return base_rsi
        
        # Ajusta RSI baseado no tempo parado
        adjustment = 0
        
        if minutes_idle > 5:
            adjustment = urgency.get('idle_5min_adjustment', 1)
        if minutes_idle > 10:
            adjustment = urgency.get('idle_10min_adjustment', 2)
        if minutes_idle > 20:
            adjustment = urgency.get('idle_20min_adjustment', 3)
        if minutes_idle > 30:
            adjustment = urgency.get('idle_30min_adjustment', 4)
        if minutes_idle > 60:
            adjustment = urgency.get('idle_60min_adjustment', 5)
        
        # Limita ajuste máximo
        max_increase = urgency.get('max_rsi_increase', 8)
        adjustment = min(adjustment, max_increase)
        
        # RSI ajustado (mas nunca passa do RSI médio - 5)
        adjusted_rsi = base_rsi + adjustment
        max_allowed = mean_rsi - 5  # Nunca compra em zona neutra
        
        return min(adjusted_rsi, max_allowed)
    
    def analyze(self, df: pd.DataFrame, symbol: str) -> Tuple[str, str, dict]:
        """
        Analisa mercado e retorna sinal de entrada
        
        Returns:
            signal: 'BUY', 'SELL', 'HOLD'
            reason: Explicação do sinal
            indicators: Dict com valores dos indicadores
        """
        
        # Calcula indicadores
        df = self.calculate_indicators(df)
        
        current = df.iloc[-1]
        profile = self.get_profile(symbol)
        
        # Indicadores atuais
        rsi = current.get('rsi', 50)
        macd = current.get('macd', 0)
        macd_signal = current.get('macd_signal', 0)
        price = current['close']
        sma20 = current.get('sma20', price)
        
        indicators = {
            'rsi': rsi,
            'macd': macd,
            'macd_signal': macd_signal,
            'price': price,
            'sma20': sma20,
            'ema9': current.get('ema9'),
            'ema21': current.get('ema21'),
        }
        
        # Detecta tendência
        trend, strength, trend_reasons = self.detect_trend(df)
        indicators['trend'] = trend
        indicators['trend_strength'] = strength
        
        # RSI de compra ajustado (sistema de urgência)
        buy_rsi = self.get_adjusted_buy_rsi(symbol)
        sell_rsi = profile.get('sell_rsi', 62)
        
        # ===== LÓGICA DE DECISÃO =====
        
        # COMPRA: RSI baixo + não em tendência de QUEDA forte
        if rsi < buy_rsi and trend != 'QUEDA':
            return 'BUY', f"RSI {rsi:.1f} < {buy_rsi} | Trend: {trend}", indicators
        
        # VENDA: RSI alto OU tendência virou para QUEDA
        if rsi > sell_rsi:
            return 'SELL', f"RSI {rsi:.1f} > {sell_rsi} (overbought)", indicators
        
        if trend == 'QUEDA' and strength >= 3:
            return 'SELL', f"Tendência QUEDA forte ({strength}/4) - {', '.join(trend_reasons)}", indicators
        
        # HOLD: Mantém posição
        return 'HOLD', f"RSI {rsi:.1f} | Trend: {trend} ({strength}/4)", indicators
    
    def should_close_position(
        self, 
        symbol: str, 
        entry_price: float, 
        current_price: float,
        entry_time: datetime,
        df: pd.DataFrame = None
    ) -> Tuple[bool, str]:
        """
        Verifica se deve fechar posição
        
        Returns:
            should_close: True se deve fechar
            reason: Motivo do fechamento
        """
        
        # Calcula PnL%
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Tempo na posição
        hold_minutes = (datetime.now() - entry_time).total_seconds() / 60
        
        # Atualiza pico de preço (para trailing stop)
        peak = self.price_peaks.get(symbol, entry_price)
        if current_price > peak:
            self.price_peaks[symbol] = current_price
            peak = current_price
        
        # ===== VERIFICAÇÕES DE SAÍDA =====
        
        # 1. Stop Loss
        if pnl_pct <= self.stop_loss_pct:
            return True, f"STOP LOSS: {pnl_pct:.2f}% <= {self.stop_loss_pct}%"
        
        # 2. Stop Loss apertado se segurando muito tempo sem lucro
        if hold_minutes > 3 and pnl_pct <= self.stop_loss_tight:
            return True, f"STOP TIGHT: {pnl_pct:.2f}% após {hold_minutes:.1f}min"
        
        # 3. Take Profit máximo
        if pnl_pct >= self.max_take_pct:
            return True, f"TAKE PROFIT: {pnl_pct:.2f}% >= {self.max_take_pct}%"
        
        # 4. Trailing Stop
        if peak > entry_price:
            drop_from_peak = ((peak - current_price) / peak) * 100
            if drop_from_peak >= self.trailing_stop_pct and pnl_pct > 0:
                return True, f"TRAILING STOP: Caiu {drop_from_peak:.2f}% do pico (lucro: {pnl_pct:.2f}%)"
        
        # 5. Tempo máximo
        if hold_minutes >= self.max_hold_minutes:
            if pnl_pct >= self.min_profit_to_hold:
                return True, f"TEMPO: {hold_minutes:.1f}min com lucro {pnl_pct:.2f}%"
            elif pnl_pct < 0:
                return True, f"TEMPO: {hold_minutes:.1f}min com prejuízo {pnl_pct:.2f}%"
        
        # 6. Tendência virou para QUEDA (se tiver df)
        if df is not None:
            df = self.calculate_indicators(df)
            trend, strength, reasons = self.detect_trend(df)
            
            if trend == 'QUEDA' and strength >= 3 and pnl_pct > 0:
                return True, f"TENDÊNCIA QUEDA: {', '.join(reasons)} | Lucro: {pnl_pct:.2f}%"
        
        return False, f"HOLD: PnL {pnl_pct:.2f}% | {hold_minutes:.1f}min"


class UnicoBot:
    """
    Bot Unificado que gerencia todas as carteiras
    
    ⚠️ DESATIVADO POR PADRÃO
    Deve ser ativado manualmente no config
    """
    
    def __init__(self, config_path: str = "config/unico_bot_config.yaml"):
        """Inicializa o UnicoBot"""
        
        self.config_path = config_path
        self.config = self._load_config()
        
        # Verifica se está habilitado
        self.enabled = self.config.get('enabled', False)
        
        if not self.enabled:
            logger.warning("⚠️ UnicoBot está DESATIVADO. Ative em unico_bot_config.yaml")
            return
        
        # Configurações
        self.name = self.config.get('name', 'UnicoBot')
        self.portfolio = self.config.get('portfolio', [])
        self.trading_config = self.config.get('trading', {})
        
        # Estatísticas
        self.stats = {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'daily_pnl': 0.0,
            'open_positions': 0,
        }
        
        # Posições abertas
        self.positions: Dict[str, dict] = {}
        
        # Inicializa estratégia
        self.strategy = SmartStrategy(self.config)
        
        logger.info(f"🤖 {self.name} inicializado")
        logger.info(f"   Moedas: {len(self.portfolio)}")
        logger.info(f"   Max posições: {self.trading_config.get('max_positions', 15)}")
    
    def _load_config(self) -> dict:
        """Carrega configuração do arquivo YAML"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            logger.error(f"❌ Arquivo de configuração não encontrado: {self.config_path}")
            return {}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            full_config = yaml.safe_load(f)
        
        return full_config.get('unico_bot', {})
    
    def get_symbols(self) -> List[str]:
        """Retorna lista de símbolos do portfólio"""
        return [p['symbol'] for p in self.portfolio]
    
    def get_symbol_category(self, symbol: str) -> str:
        """Retorna categoria da moeda"""
        for p in self.portfolio:
            if p['symbol'] == symbol:
                return p.get('category', 'medio')
        return 'medio'
    
    def analyze_symbol(self, symbol: str, df: pd.DataFrame) -> Tuple[str, str, dict]:
        """Analisa um símbolo específico"""
        return self.strategy.analyze(df, symbol)
    
    def should_close(
        self, 
        symbol: str, 
        entry_price: float,
        current_price: float,
        entry_time: datetime,
        df: pd.DataFrame = None
    ) -> Tuple[bool, str]:
        """Verifica se deve fechar posição"""
        return self.strategy.should_close_position(
            symbol, entry_price, current_price, entry_time, df
        )
    
    def update_trade_time(self, symbol: str):
        """Atualiza tempo do último trade"""
        self.strategy.last_trade_time[symbol] = datetime.now()
    
    def get_config_summary(self) -> dict:
        """Retorna resumo da configuração"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'portfolio_size': len(self.portfolio),
            'symbols': self.get_symbols(),
            'max_positions': self.trading_config.get('max_positions', 15),
            'amount_per_trade': self.trading_config.get('amount_per_trade', 500),
            'daily_target': self.config.get('targets', {}).get('daily_profit', 100),
            'strategy': self.strategy.name,
        }


# ===== FUNÇÃO PARA VERIFICAR SE DEVE USAR UNICO BOT =====
def should_use_unico_bot() -> bool:
    """Verifica se o UnicoBot está habilitado no config"""
    config_path = Path("config/unico_bot_config.yaml")
    
    if not config_path.exists():
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config.get('unico_bot', {}).get('enabled', False)


# ===== TESTE =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("🤖 UnicoBot - Teste de Inicialização")
    print("=" * 60)
    
    bot = UnicoBot()
    
    if bot.enabled:
        print(f"\n✅ UnicoBot ATIVO")
        print(f"   Nome: {bot.name}")
        print(f"   Moedas: {len(bot.portfolio)}")
        print(f"   Símbolos: {', '.join(bot.get_symbols())}")
    else:
        print(f"\n⚠️ UnicoBot DESATIVADO")
        print("   Para ativar, edite config/unico_bot_config.yaml")
        print("   Mude 'enabled: false' para 'enabled: true'")
