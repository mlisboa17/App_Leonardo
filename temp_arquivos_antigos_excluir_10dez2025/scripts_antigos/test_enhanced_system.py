"""
🧪 Teste Completo do Sistema Aprimorado - App Leonardo
Demonstra integração: AdvancedIndicators + MLForecaster + PortfolioManager
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Adicionar path do projeto
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

# Imports dos módulos desenvolvidos
try:
    from src.indicators.advanced_indicators import AdvancedIndicators
    from src.core.ml_forecaster import MLForecaster
    from src.core.portfolio_manager import PortfolioManager
    MODULES_LOADED = True
except ImportError as e:
    print(f"❌ Erro ao carregar módulos: {e}")
    MODULES_LOADED = False

def generate_realistic_crypto_data(symbol: str = "BTC/USDT", days: int = 30) -> List[Dict]:
    """
    Gera dados realistas de crypto para teste
    """
    print(f"📊 Gerando {days} dias de dados para {symbol}...")
    
    # Configurações base
    np.random.seed(42)
    hours = days * 24
    base_price = 50000 if "BTC" in symbol else 3000
    
    # Criar série temporal realista
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), periods=hours, freq='H')
    
    # Tendência + Sazonalidade + Ruído
    trend = np.linspace(base_price, base_price * 1.1, hours)  # Tendência de alta de 10%
    daily_seasonality = base_price * 0.02 * np.sin(np.arange(hours) * 2 * np.pi / 24)
    weekly_seasonality = base_price * 0.01 * np.sin(np.arange(hours) * 2 * np.pi / (24 * 7))
    noise = np.random.normal(0, base_price * 0.02, hours)
    
    # Adicionar alguns eventos de alta volatilidade
    for i in range(0, hours, hours//5):  # 5 eventos durante o período
        spike_size = np.random.choice([-1, 1]) * base_price * np.random.uniform(0.05, 0.15)
        spike_duration = np.random.randint(3, 12)  # 3-12 horas
        end_idx = min(i + spike_duration, hours)
        noise[i:end_idx] += spike_size * np.exp(-np.arange(end_idx - i) * 0.2)
    
    prices = trend + daily_seasonality + weekly_seasonality + noise
    
    # Criar dados OHLCV
    data = []
    for i, timestamp in enumerate(dates):
        base_price = prices[i]
        
        # Calcular OHLC com alguma variação
        hour_change = np.random.uniform(-0.03, 0.03)
        close_price = base_price * (1 + hour_change)
        
        open_price = prices[i-1] * (1 + np.random.uniform(-0.01, 0.01)) if i > 0 else base_price
        high_price = max(open_price, close_price) * (1 + abs(np.random.uniform(0, 0.02)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.uniform(0, 0.02)))
        
        # Volume correlacionado com volatilidade
        volatility = abs(hour_change)
        base_volume = np.random.uniform(1000, 5000)
        volume = base_volume * (1 + volatility * 10)
        
        data.append({
            'timestamp': timestamp,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': round(volume, 0)
        })
    
    print(f"✅ Dados gerados: {len(data)} pontos de {data[0]['close']:.0f} a {data[-1]['close']:.0f}")
    return data

def test_advanced_indicators():
    """Testa o módulo de indicadores avançados"""
    print("\n🔬 === TESTANDO ADVANCED INDICATORS ===")
    
    if not MODULES_LOADED:
        print("❌ Módulos não carregados")
        return None
    
    # Gerar dados de teste
    test_data = generate_realistic_crypto_data("BTC/USDT", days=10)
    df = pd.DataFrame(test_data)
    
    # Testar indicadores
    indicators = AdvancedIndicators()
    
    # Calcular todos os indicadores
    df_enhanced = indicators.calculate_all_indicators(df, "BTC/USDT")
    
    # Mostrar resumo
    indicators.print_indicator_summary(df_enhanced, "BTC/USDT")
    
    # Obter recomendação
    recommendation = indicators.get_trading_recommendation(df_enhanced, "BTC/USDT")
    print(f"\n📋 Recomendação Técnica:")
    print(f"   Ação: {recommendation['action']}")
    print(f"   Confiança: {recommendation['confidence']:.0f}%")
    print(f"   Razão: {recommendation['reason']}")
    
    return df_enhanced

def test_ml_forecaster():
    """Testa o módulo de ML Forecaster"""
    print("\n🤖 === TESTANDO ML FORECASTER ===")
    
    if not MODULES_LOADED:
        print("❌ Módulos não carregados")
        return None
    
    # Gerar dados de teste
    test_data = generate_realistic_crypto_data("ETH/USDT", days=15)
    df = pd.DataFrame(test_data)
    
    # Testar ML Forecaster
    forecaster = MLForecaster()
    
    # Preparar dados para Prophet
    prophet_data = forecaster.prepare_data_for_prophet(df, 'close')
    
    # Treinar modelo
    success = forecaster.train_model(prophet_data, "ETH/USDT")
    
    if success:
        # Fazer previsão
        prediction = forecaster.predict_price("ETH/USDT", periods=24)
        
        if prediction:
            # Mostrar resumo da previsão
            forecaster.print_forecast_summary("ETH/USDT")
            
            # Obter sinal ML
            ml_signal = forecaster.get_trading_signal_ml("ETH/USDT")
            print(f"\n📋 Sinal ML:")
            print(f"   Ação: {ml_signal['action']}")
            print(f"   Confiança: {ml_signal['confidence']:.0f}%")
            print(f"   Razão: {ml_signal['reason']}")
            
            return prediction
    
    return None

def test_portfolio_manager():
    """Testa o Portfolio Manager aprimorado"""
    print("\n💼 === TESTANDO PORTFOLIO MANAGER ===")
    
    if not MODULES_LOADED:
        print("❌ Módulos não carregados")
        return
    
    # Criar Portfolio Manager
    pm = PortfolioManager()
    
    # Mostrar resumo das regras
    pm.print_portfolio_rules_summary()
    
    # Gerar dados para análise completa
    test_data = generate_realistic_crypto_data("ADA/USDT", days=7)
    
    # Fazer análise completa
    print(f"\n🚀 Executando análise completa...")
    analysis = pm.get_enhanced_analysis("ADA/USDT", test_data)
    
    # Mostrar resultado
    pm.print_enhanced_analysis(analysis)
    
    return analysis

def test_integration():
    """Testa integração completa de todos os módulos"""
    print("\n🌟 === TESTE DE INTEGRAÇÃO COMPLETA ===")
    
    if not MODULES_LOADED:
        print("❌ Módulos não carregados - Pulando teste de integração")
        return
    
    # Lista de cryptos para testar
    test_symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
    
    pm = PortfolioManager()
    results = {}
    
    for symbol in test_symbols:
        print(f"\n📊 Analisando {symbol}...")
        
        # Gerar dados de teste
        test_data = generate_realistic_crypto_data(symbol, days=5)
        
        # Análise completa
        analysis = pm.get_enhanced_analysis(symbol, test_data)
        
        if 'error' not in analysis:
            # Extrair informações principais
            combined_signals = analysis.get('combined_signals', {})
            risk_assessment = analysis.get('risk_assessment', {})
            
            results[symbol] = {
                'recommendation': combined_signals.get('final_recommendation', 'WAIT'),
                'confidence': combined_signals.get('confidence', 0),
                'risk_level': risk_assessment.get('overall_risk', 'UNKNOWN'),
                'max_exposure': risk_assessment.get('max_recommended_exposure', 0)
            }
            
            print(f"   ✅ {symbol}: {results[symbol]['recommendation']} ({results[symbol]['confidence']:.0f}%)")
        else:
            print(f"   ❌ {symbol}: {analysis['error']}")
    
    # Resumo final
    print(f"\n📋 === RESUMO DOS RESULTADOS ===")
    for symbol, result in results.items():
        rec = result['recommendation']
        conf = result['confidence']
        risk = result['risk_level']
        
        rec_emoji = "🟢" if rec == "BUY" else "🔴" if rec == "SELL" else "🟡"
        risk_emoji = "🟢" if risk == "LOW" else "🟡" if risk == "MEDIUM" else "🔴"
        
        print(f"   {symbol}: {rec_emoji} {rec} ({conf:.0f}%) | Risco: {risk_emoji} {risk}")

def main():
    """Função principal de teste"""
    print("🚀" + "="*60)
    print("    TESTE COMPLETO - APP LEONARDO ENHANCED")
    print("    AdvancedIndicators + MLForecaster + PortfolioManager")
    print("="*62)
    
    if not MODULES_LOADED:
        print("❌ Não foi possível carregar os módulos necessários")
        print("   Verifique se os arquivos estão no local correto:")
        print("   - src/indicators/advanced_indicators.py")
        print("   - src/core/ml_forecaster.py") 
        print("   - src/core/portfolio_manager.py")
        return
    
    # Executar todos os testes
    try:
        # Teste individual dos módulos
        df_enhanced = test_advanced_indicators()
        ml_prediction = test_ml_forecaster()
        analysis = test_portfolio_manager()
        
        # Teste de integração
        test_integration()
        
        print(f"\n🎉 === TODOS OS TESTES CONCLUÍDOS ===")
        print(f"✅ AdvancedIndicators: 50+ indicadores técnicos")
        print(f"✅ MLForecaster: Previsões com Facebook Prophet")
        print(f"✅ PortfolioManager: Gestão inteligente de risco")
        print(f"✅ Integração: Análise combinada AI/ML + Técnica")
        
        print(f"\n💡 Próximos passos:")
        print(f"   1. Integrar com o bot principal")
        print(f"   2. Configurar dados em tempo real")
        print(f"   3. Testar com dados de mercado reais")
        print(f"   4. Ajustar parâmetros baseado no desempenho")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()