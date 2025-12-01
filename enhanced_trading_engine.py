"""
🚀 Enhanced Trading Engine - App Leonardo
Integra AdvancedIndicators + MLForecaster com o bot principal
"""
import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

# Adicionar paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'src'))

class EnhancedTradingEngine:
    """Engine de trading aprimorado com AI/ML"""
    
    def __init__(self):
        """Inicializa o engine aprimorado"""
        self.enhanced_mode = False
        self.advanced_indicators = None
        self.ml_forecaster = None
        self.portfolio_manager = None
        
        # Tentar carregar módulos avançados
        self._load_advanced_modules()
    
    def _load_advanced_modules(self):
        """Carrega módulos avançados se disponíveis"""
        try:
            from src.indicators.advanced_indicators import AdvancedIndicators
            from src.core.ml_forecaster import MLForecaster
            from src.core.portfolio_manager import PortfolioManager
            
            self.advanced_indicators = AdvancedIndicators()
            self.ml_forecaster = MLForecaster()
            self.portfolio_manager = PortfolioManager()
            self.enhanced_mode = True
            
            print("🚀 Enhanced Trading Engine: AI/ML Ativado")
            
        except ImportError as e:
            print(f"⚠️ Modo básico: {e}")
            self.enhanced_mode = False
    
    def analyze_symbol(self, symbol: str, ohlcv_data: List[Dict]) -> Dict:
        """
        Análise completa de um símbolo
        
        Args:
            symbol: Par de trading (ex: BTCUSDT)
            ohlcv_data: Lista com dados OHLCV
            
        Returns:
            Dict com análise completa
        """
        if not self.enhanced_mode:
            return self._basic_analysis(symbol, ohlcv_data)
        
        try:
            # Usar análise aprimorada do Portfolio Manager
            analysis = self.portfolio_manager.get_enhanced_analysis(symbol, ohlcv_data)
            
            # Adicionar timestamp e versão
            analysis['engine_version'] = 'enhanced_v1.0'
            analysis['analysis_timestamp'] = datetime.now().isoformat()
            
            return analysis
            
        except Exception as e:
            print(f"❌ Erro na análise aprimorada de {symbol}: {e}")
            return self._basic_analysis(symbol, ohlcv_data)
    
    def _basic_analysis(self, symbol: str, ohlcv_data: List[Dict]) -> Dict:
        """Análise básica como fallback"""
        if not ohlcv_data:
            return {'error': 'Sem dados disponíveis'}
        
        latest = ohlcv_data[-1]
        
        return {
            'symbol': symbol,
            'engine_version': 'basic_v1.0',
            'analysis_timestamp': datetime.now().isoformat(),
            'basic_analysis': {
                'current_price': latest.get('close', 0),
                'volume': latest.get('volume', 0),
                'recommendation': 'WAIT',
                'confidence': 50
            },
            'enhanced_features': False
        }
    
    def get_portfolio_recommendation(self, balance: float, positions: List[Dict]) -> Dict:
        """
        Recomendação de portfólio baseada em regras aprimoradas
        
        Args:
            balance: Saldo em USDT
            positions: Lista de posições abertas
            
        Returns:
            Dict com recomendação
        """
        if not self.enhanced_mode or not self.portfolio_manager:
            return {
                'can_trade': True,
                'max_position_size': 5.0,
                'reason': 'Análise básica'
            }
        
        try:
            # Usar regras aprimoradas do Portfolio Manager
            status = self.portfolio_manager.get_status_summary(balance, positions)
            can_buy, buy_reason = self.portfolio_manager.should_allow_purchase(balance, positions, 5.0)
            should_sell, sell_reason, sell_symbols = self.portfolio_manager.should_force_sell(balance, positions)
            
            return {
                'portfolio_status': status,
                'can_buy': can_buy,
                'buy_reason': buy_reason,
                'should_sell': should_sell,
                'sell_reason': sell_reason,
                'sell_symbols': sell_symbols,
                'enhanced_rules': True
            }
            
        except Exception as e:
            print(f"❌ Erro na recomendação de portfólio: {e}")
            return {
                'can_trade': True,
                'max_position_size': 5.0,
                'reason': f'Erro: {str(e)}'
            }
    
    def get_signal_summary(self, analyses: Dict[str, Dict]) -> Dict:
        """
        Resumo de sinais de múltiplos símbolos
        
        Args:
            analyses: Dict com análises de múltiplos símbolos
            
        Returns:
            Dict com resumo geral
        """
        summary = {
            'total_symbols': len(analyses),
            'buy_signals': 0,
            'sell_signals': 0,
            'wait_signals': 0,
            'high_confidence': 0,
            'recommendations': [],
            'market_sentiment': 'NEUTRAL'
        }
        
        if not analyses:
            return summary
        
        for symbol, analysis in analyses.items():
            if 'error' in analysis:
                continue
            
            # Extrair recomendação
            recommendation = 'WAIT'
            confidence = 0
            
            if self.enhanced_mode and 'combined_signals' in analysis:
                combined = analysis['combined_signals']
                recommendation = combined.get('final_recommendation', 'WAIT')
                confidence = combined.get('confidence', 0)
            elif 'basic_analysis' in analysis:
                recommendation = analysis['basic_analysis'].get('recommendation', 'WAIT')
                confidence = analysis['basic_analysis'].get('confidence', 0)
            
            # Contar sinais
            if recommendation == 'BUY':
                summary['buy_signals'] += 1
            elif recommendation == 'SELL':
                summary['sell_signals'] += 1
            else:
                summary['wait_signals'] += 1
            
            # Contar alta confiança
            if confidence > 70:
                summary['high_confidence'] += 1
            
            # Adicionar à lista de recomendações
            summary['recommendations'].append({
                'symbol': symbol,
                'recommendation': recommendation,
                'confidence': confidence
            })
        
        # Determinar sentimento geral do mercado
        if summary['buy_signals'] > summary['sell_signals'] * 1.5:
            summary['market_sentiment'] = 'BULLISH'
        elif summary['sell_signals'] > summary['buy_signals'] * 1.5:
            summary['market_sentiment'] = 'BEARISH'
        
        return summary
    
    def is_enhanced_mode(self) -> bool:
        """Retorna se está em modo aprimorado"""
        return self.enhanced_mode
    
    def get_engine_info(self) -> Dict:
        """Informações sobre o engine"""
        return {
            'enhanced_mode': self.enhanced_mode,
            'version': '1.0',
            'features': {
                'advanced_indicators': self.enhanced_mode and self.advanced_indicators is not None,
                'ml_forecasting': self.enhanced_mode and self.ml_forecaster is not None,
                'portfolio_management': self.enhanced_mode and self.portfolio_manager is not None
            },
            'indicator_count': 50 if self.enhanced_mode else 0,
            'ml_model': 'Facebook Prophet' if self.enhanced_mode else None
        }

