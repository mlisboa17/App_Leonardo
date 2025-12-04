"""
🧠 Smart Strategy - Estratégia Inteligente com Perfis por Moeda
Meta: $100/dia comprando barato e vendendo quando tendência virar

Características:
- RSI adaptativo por moeda (baseado em histórico)
- Segura enquanto tendência for de ALTA
- Vende apenas quando tendência VIRAR para QUEDA
- Sistema de urgência se ficar sem trades
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import pandas as pd
import numpy as np

# Biblioteca de Análise Técnica (profissional)
try:
    import ta
    HAS_TA = True
except ImportError:
    HAS_TA = False


class SmartStrategy:
    """
    Estratégia Inteligente:
    1. Carrega perfis de RSI de cada moeda (do arquivo JSON)
    2. Compra quando RSI está baixo para AQUELA moeda
    3. Segura enquanto tendência for de ALTA
    4. Vende APENAS quando tendência virar de QUEDA
    """
    
    name = "Smart Strategy v2.0"
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Carrega perfis das moedas
        self.profiles = self._load_crypto_profiles()
        
        # Estado de cada moeda
        self.last_trade_time: Dict[str, datetime] = {}
        self.positions_open_time: Dict[str, datetime] = {}
        
        # Configurações - SUPER AGRESSIVO PARA VENDER MAIS
        self.stop_loss_pct = -0.6  # -0.6% stop loss (mais apertado)
        self.stop_loss_apertado = -0.3  # -0.3% se ficar muito tempo sem lucro
        self.max_take_pct = 2.0    # +2% máximo (trava lucro mais cedo)
        self.max_hold_minutes = 5  # Máx 5 min segurando (era 10)
        self.min_profit_to_hold = 0.05  # Mín 0.05% para vender (quase nada)
        self.trailing_stop_pct = 0.15  # Trailing stop de 0.15% (mais apertado)
        
        # Controle de picos de preço (para trailing stop)
        self.price_peaks: Dict[str, float] = {}  # {symbol: highest_price_since_entry}
        
        # Estatísticas do dia
        self.daily_stats = {
            'trades': 0,
            'profit': 0.0,
            'wins': 0,
            'losses': 0,
            'target': 100.0,
            'last_reset': datetime.now().date()
        }
        
        print(f"✅ {self.name} inicializada")
        print(f"   Biblioteca TA: {'SIM' if HAS_TA else 'NÃO'}")
        print(f"   Moedas com perfil: {len(self.profiles)}")
    
    
    def _load_crypto_profiles(self) -> dict:
        """Carrega perfis das moedas do arquivo JSON"""
        
        # Tenta carregar do arquivo
        profile_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crypto_profiles.json'),
            'data/crypto_profiles.json',
            'App_Leonardo/data/crypto_profiles.json'
        ]
        
        for path in profile_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    print(f"   ✅ Perfis carregados de: {path}")
                    return data
                except Exception as e:
                    print(f"   ⚠️ Erro ao carregar {path}: {e}")
        
        # Perfis padrão se não encontrar arquivo
        print("   ⚠️ Usando perfis padrão (execute quick_analysis.py para gerar)")
        return {
            'BTCUSDT': {'buy_rsi': 40, 'sell_rsi': 63, 'rsi_mean': 51},
            'ETHUSDT': {'buy_rsi': 40, 'sell_rsi': 61, 'rsi_mean': 50},
            'SOLUSDT': {'buy_rsi': 40, 'sell_rsi': 63, 'rsi_mean': 50},
            'BNBUSDT': {'buy_rsi': 40, 'sell_rsi': 60, 'rsi_mean': 50},
            'XRPUSDT': {'buy_rsi': 41, 'sell_rsi': 63, 'rsi_mean': 51},
            'LINKUSDT': {'buy_rsi': 41, 'sell_rsi': 62, 'rsi_mean': 51},
            'DOGEUSDT': {'buy_rsi': 40, 'sell_rsi': 61, 'rsi_mean': 50},
            'LTCUSDT': {'buy_rsi': 39, 'sell_rsi': 60, 'rsi_mean': 49},
        }
    
    
    def get_profile(self, symbol: str) -> dict:
        """Retorna perfil de uma moeda (converte BTC/USDT para BTCUSDT)"""
        # Normaliza símbolo
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
            df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
            
            # ADX (Força da tendência)
            adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
            df['adx'] = adx.adx()
            
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
        
        # Ajusta RSI baseado no tempo parado
        adjustment = 0
        
        if minutes_idle > 5:
            adjustment = 1
        if minutes_idle > 10:
            adjustment = 2
        if minutes_idle > 20:
            adjustment = 3
        if minutes_idle > 30:
            adjustment = 4
        if minutes_idle > 60:
            adjustment = 5
        
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
            'sma_20': sma20,
            'price': price
        }
        
        # RSI de compra ajustado (com urgência)
        buy_rsi = self.get_adjusted_buy_rsi(symbol)
        
        # Detecta tendência
        trend, trend_strength, trend_reasons = self.detect_trend(df)
        
        # ===== LÓGICA DE COMPRA =====
        # Compra quando RSI está baixo E tendência começando a subir
        
        buy_conditions = 0
        buy_reasons = []
        
        # 1. RSI abaixo do threshold adaptativo
        if rsi < buy_rsi:
            buy_conditions += 1
            buy_reasons.append(f"RSI {rsi:.1f} < {buy_rsi:.1f}")
        
        # 2. MACD cruzando para cima (momentum positivo)
        if macd > macd_signal:
            buy_conditions += 1
            buy_reasons.append("MACD↑")
        
        # 3. Preço próximo ou abaixo da SMA20 (bom preço)
        distance_sma = ((price - sma20) / sma20) * 100
        if distance_sma < 0.5:
            buy_conditions += 1
            buy_reasons.append(f"Perto SMA20 ({distance_sma:+.1f}%)")
        
        # Precisa de pelo menos 2 condições para comprar
        if buy_conditions >= 2:
            reason = f"COMPRA: {' | '.join(buy_reasons)}"
            self.last_trade_time[symbol] = datetime.now()
            return 'BUY', reason, indicators
        
        # Se não comprar, retorna HOLD
        return 'HOLD', f"Aguardando (RSI {rsi:.1f}, threshold {buy_rsi:.1f})", indicators
    
    
    def should_sell(self, symbol: str, entry_price: float, current_price: float, 
                    df: pd.DataFrame, position_time: datetime = None,
                    positions_full: bool = False) -> Tuple[bool, str]:
        """
        Decide se deve vender a posição
        
        LÓGICA PRINCIPAL:
        - Stop Loss: SEMPRE ativo (-1.5%)
        - Segura enquanto tendência for ALTA
        - Vende quando tendência VIRAR para QUEDA
        
        MODO AGRESSIVO (quando positions_full=True):
        - Critério de venda mais flexível (RSI 50+ em vez de 60+)
        - Aceita vender em tendência LATERAL
        - MAS NUNCA vende no prejuízo (preço atual >= preço entrada)
        
        PROTEÇÃO DE CAPITAL:
        - Stop loss normal: -1.0%
        - Stop loss apertado após 10min sem lucro: -0.5%
        - Trailing stop: Protege lucro quando sobe
        """
        
        # Calcula lucro/prejuízo
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        profile = self.get_profile(symbol)
        sell_rsi = profile.get('sell_rsi', 65)
        
        # Calcula indicadores
        df = self.calculate_indicators(df)
        current = df.iloc[-1]
        rsi = current.get('rsi', 50)
        
        # Detecta tendência
        trend, strength, reasons = self.detect_trend(df)
        
        # Tempo da posição aberta
        minutes_open = 0
        if position_time:
            minutes_open = (datetime.now() - position_time).total_seconds() / 60
        
        # ===== 0. TRAILING STOP (PROTEGE LUCRO) =====
        # Atualiza pico de preço
        if symbol not in self.price_peaks:
            self.price_peaks[symbol] = current_price
        elif current_price > self.price_peaks[symbol]:
            self.price_peaks[symbol] = current_price
        
        peak_price = self.price_peaks.get(symbol, current_price)
        drawdown_from_peak = ((current_price - peak_price) / peak_price) * 100
        
        # Se subiu mais de 0.3% e agora caiu 0.15% do pico → VENDE
        profit_from_entry_to_peak = ((peak_price - entry_price) / entry_price) * 100
        if profit_from_entry_to_peak > 0.3 and drawdown_from_peak < -self.trailing_stop_pct:
            # Limpa o pico
            self.price_peaks.pop(symbol, None)
            return True, f"📉 TRAILING STOP (caiu {drawdown_from_peak:.2f}% do pico) +{profit_pct:.2f}%"
        
        # ===== 0.5. LUCRO MÍNIMO GARANTIDO (VENDE COM QUALQUER LUCRO) =====
        if profit_pct >= 0.1:  # Com apenas 0.1% de lucro já considera vender
            # Se RSI está subindo muito ou descendo, vende
            if rsi > 55 or (trend == 'QUEDA' and strength >= 2):
                self.price_peaks.pop(symbol, None)
                return True, f"💰 LUCRO RÁPIDO +{profit_pct:.2f}% (RSI: {rsi:.1f})"
        
        # ===== 1. STOP LOSS PROGRESSIVO =====
        # Stop mais apertado se ficar muito tempo sem lucro
        current_stop = self.stop_loss_pct  # -1.0%
        
        if minutes_open > 10 and profit_pct < 0.2:
            # Após 10min sem lucro → stop mais apertado
            current_stop = self.stop_loss_apertado  # -0.5%
        
        if minutes_open > 5 and profit_pct < -0.3:
            # Se estiver caindo rápido (já -0.3% em 5min) → vende logo
            current_stop = -0.5
        
        if profit_pct <= current_stop:
            # Limpa o pico
            self.price_peaks.pop(symbol, None)
            return True, f"🛑 STOP LOSS {profit_pct:.2f}% (limite: {current_stop}%)"
        
        # ===== 2. TAKE PROFIT MÁXIMO =====
        if profit_pct >= self.max_take_pct:
            self.price_peaks.pop(symbol, None)
            return True, f"💰 TAKE MAX +{profit_pct:.2f}%"
        
        # ===== 3. TEMPO + TENDÊNCIA (NÃO VENDE FORÇADO, SÓ SE TENDÊNCIA VIRAR) =====
        if position_time:
            # Detecta queda brusca (caiu mais de 0.3% nos últimos candles)
            if len(df) >= 3:
                price_3_candles_ago = df.iloc[-3]['close']
                queda_brusca = ((current_price - price_3_candles_ago) / price_3_candles_ago) * 100
            else:
                queda_brusca = 0
            
            # Após 3 minutos: vende se tendência não for mais ALTA ou queda brusca
            if minutes_open > 3 and profit_pct >= 0:
                if trend != 'ALTA':  # Tendência virou para LATERAL ou QUEDA
                    self.price_peaks.pop(symbol, None)
                    return True, f"⚡ TEND VIROU ({minutes_open:.0f}min) {trend} +{profit_pct:.2f}%"
                if queda_brusca < -0.3:  # Queda brusca de mais de 0.3%
                    self.price_peaks.pop(symbol, None)
                    return True, f"📉 QUEDA BRUSCA ({queda_brusca:.2f}%) +{profit_pct:.2f}%"
            
            # Após 5 minutos: mesma lógica, mas também vende se no prejuízo com tendência ruim
            if minutes_open > self.max_hold_minutes:
                if trend != 'ALTA':  # Tendência não é mais de alta
                    self.price_peaks.pop(symbol, None)
                    return True, f"⏰ TEMPO+TEND ({minutes_open:.0f}min) {trend} {profit_pct:+.2f}%"
                if queda_brusca < -0.3:  # Queda brusca
                    self.price_peaks.pop(symbol, None)
                    return True, f"⏰ TEMPO+QUEDA ({minutes_open:.0f}min) {queda_brusca:.2f}% {profit_pct:+.2f}%"
                # Se ainda está em ALTA após 5min, segura mais um pouco (até 8min máx)
                if minutes_open > 8:
                    self.price_peaks.pop(symbol, None)
                    return True, f"⏰ TEMPO MAX ({minutes_open:.0f}min) {profit_pct:+.2f}%"
        
        # ===== 4. RSI OVERBOUGHT =====
        if rsi > sell_rsi and profit_pct > 0.2:
            self.price_peaks.pop(symbol, None)
            return True, f"📈 RSI {rsi:.1f} > {sell_rsi} +{profit_pct:.2f}%"
        
        # ===== 5. MODO AGRESSIVO (POSIÇÕES CHEIAS) =====
        # Quando todas posições estão ocupadas, fica mais ansioso para vender
        # MAS NUNCA vende no prejuízo!
        if positions_full and profit_pct >= 0:  # Só se não estiver no vermelho!
            
            # RSI mais flexível (50+ em vez de 60+)
            aggressive_sell_rsi = 50
            
            if rsi > aggressive_sell_rsi:
                self.price_peaks.pop(symbol, None)
                return True, f"🚀 AGRESSIVO RSI {rsi:.1f} > {aggressive_sell_rsi} +{profit_pct:.2f}%"
            
            # Aceita vender em LATERAL com qualquer lucro
            if trend == 'LATERAL' and profit_pct > 0:
                self.price_peaks.pop(symbol, None)
                return True, f"🚀 AGRESSIVO LATERAL +{profit_pct:.2f}%"
            
            # Se estiver no lucro e com sinal de queda fraco (2+ sinais)
            if trend == 'QUEDA' and strength >= 2 and profit_pct > 0:
                self.price_peaks.pop(symbol, None)
                return True, f"🚀 AGRESSIVO QUEDA ({strength}/4) +{profit_pct:.2f}%"
        
        # ===== 6. REGRA PRINCIPAL: TENDÊNCIA VIROU QUEDA? =====
        if profit_pct > self.min_profit_to_hold:
            if trend == 'QUEDA' and strength >= 3:
                self.price_peaks.pop(symbol, None)
                return True, f"📉 QUEDA ({strength}/4): {' '.join(reasons)} +{profit_pct:.2f}%"
            elif trend == 'ALTA':
                # Tendência ainda ALTA → SEGURA!
                return False, f"📈 ALTA ({strength}/4) - Segurando +{profit_pct:.2f}%"
            else:
                # LATERAL com lucro bom → pode vender
                if profit_pct > 0.8:
                    self.price_peaks.pop(symbol, None)
                    return True, f"↔️ LATERAL +{profit_pct:.2f}%"
        
        # ===== 7. Ainda não tem lucro suficiente =====
        return False, f"⏳ Aguardando ({profit_pct:+.2f}%) - Tend: {trend}"
    
    
    def update_daily_stats(self, pnl: float):
        """Atualiza estatísticas diárias"""
        today = datetime.now().date()
        
        # Reset diário
        if self.daily_stats['last_reset'] != today:
            self.daily_stats = {
                'trades': 0,
                'profit': 0.0,
                'wins': 0,
                'losses': 0,
                'target': 100.0,
                'last_reset': today
            }
        
        self.daily_stats['trades'] += 1
        self.daily_stats['profit'] += pnl
        
        if pnl > 0:
            self.daily_stats['wins'] += 1
        else:
            self.daily_stats['losses'] += 1
        
        # Log progresso
        progress = (self.daily_stats['profit'] / self.daily_stats['target']) * 100
        win_rate = (self.daily_stats['wins'] / self.daily_stats['trades'] * 100) if self.daily_stats['trades'] > 0 else 0
        
        print(f"""
