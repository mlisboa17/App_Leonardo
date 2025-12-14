"""
Módulo de Gestão de Portfólio para App Leonardo Bot
Implementa regras avançadas de exposição e risco
Enhanced com AdvancedIndicators + MLForecaster
"""
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Importar novos módulos avançados
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from indicators.advanced_indicators import AdvancedIndicators
    from core.ml_forecaster import MLForecaster
    ADVANCED_MODULES_AVAILABLE = True
    print("🚀 Portfolio Manager Enhanced: AdvancedIndicators + MLForecaster carregados")
except ImportError as e:
    print(f"⚠️ Módulos avançados não disponíveis: {e}")
    ADVANCED_MODULES_AVAILABLE = False

class PortfolioManager:
    def __init__(self, config_path: str = '../config/portfolio_rules.json'):
        """
        Inicializa o gerenciador de portfólio com módulos avançados
        """
        self.config_path = config_path
        self.rules = self._load_portfolio_rules()
        
        # Inicializar módulos avançados se disponíveis
        if ADVANCED_MODULES_AVAILABLE:
            self.advanced_indicators = AdvancedIndicators()
            self.ml_forecaster = MLForecaster()
            print("✅ Portfolio Manager com AI/ML ativado")
        else:
            self.advanced_indicators = None
            self.ml_forecaster = None
            print("⚠️ Portfolio Manager em modo básico")
        
    def _load_portfolio_rules(self) -> Dict:
        """Carrega as regras de portfólio do arquivo de configuração"""
        default_rules = {
            'portfolio_management': {
                'max_crypto_exposure_percent': 60,  # Mais agressivo para aproveitar oportunidades
                'dynamic_exposure': True,  # Ajusta baseado no mercado
                'bull_market_exposure': 80,
                'bear_market_exposure': 20,
                'neutral_market_exposure': 40,
                'exposure_action': 'smart_capitalize',
                'exceptions': ['empty_portfolio_exception', 'market_trend_exception'],
                'min_positions': 2,
                'max_positions_exception': 8,  # Mais flexível
                'min_position_value': 10,
                'aggressive_hours': {'start': '09:00', 'end': '11:00'},
                'sell_only_hours': {'start': '15:00', 'end': '17:00'},
                'capitalization': {
                    'target_profit_percent': 20.0,  # Mais agressivo nos lucros
                    'min_profit_to_sell': 5.0,      # Aguarda lucro significativo
                    'smart_rebalance': True,
                    'profit_taking_levels': [20.0, 50.0, 100.0],  # Níveis mais realistas
                    'position_size_increase_on_profit': True,
                    'moonbag_percentage': 10  # Deixa 10% para gains extremos
                },
                'risk_management': {
                    'graduated_stop_loss': True,     # NOVA: Stop loss escalonado
                    'stop_loss_levels': {
                        'alert': -5.0,              # Apenas alerta
                        'partial_exit': -10.0,      # Vende 50%
                        'full_exit': -20.0          # Vende tudo (salva 80%)
                    },
                    'emergency_stop_loss': -25.0,   # Última linha de defesa
                    'dca_limits': {
                        'max_additions': 2,          # Máximo 2 DCA
                        'only_top_coins': True,      # Só moedas TOP 10
                        'max_dca_loss': -15.0        # Para DCA se perda > 15%
                    },
                    'market_cap_filter': 1000000000  # Só cryptos > 1B market cap para DCA
                },
                'market_analysis': {
                    'trend_detection': True,
                    'volatility_adjustment': True,
                    'rsi_market_filter': True
                },
                'last_updated': datetime.now().isoformat()
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    rules = json.load(f)
                    return rules
            else:
                # Criar arquivo com configurações padrão
                self._save_rules(default_rules)
                return default_rules
        except Exception as e:
            print(f"⚠️ Erro ao carregar regras de portfólio: {e}")
            return default_rules
    
    def _save_rules(self, rules: Dict) -> bool:
        """Salva as regras no arquivo"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(rules, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar regras: {e}")
            return False
    
    def detect_market_trend(self, crypto_positions: List[Dict]) -> str:
        """Detecta tendência geral do mercado baseado nas posições"""
        try:
            if not crypto_positions:
                return 'NEUTRAL'
            
            # Analisa performance geral das posições
            total_positions = len(crypto_positions)
            profitable_count = len([p for p in crypto_positions if float(p.get('pnl_percent', 0)) > 0])
            avg_pnl = sum(float(p.get('pnl_percent', 0)) for p in crypto_positions) / total_positions
            
            # Lógica de detecção de tendência
            profitable_ratio = profitable_count / total_positions if total_positions > 0 else 0
            
            if profitable_ratio > 0.7 and avg_pnl > 5:  # 70%+ lucrativas e média +5%
                return 'BULL'
            elif profitable_ratio < 0.3 and avg_pnl < -3:  # 70%+ perdendo e média -3%
                return 'BEAR'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            print(f"❌ Erro na detecção de tendência: {e}")
            return 'NEUTRAL'
    
    def get_dynamic_exposure_limit(self, crypto_positions: List[Dict]) -> float:
        """Calcula limite de exposição dinâmico baseado no mercado"""
        try:
            rules = self.rules['portfolio_management']
            
            if not rules.get('dynamic_exposure', False):
                return rules.get('max_crypto_exposure_percent', 40)
            
            market_trend = self.detect_market_trend(crypto_positions)
            
            if market_trend == 'BULL':
                return rules.get('bull_market_exposure', 80)
            elif market_trend == 'BEAR':
                return rules.get('bear_market_exposure', 20)
            else:
                return rules.get('neutral_market_exposure', 40)
                
        except Exception as e:
            print(f"❌ Erro no cálculo de exposição dinâmica: {e}")
            return 40
    
    def get_portfolio_exposure(self, usdt_balance: float, crypto_positions: List[Dict]) -> Tuple[float, float, float]:
        """
        Calcula a exposição atual do portfólio em crypto
        
        Returns:
            tuple: (valor_total_crypto, valor_total_portfolio, percentual_exposicao)
        """
        try:
            crypto_value = 0.0
            
            for position in crypto_positions:
                if position.get('status') == 'open':
                    quantity = float(position.get('quantity', 0))
                    current_price = float(position.get('current_price', position.get('entry_price', 0)))
                    crypto_value += quantity * current_price
            
            total_portfolio = usdt_balance + crypto_value
            exposure_percent = (crypto_value / total_portfolio * 100) if total_portfolio > 0 else 0
            
            return crypto_value, total_portfolio, exposure_percent
            
        except Exception as e:
            print(f"❌ Erro ao calcular exposição: {e}")
            return 0.0, usdt_balance, 0.0
    
    def check_graduated_stop_loss(self, crypto_positions: List[Dict]) -> Tuple[bool, str, List[Dict]]:
        """Verifica stop loss escalonado para posições"""
        try:
            rules = self.rules['portfolio_management'].get('risk_management', {})
            
            if not rules.get('graduated_stop_loss', False):
                return False, "Stop loss escalonado desabilitado", []
            
            stop_levels = rules.get('stop_loss_levels', {})
            alert_level = stop_levels.get('alert', -5.0)
            partial_level = stop_levels.get('partial_exit', -10.0)
            full_level = stop_levels.get('full_exit', -20.0)
            
            actions_needed = []
            
            for position in crypto_positions:
                if position.get('status') != 'open':
                    continue
                    
                pnl_percent = float(position.get('pnl_percent', 0))
                symbol = position.get('symbol', 'UNKNOWN')
                
                if pnl_percent <= full_level:  # -20% ou pior
                    actions_needed.append({
                        'symbol': symbol,
                        'action': 'SELL_ALL',
                        'reason': f'Stop Loss Total: {pnl_percent:.1f}% ≤ {full_level}%',
                        'urgency': 'HIGH',
                        'percentage': 100
                    })
                elif pnl_percent <= partial_level:  # -10% a -20%
                    actions_needed.append({
                        'symbol': symbol,
                        'action': 'SELL_PARTIAL',
                        'reason': f'Stop Loss Parcial: {pnl_percent:.1f}% ≤ {partial_level}%',
                        'urgency': 'MEDIUM',
                        'percentage': 50
                    })
                elif pnl_percent <= alert_level:  # -5% a -10%
                    actions_needed.append({
                        'symbol': symbol,
                        'action': 'ALERT',
                        'reason': f'Alerta Stop Loss: {pnl_percent:.1f}% ≤ {alert_level}%',
                        'urgency': 'LOW',
                        'percentage': 0
                    })
            
            if actions_needed:
                high_urgency = [a for a in actions_needed if a['urgency'] == 'HIGH']
                if high_urgency:
                    return True, f"⚠️ STOP LOSS CRÍTICO: {len(high_urgency)} posições", actions_needed
                else:
                    return True, f"📊 Stop Loss Parcial: {len(actions_needed)} alertas", actions_needed
            
            return False, "✅ Todas posições dentro dos limites de risco", []
            
        except Exception as e:
            print(f"❌ Erro no stop loss escalonado: {e}")
            return False, f"❌ Erro no cálculo: {str(e)}", []
    
    def should_allow_purchase(self, 
                            usdt_balance: float, 
                            crypto_positions: List[Dict],
                            signal_confidence: float = 0.0,
                            current_time: datetime = None) -> Tuple[bool, str]:
        """
        Determina se uma compra deve ser permitida baseado nas regras MELHORADAS
        
        Returns:
            tuple: (pode_comprar, motivo)
        """
        if current_time is None:
            current_time = datetime.now()
        
        try:
            rules = self.rules['portfolio_management']
            
            # Usar exposição dinâmica baseada no mercado
            max_exposure = self.get_dynamic_exposure_limit(crypto_positions)
            exceptions = rules['exceptions']
            
            # Calcular exposição atual
            crypto_value, total_portfolio, current_exposure = self.get_portfolio_exposure(
                usdt_balance, crypto_positions
            )
            
            # Verificar se atingiu o limite de exposição
            if current_exposure >= max_exposure:
                
                # EXCEÇÃO 1: Portfólio vazio - permite até 5 posições
                if 'empty_portfolio_exception' in exceptions:
                    active_positions = len([p for p in crypto_positions if p.get('status') == 'open'])
                    if active_positions == 0 or (active_positions < rules.get('max_positions_exception', 5) and crypto_value < 50):
                        return True, f"✅ Exceção: Portfólio com poucas posições ({active_positions}) - permitida compra"
                
                # EXCEÇÃO 2: Alta confiança no sinal
                if 'high_confidence_exception' in exceptions and signal_confidence > 0.8:
                    return True, f"✅ Exceção: Sinal de alta confiança ({signal_confidence:.1%}) - permitida compra"
                
                # EXCEÇÃO 3: DCA limitado e seletivo
                if 'dca_exception' in exceptions:
                    dca_limits = rules.get('risk_management', {}).get('dca_limits', {})
                    max_dca_loss = dca_limits.get('max_dca_loss', -15.0)
                    only_top_coins = dca_limits.get('only_top_coins', True)
                    
                    # Lista de moedas TOP para DCA seguro
                    top_coins = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 
                               'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT']
                    
                    suitable_for_dca = []
                    for p in crypto_positions:
                        if (p.get('status') == 'open' and 
                            float(p.get('pnl_percent', 0)) < -2 and  # Perdendo mais que 2%
                            float(p.get('pnl_percent', 0)) > max_dca_loss):  # Mas não mais que limite
                            
                            # Se só TOP coins, verificar se está na lista
                            if only_top_coins:
                                if p.get('symbol') in top_coins:
                                    dca_count = p.get('dca_count', 0)
                                    max_additions = dca_limits.get('max_additions', 2)
                                    if dca_count < max_additions:
                                        suitable_for_dca.append(p)
                            else:
                                suitable_for_dca.append(p)
                    
                    if suitable_for_dca:
                        return True, f"✅ DCA Inteligente: {len(suitable_for_dca)} posições qualificadas"
                
                # EXCEÇÃO 4: Primeiras horas do dia
                if 'morning_exception' in exceptions:
                    current_hour = current_time.hour
                    if 6 <= current_hour <= 8:  # 06:00 às 08:00
                        return True, f"✅ Exceção: Horário matinal ({current_hour}h) - permitida compra"
                
                # Se não há exceções aplicáveis
                return False, f"🛑 Limite de exposição atingido: {current_exposure:.1f}% (máx: {max_exposure}%)"
            
            # Verificar horários especiais
            current_time_str = current_time.strftime('%H:%M')
            
            # Horário de apenas vendas
            sell_only = rules.get('sell_only_hours', {})
            if sell_only.get('start') and sell_only.get('end'):
                if sell_only['start'] <= current_time_str <= sell_only['end']:
                    return False, f"⏰ Horário de apenas vendas: {sell_only['start']} - {sell_only['end']}"
            
            # Verificar valor mínimo da posição (REMOVIDO - permite qualquer saldo)
            # min_position_value = rules.get('min_position_value', 10)
            # if usdt_balance < min_position_value:
            #     return False, f"💰 Saldo insuficiente: ${usdt_balance:.2f} < ${min_position_value}"
            
            # Se passou por todas as verificações
            return True, f"✅ Compra permitida - Exposição: {current_exposure:.1f}% (máx: {max_exposure}%)"
            
        except Exception as e:
            print(f"❌ Erro na verificação de compra: {e}")
            return False, f"❌ Erro interno: {str(e)}"
    
    def should_force_sell(self, 
                         usdt_balance: float, 
                         crypto_positions: List[Dict]) -> Tuple[bool, str, List[str]]:
        """
        Determina se deve forçar vendas baseado nas regras
        
        Returns:
            tuple: (deve_vender, motivo, lista_de_simbolos_para_vender)
        """
        try:
            rules = self.rules['portfolio_management']
            max_exposure = rules['max_crypto_exposure_percent']
            action = rules['exposure_action']
            
            # Calcular exposição atual
            crypto_value, total_portfolio, current_exposure = self.get_portfolio_exposure(
                usdt_balance, crypto_positions
            )
            
            # Se não atingiu o limite, não precisa vender
            if current_exposure < max_exposure:
                return False, "✅ Exposição dentro do limite", []
            
            symbols_to_sell = []
            
            if action == 'sell_all':
                # Vender todas as posições
                symbols_to_sell = [p['symbol'] for p in crypto_positions if p.get('status') == 'open']
                return True, f"🔥 Venda total - Exposição crítica: {current_exposure:.1f}%", symbols_to_sell
            
            elif action == 'rebalance':
                # Vender posições até voltar ao limite
                open_positions = sorted(
                    [p for p in crypto_positions if p.get('status') == 'open'],
                    key=lambda x: float(x.get('pnl_percent', 0))  # Vender primeiro as que estão perdendo menos
                )
                
                target_crypto_value = total_portfolio * (max_exposure / 100)
                value_to_sell = crypto_value - target_crypto_value
                
                current_sell_value = 0
                for position in open_positions:
                    if current_sell_value >= value_to_sell:
                        break
                    
                    position_value = float(position.get('quantity', 0)) * float(position.get('current_price', 0))
                    symbols_to_sell.append(position['symbol'])
                    current_sell_value += position_value
                
                return True, f"⚖️ Rebalanceamento - Vender ${value_to_sell:.2f}", symbols_to_sell
            
            else:  # stop_buying (padrão)
                return False, f"🛑 Apenas parar compras - Exposição: {current_exposure:.1f}%", []
            
        except Exception as e:
            print(f"❌ Erro na verificação de venda: {e}")
            return False, f"❌ Erro interno: {str(e)}", []
    
    def get_status_summary(self, usdt_balance: float, crypto_positions: List[Dict]) -> Dict:
        """Retorna um resumo do status do portfólio"""
        try:
            rules = self.rules['portfolio_management']
            crypto_value, total_portfolio, current_exposure = self.get_portfolio_exposure(
                usdt_balance, crypto_positions
            )
            
            max_exposure = rules['max_crypto_exposure_percent']
            active_positions = len([p for p in crypto_positions if p.get('status') == 'open'])
            
            # Determinar status
            if current_exposure >= max_exposure:
                status = "🛑 LIMITE ATINGIDO"
                color = "red"
            elif current_exposure >= (max_exposure * 0.8):
                status = "⚠️ PRÓXIMO DO LIMITE"
                color = "yellow"
            else:
                status = "🟢 OK"
                color = "green"
            
            return {
                'usdt_balance': usdt_balance,
                'crypto_value': crypto_value,
                'total_portfolio': total_portfolio,
                'current_exposure': current_exposure,
                'max_exposure': max_exposure,
                'active_positions': active_positions,
                'status': status,
                'status_color': color,
                'can_buy': self.should_allow_purchase(usdt_balance, crypto_positions)[0],
                'should_sell': self.should_force_sell(usdt_balance, crypto_positions)[0]
            }
            
        except Exception as e:
            print(f"❌ Erro no resumo do status: {e}")
            return {
                'usdt_balance': usdt_balance,
                'crypto_value': 0,
                'total_portfolio': usdt_balance,
                'current_exposure': 0,
                'max_exposure': 40,
                'active_positions': 0,
                'status': "❌ ERRO",
                'status_color': "red",
                'can_buy': False,
                'should_sell': False
            }

    def get_enhanced_analysis(self, symbol: str, price_data: List[Dict]) -> Dict:
        """
        Análise completa combinando indicadores avançados + ML + regras de portfólio
        
        Args:
            symbol: Par de negociação (ex: BTC/USDT)
            price_data: Lista de dados OHLCV
            
        Returns:
            Dict com análise completa
        """
        try:
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'basic_analysis': {},
                'advanced_indicators': {},
                'ml_forecast': {},
                'portfolio_recommendation': {},
                'combined_signals': {},
                'risk_assessment': {}
            }
            
            if not price_data or len(price_data) < 50:
                analysis['error'] = 'Dados insuficientes para análise completa'
                return analysis
            
            # Converter para DataFrame
            df = pd.DataFrame(price_data)
            
            # Garantir colunas necessárias
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                analysis['error'] = f'Colunas faltantes: {missing_cols}'
                return analysis
            
            # ===== ANÁLISE BÁSICA =====
            current_price = float(df['close'].iloc[-1])
            price_change_24h = ((current_price - float(df['close'].iloc[-24])) / float(df['close'].iloc[-24])) * 100 if len(df) >= 24 else 0
            
            analysis['basic_analysis'] = {
                'current_price': current_price,
                'price_change_24h': price_change_24h,
                'volume_24h': float(df['volume'].iloc[-24:].sum()) if len(df) >= 24 else 0,
                'high_24h': float(df['high'].iloc[-24:].max()) if len(df) >= 24 else current_price,
                'low_24h': float(df['low'].iloc[-24:].min()) if len(df) >= 24 else current_price
            }
            
            # ===== INDICADORES AVANÇADOS =====
            if ADVANCED_MODULES_AVAILABLE and self.advanced_indicators:
                try:
                    # Calcular todos os indicadores avançados
                    df_enhanced = self.advanced_indicators.calculate_all_indicators(df, symbol)
                    
                    # Obter força dos sinais
                    signal_strength = self.advanced_indicators.get_signal_strength(df_enhanced)
                    
                    # Obter recomendação técnica
                    tech_recommendation = self.advanced_indicators.get_trading_recommendation(df_enhanced, symbol)
                    
                    analysis['advanced_indicators'] = {
                        'signal_strength': signal_strength,
                        'technical_recommendation': tech_recommendation,
                        'indicators_calculated': len(df_enhanced.columns) - len(df.columns)
                    }
                    
                    print(f"✅ {symbol}: {len(df_enhanced.columns)} indicadores calculados")
                    
                except Exception as e:
                    analysis['advanced_indicators']['error'] = str(e)
                    print(f"⚠️ Erro em indicadores avançados para {symbol}: {e}")
            
            # ===== PREVISÃO ML =====
            if ADVANCED_MODULES_AVAILABLE and self.ml_forecaster:
                try:
                    # Preparar dados para Prophet
                    prophet_data = self.ml_forecaster.prepare_data_for_prophet(df, 'close')
                    
                    if len(prophet_data) >= 20:
                        # Treinar modelo ML
                        model_trained = self.ml_forecaster.train_model(prophet_data, symbol)
                        
                        if model_trained:
                            # Fazer previsão para próximas 24h
                            ml_prediction = self.ml_forecaster.predict_price(symbol, periods=24)
                            
                            if ml_prediction:
                                # Obter sinal ML
                                ml_signal = self.ml_forecaster.get_trading_signal_ml(symbol)
                                
                                analysis['ml_forecast'] = {
                                    'prediction_summary': ml_prediction['summary'],
                                    'trend_analysis': ml_prediction['trend_analysis'],
                                    'ml_signal': ml_signal,
                                    'confidence_intervals': ml_prediction['confidence_intervals']
                                }
                                
                                print(f"🤖 {symbol}: Previsão ML gerada - {ml_prediction['summary']['trend_direction']}")
                    else:
                        analysis['ml_forecast']['error'] = 'Dados insuficientes para ML'
                        
                except Exception as e:
                    analysis['ml_forecast']['error'] = str(e)
                    print(f"⚠️ Erro em ML para {symbol}: {e}")
            
            # ===== RECOMENDAÇÃO DE PORTFÓLIO =====
            try:
                # Aplicar regras de exposição
                market_trend = 'NEUTRAL'  # Simplificado para este exemplo
                max_exposure = self.get_dynamic_exposure_limit(market_trend)
                
                analysis['portfolio_recommendation'] = {
                    'market_trend': market_trend,
                    'max_exposure_allowed': max_exposure,
                    'position_size_recommendation': self._calculate_position_size(symbol, current_price, analysis),
                    'risk_level': self._assess_risk_level(analysis)
                }
                
            except Exception as e:
                analysis['portfolio_recommendation']['error'] = str(e)
            
            # ===== SINAIS COMBINADOS =====
            analysis['combined_signals'] = self._combine_all_signals(analysis)
            
            # ===== AVALIAÇÃO DE RISCO =====
            analysis['risk_assessment'] = self._comprehensive_risk_assessment(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"❌ Erro na análise completa de {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_position_size(self, symbol: str, current_price: float, analysis: Dict) -> Dict:
        """Calcula tamanho de posição recomendado baseado na análise completa"""
        try:
            base_size = 2.0  # 2% base
            
            # Ajustar baseado em sinais técnicos
            if 'advanced_indicators' in analysis and 'signal_strength' in analysis['advanced_indicators']:
                signals = analysis['advanced_indicators']['signal_strength']
                overall_strength = signals.get('overall', 50)
                
                if overall_strength > 75:
                    base_size *= 1.5  # Aumentar posição em sinais fortes
                elif overall_strength < 25:
                    base_size *= 0.5  # Reduzir posição em sinais fracos
            
            # Ajustar baseado em ML
            if 'ml_forecast' in analysis and 'ml_signal' in analysis['ml_forecast']:
                ml_confidence = analysis['ml_forecast']['ml_signal'].get('confidence', 50)
                if ml_confidence > 80:
                    base_size *= 1.3
                elif ml_confidence < 30:
                    base_size *= 0.7
            
            # Limitar por regras de portfólio
            max_per_crypto = self.rules.get('portfolio_management', {}).get('diversification', {}).get('max_per_crypto', 10)
            recommended_size = min(base_size, max_per_crypto)
            
            return {
                'recommended_percentage': recommended_size,
                'max_allowed_percentage': max_per_crypto,
                'reasoning': f'Base: {base_size:.1f}%, Limitado por diversificação: {max_per_crypto}%'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _assess_risk_level(self, analysis: Dict) -> str:
        """Avalia nível de risco da operação"""
        try:
            risk_factors = 0
            
            # Volatilidade
            if 'basic_analysis' in analysis:
                price_change = abs(analysis['basic_analysis'].get('price_change_24h', 0))
                if price_change > 10:
                    risk_factors += 2
                elif price_change > 5:
                    risk_factors += 1
            
            # Indicadores técnicos
            if 'advanced_indicators' in analysis and 'signal_strength' in analysis['advanced_indicators']:
                signals = analysis['advanced_indicators']['signal_strength']
                if signals.get('volatility', 50) > 80:
                    risk_factors += 1
            
            # ML uncertainty
            if 'ml_forecast' in analysis and 'ml_signal' in analysis['ml_forecast']:
                ml_confidence = analysis['ml_forecast']['ml_signal'].get('confidence', 50)
                if ml_confidence < 40:
                    risk_factors += 1
            
            if risk_factors >= 3:
                return 'HIGH'
            elif risk_factors >= 1:
                return 'MEDIUM'
            else:
                return 'LOW'
                
        except Exception:
            return 'UNKNOWN'
    
    def _combine_all_signals(self, analysis: Dict) -> Dict:
        """Combina todos os sinais para recomendação final"""
        try:
            signals = {
                'technical_score': 50,
                'ml_score': 50,
                'portfolio_score': 50,
                'combined_score': 50,
                'final_recommendation': 'WAIT',
                'confidence': 0
            }
            
            # Score técnico
            if 'advanced_indicators' in analysis and 'technical_recommendation' in analysis['advanced_indicators']:
                tech_rec = analysis['advanced_indicators']['technical_recommendation']
                action = tech_rec.get('action', 'WAIT')
                confidence = tech_rec.get('confidence', 0)
                
                if action == 'BUY':
                    signals['technical_score'] = 50 + (confidence / 2)
                elif action == 'SELL':
                    signals['technical_score'] = 50 - (confidence / 2)
            
            # Score ML
            if 'ml_forecast' in analysis and 'ml_signal' in analysis['ml_forecast']:
                ml_signal = analysis['ml_forecast']['ml_signal']
                action = ml_signal.get('action', 'WAIT')
                confidence = ml_signal.get('confidence', 0)
                
                if action == 'BUY':
                    signals['ml_score'] = 50 + (confidence / 2)
                elif action == 'SELL':
                    signals['ml_score'] = 50 - (confidence / 2)
            
            # Score de portfólio (baseado em risco)
            if 'portfolio_recommendation' in analysis:
                risk_level = analysis['portfolio_recommendation'].get('risk_level', 'MEDIUM')
                if risk_level == 'LOW':
                    signals['portfolio_score'] = 70
                elif risk_level == 'HIGH':
                    signals['portfolio_score'] = 30
            
            # Score combinado
            scores = [signals['technical_score'], signals['ml_score'], signals['portfolio_score']]
            signals['combined_score'] = sum(scores) / len(scores)
            
            # Recomendação final
            if signals['combined_score'] > 65:
                signals['final_recommendation'] = 'BUY'
                signals['confidence'] = min(95, signals['combined_score'])
            elif signals['combined_score'] < 35:
                signals['final_recommendation'] = 'SELL'
                signals['confidence'] = min(95, 100 - signals['combined_score'])
            else:
                signals['final_recommendation'] = 'WAIT'
                signals['confidence'] = 100 - abs(signals['combined_score'] - 50) * 2
            
            return signals
            
        except Exception as e:
            return {'error': str(e)}
    
    def _comprehensive_risk_assessment(self, analysis: Dict) -> Dict:
        """Avaliação completa de risco"""
        try:
            risk_assessment = {
                'overall_risk': 'MEDIUM',
                'risk_factors': [],
                'mitigation_strategies': [],
                'max_recommended_exposure': 5.0
            }
            
            # Analisar fatores de risco
            factors = []
            
            # Volatilidade de preço
            if 'basic_analysis' in analysis:
                price_change = abs(analysis['basic_analysis'].get('price_change_24h', 0))
                if price_change > 15:
                    factors.append('EXTREME_VOLATILITY')
                elif price_change > 10:
                    factors.append('HIGH_VOLATILITY')
            
            # Sinais técnicos conflitantes
            if 'combined_signals' in analysis:
                combined_score = analysis['combined_signals'].get('combined_score', 50)
                if 40 <= combined_score <= 60:
                    factors.append('MIXED_SIGNALS')
            
            # Baixa confiança ML
            if 'ml_forecast' in analysis and 'ml_signal' in analysis['ml_forecast']:
                ml_confidence = analysis['ml_forecast']['ml_signal'].get('confidence', 50)
                if ml_confidence < 30:
                    factors.append('LOW_ML_CONFIDENCE')
            
            risk_assessment['risk_factors'] = factors
            
            # Determinar nível de risco geral
            if len(factors) >= 2:
                risk_assessment['overall_risk'] = 'HIGH'
                risk_assessment['max_recommended_exposure'] = 2.0
            elif len(factors) == 1:
                risk_assessment['overall_risk'] = 'MEDIUM'
                risk_assessment['max_recommended_exposure'] = 5.0
            else:
                risk_assessment['overall_risk'] = 'LOW'
                risk_assessment['max_recommended_exposure'] = 8.0
            
            # Estratégias de mitigação
            mitigation = []
            if 'HIGH_VOLATILITY' in factors or 'EXTREME_VOLATILITY' in factors:
                mitigation.append('Usar stop-loss mais apertado')
                mitigation.append('Reduzir tamanho da posição')
            
            if 'MIXED_SIGNALS' in factors:
                mitigation.append('Aguardar confirmação de tendência')
                mitigation.append('Considerar DCA em pequenas parcelas')
            
            if 'LOW_ML_CONFIDENCE' in factors:
                mitigation.append('Dar mais peso à análise técnica')
                mitigation.append('Monitorar indicadores de momentum')
            
            risk_assessment['mitigation_strategies'] = mitigation
            
            return risk_assessment
            
        except Exception as e:
            return {'error': str(e)}

    def print_enhanced_analysis(self, analysis: Dict):
        """Imprime análise aprimorada de forma organizada"""
        try:
            symbol = analysis.get('symbol', 'CRYPTO')
            print(f"\n🚀 === ANÁLISE COMPLETA: {symbol} ===")
            
            if 'error' in analysis:
                print(f"❌ {analysis['error']}")
                return
            
            # Análise básica
            if 'basic_analysis' in analysis:
                basic = analysis['basic_analysis']
                price = basic.get('current_price', 0)
                change = basic.get('price_change_24h', 0)
                change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                
                print(f"💰 Preço: ${price:.4f} ({change_emoji} {change:+.2f}%)")
            
            # Indicadores técnicos
            if 'advanced_indicators' in analysis and 'signal_strength' in analysis['advanced_indicators']:
                signals = analysis['advanced_indicators']['signal_strength']
                tech_rec = analysis['advanced_indicators'].get('technical_recommendation', {})
                
                print(f"📊 Análise Técnica:")
                print(f"   Tendência: {signals.get('trend', 0):.0f}/100")
                print(f"   Momentum: {signals.get('momentum', 0):.0f}/100")
                print(f"   Volume: {signals.get('volume', 0):.0f}/100")
                print(f"   Recomendação: {tech_rec.get('action', 'WAIT')} ({tech_rec.get('confidence', 0):.0f}%)")
            
            # Previsão ML
            if 'ml_forecast' in analysis and 'prediction_summary' in analysis['ml_forecast']:
                ml_summary = analysis['ml_forecast']['prediction_summary']
                ml_signal = analysis['ml_forecast'].get('ml_signal', {})
                
                trend_direction = ml_summary.get('trend_direction', 'NEUTRAL')
                trend_emoji = "🚀" if trend_direction == 'BULLISH' else "📉" if trend_direction == 'BEARISH' else "➡️"
                
                print(f"🤖 Previsão ML:")
                print(f"   Tendência: {trend_emoji} {trend_direction}")
                print(f"   Mudança esperada: {ml_summary.get('total_change_percent', 0):+.2f}%")
                print(f"   Recomendação ML: {ml_signal.get('action', 'WAIT')} ({ml_signal.get('confidence', 0):.0f}%)")
            
            # Sinais combinados
            if 'combined_signals' in analysis:
                combined = analysis['combined_signals']
                final_rec = combined.get('final_recommendation', 'WAIT')
                confidence = combined.get('confidence', 0)
                
                rec_emoji = "🟢" if final_rec == "BUY" else "🔴" if final_rec == "SELL" else "🟡"
                print(f"🎯 RECOMENDAÇÃO FINAL: {rec_emoji} {final_rec} ({confidence:.0f}%)")
            
            # Avaliação de risco
            if 'risk_assessment' in analysis:
                risk = analysis['risk_assessment']
                risk_level = risk.get('overall_risk', 'MEDIUM')
                max_exposure = risk.get('max_recommended_exposure', 5)
                
                risk_emoji = "🟢" if risk_level == "LOW" else "🟡" if risk_level == "MEDIUM" else "🔴"
                print(f"⚠️ Risco: {risk_emoji} {risk_level} (Max: {max_exposure:.1f}%)")
                
                factors = risk.get('risk_factors', [])
                if factors:
                    print(f"   Fatores: {', '.join(factors)}")
            
            print("=" * 45)
            
        except Exception as e:
            print(f"❌ Erro ao imprimir análise: {e}")

# ========================================
# EXEMPLO DE USO
# ========================================

if __name__ == "__main__":
    # Teste do sistema
    pm = PortfolioManager()
    
    # Simular posições
    mock_positions = [
        {
            'symbol': 'BTCUSDT',
            'quantity': 0.001,
            'entry_price': 45000,
            'current_price': 46000,
            'status': 'open',
            'pnl_percent': 2.2
        },
        {
            'symbol': 'ETHUSDT', 
            'quantity': 0.1,
            'entry_price': 3000,
            'current_price': 2900,
            'status': 'open',
            'pnl_percent': -3.3
        }
    ]
    
    usdt_balance = 100.0
    
    # Teste das funções
    print("🧪 Teste do Portfolio Manager")
    print("="*50)
    
    status = pm.get_status_summary(usdt_balance, mock_positions)
    print(f"💰 Saldo USDT: ${status['usdt_balance']:.2f}")
    print(f"💎 Valor Crypto: ${status['crypto_value']:.2f}")
    print(f"📊 Exposição: {status['current_exposure']:.1f}%")
    print(f"🎯 Status: {status['status']}")
    
    can_buy, buy_reason = pm.should_allow_purchase(usdt_balance, mock_positions, 0.9)
    print(f"\n🛒 Pode comprar: {can_buy}")
    print(f"📝 Motivo: {buy_reason}")
    
    should_sell, sell_reason, symbols = pm.should_force_sell(usdt_balance, mock_positions)
    print(f"\n💸 Deve vender: {should_sell}")
    print(f"📝 Motivo: {sell_reason}")
    if symbols:
        print(f"🎯 Símbolos: {', '.join(symbols)}")