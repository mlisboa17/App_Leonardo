"""
Teste rápido do SmartStrategy
"""
import sys
sys.path.insert(0, '.')

from src.strategies.smart_strategy import SmartStrategy

def test():
    print("=" * 50)
    print("TESTE DO SMART STRATEGY")
    print("=" * 50)
    
    # Criar instância
    strategy = SmartStrategy()
    print("✅ SmartStrategy carregado!")
    
    # Verificar perfis
    print(f"\n📊 Perfis carregados: {len(strategy.profiles)}")
    for symbol, profile in strategy.profiles.items():
        print(f"  {symbol}: compra<{profile['buy_rsi']:.1f}, venda>{profile['sell_rsi']:.1f}")
    
    # Verificar métodos
    print("\n🔧 Métodos disponíveis:")
    methods = ['should_buy', 'should_sell', '_is_trend_up', '_count_reversal_signals', 'update_trade_stats']
    for method in methods:
        has_method = hasattr(strategy, method)
        status = "✅" if has_method else "❌"
        print(f"  {status} {method}")
    
    # Verificar urgência
    print(f"\n⏰ Sistema de urgência:")
    for symbol, last_trade in strategy.last_trade_time.items():
        print(f"  {symbol}: última operação = {last_trade}")
    
    print("\n" + "=" * 50)
    print("SISTEMA PRONTO PARA OPERAR!")
    print("=" * 50)

if __name__ == "__main__":
    test()
