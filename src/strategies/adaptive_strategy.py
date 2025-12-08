"""
Estratégia Adaptativa - Analisa histórico de cada moeda e ajusta RSI dinamicamente
Meta: $100/dia através de trades inteligentes adaptados ao comportamento de cada cripto
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AdaptiveStrategy:
    """
    Estratégia que aprende o comportamento de cada moeda:
    - Analisa RSI mínimo histórico
    - Analisa RSI máximo histórico
    - Ajusta thresholds dinamicamente
    - Relaxa entrada se está sem trades há muito tempo
    """
    
    def __init__(self, exchange_client, config):
        self.exchange = exchange_client
        self.config = config
        
        # Configuração base
        self.symbols = config.SYMBOLS
        self.daily_target = 100.0  # Meta: $100/dia
        self.amount_per_trade = 50.0  # $50 por trade
        
        # Proteções
        self.stop_loss_pct = -1.5
        self.max_position_time = 10  # minutos
        self.max_daily_loss = -50.0
        
        # Histórico de cada moeda (será populado)
        self.crypto_profiles = {}
        
        # Estado de trading
        self.last_trade_time = {}  # Última vez que operou cada moeda
        self.daily_stats = {
            'trades_today': 0,
            'profit_today': 0.0,
            'wins': 0,
            'losses': 0,
            'last_reset': datetime.now().date()
        }
        
        # Inicializa perfis
        logger.info("Inicializando estratégia adaptativa...")
        self._initialize_crypto_profiles()
    
    
    def _initialize_crypto_profiles(self):
        """
        Analisa histórico de 7 dias de cada moeda para descobrir:
        - RSI mínimo que ela realmente atinge
        - RSI máximo que ela realmente atinge
        - Média de RSI em compras lucrativas
        - Média de RSI em vendas lucrativas
        """
        logger.info("Analisando histórico de 7 dias para cada moeda...")
        
        for symbol in self.symbols:
            try:
                logger.info(f"Analisando {symbol}...")
                
                # Busca 7 dias de dados (velas de 1 minuto)
                candles = self._fetch_historical_data(symbol, days=7)
                
                if candles is None or len(candles) < 100:
                    logger.warning(f"Dados insuficientes para {symbol}")
                    self._set_default_profile(symbol)
                    continue
                
                # Calcula indicadores históricos
                df = self._calculate_historical_indicators(candles)
                
                # Analisa padrões
                profile = self._analyze_crypto_behavior(symbol, df)
                
                self.crypto_profiles[symbol] = profile
                
                logger.info(f"""
{symbol} - Perfil Criado:
  RSI Mínimo (7d): {profile['rsi_min']:.1f}
  RSI Máximo (7d): {profile['rsi_max']:.1f}
  RSI Compra Ideal: {profile['buy_rsi_threshold']:.1f}
  RSI Venda Ideal: {profile['sell_rsi_threshold']:.1f}
  Volatilidade: {profile['volatility']:.2f}%
  Volume Médio: ${profile['avg_volume']:,.0f}
