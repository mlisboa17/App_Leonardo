"""
🧠 Smart Strategy - Estratégia Inteligente com Perfis por Moeda
Meta: $100/dia comprando barato e vendendo quando tendência virar

Características:
- RSI adaptativo por moeda (baseado em histórico)
- RSI que ENCURTA ao longo do dia (mais agressivo)
- Configurações ESPECÍFICAS por cripto (volatilidade)
- Segura enquanto tendência for de ALTA
- Vende apenas quando tendência VIRAR para QUEDA
"""

import json
import os
import logging
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
        
        # Logger
        self.logger = logging.getLogger('SmartStrategy')
        
        # =====================================================
        # CONFIGURAÇÕES DO BOT (do YAML)
        # Cada bot pode ter configs diferentes!
        # =====================================================
        self.bot_type = self.config.get('bot_type', 'unknown')
        self.bot_rsi_config = self.config.get('rsi', {})
        self.bot_risk_config = self.config.get('risk', {})
        
        # Carrega perfis das moedas
        self.profiles = self._load_crypto_profiles()
        
        # Estado de cada moeda
        self.last_trade_time: Dict[str, datetime] = {}
        self.positions_open_time: Dict[str, datetime] = {}
        
        # =====================================================
        # CONFIGURAÇÕES ESPECÍFICAS POR CRIPTO
        # Baseadas em: ESTUDO_CLASSIFICACAO_CRYPTO.md
        # CoinMarketCap volatility data + TradingView analysis
        # =====================================================
        self.crypto_configs = {
            # === CATEGORIA: ESTÁVEL (vol 1-3%) ===
            # BTC - Líder do mercado, $1.77T cap, baixa volatilidade
            'BTCUSDT': {
                'stop_loss': -0.5,
                'take_profit': 0.3,
                'max_hold_min': 240,
                'rsi_buy': 40,
                'rsi_sell': 60,
                'rsi_urgency_factor': 0.8,
                'min_profit': 0.10,
                'category': 'stable',
            },
            # ETH - Smart contracts base, correlação 0.85+ c/ BTC
            'ETHUSDT': {
                'stop_loss': -0.5,
                'take_profit': 0.3,
                'max_hold_min': 240,
                'rsi_buy': 40,
                'rsi_sell': 60,
                'rsi_urgency_factor': 0.8,
                'min_profit': 0.10,
                'category': 'stable',
            },
            # LTC - Digital silver, correlação 0.80+ c/ BTC
            'LTCUSDT': {
                'stop_loss': -0.5,
                'take_profit': 0.3,
                'max_hold_min': 240,
                'rsi_buy': 38,
                'rsi_sell': 62,
                'rsi_urgency_factor': 0.9,
                'min_profit': 0.10,
                'category': 'stable',
            },
            # UNI - DeFi líder, Uniswap
            'UNIUSDT': {
                'stop_loss': -0.5,
                'take_profit': 0.35,
                'max_hold_min': 240,
                'rsi_buy': 38,
                'rsi_sell': 62,
                'rsi_urgency_factor': 0.9,
                'min_profit': 0.10,
                'category': 'stable',
            },
            # AAVE - DeFi lending
            'AAVEUSDT': {
                'stop_loss': -0.5,
                'take_profit': 0.35,
                'max_hold_min': 240,
                'rsi_buy': 38,
                'rsi_sell': 62,
                'rsi_urgency_factor': 0.9,
                'min_profit': 0.10,
                'category': 'stable',
            },
            # MKR - Maker governance
            'MKRUSDT': {
                'stop_loss': -0.6,
                'take_profit': 0.4,
                'max_hold_min': 240,
                'rsi_buy': 38,
                'rsi_sell': 62,
                'rsi_urgency_factor': 0.9,
                'min_profit': 0.12,
                'category': 'stable',
            },
            
            # === CATEGORIA: MÉDIO (vol 3-5%) ===
            # SOL - Layer 1 rápida, ecossistema crescente
            'SOLUSDT': {
                'stop_loss': -1.0,
                'take_profit': 0.7,
                'max_hold_min': 180,
                'rsi_buy': 35,
                'rsi_sell': 65,
                'rsi_urgency_factor': 1.0,
                'min_profit': 0.20,
                'category': 'medium',
            },
            # BNB - Exchange token, utilidade forte
            'BNBUSDT': {
                'stop_loss': -1.0,
                'take_profit': 0.7,
                'max_hold_min': 180,
                'rsi_buy': 35,
                'rsi_sell': 65,
                'rsi_urgency_factor': 1.0,
                'min_profit': 0.20,
                'category': 'medium',
            },
            # LINK - Oracle DeFi fundamental
            'LINKUSDT': {
                'stop_loss': -1.0,
                'take_profit': 0.7,
                'max_hold_min': 180,
                'rsi_buy': 35,
                'rsi_sell': 65,
                'rsi_urgency_factor': 1.0,
                'min_profit': 0.20,
                'category': 'medium',
            },
            # ATOM - Cosmos, interoperabilidade
            'ATOMUSDT': {
                'stop_loss': -1.0,
                'take_profit': 0.7,
                'max_hold_min': 180,
                'rsi_buy': 34,
                'rsi_sell': 66,
                'rsi_urgency_factor': 1.0,
                'min_profit': 0.20,
                'category': 'medium',
            },
            # AVAX - Avalanche, Layer 1
            'AVAXUSDT': {
                'stop_loss': -1.0,
                'take_profit': 0.75,
                'max_hold_min': 180,
                'rsi_buy': 34,
                'rsi_sell': 66,
                'rsi_urgency_factor': 1.0,
                'min_profit': 0.20,
                'category': 'medium',
            },
            # DOT - Polkadot, parachains
            'DOTUSDT': {
                'stop_loss': -1.0,
                'take_profit': 0.7,
                'max_hold_min': 180,
                'rsi_buy': 34,
                'rsi_sell': 66,
                'rsi_urgency_factor': 1.0,
                'min_profit': 0.20,
                'category': 'medium',
            },
            # NEAR - Near Protocol
            'NEARUSDT': {
                'stop_loss': -1.0,
                'take_profit': 0.75,
                'max_hold_min': 180,
                'rsi_buy': 33,
                'rsi_sell': 67,
                'rsi_urgency_factor': 1.1,
                'min_profit': 0.22,
                'category': 'medium',
            },
            
            # === CATEGORIA: VOLÁTIL (vol 5-8%) ===
            # XRP - Pagamentos, notícias legais causam pumps
            'XRPUSDT': {
                'stop_loss': -1.2,
                'take_profit': 1.0,
                'max_hold_min': 120,
                'rsi_buy': 30,
                'rsi_sell': 70,
                'rsi_urgency_factor': 1.3,
                'min_profit': 0.25,
                'category': 'volatile',
            },
            # TRX - DApp ecosystem, movimentos bruscos
            'TRXUSDT': {
                'stop_loss': -1.2,
                'take_profit': 1.0,
                'max_hold_min': 120,
                'rsi_buy': 30,
                'rsi_sell': 70,
                'rsi_urgency_factor': 1.3,
                'min_profit': 0.25,
                'category': 'volatile',
            },
            # XLM - Stellar, pagamentos
            'XLMUSDT': {
                'stop_loss': -1.2,
                'take_profit': 1.0,
                'max_hold_min': 120,
                'rsi_buy': 30,
                'rsi_sell': 70,
                'rsi_urgency_factor': 1.3,
                'min_profit': 0.25,
                'category': 'volatile',
            },
            # FTM - Fantom, DeFi rápido
            'FTMUSDT': {
                'stop_loss': -1.3,
                'take_profit': 1.1,
                'max_hold_min': 120,
                'rsi_buy': 28,
                'rsi_sell': 72,
                'rsi_urgency_factor': 1.4,
                'min_profit': 0.28,
                'category': 'volatile',
            },
            # SAND - Sandbox, metaverso
            'SANDUSDT': {
                'stop_loss': -1.3,
                'take_profit': 1.2,
                'max_hold_min': 100,
                'rsi_buy': 28,
                'rsi_sell': 72,
                'rsi_urgency_factor': 1.4,
                'min_profit': 0.30,
                'category': 'volatile',
            },
            # MANA - Decentraland
            'MANAUSDT': {
                'stop_loss': -1.3,
                'take_profit': 1.2,
                'max_hold_min': 100,
                'rsi_buy': 28,
                'rsi_sell': 72,
                'rsi_urgency_factor': 1.4,
                'min_profit': 0.30,
                'category': 'volatile',
            },
            # GALA - Gaming
            'GALAUSDT': {
                'stop_loss': -1.4,
                'take_profit': 1.2,
                'max_hold_min': 90,
                'rsi_buy': 27,
                'rsi_sell': 73,
                'rsi_urgency_factor': 1.5,
                'min_profit': 0.32,
                'category': 'volatile',
            },
            # APE - ApeCoin, NFT/Gaming
            'APEUSDT': {
                'stop_loss': -1.4,
                'take_profit': 1.3,
                'max_hold_min': 90,
                'rsi_buy': 27,
                'rsi_sell': 73,
                'rsi_urgency_factor': 1.5,
                'min_profit': 0.32,
                'category': 'volatile',
            },
            
            # === CATEGORIA: MEME (vol 8%+) ===
            # DOGE - Original meme, Elon effect, $25B cap
            'DOGEUSDT': {
                'stop_loss': -1.5,
                'take_profit': 1.5,
                'max_hold_min': 60,
                'rsi_buy': 25,
                'rsi_sell': 75,
                'rsi_urgency_factor': 1.8,
                'min_profit': 0.40,
                'category': 'meme',
            },
            # SHIB - Shiba Inu
            'SHIBUSDT': {
                'stop_loss': -1.5,
                'take_profit': 1.5,
                'max_hold_min': 60,
                'rsi_buy': 25,
                'rsi_sell': 75,
                'rsi_urgency_factor': 1.8,
                'min_profit': 0.40,
                'category': 'meme',
            },
            # PEPE - Nova geração meme
            'PEPEUSDT': {
                'stop_loss': -1.6,
                'take_profit': 1.8,
                'max_hold_min': 45,
                'rsi_buy': 23,
                'rsi_sell': 77,
                'rsi_urgency_factor': 2.0,
                'min_profit': 0.50,
                'category': 'meme',
            },
            # FLOKI - Meme Viking
            'FLOKIUSDT': {
                'stop_loss': -1.6,
                'take_profit': 1.8,
                'max_hold_min': 45,
                'rsi_buy': 23,
                'rsi_sell': 77,
                'rsi_urgency_factor': 2.0,
                'min_profit': 0.50,
                'category': 'meme',
            },
            # BONK - Meme Solana
            'BONKUSDT': {
                'stop_loss': -1.7,
                'take_profit': 2.0,
                'max_hold_min': 40,
                'rsi_buy': 22,
                'rsi_sell': 78,
                'rsi_urgency_factor': 2.2,
                'min_profit': 0.55,
                'category': 'meme',
            },
        }
        
        # Configuração padrão para moedas não listadas
        self.default_config = {
            'stop_loss': -0.6,
            'take_profit': 0.4,
            'max_hold_min': 6,
            'rsi_urgency_factor': 1.3,
            'min_profit': 0.10,
        }
        
        # Configurações globais - MAIS AGRESSIVO
        self.stop_loss_pct = -0.6  # -0.6% stop loss base
        self.stop_loss_apertado = -0.3  # -0.3% se ficar muito tempo
        self.max_take_pct = 2.0    # +2% máximo
        self.max_hold_minutes = 5  # Máx 5 min base
        self.min_profit_to_hold = 0.05  # Mín 0.05% para vender
        self.trailing_stop_pct = 0.15  # Trailing stop 0.15%
        
        # Controle de picos de preço
        self.price_peaks: Dict[str, float] = {}
        
        # Estatísticas do dia
        self.daily_stats = {
            'trades': 0,
            'profit': 0.0,
            'wins': 0,
            'losses': 0,
            'target': 100.0,
            'last_reset': datetime.now().date()
        }
        
        # Hora de início do dia (para calcular urgência)
        self.day_start = datetime.now().replace(hour=0, minute=0, second=0)
        
        print(f"✅ {self.name} inicializada [{self.bot_type}]")
        print(f"   Biblioteca TA: {'SIM' if HAS_TA else 'NÃO'}")
        print(f"   Moedas com perfil: {len(self.profiles)}")
        print(f"   📊 Configs específicas: {len(self.crypto_configs)} moedas")
        if self.bot_risk_config:
            print(f"   ⚙️ Risk do Bot: SL={self.bot_risk_config.get('stop_loss')}% TP={self.bot_risk_config.get('take_profit')}%")
    
    
    def get_crypto_config(self, symbol: str) -> dict:
        """
        Retorna configuração específica da cripto.
        PRIORIDADE:
        1. Configuração do BOT (do YAML) - se existir
        2. Configuração específica da crypto
        3. Configuração default
        """
        key = symbol.replace('/', '')
        crypto_config = self.crypto_configs.get(key, self.default_config).copy()
        
        # SOBRESCREVE com configurações do bot (se existirem)
        if self.bot_risk_config:
            if 'stop_loss' in self.bot_risk_config:
                crypto_config['stop_loss'] = self.bot_risk_config['stop_loss']
            if 'take_profit' in self.bot_risk_config:
                crypto_config['take_profit'] = self.bot_risk_config['take_profit']
            if 'max_hold_minutes' in self.bot_risk_config:
                crypto_config['max_hold_min'] = self.bot_risk_config['max_hold_minutes']
            if 'min_profit' in self.bot_risk_config:
                crypto_config['min_profit'] = self.bot_risk_config['min_profit']
            if 'trailing_stop' in self.bot_risk_config:
                crypto_config['trailing_stop'] = self.bot_risk_config['trailing_stop']
        
        if self.bot_rsi_config:
            if 'oversold' in self.bot_rsi_config:
                crypto_config['rsi_buy'] = self.bot_rsi_config['oversold']
            if 'overbought' in self.bot_rsi_config:
                crypto_config['rsi_sell'] = self.bot_rsi_config['overbought']
            if 'urgency_factor' in self.bot_rsi_config:
                crypto_config['rsi_urgency_factor'] = self.bot_rsi_config['urgency_factor']
        
        return crypto_config
    
    
    def get_day_urgency_factor(self) -> float:
        """
        Calcula fator de urgência baseado na hora do dia
        
        Início do dia (00:00-08:00): Fator 1.0 (normal)
        Meio do dia (08:00-16:00): Fator 1.3 (mais agressivo)
        Final do dia (16:00-20:00): Fator 1.6 (bem agressivo)
        Noite (20:00-24:00): Fator 2.0 (máxima urgência)
        """
        hour = datetime.now().hour
        
        if hour < 8:
            return 1.0
        elif hour < 12:
            return 1.2
        elif hour < 16:
            return 1.4
        elif hour < 20:
            return 1.7
        else:
            return 2.0
    
    
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
        Retorna RSI de compra ajustado com base em:
        1. Configuração específica da crypto (rsi_buy do estudo)
        2. Tempo sem trades (urgência por inatividade)
        3. Hora do dia (urgência temporal - mais agressivo à noite)
        4. Fator de urgência da crypto (volatilidade)
        """
        profile = self.get_profile(symbol)
        crypto_config = self.get_crypto_config(symbol)
        
        # ===== NOVO: Usa rsi_buy do estudo se disponível =====
        # Cada crypto tem RSI específico baseado em sua volatilidade
        base_rsi = crypto_config.get('rsi_buy', profile.get('buy_rsi', 38))
        mean_rsi = profile.get('rsi_mean', 50)
        
        # Fator de urgência específico da crypto (0.8 estável a 1.8 meme)
        crypto_urgency = crypto_config.get('rsi_urgency_factor', 1.0)
        
        # Fator de urgência do dia (1.0 manhã -> 2.0 noite)
        day_urgency = self.get_day_urgency_factor()
        
        # Quanto tempo sem trade nessa moeda?
        last_time = self.last_trade_time.get(symbol)
        
        if not last_time:
            minutes_idle = 999
        else:
            minutes_idle = (datetime.now() - last_time).total_seconds() / 60
        
        # Ajuste base por tempo parado
        idle_adjustment = 0
        if minutes_idle > 5:
            idle_adjustment = 1
        if minutes_idle > 10:
            idle_adjustment = 2
        if minutes_idle > 15:
            idle_adjustment = 3
        if minutes_idle > 20:
            idle_adjustment = 4
        if minutes_idle > 30:
            idle_adjustment = 5
        if minutes_idle > 45:
            idle_adjustment = 6
        
        # ===== Aplica multiplicadores de urgência =====
        # Cryptos estáveis: relaxa pouco (urgency 0.8)
        # Cryptos voláteis: relaxa mais (urgency 1.3-1.8)
        total_adjustment = idle_adjustment * day_urgency * crypto_urgency
        
        # RSI ajustado
        adjusted_rsi = base_rsi + total_adjustment
        
        # Limite máximo baseado na categoria da crypto
        # Estáveis: max mais conservador
        # Memes: max mais agressivo
        category = crypto_config.get('category', 'medium')
        category_max_bonus = {
            'stable': 5,    # Conservador
            'medium': 10,   # Balanceado
            'volatile': 15, # Agressivo
            'meme': 20      # Muito agressivo
        }
        
        base_max = mean_rsi - 5
        urgency_bonus = (day_urgency - 1.0) * category_max_bonus.get(category, 10) * crypto_urgency
        max_allowed = base_max + urgency_bonus
        
        # Log para debug
        self.logger.debug(f"[{symbol}] RSI Compra: base={base_rsi} ({category}), adj={adjusted_rsi:.1f}, "
                         f"day_urg={day_urgency:.1f}, crypto_urg={crypto_urgency}, max={max_allowed:.1f}")
        
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
                    positions_full: bool = False,
                    position_size: float = None) -> Tuple[bool, str]:
        """
        Decide se deve vender a posição
        
        🏪 ESTRATÉGIA DE FEIRA (NOVO!):
        - Com o tempo, o Take Profit DIMINUI (feirante baixando preço)
        - Só vende quando tendência SAI de ALTA para LATERAL/QUEDA
        - Cryptos diferentes têm fatores diferentes:
          * BTC/ETH: HOLD (fator 0.3) - blue chips, segura mais
          * DOGE/SHIB: FEIRA AGRESSIVA (fator 0.9) - vende rápido
          * LINK/SOL: FEIRA MODERADA (fator 0.5-0.7)
        
        💰 REGRA DOS 2 USDT (NOVO!):
        - Se lucro > 2 USDT e tendência ALTA → SEGURA
        - Se lucro > 2 USDT e tendência LATERAL/QUEDA → VENDE
        
        PROTEÇÃO DE CAPITAL:
        - Nunca vende no prejuízo (a menos que atinja stop loss)
        - Stop loss protege contra quedas bruscas
        - Trailing stop protege lucro já conquistado
        """
        
        # Calcula lucro/prejuízo
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Calcula lucro em USDT (se position_size fornecido)
        profit_usdt = 0
        if position_size:
            profit_usdt = position_size * (profit_pct / 100)
        
        profile = self.get_profile(symbol)
        crypto_config = self.get_crypto_config(symbol)
        
        # ===== ESTRATÉGIA DE FEIRA - FATOR POR CRYPTO =====
        # Carrega config da feira se existir
        feira_factors = {
            'BTCUSDT': 0.3, 'ETHUSDT': 0.3,  # Blue chips - HOLD
            'BNBUSDT': 0.4, 'LTCUSDT': 0.7,  # Médio
            'SOLUSDT': 0.5, 'XRPUSDT': 0.5,  # Voláteis - FEIRA MODERADA
            'LINKUSDT': 0.7, 'AVAXUSDT': 0.6,  # Alta vol + baixo volume
            'DOTUSDT': 0.6, 'NEARUSDT': 0.6, 'ADAUSDT': 0.5, 'TRXUSDT': 0.5,
            'DOGEUSDT': 0.9, 'SHIBUSDT': 0.9, 'PEPEUSDT': 0.9,  # Memes - FEIRA AGRESSIVA
            'UNIUSDT': 0.5, 'AAVEUSDT': 0.5,
        }
        feira_factor = feira_factors.get(symbol, 0.5)
        
        # ===== PARÂMETROS ESPECÍFICOS DA CRYPTO (baseado no estudo) =====
        # Cada categoria tem configs diferentes:
        # - Estáveis (BTC, ETH): stops apertados, takes pequenos, hold longo
        # - Médios (SOL, BNB): stops/takes médios
        # - Voláteis (XRP, TRX): stops/takes largos, hold curto
        # - Memes (DOGE): stops/takes muito largos, hold muito curto
        crypto_stop_loss = crypto_config.get('stop_loss', -1.0)
        crypto_take_profit = crypto_config.get('take_profit', 0.5)
        crypto_max_hold = crypto_config.get('max_hold_min', 120)
        crypto_min_profit = crypto_config.get('min_profit', 0.15)
        crypto_rsi_sell = crypto_config.get('rsi_sell', profile.get('sell_rsi', 65))
        crypto_category = crypto_config.get('category', 'medium')
        
        sell_rsi = crypto_rsi_sell  # Usa RSI de venda específico da crypto
        
        # Calcula indicadores
        df = self.calculate_indicators(df)
        current = df.iloc[-1]
        rsi = current.get('rsi', 50)
        
        # Detecta tendência
        trend, strength, reasons = self.detect_trend(df)
        
        # ===== 💰 REGRA DOS 2 USDT - HOLD EM ALTA, VENDE EM NEUTRO/BAIXA =====
        # Se lucro > 2 USDT: só vende quando tendência sair de ALTA
        MIN_PROFIT_USDT_HOLD = 2.0  # Lucro mínimo em USDT para aplicar regra
        
        if profit_usdt >= MIN_PROFIT_USDT_HOLD:
            if trend == 'ALTA':
                # Tendência de ALTA → SEGURA para maximizar lucro
                self.logger.info(f"💰 [{symbol}] Lucro ${profit_usdt:.2f} com tendência ALTA - SEGURANDO!")
                return False, f"💰 HOLD ALTA: ${profit_usdt:.2f} lucro ({strength}/4 sinais alta) - Segurando!"
            else:
                # Tendência LATERAL ou QUEDA → VENDE para garantir lucro
                self.price_peaks.pop(symbol, None)
                self.logger.info(f"💰 [{symbol}] Lucro ${profit_usdt:.2f} com tendência {trend} - VENDENDO!")
                return True, f"💰 VENDA {trend}: ${profit_usdt:.2f} lucro (+{profit_pct:.2f}%) - Tendência virou!"
        
        # Tempo da posição aberta
        minutes_open = 0
        if position_time:
            minutes_open = (datetime.now() - position_time).total_seconds() / 60
        
        # Urgência do dia (mais agressivo à noite)
        day_urgency = self.get_day_urgency_factor()
        
        # ===== 0. TRAILING STOP (PROTEGE LUCRO) =====
        # Atualiza pico de preço
        if symbol not in self.price_peaks:
            self.price_peaks[symbol] = current_price
        elif current_price > self.price_peaks[symbol]:
            self.price_peaks[symbol] = current_price
        
        peak_price = self.price_peaks.get(symbol, current_price)
        drawdown_from_peak = ((current_price - peak_price) / peak_price) * 100
        
        # Se subiu mais que take_profit e agora caiu 0.15% do pico → VENDE
        profit_from_entry_to_peak = ((peak_price - entry_price) / entry_price) * 100
        trailing_trigger = crypto_take_profit * 0.6  # 60% do take profit
        if profit_from_entry_to_peak > trailing_trigger and drawdown_from_peak < -self.trailing_stop_pct:
            # Limpa o pico
            self.price_peaks.pop(symbol, None)
            return True, f"📉 TRAILING STOP (caiu {drawdown_from_peak:.2f}% do pico) +{profit_pct:.2f}%"
        
        # ===== 0.5. LUCRO MÍNIMO GARANTIDO (ESPECÍFICO POR CRYPTO) =====
        if profit_pct >= crypto_min_profit:
            # Se RSI está subindo muito ou descendo, vende
            if rsi > 55 or (trend == 'QUEDA' and strength >= 2):
                self.price_peaks.pop(symbol, None)
                return True, f"💰 LUCRO RÁPIDO +{profit_pct:.2f}% (min: {crypto_min_profit}%)"
        
        # ===== 1. STOP LOSS ESPECÍFICO POR CRYPTO =====
        current_stop = crypto_stop_loss
        
        # Stop mais apertado se ficar muito tempo sem lucro
        if minutes_open > crypto_max_hold and profit_pct < 0.2:
            current_stop = crypto_stop_loss * 0.5
        
        if minutes_open > crypto_max_hold * 0.5 and profit_pct < -0.3:
            current_stop = max(crypto_stop_loss * 0.5, -0.5)
        
        if profit_pct <= current_stop:
            self.price_peaks.pop(symbol, None)
            return True, f"🛑 STOP LOSS {profit_pct:.2f}% (limite: {current_stop:.2f}%)"
        
        # ===== 2. 🏪 TAKE PROFIT DINÂMICO (ESTRATÉGIA FEIRA) =====
        # Com o tempo, o TP DIMINUI (feirante baixando preço)
        time_factor = min(1.0, minutes_open / crypto_max_hold)
        tp_reduction = time_factor * feira_factor  # Quanto reduzir (0 a feira_factor)
        tp_dinamico = crypto_take_profit * (1 - tp_reduction * 0.7)  # Reduz até 70% do TP
        tp_dinamico = max(tp_dinamico, 0.2)  # Mínimo 0.2%
        
        # REGRA DA FEIRA: Só vende quando tendência SAI de ALTA
        pode_vender_feira = False
        
        if trend == 'ALTA':
            # Em ALTA: SEGURA! (a menos que tempo muito longo)
            if time_factor > 0.9:  # Mais de 90% do tempo max
                pode_vender_feira = True
                motivo_feira = f"⏰ Tempo longo ({minutes_open:.0f}m) - liberando capital"
            else:
                pode_vender_feira = False
                motivo_feira = f"📈 ALTA - segurando (TP feira: {tp_dinamico:.2f}%)"
        elif trend == 'LATERAL':
            # LATERAL: Pode vender no TP dinâmico
            pode_vender_feira = True
            motivo_feira = f"➖ LATERAL - TP feira: {tp_dinamico:.2f}%"
        else:  # QUEDA
            # QUEDA: Vende mais rápido ainda
            pode_vender_feira = True
            tp_dinamico = max(0.1, tp_dinamico * 0.5)  # Reduz mais
            motivo_feira = f"📉 QUEDA - vendendo rápido (TP: {tp_dinamico:.2f}%)"
        
        # Verifica se atingiu TP dinâmico E pode vender
        if profit_pct >= tp_dinamico and pode_vender_feira:
            self.price_peaks.pop(symbol, None)
            return True, f"🏪 FEIRA {motivo_feira} +{profit_pct:.2f}%"
        
        # Se não pode vender (em ALTA), mostra status
        if profit_pct >= tp_dinamico and not pode_vender_feira:
            # Logga que está segurando
            pass  # Continua segurando
        
        # ===== 3. TEMPO + TENDÊNCIA (ESPECÍFICO POR CRYPTO) =====
        if position_time:
            # Detecta queda brusca (caiu mais de 0.3% nos últimos candles)
            if len(df) >= 3:
                price_3_candles_ago = df.iloc[-3]['close']
                queda_brusca = ((current_price - price_3_candles_ago) / price_3_candles_ago) * 100
            else:
                queda_brusca = 0
            
            # Tempo de hold ajustado pela urgência do dia (mais curto à noite)
            adjusted_max_hold = crypto_max_hold / day_urgency
            
            # Após 60% do tempo max: vende se tendência não for mais ALTA ou queda brusca
            if minutes_open > adjusted_max_hold * 0.6 and profit_pct >= 0:
                if trend != 'ALTA':  # Tendência virou para LATERAL ou QUEDA
                    self.price_peaks.pop(symbol, None)
                    return True, f"⚡ TEND VIROU ({minutes_open:.0f}min) {trend} +{profit_pct:.2f}%"
                if queda_brusca < -0.3:  # Queda brusca de mais de 0.3%
                    self.price_peaks.pop(symbol, None)
                    return True, f"📉 QUEDA BRUSCA ({queda_brusca:.2f}%) +{profit_pct:.2f}%"
            
            # Após tempo max: mesma lógica, mas também vende se no prejuízo com tendência ruim
            if minutes_open > adjusted_max_hold:
                if trend != 'ALTA':  # Tendência não é mais de alta
                    self.price_peaks.pop(symbol, None)
                    return True, f"⏰ TEMPO+TEND ({minutes_open:.0f}min/{adjusted_max_hold:.0f}max) {trend} {profit_pct:+.2f}%"
                if queda_brusca < -0.3:  # Queda brusca
                    self.price_peaks.pop(symbol, None)
                    return True, f"⏰ TEMPO+QUEDA ({minutes_open:.0f}min) {queda_brusca:.2f}% {profit_pct:+.2f}%"
                # Se ainda está em ALTA após max_hold, segura mais 60% do tempo
                if minutes_open > adjusted_max_hold * 1.6:
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
