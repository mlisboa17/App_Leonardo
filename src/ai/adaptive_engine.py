# -*- coding: utf-8 -*-
"""
R7_V1 - Motor de IA Adaptativa
==========================================

Motor de Machine Learning que aprende com o histórico de trades,
identificando padrões de sucesso e fracasso para melhorar as decisões.

Features:
- Aprende com trades passados (wins/losses)
- Identifica condições de mercado favoráveis
- Prediz probabilidade de sucesso de trades
- Ajusta parâmetros dinamicamente
"""

import os
import json
import pickle
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
# TEMPORÁRIO: sklearn desabilitado por problemas com Python 3.14
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    RandomForestClassifier = None
    GradientBoostingClassifier = None
    StandardScaler = None
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger('AdaptiveEngine')


class AdaptiveEngine:
    """
    Motor de IA que aprende com o histórico de trades.
    
    Funcionalidades:
    - Treina modelos com base em trades históricos
    - Prediz probabilidade de sucesso
    - Identifica padrões de mercado
    - Sugere ajustes de parâmetros
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.model_dir = os.path.join(data_dir, "ai_models")
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Modelos por bot e global
        self.models: Dict[str, RandomForestClassifier] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        
        # Histórico de aprendizado
        self.learning_history = {
            'accuracy': [],
            'precision': [],
            'recall': [],
            'samples': [],
            'last_training': None
        }
        
        # Insights descobertos
        self.insights = {
            'best_rsi_range': {},
            'best_hours': {},
            'dangerous_patterns': [],
            'favorable_conditions': [],
            'crypto_performance': {}
        }
        
        # Cache de predições
        self.prediction_cache = {}
        
        # Carregar modelos existentes
        self._load_models()
        self._load_insights()
    
    def _load_models(self):
        """Carrega modelos salvos do disco"""
        try:
            model_file = os.path.join(self.model_dir, "models.pkl")
            if os.path.exists(model_file):
                with open(model_file, 'rb') as f:
                    data = pickle.load(f)
                    self.models = data.get('models', {})
                    self.scalers = data.get('scalers', {})
                    self.learning_history = data.get('history', self.learning_history)
                logger.info(f"✅ Modelos carregados: {list(self.models.keys())}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar modelos: {e}")
    
    def _save_models(self):
        """Salva modelos no disco"""
        try:
            model_file = os.path.join(self.model_dir, "models.pkl")
            with open(model_file, 'wb') as f:
                pickle.dump({
                    'models': self.models,
                    'scalers': self.scalers,
                    'history': self.learning_history
                }, f)
            logger.info("💾 Modelos salvos com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar modelos: {e}")
    
    def _load_insights(self):
        """Carrega insights descobertos"""
        try:
            insights_file = os.path.join(self.model_dir, "insights.json")
            if os.path.exists(insights_file):
                with open(insights_file, 'r') as f:
                    self.insights = json.load(f)
                logger.info("✅ Insights carregados")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar insights: {e}")
    
    def _save_insights(self):
        """Salva insights descobertos"""
        try:
            insights_file = os.path.join(self.model_dir, "insights.json")
            with open(insights_file, 'w') as f:
                json.dump(self.insights, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Erro ao salvar insights: {e}")
    
    def _extract_features(self, trade: Dict) -> Optional[np.ndarray]:
        """
        Extrai features de um trade para ML.
        
        Features extraídas:
        - RSI no momento da compra
        - MACD histogram
        - Distância da SMA20
        - Hora do dia
        - Dia da semana
        - Volatilidade recente
        - Volume relativo
        """
        try:
            features = []
            
            # RSI
            reason = trade.get('buy_reason', trade.get('reason', ''))
            rsi = self._extract_number(reason, 'RSI')
            features.append(rsi if rsi else 30)
            
            # MACD trend (1 = bullish, 0 = bearish)
            macd_up = 1 if 'MACD↑' in reason or 'MACD_UP' in reason else 0
            features.append(macd_up)
            
            # Distância SMA
            sma_dist = self._extract_number(reason, 'SMA')
            features.append(sma_dist if sma_dist else 0)
            
            # Hora do dia (0-23)
            timestamp = trade.get('buy_time', trade.get('timestamp', ''))
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        features.append(dt.hour)
                        features.append(dt.weekday())
                    except:
                        features.extend([12, 3])  # defaults
                else:
                    features.extend([12, 3])
            else:
                features.extend([12, 3])
            
            # Preço de entrada
            entry_price = trade.get('entry_price', trade.get('buy_price', 0))
            features.append(np.log1p(entry_price) if entry_price > 0 else 0)
            
            # Quantidade
            amount = trade.get('amount', trade.get('quantity', 0))
            features.append(np.log1p(amount) if amount > 0 else 0)
            
            # Stop loss configurado
            stop = trade.get('stop_loss_pct', 2.5)
            features.append(stop)
            
            # Take profit configurado
            tp = trade.get('take_profit_pct', 2.0)
            features.append(tp)
            
            return np.array(features)
        except Exception as e:
            logger.warning(f"Erro ao extrair features: {e}")
            return None
    
    def _extract_number(self, text: str, prefix: str) -> Optional[float]:
        """Extrai número de uma string com prefixo"""
        import re
        patterns = [
            rf'{prefix}\s*[:=]?\s*([-+]?\d+\.?\d*)',
            rf'{prefix}\s+([-+]?\d+\.?\d*)',
            rf'([-+]?\d+\.?\d*)\s*%?\s*\({prefix}\)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        return None
    
    def train_from_history(self, trades: List[Dict], bot_name: str = "global") -> Dict:
        """
        Treina o modelo com base no histórico de trades.
        
        Args:
            trades: Lista de trades históricos
            bot_name: Nome do bot (ou "global" para modelo geral)
            
        Returns:
            Dict com métricas de treinamento
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("⚠️ sklearn não disponível - treinamento desabilitado")
            return {'status': 'sklearn_unavailable', 'trades': len(trades)}
        
        logger.info(f"🧠 Iniciando treinamento para {bot_name} com {len(trades)} trades")
        
        if len(trades) < 10:
            logger.warning(f"⚠️ Poucos trades ({len(trades)}) para treinar. Mínimo: 10")
            return {'status': 'insufficient_data', 'trades': len(trades)}
        
        # Preparar dados
        X = []
        y = []
        
        for trade in trades:
            features = self._extract_features(trade)
            if features is None:
                continue
            
            # Label: 1 = lucro, 0 = prejuízo
            pnl = trade.get('pnl', trade.get('profit_loss', 0))
            if isinstance(pnl, str):
                try:
                    pnl = float(pnl.replace('$', '').replace(',', ''))
                except:
                    pnl = 0
            
            label = 1 if pnl > 0 else 0
            
            X.append(features)
            y.append(label)
        
        if len(X) < 10:
            logger.warning(f"⚠️ Features válidas insuficientes: {len(X)}")
            return {'status': 'insufficient_features', 'valid': len(X)}
        
        X = np.array(X)
        y = np.array(y)
        
        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split treino/teste
        if len(X) >= 20:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
        else:
            X_train, X_test, y_train, y_test = X_scaled, X_scaled, y, y
        
        # Treinar modelo
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_split=3,
            random_state=42,
            class_weight='balanced'
        )
        model.fit(X_train, y_train)
        
        # Avaliar
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        
        # Salvar modelo
        self.models[bot_name] = model
        self.scalers[bot_name] = scaler
        
        # Atualizar histórico
        self.learning_history['accuracy'].append(accuracy)
        self.learning_history['precision'].append(precision)
        self.learning_history['recall'].append(recall)
        self.learning_history['samples'].append(len(X))
        self.learning_history['last_training'] = datetime.now().isoformat()
        
        # Salvar no disco
        self._save_models()
        
        # Analisar feature importance
        feature_names = ['RSI', 'MACD', 'SMA_dist', 'Hora', 'DiaSemana', 
                        'LogPreco', 'LogQtd', 'StopLoss', 'TakeProfit']
        importances = dict(zip(feature_names, model.feature_importances_))
        
        # Descobrir insights
        self._discover_insights(trades, bot_name)
        
        result = {
            'status': 'success',
            'bot': bot_name,
            'samples': len(X),
            'accuracy': round(accuracy * 100, 1),
            'precision': round(precision * 100, 1),
            'recall': round(recall * 100, 1),
            'feature_importance': importances,
            'win_rate_data': round(sum(y) / len(y) * 100, 1)
        }
        
        logger.info(f"✅ Modelo treinado: Accuracy={accuracy:.1%}, Precision={precision:.1%}")
        return result
    
    def _discover_insights(self, trades: List[Dict], bot_name: str):
        """
        Descobre insights a partir dos trades.
        Identifica padrões que levam a sucesso ou fracasso.
        """
        wins = []
        losses = []
        
        for trade in trades:
            pnl = trade.get('pnl', trade.get('profit_loss', 0))
            if isinstance(pnl, str):
                try:
                    pnl = float(pnl.replace('$', '').replace(',', ''))
                except:
                    continue
            
            reason = trade.get('buy_reason', trade.get('reason', ''))
            rsi = self._extract_number(reason, 'RSI')
            
            timestamp = trade.get('buy_time', trade.get('timestamp', ''))
            hour = 12
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        hour = dt.hour
                except:
                    pass
            
            symbol = trade.get('symbol', '')
            
            if pnl > 0:
                wins.append({'rsi': rsi, 'hour': hour, 'symbol': symbol, 'pnl': pnl})
            else:
                losses.append({'rsi': rsi, 'hour': hour, 'symbol': symbol, 'pnl': pnl})
        
        # Melhor range de RSI
        win_rsis = [w['rsi'] for w in wins if w['rsi']]
        loss_rsis = [l['rsi'] for l in losses if l['rsi']]
        
        if win_rsis:
            self.insights['best_rsi_range'][bot_name] = {
                'min': round(np.percentile(win_rsis, 10), 1),
                'max': round(np.percentile(win_rsis, 90), 1),
                'mean': round(np.mean(win_rsis), 1)
            }
        
        # Melhores horários
        win_hours = [w['hour'] for w in wins]
        if win_hours:
            hour_counts = {}
            for h in win_hours:
                hour_counts[h] = hour_counts.get(h, 0) + 1
            best_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            self.insights['best_hours'][bot_name] = [h[0] for h in best_hours]
        
        # Performance por crypto
        crypto_stats = {}
        for trade in trades:
            symbol = trade.get('symbol', '')
            if not symbol:
                continue
            
            pnl = trade.get('pnl', trade.get('profit_loss', 0))
            if isinstance(pnl, str):
                try:
                    pnl = float(pnl.replace('$', '').replace(',', ''))
                except:
                    pnl = 0
            
            if symbol not in crypto_stats:
                crypto_stats[symbol] = {'wins': 0, 'losses': 0, 'total_pnl': 0}
            
            if pnl > 0:
                crypto_stats[symbol]['wins'] += 1
            else:
                crypto_stats[symbol]['losses'] += 1
            crypto_stats[symbol]['total_pnl'] += pnl
        
        self.insights['crypto_performance'][bot_name] = crypto_stats
        
        # Identificar padrões perigosos
        dangerous = []
        for symbol, stats in crypto_stats.items():
            total = stats['wins'] + stats['losses']
            if total >= 3 and stats['losses'] / total > 0.7:
                dangerous.append({
                    'symbol': symbol,
                    'loss_rate': round(stats['losses'] / total * 100, 1),
                    'total_loss': round(stats['total_pnl'], 2)
                })
        
        self.insights['dangerous_patterns'] = dangerous
        
        # Condições favoráveis
        if win_rsis and loss_rsis:
            favorable = []
            if np.mean(win_rsis) < np.mean(loss_rsis):
                favorable.append("RSI mais baixo tende a ter mais sucesso")
            if self.insights.get('best_hours', {}).get(bot_name):
                favorable.append(f"Melhores horários: {self.insights['best_hours'][bot_name]}")
            self.insights['favorable_conditions'] = favorable
        
        self._save_insights()
        logger.info(f"💡 Insights descobertos para {bot_name}")
    
    def predict_trade_success(self, trade_params: Dict, bot_name: str = "global") -> Dict:
        """
        Prediz a probabilidade de sucesso de um trade.
        
        Args:
            trade_params: Parâmetros do trade (RSI, MACD, etc)
            bot_name: Nome do bot
            
        Returns:
            Dict com probabilidade e recomendação
        """
        if not SKLEARN_AVAILABLE:
            return {
                'prediction': 'unknown',
                'probability': 0.5,
                'confidence': 'low',
                'reason': 'sklearn não disponível'
            }
        
        # Tentar modelo específico ou global
        model = self.models.get(bot_name) or self.models.get('global')
        scaler = self.scalers.get(bot_name) or self.scalers.get('global')
        
        if model is None:
            return {
                'prediction': 'unknown',
                'probability': 0.5,
                'confidence': 'low',
                'reason': 'Modelo não treinado ainda'
            }
        
        # Extrair features
        features = self._extract_features(trade_params)
        if features is None:
            return {
                'prediction': 'unknown',
                'probability': 0.5,
                'confidence': 'low',
                'reason': 'Não foi possível extrair features'
            }
        
        # Normalizar e predizer
        features_scaled = scaler.transform([features])
        prob = model.predict_proba(features_scaled)[0]
        
        success_prob = prob[1] if len(prob) > 1 else prob[0]
        
        # Determinar recomendação
        if success_prob >= 0.7:
            prediction = 'FORTE COMPRA'
            confidence = 'high'
        elif success_prob >= 0.55:
            prediction = 'COMPRA'
            confidence = 'medium'
        elif success_prob >= 0.45:
            prediction = 'NEUTRO'
            confidence = 'low'
        elif success_prob >= 0.3:
            prediction = 'EVITAR'
            confidence = 'medium'
        else:
            prediction = 'FORTE EVITAR'
            confidence = 'high'
        
        return {
            'prediction': prediction,
            'probability': round(success_prob * 100, 1),
            'confidence': confidence,
            'insights': self._get_relevant_insights(trade_params, bot_name)
        }
    
    def _get_relevant_insights(self, trade_params: Dict, bot_name: str) -> List[str]:
        """Retorna insights relevantes para o trade"""
        insights = []
        
        reason = trade_params.get('buy_reason', trade_params.get('reason', ''))
        rsi = self._extract_number(reason, 'RSI')
        
        best_rsi = self.insights.get('best_rsi_range', {}).get(bot_name)
        if best_rsi and rsi:
            if best_rsi['min'] <= rsi <= best_rsi['max']:
                insights.append(f"✅ RSI {rsi} está no range ideal ({best_rsi['min']}-{best_rsi['max']})")
            elif rsi < best_rsi['min']:
                insights.append(f"⚠️ RSI {rsi} muito baixo (ideal: {best_rsi['min']}+)")
            else:
                insights.append(f"⚠️ RSI {rsi} alto demais (ideal: até {best_rsi['max']})")
        
        symbol = trade_params.get('symbol', '')
        crypto_perf = self.insights.get('crypto_performance', {}).get(bot_name, {}).get(symbol)
        if crypto_perf:
            total = crypto_perf['wins'] + crypto_perf['losses']
            win_rate = crypto_perf['wins'] / total * 100 if total > 0 else 0
            if win_rate >= 70:
                insights.append(f"✅ {symbol} tem win rate de {win_rate:.0f}%")
            elif win_rate <= 40:
                insights.append(f"⚠️ {symbol} tem win rate baixo: {win_rate:.0f}%")
        
        dangerous = self.insights.get('dangerous_patterns', [])
        for d in dangerous:
            if d['symbol'] == symbol:
                insights.append(f"🚨 CUIDADO: {symbol} tem {d['loss_rate']}% de perdas!")
        
        return insights
    
    def get_bot_recommendations(self, bot_name: str, current_config: Dict) -> Dict:
        """
        Gera recomendações de ajuste para um bot baseado no aprendizado.
        
        Args:
            bot_name: Nome do bot
            current_config: Configuração atual do bot
            
        Returns:
            Dict com recomendações de ajuste
        """
        recommendations = {
            'adjustments': [],
            'warnings': [],
            'opportunities': []
        }
        
        # Análise de RSI
        best_rsi = self.insights.get('best_rsi_range', {}).get(bot_name)
        if best_rsi:
            current_rsi_buy = current_config.get('rsi_buy', 30)
            if current_rsi_buy > best_rsi['mean']:
                recommendations['adjustments'].append({
                    'param': 'rsi_buy',
                    'current': current_rsi_buy,
                    'suggested': round(best_rsi['mean']),
                    'reason': f"RSI médio de sucesso é {best_rsi['mean']}"
                })
        
        # Cryptos perigosas
        dangerous = self.insights.get('dangerous_patterns', [])
        for d in dangerous:
            recommendations['warnings'].append(
                f"⚠️ {d['symbol']}: {d['loss_rate']}% perdas (${d['total_loss']:.2f})"
            )
        
        # Melhores horários
        best_hours = self.insights.get('best_hours', {}).get(bot_name)
        if best_hours:
            current_hour = datetime.now().hour
            if current_hour in best_hours:
                recommendations['opportunities'].append(
                    f"✅ Horário atual ({current_hour}h) é favorável para trades"
                )
            else:
                recommendations['opportunities'].append(
                    f"ℹ️ Melhores horários: {best_hours}"
                )
        
        return recommendations
    
    def get_market_regime(self, prices: List[float], window: int = 20) -> str:
        """
        Detecta o regime de mercado atual.
        
        Returns:
            'bullish', 'bearish', 'sideways', 'volatile'
        """
        if len(prices) < window:
            return 'unknown'
        
        prices = np.array(prices[-window:])
        
        # Calcular métricas
        returns = np.diff(prices) / prices[:-1]
        mean_return = np.mean(returns)
        volatility = np.std(returns)
        trend = (prices[-1] - prices[0]) / prices[0]
        
        # Classificar regime
        if volatility > 0.03:  # Alta volatilidade
            return 'volatile'
        elif trend > 0.02:  # Tendência de alta
            return 'bullish'
        elif trend < -0.02:  # Tendência de baixa
            return 'bearish'
        else:
            return 'sideways'
    
    def suggest_strategy_adjustments(self, regime: str, bot_profile: str) -> Dict:
        """
        Sugere ajustes de estratégia baseado no regime de mercado.
        
        Args:
            regime: Regime de mercado atual
            bot_profile: Perfil do bot (estavel, medio, volatil, meme)
            
        Returns:
            Dict com ajustes sugeridos
        """
        adjustments = {
            'stop_loss': None,
            'take_profit': None,
            'rsi_buy': None,
            'rsi_sell': None,
            'max_positions': None,
            'reason': ''
        }
        
        if regime == 'volatile':
            adjustments.update({
                'stop_loss': {'multiply': 1.5, 'reason': 'Mercado volátil - aumentar stop'},
                'take_profit': {'multiply': 1.3, 'reason': 'Aproveitar movimentos maiores'},
                'max_positions': {'multiply': 0.7, 'reason': 'Reduzir exposição'},
                'reason': '⚠️ MERCADO VOLÁTIL - Modo defensivo ativado'
            })
        
        elif regime == 'bearish':
            adjustments.update({
                'stop_loss': {'multiply': 0.8, 'reason': 'Stops mais apertados em bear market'},
                'take_profit': {'multiply': 0.7, 'reason': 'Realizar lucros mais rápido'},
                'rsi_buy': {'add': -5, 'reason': 'Comprar em RSI mais baixo'},
                'max_positions': {'multiply': 0.5, 'reason': 'Reduzir muito a exposição'},
                'reason': '🐻 BEAR MARKET - Modo muito conservador'
            })
        
        elif regime == 'bullish':
            adjustments.update({
                'stop_loss': {'multiply': 1.2, 'reason': 'Dar mais espaço em bull market'},
                'take_profit': {'multiply': 1.2, 'reason': 'Deixar lucros correrem'},
                'rsi_buy': {'add': 5, 'reason': 'Aceitar RSI mais alto em bull'},
                'max_positions': {'multiply': 1.2, 'reason': 'Aumentar exposição'},
                'reason': '🚀 BULL MARKET - Modo agressivo ativado'
            })
        
        else:  # sideways
            adjustments.update({
                'take_profit': {'multiply': 0.8, 'reason': 'Realizar lucros rápido em range'},
                'reason': '↔️ MERCADO LATERAL - Trades rápidos'
            })
        
        # Ajustes específicos por perfil
        if bot_profile == 'meme' and regime == 'volatile':
            adjustments['max_positions'] = {'multiply': 0.3, 'reason': 'Memes muito arriscados em vol'}
        elif bot_profile == 'estavel' and regime == 'bullish':
            adjustments['max_positions'] = {'multiply': 1.0, 'reason': 'Manter conservador mesmo em bull'}
        
        return adjustments
    
    def get_learning_summary(self) -> Dict:
        """Retorna resumo do aprendizado"""
        return {
            'models_trained': list(self.models.keys()),
            'total_samples': sum(self.learning_history.get('samples', [])),
            'avg_accuracy': round(np.mean(self.learning_history.get('accuracy', [0])) * 100, 1),
            'last_training': self.learning_history.get('last_training'),
            'insights_count': sum([
                len(self.insights.get('best_rsi_range', {})),
                len(self.insights.get('best_hours', {})),
                len(self.insights.get('dangerous_patterns', [])),
                len(self.insights.get('favorable_conditions', []))
            ])
        }


