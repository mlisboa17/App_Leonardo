"""
🤖 Machine Learning Forecasting - R7_V1
Powered by Facebook Prophet - Previsões inteligentes de preço
"""
import pandas as pd
import numpy as np
from prophet import Prophet
from typing import Dict, List, Optional, Tuple, Union
import warnings
import logging
from datetime import datetime, timedelta
import json

# Suprimir warnings do Prophet
logging.getLogger('prophet').setLevel(logging.WARNING)
warnings.filterwarnings('ignore')

class MLForecaster:
    """Classe para previsões de Machine Learning usando Prophet"""
    
    def __init__(self):
        """Inicializa o módulo de ML Forecasting"""
        self.models = {}  # Cache de modelos treinados
        self.forecasts = {}  # Cache de previsões
        self.model_params = {
            'daily_seasonality': True,
            'weekly_seasonality': True,
            'yearly_seasonality': False,  # Crypto não segue padrões anuais
            'seasonality_mode': 'multiplicative',  # Crypto tem sazonalidade multiplicativa
            'interval_width': 0.80,  # 80% de intervalo de confiança
            'changepoint_prior_scale': 0.05,  # Flexibilidade para mudanças de tendência
            'seasonality_prior_scale': 10.0,  # Força da sazonalidade
        }
        print("🤖 MLForecaster inicializado com Prophet")
    
    def prepare_data_for_prophet(self, df: pd.DataFrame, price_column: str = 'close') -> pd.DataFrame:
        """
        Prepara dados no formato exigido pelo Prophet
        
        Args:
            df: DataFrame com dados de preço
            price_column: Nome da coluna de preço
            
        Returns:
            DataFrame no formato Prophet (ds, y)
        """
        try:
            # Prophet exige colunas 'ds' (timestamp) e 'y' (valor)
            prophet_df = pd.DataFrame()
            
            # Timestamp
            if 'timestamp' in df.columns:
                prophet_df['ds'] = pd.to_datetime(df['timestamp'])
            elif df.index.name == 'timestamp' or pd.api.types.is_datetime64_any_dtype(df.index):
                prophet_df['ds'] = df.index
            else:
                # Criar timestamps artificiais se necessário
                prophet_df['ds'] = pd.date_range(start='2025-01-01', periods=len(df), freq='H')
            
            # Valor (preço)
            if price_column in df.columns:
                prophet_df['y'] = df[price_column].astype(float)
            else:
                raise ValueError(f"Coluna {price_column} não encontrada")
            
            # Remover valores NaN
            prophet_df = prophet_df.dropna()
            
            # Ordenar por data
            prophet_df = prophet_df.sort_values('ds').reset_index(drop=True)
            
            print(f"✅ Dados preparados: {len(prophet_df)} pontos válidos")
            return prophet_df
            
        except Exception as e:
            print(f"❌ Erro ao preparar dados: {e}")
            return pd.DataFrame()
    
    def train_model(self, df: pd.DataFrame, symbol: str, 
                   custom_params: Optional[Dict] = None) -> bool:
        """
        Treina modelo Prophet para um símbolo específico
        
        Args:
            df: DataFrame preparado para Prophet
            symbol: Símbolo da crypto
            custom_params: Parâmetros personalizados
            
        Returns:
            True se treinamento foi bem-sucedido
        """
        try:
            print(f"🏋️ Treinando modelo ML para {symbol}...")
            
            if len(df) < 20:
                print(f"❌ Dados insuficientes para {symbol} (min: 20 pontos)")
                return False
            
            # Usar parâmetros customizados ou padrão
            params = self.model_params.copy()
            if custom_params:
                params.update(custom_params)
            
            # Criar e configurar modelo
            model = Prophet(**params)
            
            # Adicionar sazonalidades customizadas para crypto
            # Padrão de 4 horas (comum em crypto)
            model.add_seasonality(name='4h_cycle', period=4/24, fourier_order=3)
            
            # Padrão de 12 horas
            model.add_seasonality(name='12h_cycle', period=12/24, fourier_order=5)
            
            # Treinar modelo
            model.fit(df)
            
            # Salvar modelo treinado
            self.models[symbol] = {
                'model': model,
                'trained_at': datetime.now(),
                'data_points': len(df),
                'last_price': float(df['y'].iloc[-1]),
                'price_range': {
                    'min': float(df['y'].min()),
                    'max': float(df['y'].max()),
                    'mean': float(df['y'].mean()),
                    'std': float(df['y'].std())
                }
            }
            
            print(f"✅ Modelo {symbol} treinado com {len(df)} pontos")
            return True
            
        except Exception as e:
            print(f"❌ Erro no treinamento de {symbol}: {e}")
            return False
    
    def predict_price(self, symbol: str, periods: int = 24, 
                     freq: str = 'H') -> Optional[Dict]:
        """
        Faz previsão de preço para períodos futuros
        
        Args:
            symbol: Símbolo da crypto
            periods: Número de períodos futuros
            freq: Frequência ('H' = hora, 'D' = dia)
            
        Returns:
            Dict com previsões e métricas
        """
        try:
            if symbol not in self.models:
                print(f"❌ Modelo não encontrado para {symbol}")
                return None
            
            model_info = self.models[symbol]
            model = model_info['model']
            
            print(f"🔮 Prevendo {periods} períodos para {symbol}...")
            
            # Criar dataframe de datas futuras
            future = model.make_future_dataframe(periods=periods, freq=freq)
            
            # Fazer previsão
            forecast = model.predict(future)
            
            # Extrair previsões futuras (últimos 'periods' pontos)
            future_forecast = forecast.tail(periods).copy()
            
            # Calcular métricas da previsão
            current_price = model_info['last_price']
            
            predictions = {
                'symbol': symbol,
                'current_price': current_price,
                'predictions': [],
                'summary': {},
                'confidence_intervals': {},
                'trend_analysis': {}
            }
            
            # Processar cada previsão
            for idx, row in future_forecast.iterrows():
                pred_data = {
                    'timestamp': row['ds'],
                    'predicted_price': float(row['yhat']),
                    'lower_bound': float(row['yhat_lower']),
                    'upper_bound': float(row['yhat_upper']),
                    'change_percent': ((float(row['yhat']) - current_price) / current_price) * 100,
                    'confidence_width': float(row['yhat_upper'] - row['yhat_lower'])
                }
                predictions['predictions'].append(pred_data)
            
            # Calcular resumo
            final_prediction = predictions['predictions'][-1]
            first_prediction = predictions['predictions'][0]
            
            predictions['summary'] = {
                'final_price': final_prediction['predicted_price'],
                'total_change_percent': final_prediction['change_percent'],
                'trend_direction': 'BULLISH' if final_prediction['change_percent'] > 0 else 'BEARISH',
                'volatility_forecast': np.mean([p['confidence_width'] for p in predictions['predictions']]),
                'max_upside': max([p['upper_bound'] for p in predictions['predictions']]),
                'max_downside': min([p['lower_bound'] for p in predictions['predictions']]),
            }
            
            # Análise de tendência
            prices = [p['predicted_price'] for p in predictions['predictions']]
            trend_slope = np.polyfit(range(len(prices)), prices, 1)[0]
            
            predictions['trend_analysis'] = {
                'slope': float(trend_slope),
                'is_trending_up': trend_slope > 0,
                'trend_strength': abs(trend_slope) / current_price * 100,
                'momentum': 'STRONG' if abs(trend_slope) / current_price > 0.01 else 'WEAK'
            }
            
            # Intervalos de confiança
            predictions['confidence_intervals'] = {
                '1h': predictions['predictions'][0] if len(predictions['predictions']) > 0 else None,
                '6h': predictions['predictions'][5] if len(predictions['predictions']) > 5 else None,
                '12h': predictions['predictions'][11] if len(predictions['predictions']) > 11 else None,
                '24h': predictions['predictions'][23] if len(predictions['predictions']) > 23 else None,
            }
            
            # Salvar no cache
            self.forecasts[symbol] = predictions
            
            print(f"✅ Previsão gerada: {final_prediction['change_percent']:+.2f}% em {periods}h")
            return predictions
            
        except Exception as e:
            print(f"❌ Erro na previsão de {symbol}: {e}")
            return None
    
    def get_trading_signal_ml(self, symbol: str) -> Dict[str, any]:
        """
        Gera sinal de trading baseado em ML
        
        Returns:
            Dict com sinal e análise ML
        """
        try:
            if symbol not in self.forecasts:
                return {
                    'action': 'WAIT',
                    'confidence': 0,
                    'reason': 'Previsão ML não disponível',
                    'ml_analysis': {}
                }
            
            forecast = self.forecasts[symbol]
            summary = forecast['summary']
            trend = forecast['trend_analysis']
            
            # Análise para próximas horas
            short_term = forecast['confidence_intervals'].get('1h', {})
            medium_term = forecast['confidence_intervals'].get('6h', {})
            
            # Score baseado em múltiplos fatores
            ml_score = 0
            
            # Fator 1: Direção da tendência (30 pontos)
            if summary['trend_direction'] == 'BULLISH':
                ml_score += 30
            
            # Fator 2: Força da tendência (20 pontos)
            if trend['momentum'] == 'STRONG':
                ml_score += 20
            elif trend['momentum'] == 'MODERATE':
                ml_score += 10
            
            # Fator 3: Mudança percentual esperada (30 pontos)
            change_pct = abs(summary['total_change_percent'])
            if change_pct > 5:
                ml_score += 30
            elif change_pct > 2:
                ml_score += 20
            elif change_pct > 1:
                ml_score += 10
            
            # Fator 4: Consistência das previsões (20 pontos)
            prices = [p['predicted_price'] for p in forecast['predictions'][:6]]  # Próximas 6h
            if len(prices) > 1:
                price_trend = all(prices[i] >= prices[i-1] for i in range(1, len(prices)))
                if price_trend or all(prices[i] <= prices[i-1] for i in range(1, len(prices))):
                    ml_score += 20  # Tendência consistente
            
            # Determinar ação
            if ml_score >= 70 and summary['trend_direction'] == 'BULLISH':
                action = 'BUY'
                confidence = min(95, ml_score)
                reason = f"ML prevê alta de {summary['total_change_percent']:+.2f}% (Score: {ml_score})"
            elif ml_score >= 70 and summary['trend_direction'] == 'BEARISH':
                action = 'SELL'  
                confidence = min(95, ml_score)
                reason = f"ML prevê queda de {summary['total_change_percent']:+.2f}% (Score: {ml_score})"
            else:
                action = 'WAIT'
                confidence = 100 - ml_score
                reason = f"Previsão ML incerta (Score: {ml_score})"
            
            return {
                'action': action,
                'confidence': confidence,
                'reason': reason,
                'ml_analysis': {
                    'ml_score': ml_score,
                    'predicted_change': summary['total_change_percent'],
                    'trend_direction': summary['trend_direction'],
                    'trend_strength': trend['momentum'],
                    'price_targets': {
                        'optimistic': summary['max_upside'],
                        'realistic': summary['final_price'],
                        'pessimistic': summary['max_downside']
                    },
                    'time_horizons': {
                        '1h_change': short_term.get('change_percent', 0),
                        '6h_change': medium_term.get('change_percent', 0),
                        'final_change': summary['total_change_percent']
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ Erro no sinal ML para {symbol}: {e}")
            return {
                'action': 'WAIT',
                'confidence': 0,
                'reason': f'Erro ML: {str(e)}',
                'ml_analysis': {}
            }
    
    def analyze_forecast_accuracy(self, symbol: str, actual_df: pd.DataFrame) -> Dict[str, float]:
        """
        Analisa precisão das previsões comparando com dados reais
        
        Args:
            symbol: Símbolo da crypto
            actual_df: DataFrame com dados reais para comparação
            
        Returns:
            Dict com métricas de precisão
        """
        try:
            if symbol not in self.forecasts:
                return {'error': 'Nenhuma previsão encontrada'}
            
            forecast = self.forecasts[symbol]
            
            # Comparar previsões com dados reais
            accuracy_metrics = {
                'mae': 0,  # Mean Absolute Error
                'mape': 0,  # Mean Absolute Percentage Error
                'rmse': 0,  # Root Mean Square Error
                'directional_accuracy': 0,  # Acurácia da direção
                'samples_compared': 0
            }
            
            predictions = forecast['predictions']
            errors = []
            direction_correct = 0
            
            for pred in predictions:
                # Encontrar dados reais correspondentes
                pred_time = pred['timestamp']
                matching_real = actual_df[actual_df['timestamp'] == pred_time]
                
                if not matching_real.empty:
                    real_price = float(matching_real['close'].iloc[0])
                    pred_price = pred['predicted_price']
                    
                    # Calcular erros
                    error = abs(real_price - pred_price)
                    errors.append(error)
                    
                    # Verificar direção
                    if len(errors) > 1:
                        real_direction = real_price > forecast['current_price']
                        pred_direction = pred_price > forecast['current_price']
                        if real_direction == pred_direction:
                            direction_correct += 1
            
            if errors:
                real_prices = [float(matching_real['close'].iloc[0]) for matching_real in 
                              [actual_df[actual_df['timestamp'] == pred['timestamp']] 
                               for pred in predictions] if not matching_real.empty]
                
                if real_prices:
                    accuracy_metrics['mae'] = np.mean(errors)
                    accuracy_metrics['mape'] = np.mean([abs(e/r)*100 for e, r in zip(errors, real_prices)])
                    accuracy_metrics['rmse'] = np.sqrt(np.mean([e**2 for e in errors]))
                    accuracy_metrics['directional_accuracy'] = (direction_correct / len(errors)) * 100
                    accuracy_metrics['samples_compared'] = len(errors)
            
            print(f"📊 Precisão do modelo {symbol}: MAPE={accuracy_metrics['mape']:.2f}%")
            return accuracy_metrics
            
        except Exception as e:
            print(f"❌ Erro na análise de precisão: {e}")
            return {'error': str(e)}
    
    def print_forecast_summary(self, symbol: str):
        """Imprime resumo da previsão ML"""
        try:
            if symbol not in self.forecasts:
                print(f"❌ Nenhuma previsão ML disponível para {symbol}")
                return
            
            forecast = self.forecasts[symbol]
            summary = forecast['summary']
            trend = forecast['trend_analysis']
            
            print(f"\n🤖 === PREVISÃO ML: {symbol} ===")
            print(f"💰 Preço Atual: ${forecast['current_price']:.4f}")
            print(f"🔮 Previsão Final: ${summary['final_price']:.4f}")
            print(f"📈 Mudança Esperada: {summary['total_change_percent']:+.2f}%")
            
            trend_emoji = "🚀" if summary['trend_direction'] == 'BULLISH' else "📉"
            print(f"📊 Tendência: {trend_emoji} {summary['trend_direction']}")
            print(f"💪 Força: {trend['momentum']}")
            
            print(f"\n🎯 Cenários:")
            print(f"   📈 Otimista: ${summary['max_upside']:.4f}")
            print(f"   🎯 Realista: ${summary['final_price']:.4f}")
            print(f"   📉 Pessimista: ${summary['max_downside']:.4f}")
            
            # Intervalos de tempo
            intervals = forecast['confidence_intervals']
            print(f"\n⏰ Previsões por Período:")
            for period, data in intervals.items():
                if data:
                    change = data['change_percent']
                    emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    print(f"   {period}: {emoji} {change:+.2f}%")
            
            print("=" * 35)
            
        except Exception as e:
            print(f"❌ Erro no resumo ML de {symbol}: {e}")
    
    def retrain_if_needed(self, symbol: str, hours_threshold: int = 24) -> bool:
        """
        Retreina modelo se passou muito tempo desde último treinamento
        
        Args:
            symbol: Símbolo da crypto
            hours_threshold: Horas máximas sem retreinamento
            
        Returns:
            True se retreinou
        """
        try:
            if symbol not in self.models:
                return False
            
            model_info = self.models[symbol]
            trained_at = model_info['trained_at']
            hours_since_training = (datetime.now() - trained_at).total_seconds() / 3600
            
            if hours_since_training > hours_threshold:
                print(f"🔄 Retreinando {symbol} (último treino há {hours_since_training:.1f}h)")
                # Aqui você precisaria dos dados atualizados para retreinar
                # Por enquanto, apenas atualiza timestamp
                model_info['trained_at'] = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro no retreinamento de {symbol}: {e}")
            return False

# ========================================
# TESTE RÁPIDO
# ========================================

if __name__ == "__main__":
    print("🧪 Testando MLForecaster...")
    
    # Criar dados de teste
    dates = pd.date_range(start='2025-01-01', periods=200, freq='H')
    
    # Simular dados realistas de crypto
    np.random.seed(42)
    
    # Criar série temporal com tendência e sazonalidade
    trend = np.linspace(50000, 52000, 200)
    seasonality = 1000 * np.sin(np.arange(200) * 2 * np.pi / 24)  # Padrão diário
    noise = np.random.normal(0, 500, 200)
    
    prices = trend + seasonality + noise
    
    # Criar DataFrame
    test_data = pd.DataFrame({
        'timestamp': dates,
        'close': prices,
        'open': prices * (1 + np.random.normal(0, 0.001, 200)),
        'high': prices * (1 + abs(np.random.normal(0, 0.005, 200))),
        'low': prices * (1 - abs(np.random.normal(0, 0.005, 200))),
        'volume': np.random.randint(1000, 10000, 200)
    })
    
    # Testar MLForecaster
    forecaster = MLForecaster()
    
    # Preparar dados
    prophet_data = forecaster.prepare_data_for_prophet(test_data, 'close')
    print(f"📊 Dados preparados: {len(prophet_data)} pontos")
    
    # Treinar modelo
    success = forecaster.train_model(prophet_data, 'BTC/USDT')
    
    if success:
        # Fazer previsão
        prediction = forecaster.predict_price('BTC/USDT', periods=24)
        
        if prediction:
            # Mostrar resumo
            forecaster.print_forecast_summary('BTC/USDT')
            
            # Gerar sinal de trading
            ml_signal = forecaster.get_trading_signal_ml('BTC/USDT')
            print(f"\n🎯 Sinal ML: {ml_signal['action']} ({ml_signal['confidence']:.0f}%)")
            print(f"💭 Razão: {ml_signal['reason']}")
    
    print("\n🔥 MLForecaster pronto para uso!")