📊 PROGRESSO DO DIA:
   Trades: {self.daily_stats['trades']}
   Lucro: ${self.daily_stats['profit']:.2f} / ${self.daily_stats['target']:.2f} ({progress:.1f}%)
   Win Rate: {win_rate:.1f}%
""")
        
        if self.daily_stats['profit'] >= self.daily_stats['target']:
            print("🎉 META DIÁRIA ATINGIDA!")
    
    
    def get_status(self) -> dict:
        """Retorna status atual da estratégia"""
        return {
            'name': self.name,
            'profiles_loaded': len(self.profiles),
            'has_ta_library': HAS_TA,
            'daily_stats': self.daily_stats,
            'config': {
                'stop_loss': self.stop_loss_pct,
                'max_take': self.max_take_pct,
                'max_hold_minutes': self.max_hold_minutes
            }
        }
    
    
    # =====================================================
    # MÉTODOS DE COMPATIBILIDADE COM main.py
    # =====================================================
    
    def should_buy(self, symbol: str, df: pd.DataFrame, current_price: float) -> Tuple[bool, str]:
        """
        Verifica se deve comprar (wrapper para analyze)
        
        Args:
            symbol: Par de trading (ex: BTC/USDT)
            df: DataFrame com dados OHLCV
            current_price: Preço atual
            
        Returns:
            (should_buy: bool, reason: str)
        """
        signal, reason, indicators = self.analyze(df, symbol)
        
        if signal == 'BUY':
            return True, reason
        return False, reason
    
    
    def _is_trend_up(self, df: pd.DataFrame) -> bool:
        """
        Verifica se tendência é de alta
        Usado para decidir se deve segurar posição
        """
        trend, strength, _ = self.detect_trend(df)
        return trend == 'ALTA' and strength >= 2
    
    
    def _count_reversal_signals(self, df: pd.DataFrame) -> int:
        """
        Conta sinais de reversão (queda)
        Retorna número de sinais de queda (0-4)
        """
        trend, strength, _ = self.detect_trend(df)
        
        if trend == 'QUEDA':
            return strength
        return 0
    
    
    def update_trade_stats(self, symbol: str, pnl: float):
        """
        Atualiza estatísticas após fechar uma posição
        
        Args:
            symbol: Par de trading
            pnl: Lucro/Prejuízo da operação em USD
        """
        # Atualiza tempo do último trade
        self.last_trade_time[symbol] = datetime.now()
        
        # Atualiza estatísticas diárias
        self.update_daily_stats(pnl)
    
    
    def get_daily_progress(self) -> dict:
        """Retorna progresso do dia em formato legível"""
        stats = self.daily_stats
        progress = (stats['profit'] / stats['target']) * 100 if stats['target'] > 0 else 0
        win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
        
        return {
            'trades': stats['trades'],
            'profit': stats['profit'],
            'target': stats['target'],
            'progress_pct': progress,
            'win_rate': win_rate,
            'target_reached': stats['profit'] >= stats['target']
        }


# Função para integração com trading_engine.py
def get_strategy(strategy_type: str = 'smart', config: dict = None):
    """Factory function para criar estratégia"""
    return SmartStrategy(config)