""")
                
            except Exception as e:
                logger.error(f"Erro ao analisar {symbol}: {e}")
                self._set_default_profile(symbol)
    
    
    def _fetch_historical_data(self, symbol: str, days: int = 7) -> Optional[pd.DataFrame]:
        """Busca dados históricos da exchange"""
        try:
            # Calcula timestamp de 7 dias atrás
            since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
            # Busca candles de 1 minuto (limite da API: ~1000 candles)
            # Para 7 dias completos, faremos múltiplas requisições
            all_candles = []
            
            # Divide em chunks de 1000 candles (aproximadamente 16 horas por chunk)
            chunks_needed = min((days * 24 * 60) // 1000 + 1, 10)  # Máximo 10 chunks
            
            logger.info(f"Buscando {chunks_needed} chunks de dados para {symbol}...")
            
            for i in range(chunks_needed):
                chunk_since = since + (i * 1000 * 60 * 1000)  # 1000 minutos depois
                
                try:
                    # Verifica se exchange tem método síncrono ou async
                    if hasattr(self.exchange, 'fetch_ohlcv'):
                        # Método síncrono
                        candles = self.exchange.fetch_ohlcv(
                            symbol=symbol,
                            timeframe='1m',
                            since=chunk_since,
                            limit=1000
                        )
                    else:
                        # Usa API direta da Binance (fallback)
                        import requests
                        url = f"https://api.binance.com/api/v3/klines"
                        params = {
                            'symbol': symbol.replace('/', ''),
                            'interval': '1m',
                            'startTime': chunk_since,
                            'limit': 1000
                        }
                        response = requests.get(url, params=params)
                        data = response.json()
                        
                        # Converte formato Binance para CCXT
                        candles = [
                            [k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])]
                            for k in data
                        ]
                    
                    if candles:
                        all_candles.extend(candles)
                        logger.info(f"Chunk {i+1}/{chunks_needed}: {len(candles)} candles")
                    
                except Exception as e:
                    logger.warning(f"Erro no chunk {i}: {e}")
                    continue
            
            if not all_candles:
                logger.warning(f"Nenhum dado histórico para {symbol}")
                return None
            
            # Converte para DataFrame
            df = pd.DataFrame(
                all_candles,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            logger.info(f"Total de {len(df)} candles para {symbol}")
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados históricos de {symbol}: {e}")
            return None
    
    
    def _calculate_historical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula RSI, MACD, médias móveis no histórico"""
        
        # RSI (14 períodos)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Médias Móveis
        df['sma20'] = df['close'].rolling(window=20).mean()
        df['sma50'] = df['close'].rolling(window=50).mean()
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # Volatilidade (ATR simplificado)
        df['atr'] = (df['high'] - df['low']).rolling(window=14).mean()
        
        return df
    
    
    def _analyze_crypto_behavior(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Analisa o comportamento histórico e define thresholds personalizados
        """
        
        # Remove NaN dos primeiros registros
        df = df.dropna()
        
        if len(df) < 100:
            return self._get_default_profile()
        
        # 1. RSI Mínimo e Máximo (percentil 5% e 95%)
        rsi_min = df['rsi'].quantile(0.05)  # 5% mais baixo
        rsi_max = df['rsi'].quantile(0.95)  # 5% mais alto
        
        # 2. Identifica movimentos de alta (preço subiu > 1% em 15 min)
        df['future_return'] = df['close'].shift(-15) / df['close'] - 1
        
        profitable_moves = df[df['future_return'] > 0.01]  # Subiu > 1%
        
        if len(profitable_moves) > 10:
            # RSI médio quando teve movimento lucrativo
            buy_rsi_ideal = profitable_moves['rsi'].mean()
        else:
            # Se não tem dados suficientes, usa percentil 15%
            buy_rsi_ideal = df['rsi'].quantile(0.15)
        
        # 3. Identifica topos (preço caiu > 1% depois de 15 min)
        losing_moves = df[df['future_return'] < -0.01]  # Caiu > 1%
        
        if len(losing_moves) > 10:
            # RSI médio quando teve reversão
            sell_rsi_ideal = losing_moves['rsi'].mean()
        else:
            # Se não tem dados suficientes, usa percentil 85%
            sell_rsi_ideal = df['rsi'].quantile(0.85)
        
        # 4. Volatilidade média
        volatility = (df['atr'] / df['close'] * 100).mean()
        
        # 5. Volume médio
        avg_volume = df['volume'].mean()
        
        # 6. Ajusta thresholds com margem de segurança
        buy_threshold = max(rsi_min + 2, buy_rsi_ideal - 3)  # Compra um pouco antes
        sell_threshold = min(rsi_max - 2, sell_rsi_ideal + 3)  # Vende um pouco depois
        
        # Garante limites razoáveis
        buy_threshold = max(25, min(45, buy_threshold))  # Entre 25 e 45
        sell_threshold = max(55, min(75, sell_threshold))  # Entre 55 e 75
        
        return {
            'symbol': symbol,
            'rsi_min': rsi_min,
            'rsi_max': rsi_max,
            'buy_rsi_threshold': buy_threshold,
            'sell_rsi_threshold': sell_threshold,
            'volatility': volatility,
            'avg_volume': avg_volume,
            'last_update': datetime.now()
        }
    
    
    def _set_default_profile(self, symbol: str):
        """Define perfil padrão caso não consiga analisar histórico"""
        self.crypto_profiles[symbol] = self._get_default_profile()
        self.crypto_profiles[symbol]['symbol'] = symbol
    
    
    def _get_default_profile(self) -> Dict:
        """Retorna perfil padrão conservador"""
        return {
            'symbol': 'UNKNOWN',
            'rsi_min': 30.0,
            'rsi_max': 70.0,
            'buy_rsi_threshold': 38.0,
            'sell_rsi_threshold': 62.0,
            'volatility': 1.5,
            'avg_volume': 1000000,
            'last_update': datetime.now()
        }
    
    
    def should_buy(self, symbol: str, current_data: Dict) -> Tuple[bool, str]:
        """
        Decide se deve comprar baseado no perfil da moeda
        
        LÓGICA ADAPTATIVA:
        1. Usa RSI threshold específico da moeda
        2. Se está sem trades há muito tempo, relaxa entrada (38, 39, 40...)
        3. Verifica outros indicadores de confirmação
        """
        
        profile = self.crypto_profiles.get(symbol)
        if not profile:
            return False, "Perfil não encontrado"
        
        # Indicadores atuais
        rsi = current_data.get('rsi', 50)
        macd = current_data.get('macd', 0)
        macd_signal = current_data.get('macd_signal', 0)
        price = current_data.get('close', 0)
        sma20 = current_data.get('sma20', price)
        volume = current_data.get('volume', 0)
        
        # Threshold base da moeda
        buy_threshold = profile['buy_rsi_threshold']
        
        # AJUSTE DINÂMICO: Se está sem trades há muito tempo, relaxa entrada
        minutes_since_last_trade = self._minutes_since_last_trade(symbol)
        
        if minutes_since_last_trade > 30:
            # Sem trades há 30+ minutos, relaxa em 2 pontos
            buy_threshold += 2
            reason_suffix = " (relaxado +2 - sem trades 30min)"
        elif minutes_since_last_trade > 60:
            # Sem trades há 1+ hora, relaxa em 4 pontos
            buy_threshold += 4
            reason_suffix = " (relaxado +4 - sem trades 1h)"
        elif minutes_since_last_trade > 120:
            # Sem trades há 2+ horas, relaxa em 6 pontos
            buy_threshold += 6
            reason_suffix = " (relaxado +6 - sem trades 2h)"
        else:
            reason_suffix = ""
        
        # Limita threshold máximo em 45 (não compra acima disso)
        buy_threshold = min(45, buy_threshold)
        
        # CONDIÇÕES DE COMPRA
        conditions_met = 0
        reasons = []
        
        # 1. RSI abaixo do threshold adaptativo
        if rsi < buy_threshold:
            conditions_met += 1
            reasons.append(f"RSI {rsi:.1f} < {buy_threshold:.1f}{reason_suffix}")
        
        # 2. MACD cruzando para cima (momentum positivo)
        if macd > macd_signal:
            conditions_met += 1
            reasons.append("MACD↑")
        
        # 3. Preço próximo ou abaixo da SMA20 (suporte)
        distance_from_sma = ((price - sma20) / sma20) * 100
        if distance_from_sma < 0.5:
            conditions_met += 1
            reasons.append(f"Próx SMA20 ({distance_from_sma:+.1f}%)")
        
        # 4. Volume razoável (não está morto)
        if volume > profile['avg_volume'] * 0.5:
            conditions_met += 1
            reasons.append("Volume OK")
        
        # Precisa de pelo menos 2 condições
        if conditions_met >= 2:
            return True, " | ".join(reasons)
        
        return False, f"Aguardando ({conditions_met}/2) - RSI {rsi:.1f} (threshold {buy_threshold:.1f})"
    
    
    def should_sell(self, symbol: str, entry_price: float, current_data: Dict, 
                    position_open_time: datetime) -> Tuple[bool, str]:
        """
        Decide se deve vender baseado em:
        1. Stop loss (-1.5%)
        2. Tendência virou de QUEDA (sua ideia!)
        3. Lucro bom + sinais de reversão
        """
        
        profile = self.crypto_profiles.get(symbol)
        if not profile:
            return True, "Perfil não encontrado - vendendo por segurança"
        
        # Dados atuais
        current_price = current_data.get('close', 0)
        rsi = current_data.get('rsi', 50)
        macd = current_data.get('macd', 0)
        macd_signal = current_data.get('macd_signal', 0)
        sma20 = current_data.get('sma20', current_price)
        
        # Calcula lucro/prejuízo
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        # 1. STOP LOSS (sempre ativo)
        if profit_pct <= self.stop_loss_pct:
            return True, f"STOP LOSS {profit_pct:.2f}%"
        
        # 2. PROTEÇÃO DE TEMPO (não segura forever)
        minutes_open = (datetime.now() - position_open_time).seconds / 60
        if minutes_open > self.max_position_time:
            if profit_pct > 0:
                return True, f"Tempo máximo ({minutes_open:.0f}min) - Lucro {profit_pct:.2f}%"
            else:
                # Está em prejuízo mas não bateu stop, aguarda mais um pouco
                if minutes_open > self.max_position_time * 1.5:
                    return True, f"Tempo máximo estendido - Prejuízo {profit_pct:.2f}%"
        
        # 3. SUA ESTRATÉGIA: Só vende se tendência virou QUEDA
        # Ajusta sell_rsi_threshold com base no mapeamento dinâmico, se houver
        sell_rsi_threshold = profile.get('sell_rsi_threshold', 65)
        if self.dynamic_factor and self.bot_key:
            dyn_rsi = self.dynamic_factor.get_dynamic_rsi_by_name(self.bot_key, minutes_open)
            if dyn_rsi and isinstance(dyn_rsi, dict) and 'venda' in dyn_rsi:
                try:
                    sell_rsi_threshold = int(dyn_rsi['venda'])
                except Exception:
                    pass

        if profit_pct > 0.3:  # Tem pelo menos 0.3% de lucro
            
            queda_signals = 0
            queda_reasons = []
            
            # Sinal 1: MACD cruzou para baixo
            if macd < macd_signal:
                queda_signals += 1
                queda_reasons.append("MACD↓")
            
            # Sinal 2: Preço caiu abaixo da SMA20
            if current_price < sma20:
                queda_signals += 1
                queda_reasons.append("< SMA20")
            
            # Sinal 3: RSI acima do threshold de venda (overbought para essa moeda)
            if rsi > sell_rsi_threshold:
                queda_signals += 1
                queda_reasons.append(f"RSI {rsi:.1f} > {profile['sell_rsi_threshold']:.1f}")
            
            # Sinal 4: Lucro já está bom (> 2%)
            if profit_pct > 2.0:
                queda_signals += 1
                queda_reasons.append(f"Lucro ótimo {profit_pct:.2f}%")
            
            # Se tem 2+ sinais de QUEDA → VENDE
            if queda_signals >= 2:
                return True, f"QUEDA ({queda_signals}/4): {' | '.join(queda_reasons)}"
            else:
                # Tendência ainda ALTA → SEGURA
                return False, f"ALTA - Segurando +{profit_pct:.2f}% ({queda_signals}/4 sinais queda)"
        
        # 4. Lucro ainda pequeno, aguarda
        return False, f"Aguardando +{profit_pct:.2f}%"
    
    
    def _minutes_since_last_trade(self, symbol: str) -> int:
        """Retorna quantos minutos desde o último trade dessa moeda"""
        last_time = self.last_trade_time.get(symbol)
        
        if not last_time:
            return 999  # Nunca operou, retorna valor alto
        
        delta = datetime.now() - last_time
        return int(delta.seconds / 60)
    
    
    def update_trade_record(self, symbol: str, trade_type: str, profit: float):
        """Atualiza registro de trades"""
        
        self.last_trade_time[symbol] = datetime.now()
        
        self.daily_stats['trades_today'] += 1
        self.daily_stats['profit_today'] += profit
        
        if profit > 0:
            self.daily_stats['wins'] += 1
        else:
            self.daily_stats['losses'] += 1
        
        # Log de progresso
        progress_pct = (self.daily_stats['profit_today'] / self.daily_target) * 100
        
        logger.info(f"""
Trade #{self.daily_stats['trades_today']} - {symbol} {trade_type}
Lucro: ${profit:+.2f}
Hoje: ${self.daily_stats['profit_today']:+.2f} ({progress_pct:.1f}% da meta)
Win Rate: {self._calculate_win_rate():.1f}%
""")
        
        # Atingiu meta?
        if self.daily_stats['profit_today'] >= self.daily_target:
            logger.info(f"🎉 META DIÁRIA ATINGIDA! ${self.daily_stats['profit_today']:.2f}")
    
    
    def _calculate_win_rate(self) -> float:
        """Calcula win rate"""
        total = self.daily_stats['wins'] + self.daily_stats['losses']
        if total == 0:
            return 0.0
        return (self.daily_stats['wins'] / total) * 100
    
    
    def reset_daily_stats(self):
        """Reseta estatísticas diárias (chamado à meia-noite)"""
        today = datetime.now().date()
        
        if self.daily_stats['last_reset'] != today:
            logger.info(f"""
═══════════════════════════════════════
RESUMO DO DIA {self.daily_stats['last_reset']}
═══════════════════════════════════════
Trades: {self.daily_stats['trades_today']}
Lucro: ${self.daily_stats['profit_today']:+.2f}
Meta: ${self.daily_target} ({(self.daily_stats['profit_today']/self.daily_target*100):.1f}%)
Win Rate: {self._calculate_win_rate():.1f}%
Wins: {self.daily_stats['wins']} | Losses: {self.daily_stats['losses']}
═══════════════════════════════════════
""")
            
            self.daily_stats = {
                'trades_today': 0,
                'profit_today': 0.0,
                'wins': 0,
                'losses': 0,
                'last_reset': today
            }
    
    
    def get_best_symbols_to_trade(self, n: int = 4) -> list:
        """
        Retorna as N melhores moedas para operar agora
        Baseado em:
        - Tempo desde último trade (prioriza quem está parado)
        - Volatilidade (prefere mais volátil)
        - Volume (prefere mais líquido)
        """
        
        scores = []
        
        for symbol in self.symbols:
            profile = self.crypto_profiles.get(symbol)
            if not profile:
                continue
            
            # Score baseado em múltiplos fatores
            score = 0
            
            # 1. Tempo sem operar (40% do score)
            minutes = self._minutes_since_last_trade(symbol)
            time_score = min(minutes / 60, 5) * 40  # Max 5 horas
            score += time_score
            
            # 2. Volatilidade (30% do score)
            vol_score = min(profile['volatility'] / 3, 1) * 30  # Normaliza em 3%
            score += vol_score
            
            # 3. Volume (30% do score)
            vol_usd = profile['avg_volume']
            volume_score = min(vol_usd / 1000000, 1) * 30  # Normaliza em $1M
            score += volume_score
            
            scores.append({
                'symbol': symbol,
                'score': score,
                'minutes_idle': minutes,
                'volatility': profile['volatility'],
                'volume': vol_usd
            })
        
        # Ordena por score (maior primeiro)
        scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Retorna top N
        return [s['symbol'] for s in scores[:n]]
    
    
    def get_daily_summary(self) -> Dict:
        """Retorna resumo do dia"""
        return {
            'trades_today': self.daily_stats['trades_today'],
            'profit_today': self.daily_stats['profit_today'],
            'target': self.daily_target,
            'progress_pct': (self.daily_stats['profit_today'] / self.daily_target) * 100,
            'win_rate': self._calculate_win_rate(),
            'wins': self.daily_stats['wins'],
            'losses': self.daily_stats['losses']
        }
