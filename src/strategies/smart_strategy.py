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
import time
import random

# Biblioteca de Análise Técnica (profissional)
try:
    import ta
    HAS_TA = True
except ImportError:
    HAS_TA = False

# Mensagem de prioridade operacional (Preservação de Capital)
CAPITAL_PRESERVATION_MESSAGE = (
    "Sua prioridade agora é a Preservação de Capital. "
    "Não execute ordens se os indicadores de tendência (EMA_200) e volume "
    "não estiverem confirmados, mesmo que o RSI indique sobrevenda. "
    "O objetivo é um crescimento constante de volume com baixo risco."
)


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
        # Histórico de trades por símbolo (timestamps) para ajustes dinâmicos de RSI
        self.trade_events: Dict[str, list] = {}
        # Janela para contar trades (em segundos) - usamos 24h
        self.trade_count_window_sec = 24 * 3600
        
        # =====================================================
        # CONFIGURAÇÕES ESPECÍFICAS POR CRIPTO
        # Baseadas em: ESTUDO_CLASSIFICACAO_CRYPTO.md
        # CoinMarketCap volatility data + TradingView analysis
        # =====================================================
        self.crypto_configs = {
            # === CATEGORIA: ESTÁVEL (vol 1-3%) ===
            # BTC - Líder do mercado, $1.77T cap, baixa volatilidade
            'BTCUSDT': {
                'stop_loss': -0.45,
                'take_profit': 0.8,
                'max_hold_min': 150,
                'rsi_buy': 44,
                'rsi_sell': 63,
                'rsi_urgency_factor': 0.8,
                'min_profit': 0.10,
                'category': 'stable',
                'allow_below_sma': False,
                'trailing': {
                    'activate_at_profit_pct': 0.5,
                    'retrace_pct': 0.15
                }
            },
            # ETH - Smart contracts base, correlação 0.85+ c/ BTC
            'ETHUSDT': {
                'stop_loss': -0.45,
                'take_profit': 0.8,
                'max_hold_min': 150,
                'rsi_buy': 44,
                'rsi_sell': 63,
                'rsi_urgency_factor': 0.8,
                'min_profit': 0.10,
                'category': 'stable',
                'allow_below_sma': False,
                'trailing': {
                    'activate_at_profit_pct': 0.5,
                    'retrace_pct': 0.15
                }
            },
            # LTC - Digital silver, correlação 0.80+ c/ BTC
            'LTCUSDT': {
                'stop_loss': -0.5,
                'take_profit': 0.6,
                'max_hold_min': 120,
                'rsi_buy': 38,
                'rsi_sell': 62,
                'rsi_urgency_factor': 0.9,
                'min_profit': 0.10,
                'category': 'stable',
            },
            # UNI - DeFi líder, Uniswap
            'UNIUSDT': {
                'stop_loss': -0.5,
                'take_profit': 0.6,
                'max_hold_min': 120,
                'rsi_buy': 38,
                'rsi_sell': 62,
                'rsi_urgency_factor': 0.9,
                'min_profit': 0.10,
                'category': 'stable',
            },
            # AAVE - DeFi lending
            'AAVEUSDT': {
                'stop_loss': -0.5,
                'take_profit': 0.6,
                'max_hold_min': 120,
                'rsi_buy': 38,
                'rsi_sell': 62,
                'rsi_urgency_factor': 0.9,
                'min_profit': 0.10,
                'category': 'stable',
            },
            # MKR - Maker governance
            'MKRUSDT': {
                'stop_loss': -0.6,
                'take_profit': 0.6,
                'max_hold_min': 150,
                'rsi_buy': 38,
                'rsi_sell': 62,
                'rsi_urgency_factor': 0.9,
                'min_profit': 0.12,
                'category': 'stable',
            },
            
            # === CATEGORIA: MÉDIO (vol 3-5%) ===
            # SOL - Layer 1 rápida, ecossistema crescente
            'SOLUSDT': {
                'stop_loss': -0.9,
                'take_profit': 1.1,
                'max_hold_min': 120,
                'rsi_buy': 36,
                'rsi_sell': 65,
                'rsi_urgency_factor': 1.0,
                'min_profit': 0.20,
                'category': 'medium',
            },
            # BNB - Exchange token, utilidade forte
            'BNBUSDT': {
                'stop_loss': -1.0,
                'take_profit': 1.0,
                'max_hold_min': 120,
                'rsi_buy': 36,
                'rsi_sell': 65,
                'rsi_urgency_factor': 1.0,
                'min_profit': 0.20,
                'category': 'medium',
            },
            # LINK - Oracle DeFi fundamental
            'LINKUSDT': {
                'stop_loss': -0.9,
                'take_profit': 1.0,
                'max_hold_min': 120,
                'rsi_buy': 36,
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
                'take_profit': 1.1,
                'max_hold_min': 100,
                'rsi_buy': 36,
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
                'take_profit': 1.5,
                'max_hold_min': 100,
                'rsi_buy': 33,
                'rsi_sell': 70,
                'rsi_urgency_factor': 1.3,
                'min_profit': 0.25,
                'category': 'volatile',
            },
            # TRX - DApp ecosystem, movimentos bruscos
            'TRXUSDT': {
                'stop_loss': -1.2,
                'take_profit': 1.5,
                'max_hold_min': 100,
                'rsi_buy': 33,
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
                'stop_loss': -1.3,
                'take_profit': 2.0,
                'max_hold_min': 40,
                'rsi_buy': 26,
                'rsi_sell': 75,
                'rsi_urgency_factor': 1.8,
                'min_profit': 0.40,
                'category': 'meme',
            },
            # SHIB - Shiba Inu
            'SHIBUSDT': {
                'stop_loss': -1.3,
                'take_profit': 2.0,
                'max_hold_min': 40,
                'rsi_buy': 26,
                'rsi_sell': 75,
                'rsi_urgency_factor': 1.8,
                'min_profit': 0.40,
                'category': 'meme',
            },
            # PEPE - Nova geração meme
            'PEPEUSDT': {
                'stop_loss': -1.3,
                'take_profit': 2.0,
                'max_hold_min': 40,
                'rsi_buy': 26,
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
        self.trailing_stop_pct = 2.0  # Trailing stop default 2.0% (wider to avoid early cuts)
        # Trailing retrace for winner logic (Protocol update): use 0.15% drawdown from peak
        self.trailing_retrace_pct = 0.15

        # Minimum hold time before considering optimized exit (minutes)
        self.min_hold_minutes = 15  # default min hold (minutes) to avoid quick sells

        # ===== Sobrescreve com configurações do bot (se fornecidas) =====
        # Permite ajustar agressividade via `bot_risk_config` do YAML
        try:
            br = self.bot_risk_config or {}
            # mapear chaves comuns do YAML para atributos internos
            if 'max_hold_minutes' in br:
                self.max_hold_minutes = int(br.get('max_hold_minutes'))
            if 'min_profit' in br:
                # min_profit no YAML é percentual (ex: 0.5 significa 0.5%)
                self.min_profit_to_hold = float(br.get('min_profit'))
            if 'trailing_stop' in br:
                self.trailing_stop_pct = float(br.get('trailing_stop'))
            if 'take_profit' in br:
                self.max_take_pct = float(br.get('take_profit'))
            # Allow automatic override of SMA200 per-bot
            self.allow_below_sma_global = bool(br.get('allow_below_sma_global', False))
            if 'min_hold_minutes' in br:
                self.min_hold_minutes = int(br.get('min_hold_minutes'))
        except Exception:
            # Não falha a inicialização por problema no parsing
            self.logger.debug('Nenhuma sobrescrita de risco aplicada (bot_risk_config inválido)')
        
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
        
        # Proteções diárias e autorização externa
        self.daily_pnl_pct = 0.0  # acumulado em percentagem do dia
        self.max_daily_loss = float(self.config.get('max_daily_loss_pct', -2.0))
        # Autorizações possíveis: claude, gemini, user
        self.claude_authorized = False
        self.gemini_authorized = False
        self.user_authorized = False
        print(f"✅ {self.name} inicializada [{self.bot_type}]")
        print(f"   Biblioteca TA: {'SIM' if HAS_TA else 'NÃO'}")
        print(f"   Moedas com perfil: {len(self.profiles)}")
        print(f"   📊 Configs específicas: {len(self.crypto_configs)} moedas")
        # Mensagem operacional de prioridade (Preservação de Capital)
        print(f"⚠️ PRIORIDADE: {CAPITAL_PRESERVATION_MESSAGE}")
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
            if 'allow_below_sma' in self.bot_risk_config:
                # permite override por crypto via configuração do bot
                crypto_config['allow_below_sma'] = bool(self.bot_risk_config['allow_below_sma'])
        
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
                    with open(path, 'r', encoding='utf-8') as f:
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
        
# ===== Adaptive RSI (per spec) =====
        # Afrouxamento: a cada 30 minutos sem trades -> +2 pontos (máx +10)
        # Aperto: a cada trade executado -> -2 pontos (nunca abaixo do base)

        # Minutes since last trade for this symbol
        minutes_idle = 0 if last_time is None else (datetime.now() - last_time).total_seconds() / 60

        # Relaxation steps (every 30 minutes -> +2)
        relax_steps = int(minutes_idle // 30)
        relax_points = relax_steps * 2
        # cap relaxation to +10 above base
        if relax_points > 10:
            relax_points = 10

        # Trades since window (24h)
        now = datetime.now()
        events = self.trade_events.get(symbol, [])
        trades_recent = sum(1 for t in events if (now - t).total_seconds() <= self.trade_count_window_sec)
        tighten_points = trades_recent * 2

        # Compute adjusted RSI
        adjusted_rsi = base_rsi + relax_points - tighten_points
        if adjusted_rsi < base_rsi:
            adjusted_rsi = base_rsi
        if adjusted_rsi > base_rsi + 10:
            adjusted_rsi = base_rsi + 10

        # Keep previous urgency multipliers mild (optional): small factor
        # Apply day and crypto urgency as small modifiers (max +/-1) to avoid large shifts
        urgency_modifier = (day_urgency - 1.0) * crypto_urgency
        adjusted_rsi += urgency_modifier

        adjusted_rsi = round(float(adjusted_rsi), 2)
        self.logger.debug(f"[RSI ADJUST] {symbol} base={base_rsi} idle_min={minutes_idle:.1f} relax={relax_points} trades_recent={trades_recent} tighten={tighten_points} result={adjusted_rsi}")
        
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
            # ATR gating: open only if ATR% < abs(stop_loss%)
            atr = current.get('atr', None)
            crypto_cfg = self.get_crypto_config(symbol)
            stop_loss_pct = float(crypto_cfg.get('stop_loss', self.stop_loss_pct))
            if atr is not None and atr > 0:
                atr_pct = (atr / price) * 100.0
                if atr_pct >= abs(stop_loss_pct):
                    reason = f"ATR alto: {atr_pct:.2f}% >= SL {abs(stop_loss_pct):.2f}% - Compra bloqueada"
                    return 'HOLD', reason, indicators

            reason = f"COMPRA: {' | '.join(buy_reasons)}"
            self.last_trade_time[symbol] = datetime.now()
            return 'BUY', reason, indicators
        
        # Se não comprar, retorna HOLD
        return 'HOLD', f"Aguardando (RSI {rsi:.1f}, threshold {buy_rsi:.1f})", indicators
    
    
    def should_sell(self, symbol: str, entry_price: float, current_price: float, 
                    df: pd.DataFrame, position_time: datetime = None,
                    positions_full: bool = False,
                    position_size: float = None) -> Tuple[bool, str]:
        """Optimized sell decision per A+B (stop-loss priority + 2 signals + min-hold)

        Rules implemented:
        1) If stop-loss reached and STOP_LOSS_ATIVO -> SELL (highest priority)
        2) Else if has_strong_signal (EMA9<EMA21 AND MACD < Signal) AND position held >= min_hold_minutes -> SELL
        3) Otherwise -> HOLD

        Logs detailed indicators when selling by rule 2.
        """
        # Ensure indicators present
        df = self.calculate_indicators(df)
        current = df.iloc[-1]
        ema9 = float(current.get('ema9', current['close']))
        ema21 = float(current.get('ema21', current['close']))
        macd = float(current.get('macd', 0.0))
        macd_signal = float(current.get('macd_signal', 0.0))
        price = float(current['close'])

        # Profit calculations
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        profit_usdt = 0.0
        if position_size:
            profit_usdt = position_size * (profit_pct / 100.0)

        # Stop loss check (priority)
        crypto_cfg = self.get_crypto_config(symbol)
        stop_loss_pct = float(crypto_cfg.get('stop_loss', self.stop_loss_pct))
        stop_loss_active = bool(self.config.get('safety', {}).get('stop_loss_active', True))
        stop_loss_price = entry_price * (1.0 + (stop_loss_pct / 100.0))
        stop_loss_hit = current_price <= stop_loss_price

        if stop_loss_hit and stop_loss_active:
            self.logger.info(f"[SELL][STOP-LOSS] {symbol} stop_loss_hit price={current_price:.6f} threshold={stop_loss_price:.6f} (SL={stop_loss_pct}%)")
            return True, 'STOP_LOSS'

        # Indicator-based confirmation: require at least 2 of these to align before selling
        is_ema_down = ema9 < ema21
        is_macd_down = macd < macd_signal
        # RSI sell threshold (less sensitive by default)
        default_sell_rsi = self.config.get('strategy', {}).get('sell_rsi', 55)
        rsi = current.get('rsi', 50)
        is_rsi_sell = rsi >= float(default_sell_rsi)

        indicators_true = [is_ema_down, is_macd_down, is_rsi_sell]
        indicators_count = sum(1 for v in indicators_true if v)

        # Hold time check - conservative: require position_time to be present
        is_hold_expired = False
        minutes_held = 0.0
        if position_time:
            minutes_held = (datetime.now() - position_time).total_seconds() / 60.0
            is_hold_expired = minutes_held >= float(self.min_hold_minutes)

        # Require at least 2 indicators aligned AND min hold before selling (unless stop-loss or trailing stop)
        if indicators_count >= 2 and is_hold_expired:
            # Detailed log per monitoring requirement
            self.logger.info(
                f"[SELL][INDICATORS+HOLD] {symbol} indicators_count={indicators_count} (EMA9<EMA21={is_ema_down}, MACD<SIG={is_macd_down}, RSI>={default_sell_rsi}={is_rsi_sell}) "
                f"minutes_held={minutes_held:.1f} min_hold_req={self.min_hold_minutes} profit_pct={profit_pct:.3f}% profit_usdt={profit_usdt:.2f}"
            )
            return True, 'INDICATORS+MIN_HOLD'

        # Default: keep position
        return False, 'HOLD: no strong signal or hold time not met'
        # - Médios (SOL, BNB): stops/takes médios
        # - Voláteis (XRP, TRX): stops/takes largos, hold curto
        # - Memes (DOGE): stops/takes muito largos, hold muito curto
        crypto_stop_loss = crypto_config.get('stop_loss', -1.0)
        crypto_take_profit = crypto_config.get('take_profit', 0.5)
        # Enforce minimum TP per Protocol v2.0
        crypto_take_profit = max(crypto_take_profit, 0.40)
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
            # Detailed indicators log
            self.logger.info(
                f"[SELL][TRAILING] {symbol} drawdown_from_peak={drawdown_from_peak:.2f}% peak={peak_price:.6f} curr={current_price:.6f} "
                f"EMA9={ema9:.6f} EMA21={ema21:.6f} MACD={macd:.6f} SIGNAL={macd_signal:.6f} RSI={rsi:.1f} minutes_held={minutes_open:.1f}"
            )
            return True, f"TRAILING_STOP: drop {drawdown_from_peak:.2f}% from peak"
        
        # ===== 0.5. LUCRO MÍNIMO GARANTIDO (ESPECÍFICO POR CRYPTO) =====
        if profit_pct >= crypto_min_profit:
            # Require indicator confirmation + min-hold before quick profit sells to avoid premature exits
            # Use a conservative RSI sell threshold for quick profit logic (configurable)
            sell_rsi_quick = float(self.config.get('strategy', {}).get('sell_rsi', 55))
            quick_indicators = [ema9 < ema21, macd < macd_signal, rsi > sell_rsi_quick]
            quick_count = sum(1 for v in quick_indicators if v)
            if quick_count >= 2 and minutes_open >= float(self.min_hold_minutes):
                self.price_peaks.pop(symbol, None)
                self.logger.info(
                    f"[SELL][QUICK_PROFIT] {symbol} quick_count={quick_count} profit_pct={profit_pct:.2f}% "
                    f"EMA9={ema9:.6f} EMA21={ema21:.6f} MACD={macd:.6f} SIGNAL={macd_signal:.6f} RSI={rsi:.1f} minutes_open={minutes_open:.1f}"
                )
                return True, f"QUICK_PROFIT_INDICATORS ({quick_count}) +{profit_pct:.2f}%"
        
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
        Verifica se deve comprar (wrapper para analyze) com filtros adicionais:
        - Filtro de Tendência: EMA_200 (bloqueia compra se price < EMA_200)
        - Filtro de Volume: volume atual deve ser > média das últimas 20 barras

        Args:
            symbol: Par de trading (ex: BTC/USDT)
            df: DataFrame com dados OHLCV
            current_price: Preço atual

        Returns:
            (should_buy: bool, reason: str)
        """
        # Verificações de suficiência de dados
        if df is None or df.empty:
            return False, "Dados insuficientes (df vazio)"

        # Requer pelo menos 200 barras para calcular EMA_200 com confiança
        if len(df) < 200:
            return False, "Dados insuficientes para EMA_200 (necessárias 200 barras)"

        # Requer pelo menos 20 barras para checar volume
        if len(df) < 20:
            return False, "Dados insuficientes para verificação de volume (necessárias 20 barras)"

        # Calcula EMA_200
        try:
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        except Exception:
            return False, "Erro ao calcular EMA_200"

        # Bloqueia compra se preço atual estiver abaixo da EMA_200 (tendência de baixa)
        if current_price < ema_200:
            # Log audit event and increment daily counter
            try:
                from src.audit import get_audit_logger, AuditEvent
                audit = get_audit_logger()
                event = AuditEvent(
                    timestamp=datetime.now().isoformat(),
                    event_type='sma_block',
                    severity='info',
                    source='strategy',
                    target=symbol,
                    action='blocked_by_ema200',
                    details={'price': current_price, 'ema_200': ema_200}
                )
                audit.log_event(event)
            except Exception:
                self.logger.exception("Falha ao registrar evento de auditoria SMA block")
            try:
                from src.metrics.sma_block_counter import increment
                increment(symbol.replace('/', '').upper())
            except Exception:
                self.logger.exception("Falha ao incrementar contador de SMA blocks")
            return False, f"Bloqueado pela tendência (price {current_price:.8f} < EMA_200 {ema_200:.8f})"

        # Checa volume: precisa ser maior que média das últimas 20 barras
        try:
            avg_vol_20 = df['volume'].tail(20).mean()
            current_vol = float(df['volume'].iloc[-1])
        except Exception:
            return False, "Erro ao ler volume para verificação"

        if current_vol < avg_vol_20:
            return False, f"Bloqueado por baixo volume ({current_vol:.2f} < avg20 {avg_vol_20:.2f})"

        # Se passou pelos filtros, usa a lógica existente de decisão
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

    def _simple_rsi(self, series: pd.Series, period: int = 14) -> float:
        """Fallback simple RSI caso a biblioteca 'ta' não esteja disponível.
        Retorna o valor RSI mais recente (float).
        """
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        # Wilder smoothing (EMA) approximation
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    
    
    def update_trade_stats(self, symbol: str, pnl: float):
        """
        Atualiza estatísticas após fechar uma posição
        
        Args:
            symbol: Par de trading
            pnl: Lucro/Prejuízo da operação em USD
        """
        # Atualiza tempo do último trade
        now = datetime.now()
        self.last_trade_time[symbol] = now
        # Registra evento de trade para ajuste de RSI
        evs = self.trade_events.setdefault(symbol, [])
        evs.append(now)
        # Remove eventos antigos (> janela)
        cutoff = now.timestamp() - self.trade_count_window_sec
        self.trade_events[symbol] = [t for t in evs if t.timestamp() >= cutoff]
        
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

    # ---------- Proteções e utilitários adicionais ----------
    def check_daily_limit(self, pnl_trade_pct: float) -> bool:
        """
        Atualiza o acumulado percentual do dia e verifica se o limite de perda diária foi atingido.
        Retorna False se o limite foi ultrapassado (deve parar o bot).
        """
        try:
            self.daily_pnl_pct += float(pnl_trade_pct)
        except Exception:
            return True

        if self.daily_pnl_pct <= self.max_daily_loss:
            self.logger.warning(f"[DAILY LIMIT] daily_pnl_pct={self.daily_pnl_pct:.2f}% <= max_daily_loss={self.max_daily_loss}%")
            return False
        return True

    def run_winner_logic(self, entry_price: float, current_price: float, max_price: float) -> bool:
        """
        Lógica de trailing winner: se a moeda subiu e depois recuou uma distância
        mínima relativa ao pico, realiza o lucro.
        Usa percentuais (ex: 0.10 = 0.10%).
        """
        if max_price <= 0:
            return False

        # Percentuais em formato porcentagem (ex: 0.40 = 0.40%)
        drawdown_from_peak = ((max_price - current_price) / max_price) * 100
        profit_so_far = ((current_price - entry_price) / entry_price) * 100

        # 1) Ativação do trailing: quando atingir >= 0.40% de lucro
        # 2) Fecha se retrair 0.10% do topo
        if profit_so_far >= 0.40 and drawdown_from_peak >= getattr(self, 'trailing_retrace_pct', 0.15):
            return True

        # 3) Spike capture: se subiu >=5% do entry, garante 4.9% ao recuar
        if max_price >= entry_price * (1 + 0.05):
            # Se recuou para <= 4.9% acima do entry, realiza
            if current_price <= entry_price * (1 + 0.049):
                return True

        return False

    def authorize_claude(self):
        """Marca autorização externa (ex: Claude) para permitir operações que dependem de revisão."""
        self.claude_authorized = True

    def authorize(self, approver: str):
        """Marca autorização de um approver: 'claude', 'gemini' ou 'user'."""
        a = approver.lower()
        if a == 'claude':
            self.claude_authorized = True
        elif a == 'gemini':
            self.gemini_authorized = True
        elif a == 'user':
            self.user_authorized = True

    def revoke(self, approver: str):
        """Revoga autorização de um approver."""
        a = approver.lower()
        if a == 'claude':
            self.claude_authorized = False
        elif a == 'gemini':
            self.gemini_authorized = False
        elif a == 'user':
            self.user_authorized = False

    def approvals_count(self) -> int:
        """Retorna número de aprovações ativas (claude/gemini/user)."""
        return int(bool(self.claude_authorized)) + int(bool(self.gemini_authorized)) + int(bool(self.user_authorized))

    def smart_trade(self, exchange, symbol: str, buy_amount_usd: float = None,
                    wait_time: int = 30, dry_run: bool = True, max_checks: Optional[int] = None,
                    trailing_dist: Optional[float] = None, require_claude_auth: bool = False,
                    override_limits: bool = False, override_level: int = 1,
                    allow_below_sma: bool = False) -> dict:
        """
        Execução simplificada de trade inteligente inspirada no snippet do usuário.

        Args:
            exchange: objeto ccxt exchange já inicializado
            symbol: par (ex: 'SOL/USDT' ou 'SOLUSDT')
            buy_amount_usd: valor em USDT para comprar (se None usa 100)
            wait_time: segundos entre verificações de preço
            dry_run: se True não envia ordens reais
            max_checks: número máximo de loops antes de abortar (None = usa max_hold)
            trailing_dist: distância do trailing stop em % (ex: 0.1 = 0.10%)

        Returns:
            dict com resumo da operação
        """
        result = {'symbol': symbol, 'status': 'not_executed', 'entry_price': None, 'exit_price': None, 'pnl_usd': 0.0}

        # Authorization check (external review required)
        if require_claude_auth and not getattr(self, 'claude_authorized', False):
            self.logger.warning(f"[smart_trade] awaiting Claude authorization for {symbol}")
            return {**result, 'status': 'awaiting_claude_auth'}

        # Daily loss protection pre-check
        if getattr(self, 'daily_pnl_pct', 0.0) <= getattr(self, 'max_daily_loss', -2.0):
            if not override_limits:
                self.logger.warning(f"[smart_trade] daily loss limit reached ({self.daily_pnl_pct:.2f}% <= {self.max_daily_loss}%) - aborting trade")
                return {**result, 'status': 'halted_daily_loss', 'daily_pnl_pct': self.daily_pnl_pct}
            # override requested: validate approvals
            if override_level <= 1:
                # single approval required: Claude must authorize
                if not getattr(self, 'claude_authorized', False):
                    return {**result, 'status': 'awaiting_claude_auth'}
            else:
                # two approvals required: any two among claude/gemini/user
                if self.approvals_count() < 2:
                    return {**result, 'status': 'awaiting_two_approvals', 'approvals': self.approvals_count()}

        # Normaliza símbolo para buscar config
        key = symbol.replace('/', '').upper()
        cfg = self.get_crypto_config(key)

        buy_amount_usd = float(buy_amount_usd or self.config.get('buy_amount') or 30.0)  # default reduced to 30 USDT per trade for safety and validation
        trailing_dist = float(trailing_dist or cfg.get('trailing_stop', self.trailing_stop_pct))

        # Enforce Protocol v2.0 risk parameters:
        # - Fixed Stop Loss: -0.35%
        # - Minimum Take Profit: 0.40%
        protocol_stop_loss = -0.35
        protocol_min_tp = 0.40

        # 1) Verifica bias de mercado (SMA200)
        try:
            ohlc = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=200)
            df = pd.DataFrame(ohlc, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            sma200 = df['c'].rolling(200).mean().iloc[-1]
            sma20 = df['c'].rolling(20).mean().iloc[-1]
            last_close = df['c'].iloc[-1]

            # Indicadores adicionais (RSI, EMA9/21, MACD simples)
            if HAS_TA:
                rsi = float(ta.momentum.RSIIndicator(df['c'], window=self.config.get('indicators', {}).get('rsi', {}).get('period', 14)).rsi().iloc[-1])
                ema9 = float(df['c'].ewm(span=9, adjust=False).mean().iloc[-1])
                ema21 = float(df['c'].ewm(span=21, adjust=False).mean().iloc[-1])
                macd_line = float(ta.trend.MACD(df['c'], window_slow=self.config.get('indicators', {}).get('macd', {}).get('slow', 26), window_fast=self.config.get('indicators', {}).get('macd', {}).get('fast', 12)).macd().iloc[-1])
            else:
                # Fallback sem ta: cálculo básico
                rsi = self._simple_rsi(df['c'], period=self.config.get('indicators', {}).get('rsi', {}).get('period', 14))
                ema9 = float(df['c'].ewm(span=9, adjust=False).mean().iloc[-1])
                ema21 = float(df['c'].ewm(span=21, adjust=False).mean().iloc[-1])
                macd_line = float(df['c'].ewm(span=self.config.get('indicators', {}).get('macd', {}).get('fast', 12), adjust=False).mean().iloc[-1] - df['c'].ewm(span=self.config.get('indicators', {}).get('macd', {}).get('slow', 26), adjust=False).mean().iloc[-1])
        except Exception as e:
            self.logger.error(f"[smart_trade] erro ao buscar candles/indicadores {symbol}: {e}")
            return {**result, 'status': 'error_fetch_ohlcv', 'error': str(e)}

        # Normalize key and allowed symbols from config
        key = symbol.replace('/', '').upper()
        strategy_cfg = self.config.get('strategy', {})
        allowed_below_sma_list = [s.replace('/', '').upper() for s in strategy_cfg.get('allow_below_sma_symbols', [])]

        # Per-symbol SMA200 override logic (Option C): only allowed for specific symbols
        strategy_global_flag = bool(getattr(self, 'allow_below_sma_global', False)) or bool(strategy_cfg.get('allow_below_sma_global', False))
        cfg_allow = bool(cfg.get('allow_below_sma', False)) or strategy_global_flag or (key in allowed_below_sma_list)

        # --- Opportunity notifier (price > SMA200) with rate limit ---
        try:
            from src.communication import telegram_client as tg
            from datetime import datetime, timedelta

            now = datetime.utcnow()
            last = getattr(self, '_opportunity_last_notified', {})
            notify_interval = timedelta(minutes=60)
            if last.get(key) is None:
                self._opportunity_last_notified = self._opportunity_last_notified if hasattr(self, '_opportunity_last_notified') else {}
            if last.get(key) is None:
                last_time = None
            else:
                last_time = last.get(key)

            if last_time is None or (now - last_time) >= notify_interval:
                # If price above SMA200, send a short notification that opportunity detected
                if last_close > sma200:
                    msg = f"Oportunidade detectada: {symbol} \nPreço: {last_close:.4f} > SMA200: {sma200:.4f} (monitorando para sinal de compra)"
                    try:
                        tg.send_markdown_v2(tg.escape_markdown_v2(msg))
                    except Exception:
                        try:
                            tg.send_message(msg)
                        except Exception:
                            pass
                    self._opportunity_last_notified[key] = now
        except Exception:
            # If telegram not available, skip silently
            pass

        # Sanity: required safety flags
        safety_cfg = self.config.get('safety', {})
        if not safety_cfg.get('require_safety_manager', True):
            self.logger.warning("[safety] require_safety_manager não está habilitado no config; forçando habilitação em memória")
            safety_cfg['require_safety_manager'] = True
        if not safety_cfg.get('enforce_kill_switch', True):
            self.logger.warning("[safety] enforce_kill_switch não está habilitado no config; forçando habilitação em memória")
            safety_cfg['enforce_kill_switch'] = True
        # Force expected limits if configured lower
        if float(safety_cfg.get('max_daily_loss', 2.0)) > 2.0:
            self.logger.warning(f"[safety] max_daily_loss configurado > 2.0% ({safety_cfg.get('max_daily_loss')}); mantendo 2.0% como limite máximo para este trade")
            safety_cfg['max_daily_loss'] = 2.0

        # Require an active SafetyManager at runtime if configured
        try:
            from src.coordinator import get_coordinator
            coord = get_coordinator()
            if safety_cfg.get('require_safety_manager', True) and not getattr(coord, 'safety_manager', None):
                self.logger.error(f"[safety] require_safety_manager ativo, mas SafetyManager não encontrado no Coordinator - abortando trade")
                return {**result, 'status': 'abort_safety_missing', 'reason': 'safety_manager_missing'}
            # Enforce kill switch
            if safety_cfg.get('enforce_kill_switch', True) and getattr(coord, 'safety_manager', None):
                ks = coord.safety_manager.kill_switch
                if getattr(ks, 'is_active', False):
                    self.logger.error(f"[safety] Kill switch ativo ({ks.reason if hasattr(ks, 'reason') else 'N/A'}) - abortando trade")
                    return {**result, 'status': 'halted_kill_switch'}
        except Exception:
            # If coordinator import fails, be conservative and abort
            self.logger.error("[safety] não foi possível verificar SafetyManager no Coordinator - abortando por segurança")
            return {**result, 'status': 'abort_safety_missing', 'reason': 'safety_check_error'}

        # 1a) SMA200 filter + extended indicator checks
        if last_close <= sma200:
            # If cfg_allow True we can bypass automatically
            if cfg_allow:
                self.logger.warning(f"[AUTOMATIC OVERRIDE] Bypass SMA200 enabled for {symbol} (cfg_allow={cfg_allow})")
            else:
                # allow_below_sma param still supported (manual override via call) but needs overrides/approvals
                if not allow_below_sma:
                    # Log audit event and increment daily counter
                    try:
                        from src.audit import get_audit_logger, AuditEvent
                        audit = get_audit_logger()
                        event = AuditEvent(
                            timestamp=datetime.now().isoformat(),
                            event_type='sma_block',
                            severity='info',
                            source='strategy',
                            target=symbol,
                            action='blocked_by_sma200',
                            details={'last_close': last_close, 'sma200': sma200}
                        )
                        audit.log_event(event)
                    except Exception:
                        self.logger.exception("Falha ao registrar evento de auditoria SMA block")
                    try:
                        from src.metrics.sma_block_counter import increment
                        increment(key)
                    except Exception:
                        self.logger.exception("Falha ao incrementar contador de SMA blocks")

                    self.logger.info(f"[-] Mercado perigoso para {symbol}: preço abaixo da SMA200 ({last_close:.4f} <= {sma200:.4f})")
                    return {**result, 'status': 'aborted_market_bias', 'reason': 'below_sma200'}
                # If allow_below_sma requested, require override_limits and at least one approval
                if not override_limits:
                    self.logger.info(f"[-] allow_below_sma solicitado mas override_limits não fornecido para {symbol}")
                    return {**result, 'status': 'aborted_market_bias', 'reason': 'allow_below_sma_requires_override'}
                # Validate approvals: require at least one approver (user/claude/gemini) for a single override
                if self.approvals_count() < 1:
                    self.logger.info(f"[-] allow_below_sma solicitado mas aprovações insuficientes ({self.approvals_count()}) para {symbol}")
                    return {**result, 'status': 'aborted_market_bias', 'reason': 'insufficient_approvals'}
                # If we reach here, bypass SMA200 with approval
                self.logger.warning(f"[OVERRIDE] Bypass SMA200 autorizado para {symbol} (aprovações={self.approvals_count()})")

        # RSI threshold by bot profile: Bot Estável -> 42, Bot Médio -> 39
        if isinstance(self.bot_type, str):
            bt = self.bot_type.lower()
            if 'estavel' in bt or 'stable' in bt:
                rsi_threshold = 42
            elif 'medio' in bt or 'medium' in bt:
                rsi_threshold = 39
            else:
                rsi_threshold = cfg.get('rsi_buy', cfg.get('rsi_buy', 40))
        else:
            rsi_threshold = cfg.get('rsi_buy', 40)

        # compute macd signal if available
        try:
            if HAS_TA:
                macd_signal = float(ta.trend.MACD(df['c'], window_slow=self.config.get('indicators', {}).get('macd', {}).get('slow', 26), window_fast=self.config.get('indicators', {}).get('macd', {}).get('fast', 12)).macd_signal().iloc[-1])
            else:
                macd_signal = 0.0
        except Exception:
            macd_signal = 0.0

        macd_pct = (macd_line / last_close) if last_close and last_close != 0 else macd_line
        vol_latest = float(df['v'].iloc[-1])
        vol_mean = float(df['v'].rolling(20).mean().iloc[-1]) if len(df['v']) >= 20 else float(df['v'].mean())
        volume_high = vol_latest > (vol_mean * 1.5)

        # Load bot profile thresholds from config if available
        strategy_profiles = self.config.get('strategy', {}).get('bot_profiles', {})
        profile = strategy_profiles.get(self.bot_type, {}) if isinstance(self.bot_type, str) else {}

        # Default per-bot rules
        rsi_threshold = profile.get('rsi_buy', rsi_threshold)
        rsi_sell_threshold = profile.get('rsi_sell', cfg.get('rsi_sell', cfg.get('rsi_sell', 60)))
        macd_threshold = float(profile.get('macd_threshold', -0.01))
        require_ema_flag = bool(profile.get('require_ema9_above_ema21', False))
        allow_macd_neutral = bool(profile.get('allow_macd_neutral', False))
        require_volume_high = bool(profile.get('require_volume_high', False))

        # Per-bot indicator acceptance
        if 'estavel' in str(self.bot_type).lower() or 'stable' in str(self.bot_type).lower():
            macd_ok = (macd_pct >= macd_threshold) and (ema9 > ema21)
            sma20_ok = (last_close > sma20)
        elif 'medio' in str(self.bot_type).lower() or 'medium' in str(self.bot_type).lower():
            macd_ok = (macd_pct >= macd_threshold) and (ema9 > ema21)
            sma20_ok = (last_close > sma20)
        elif 'volatil' in str(self.bot_type).lower() or 'volatile' in str(self.bot_type).lower():
            macd_ok = (macd_pct >= -abs(macd_threshold)) and (macd_pct <= abs(macd_threshold))  # neutral allowed ±macd_threshold
            sma20_ok = (last_close > sma20)
        else:  # meme or other
            macd_ok = (macd_pct >= -abs(macd_threshold)) and (ema9 > ema21)
            sma20_ok = (last_close > sma20) and (not require_volume_high or volume_high)

        self.logger.debug(f"[indicators] {symbol} rsi={rsi:.2f} rsi_thr={rsi_threshold} macd={macd_line:.4f} macd_pct={macd_pct:.6f} macd_signal={macd_signal:.6f} ema9={ema9:.4f} ema21={ema21:.4f} sma20={sma20:.4f} vol={vol_latest:.2f} vol_mean={vol_mean:.2f}")

        if not ( (cfg_allow or (last_close > sma200)) and (rsi <= rsi_threshold) and macd_ok and sma20_ok ):
            reason = 'indicators_failed'
            details = {
                'rsi': rsi, 'rsi_thr': rsi_threshold,
                'macd': macd_line, 'macd_pct': macd_pct, 'macd_signal': macd_signal,
                'ema9': ema9, 'ema21': ema21,
                'sma20': sma20, 'price': last_close, 'vol': vol_latest
            }
            self.logger.info(f"[-] Entrada bloqueada para {symbol} por indicadores: {details}")
            return {**result, 'status': 'aborted_indicators', 'reason': reason, 'details': details}

        # If we are here and price <= SMA200 but cfg_allow is True (per-symbol override), apply tighter protections
        override_below_sma_in_use = False
        if last_close <= sma200 and cfg_allow:
            override_below_sma_in_use = True
            # Apply requested protective parameters for below-SMA override
            protocol_stop_loss = -0.45
            protocol_min_tp = 0.80
            trailing_dist = trailing_dist or 0.5
            self.logger.warning(f"[OVERRIDE] Aplicando parâmetros de override abaixo da SMA200 para {symbol}: SL={protocol_stop_loss}%, TP={protocol_min_tp}%, trailing@{trailing_dist}%")

        # 2) Entrada (usa preço atual para calcular quantidade)
        try:
            ticker = exchange.fetch_ticker(symbol)
            entry_price = float(ticker.get('last') or ticker.get('close') or last_close)
            amount = buy_amount_usd / entry_price if entry_price > 0 else 0
        except Exception as e:
            self.logger.error(f"[smart_trade] erro ao buscar ticker {symbol}: {e}")
            return {**result, 'status': 'error_fetch_ticker', 'error': str(e)}

        if amount <= 0:
            return {**result, 'status': 'invalid_amount', 'reason': 'calculated amount <= 0'}

        result['entry_price'] = entry_price

        if dry_run:
            self.logger.info(f"[DRY] BUY {symbol} simulated: {buy_amount_usd:.2f} USDT -> {amount:.6f} @ {entry_price:.6f}")
            bought_amount = amount
            buy_order = {'price': entry_price, 'amount': amount, 'info': 'dry_run'}
        else:
            try:
                buy_order = exchange.create_market_buy_order(symbol, amount)
                # Tenta extrair preço preenchido
                bought_amount = float(buy_order.get('filled') or buy_order.get('amount') or amount)
                entry_price = float(buy_order.get('price') or entry_price)
                result['entry_price'] = entry_price
                self.logger.info(f"[BUY] {symbol} {bought_amount} @ {entry_price}")
            except Exception as e:
                self.logger.error(f"[smart_trade] erro ao criar ordem de compra: {e}")
                return {**result, 'status': 'error_create_buy', 'error': str(e)}

        max_price = entry_price
        checks = 0
        # Protocol v2.0: time-stop entre 60 e 90 minutos (prioriza liquidez)
        if max_checks is None:
            window_min = int(self.config.get('protocol_v2_window_min', 60))
            window_max = int(self.config.get('protocol_v2_window_max', 90))
            chosen_minutes = random.randint(window_min, window_max)
            max_checks = int(chosen_minutes * 60 / max(1, wait_time))
        else:
            max_checks = int(max_checks)

        # 3) Loop de gestão dinâmica
        while True:
            try:
                ticker = exchange.fetch_ticker(symbol)
                curr_p = float(ticker.get('last') or ticker.get('close') or entry_price)
            except Exception as e:
                self.logger.debug(f"[smart_trade] fetch_ticker falhou: {e}")
                curr_p = entry_price

            pnl_pct = ((curr_p - entry_price) / entry_price) * 100

            if curr_p > max_price:
                max_price = curr_p

            # Stop loss: enforce protocol fixed SL (-0.35%)
            stop_threshold = protocol_stop_loss
            if pnl_pct <= stop_threshold:
                # vende
                if dry_run:
                    sell_price = curr_p
                    result.update({'status': 'stopped_loss', 'exit_price': sell_price, 'reason': 'STOP_LOSS'})
                    pnl_usd = (sell_price - entry_price) * bought_amount
                    result['pnl_usd'] = pnl_usd
                    self.logger.info(f"[DRY] STOP LOSS {symbol} exit @ {sell_price:.6f} pnl_usd={pnl_usd:.2f}")
                    self.update_trade_stats(symbol, pnl_usd)
                    # atualiza % diário e verifica limite
                    trade_pnl_pct = ((sell_price - entry_price) / entry_price) * 100
                    if not self.check_daily_limit(trade_pnl_pct):
                        result['status'] = 'halted_after_trade_daily_limit'
                    return result
                try:
                    sell_order = exchange.create_market_sell_order(symbol, bought_amount)
                    sell_price = float(sell_order.get('price') or sell_order.get('average') or curr_p)
                    pnl_usd = (sell_price - entry_price) * bought_amount
                    result.update({'status': 'stopped_loss', 'exit_price': sell_price, 'pnl_usd': pnl_usd, 'reason': 'STOP_LOSS'})
                    self.logger.info(f"[SELL STOP] {symbol} @ {sell_price} pnl_usd={pnl_usd:.2f}")
                    self.update_trade_stats(symbol, pnl_usd)
                    trade_pnl_pct = ((sell_price - entry_price) / entry_price) * 100
                    if not self.check_daily_limit(trade_pnl_pct):
                        result['status'] = 'halted_after_trade_daily_limit'
                    return result
                except Exception as e:
                    self.logger.error(f"[smart_trade] erro ao criar ordem de venda (stop): {e}")
                    result.update({'status': 'error_create_sell', 'error': str(e)})
                    return result

            # Trailing take profit
            # Winner trailing logic: se ganhou >0.5% e recuou >=0.10% do pico
            if self.run_winner_logic(entry_price, curr_p, max_price):
                if dry_run:
                    sell_price = curr_p
                    pnl_usd = (sell_price - entry_price) * bought_amount
                    result.update({'status': 'profit_taken_winner', 'exit_price': sell_price, 'pnl_usd': pnl_usd, 'reason': 'WINNER_TAKE'})
                    self.logger.info(f"[DRY] WINNER TAKE {symbol} exit @ {sell_price:.6f} pnl_usd={pnl_usd:.2f}")
                    # Detailed indicators snapshot
                    self.logger.info(f"[DRY][WINNER] EMA9={ema9:.6f} EMA21={ema21:.6f} MACD={macd:.6f} SIGNAL={macd_signal:.6f} RSI={rsi:.1f} minutes_held={minutes_held if 'minutes_held' in locals() else 'N/A'}")
                    self.update_trade_stats(symbol, pnl_usd)
                    trade_pnl_pct = ((sell_price - entry_price) / entry_price) * 100
                    if not self.check_daily_limit(trade_pnl_pct):
                        result['status'] = 'halted_after_trade_daily_limit'
                    return result
                try:
                    sell_order = exchange.create_market_sell_order(symbol, bought_amount)
                    sell_price = float(sell_order.get('price') or sell_order.get('average') or curr_p)
                    pnl_usd = (sell_price - entry_price) * bought_amount
                    result.update({'status': 'profit_taken_winner', 'exit_price': sell_price, 'pnl_usd': pnl_usd, 'reason': 'WINNER_TAKE'})
                    self.logger.info(f"[SELL WINNER] {symbol} @ {sell_price} pnl_usd={pnl_usd:.2f}")
                    # Detailed indicators snapshot
                    self.logger.info(f"[SELL][WINNER] EMA9={ema9:.6f} EMA21={ema21:.6f} MACD={macd:.6f} SIGNAL={macd_signal:.6f} RSI={rsi:.1f} minutes_held={minutes_held if 'minutes_held' in locals() else 'N/A'}")
                    self.update_trade_stats(symbol, pnl_usd)
                    trade_pnl_pct = ((sell_price - entry_price) / entry_price) * 100
                    if not self.check_daily_limit(trade_pnl_pct):
                        result['status'] = 'halted_after_trade_daily_limit'
                    return result
                except Exception as e:
                    self.logger.error(f"[smart_trade] erro ao criar ordem de venda (winner): {e}")
                    result.update({'status': 'error_create_sell', 'error': str(e)})
                    return result

            drop_from_peak = ((max_price - curr_p) / max_price) * 100 if max_price and max_price > 0 else 0
            min_profit = float(cfg.get('min_profit', 0.1))
            # Force trailing activation only after protocol minimum TP (0.40%)
            min_profit = max(min_profit, 0.40)
            if pnl_pct >= min_profit and drop_from_peak >= (trailing_dist):
                if dry_run:
                    sell_price = curr_p
                    pnl_usd = (sell_price - entry_price) * bought_amount
                    result.update({'status': 'profit_taken', 'exit_price': sell_price, 'pnl_usd': pnl_usd, 'reason': 'TAKE_PROFIT'})
                    self.logger.info(f"[DRY] TAKE PROFIT {symbol} exit @ {sell_price:.6f} pnl_usd={pnl_usd:.2f}")
                    self.logger.info(f"[DRY][TP] EMA9={ema9:.6f} EMA21={ema21:.6f} MACD={macd:.6f} SIGNAL={macd_signal:.6f} RSI={rsi:.1f} minutes_held={minutes_held if 'minutes_held' in locals() else 'N/A'}")
                    self.update_trade_stats(symbol, pnl_usd)
                    # atualiza % diário e verifica limite
                    trade_pnl_pct = ((sell_price - entry_price) / entry_price) * 100
                    if not self.check_daily_limit(trade_pnl_pct):
                        result['status'] = 'halted_after_trade_daily_limit'
                    return result
                try:
                    sell_order = exchange.create_market_sell_order(symbol, bought_amount)
                    sell_price = float(sell_order.get('price') or sell_order.get('average') or curr_p)
                    pnl_usd = (sell_price - entry_price) * bought_amount
                    result.update({'status': 'profit_taken', 'exit_price': sell_price, 'pnl_usd': pnl_usd, 'reason': 'TAKE_PROFIT'})
                    self.logger.info(f"[SELL TP] {symbol} @ {sell_price} pnl_usd={pnl_usd:.2f}")
                    self.logger.info(f"[SELL][TP] EMA9={ema9:.6f} EMA21={ema21:.6f} MACD={macd:.6f} SIGNAL={macd_signal:.6f} RSI={rsi:.1f} minutes_held={minutes_held if 'minutes_held' in locals() else 'N/A'}")
                    self.update_trade_stats(symbol, pnl_usd)
                    trade_pnl_pct = ((sell_price - entry_price) / entry_price) * 100
                    if not self.check_daily_limit(trade_pnl_pct):
                        result['status'] = 'halted_after_trade_daily_limit'
                    return result
                except Exception as e:
                    self.logger.error(f"[smart_trade] erro ao criar ordem de venda (tp): {e}")
                    result.update({'status': 'error_create_sell', 'error': str(e)})
                    return result

            # incrementa checks e timeout
            checks += 1
            if max_checks and checks >= max_checks:
                # timeout: tenta fechar se tem qualquer lucro mínimo
                if pnl_pct > 0:
                    if dry_run:
                        sell_price = curr_p
                        pnl_usd = (sell_price - entry_price) * bought_amount
                        result.update({'status': 'timeout_closed', 'exit_price': sell_price, 'pnl_usd': pnl_usd, 'reason': 'TIMEOUT_CLOSED'})
                        self.update_trade_stats(symbol, pnl_usd)
                        trade_pnl_pct = ((sell_price - entry_price) / entry_price) * 100
                        if not self.check_daily_limit(trade_pnl_pct):
                            result['status'] = 'halted_after_trade_daily_limit'
                        return result
                    try:
                        sell_order = exchange.create_market_sell_order(symbol, bought_amount)
                        sell_price = float(sell_order.get('price') or sell_order.get('average') or curr_p)
                        pnl_usd = (sell_price - entry_price) * bought_amount
                        result.update({'status': 'timeout_closed', 'exit_price': sell_price, 'pnl_usd': pnl_usd, 'reason': 'TIMEOUT_CLOSED'})
                        self.update_trade_stats(symbol, pnl_usd)
                        trade_pnl_pct = ((sell_price - entry_price) / entry_price) * 100
                        if not self.check_daily_limit(trade_pnl_pct):
                            result['status'] = 'halted_after_trade_daily_limit'
                        return result
                    except Exception as e:
                        result.update({'status': 'error_timeout_sell', 'error': str(e)})
                        return result
                else:
                    result.update({'status': 'timeout_no_action', 'pnl_pct': pnl_pct})
                    return result

            time.sleep(max(1, wait_time))



# Função para integração com trading_engine.py
def get_strategy(strategy_type: str = 'smart', config: dict = None):
    """Factory function para criar estratégia"""
    return SmartStrategy(config)