# ========================================
# INTEGRAÇÃO COM DASHBOARD
# ========================================

def create_enhanced_analysis_endpoint(app, engine):
    """Cria endpoint para análise aprimorada no dashboard"""
    
    @app.route('/api/enhanced_analysis/<symbol>')
    def enhanced_analysis(symbol):
        """Endpoint para análise aprimorada de um símbolo"""
        try:
            # Aqui você pegaria dados reais da exchange
            # Por enquanto, vou simular
            mock_data = [
                {
                    'timestamp': datetime.now(),
                    'open': 50000,
                    'high': 51000,
                    'low': 49500,
                    'close': 50500,
                    'volume': 1000
                }
            ] * 100  # Simular 100 períodos
            
            analysis = engine.analyze_symbol(symbol, mock_data)
            
            return {
                'success': True,
                'data': analysis
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @app.route('/api/engine_status')
    def engine_status():
        """Status do engine aprimorado"""
        return {
            'success': True,
            'data': engine.get_engine_info()
        }
    
    return app

# ========================================
# TESTE RÁPIDO
# ========================================

if __name__ == "__main__":
    print("🧪 Testando Enhanced Trading Engine...")
    
    # Criar engine
    engine = EnhancedTradingEngine()
    
    # Mostrar informações
    info = engine.get_engine_info()
    print(f"\n📊 Engine Info:")
    print(f"   Modo Aprimorado: {'✅' if info['enhanced_mode'] else '❌'}")
    print(f"   Indicadores Avançados: {'✅' if info['features']['advanced_indicators'] else '❌'}")
    print(f"   ML Forecasting: {'✅' if info['features']['ml_forecasting'] else '❌'}")
    print(f"   Portfolio Management: {'✅' if info['features']['portfolio_management'] else '❌'}")
    
    if info['enhanced_mode']:
        print(f"   📈 {info['indicator_count']} indicadores técnicos")
        print(f"   🤖 Modelo ML: {info['ml_model']}")
        
        # Teste básico com dados simulados
        mock_data = []
        base_price = 50000
        
        for i in range(50):
            price = base_price + (i * 10) + (i % 10 - 5) * 100
            mock_data.append({
                'timestamp': datetime.now(),
                'open': price,
                'high': price * 1.01,
                'low': price * 0.99,
                'close': price,
                'volume': 1000 + i * 10
            })
        
        # Teste de análise
        print(f"\n🔬 Testando análise de BTC/USDT...")
        analysis = engine.analyze_symbol('BTC/USDT', mock_data)
        
        if 'error' not in analysis:
            print(f"   ✅ Análise gerada com sucesso")
            
            if 'combined_signals' in analysis:
                combined = analysis['combined_signals']
                print(f"   🎯 Recomendação: {combined.get('final_recommendation', 'WAIT')}")
                print(f"   📊 Confiança: {combined.get('confidence', 0):.0f}%")
        else:
            print(f"   ❌ Erro: {analysis['error']}")
    
    print(f"\n🔥 Enhanced Trading Engine pronto para integração!")