# Teste standalone
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = AdaptiveEngine()
    
    # Teste com trades simulados
    sample_trades = [
        {'symbol': 'BTCUSDT', 'buy_reason': 'RSI 25 | MACD↑', 'buy_time': '2025-12-05T10:00:00', 
         'entry_price': 95000, 'amount': 0.01, 'pnl': 15.0},
        {'symbol': 'ETHUSDT', 'buy_reason': 'RSI 30 | MACD↑', 'buy_time': '2025-12-05T14:00:00',
         'entry_price': 3500, 'amount': 0.1, 'pnl': -5.0},
        {'symbol': 'BTCUSDT', 'buy_reason': 'RSI 22 | MACD↑', 'buy_time': '2025-12-05T10:30:00',
         'entry_price': 94500, 'amount': 0.01, 'pnl': 20.0},
    ]
    
    # Adicionar mais trades para treino
    for i in range(20):
        sample_trades.append({
            'symbol': 'BTCUSDT' if i % 2 == 0 else 'ETHUSDT',
            'buy_reason': f'RSI {20 + i} | MACD↑',
            'buy_time': f'2025-12-0{(i%5)+1}T{10+i%8}:00:00',
            'entry_price': 95000 + i * 100,
            'amount': 0.01,
            'pnl': 10 if i % 3 != 0 else -5
        })
    
    result = engine.train_from_history(sample_trades)
    print(f"\n📊 Resultado do treino: {result}")
    
    # Testar predição
    test_trade = {
        'symbol': 'BTCUSDT',
        'buy_reason': 'RSI 28 | MACD↑',
        'entry_price': 96000
    }
    prediction = engine.predict_trade_success(test_trade)
    print(f"\n🔮 Predição: {prediction}")
    
    print(f"\n📈 Resumo: {engine.get_learning_summary()}")
