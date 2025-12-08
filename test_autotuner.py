"""
🧪 TESTE DO SISTEMA AUTO-TUNER + METAS - R7 TRADING BOT API
==============================================
Verifica se todos os componentes estão funcionando:
1. Auto-Tuner (ajuste dinâmico)
2. Market Analyzer (análise de mercado)
3. Goal Monitor (metas mensais)

Execute: python test_autotuner.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime


def print_header(text: str):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def test_exchange_connection():
    """Testa conexão com a Binance"""
    print_header("📡 TESTE DE CONEXÃO")
    
    try:
        from src.core.exchange_client import ExchangeClient
        exchange = ExchangeClient()
        
        # Testa saldo
        balance = exchange.fetch_balance()
        usdt = balance.get('USDT', {}).get('free', 0)
        print(f"✅ Conexão OK!")
        print(f"   Saldo USDT: ${usdt:.2f}")
        
        return exchange
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return None


def test_market_analyzer(exchange):
    """Testa o analisador de mercado"""
    print_header("📊 TESTE DO MARKET ANALYZER")
    
    try:
        from src.ai.market_analyzer import MarketAnalyzer
        
        analyzer = MarketAnalyzer(exchange)
        conditions = analyzer.analyze_sync()
        
        print(f"✅ Market Analyzer OK!")
        print(f"   BTC: ${conditions.btc_price:,.2f}")
        print(f"   24h: {conditions.btc_change_24h:+.2f}%")
        print(f"   Tendência: {conditions.trend}")
        print(f"   Volatilidade: {conditions.volatility_level} ({conditions.volatility:.2f}%)")
        print(f"   Volume: {conditions.volume_ratio:.2f}x média")
        print(f"   Ação Recomendada: {conditions.recommended_action}")
        
        print("\n" + analyzer.get_status_report())
        
        return analyzer
        
    except Exception as e:
        print(f"❌ Erro no Market Analyzer: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_autotuner(exchange):
    """Testa o auto-tuner"""
    print_header("🎛️ TESTE DO AUTO-TUNER")
    
    try:
        from src.ai.auto_tuner import AutoTuner
        
        tuner = AutoTuner(exchange, "config/bots_config.yaml")
        
        print("✅ AutoTuner inicializado!")
        print("   Fazendo primeiro ajuste...")
        
        result = tuner.tune()
        
        print(f"\n📈 Resultado do ajuste:")
        print(f"   Tendência: {result['market']['trend']}")
        print(f"   Volatilidade: {result['market']['volatility']}")
        print(f"   Ação: {result['market']['action']}")
        
        if result['changes']:
            print(f"\n🔧 Mudanças aplicadas:")
            for bot, changes in result['changes'].items():
                print(f"   {bot}:")
                for param, value in changes.items():
                    print(f"      - {param}: {value}")
        else:
            print(f"\n✅ Nenhum ajuste necessário (configs já otimizadas)")
        
        return tuner
        
    except Exception as e:
        print(f"❌ Erro no AutoTuner: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_goal_monitor():
    """Testa o monitor de metas"""
    print_header("🎯 TESTE DO GOAL MONITOR")
    
    try:
        from src.ai.goal_monitor import GoalMonitor
        
        monitor = GoalMonitor(capital=1000)
        
        print("✅ Goal Monitor inicializado!")
        
        # Mostra progresso atual
        daily = monitor.get_daily_progress()
        monthly = monitor.get_monthly_progress()
        
        print(f"\n📅 Progresso Diário ({daily['date']}):")
        print(f"   PnL Hoje: ${daily['pnl']:.2f}")
        for goal_key, goal_data in daily['goals'].items():
            status = "✅" if goal_data['achieved'] else f"{goal_data['progress']:.0f}%"
            print(f"   {goal_data['emoji']} {goal_data['name']}: ${goal_data['target']:.2f}/dia [{status}]")
        
        print(f"\n📆 Progresso Mensal ({monthly['month']}):")
        print(f"   PnL Mês: ${monthly['pnl']:.2f}")
        for goal_key, goal_data in monthly['goals'].items():
            status = "✅" if goal_data['achieved'] else f"{goal_data['progress']:.0f}%"
            proj = "📈" if goal_data['on_track'] else "📉"
            print(f"   {goal_data['emoji']} {goal_data['name']}: ${goal_data['target']}/mês [{status}] {proj}")
        
        print("\n" + monitor.get_status_report())
        
        return monitor
        
    except Exception as e:
        print(f"❌ Erro no Goal Monitor: {e}")
        import traceback
        traceback.print_exc()
        return None


def show_current_config():
    """Mostra configuração atual"""
    print_header("⚙️ CONFIGURAÇÃO ATUAL")
    
    try:
        import yaml
        
        with open("config/bots_config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        global_config = config.get('global', {})
        
        # Metas
        monthly_targets = global_config.get('monthly_targets', {})
        print("\n🎯 METAS MENSAIS:")
        print(f"   🏆 SUPER-META: ${monthly_targets.get('super_meta', 120)}/mês")
        print(f"   ✅ META NORMAL: ${monthly_targets.get('meta_normal', 100)}/mês")
        print(f"   📊 MÉDIA: ${monthly_targets.get('media', 80)}/mês")
        print(f"   ⚠️ MÍNIMO: ${monthly_targets.get('minimo', 60)}/mês")
        
        # Auto-tuner config
        tuner_config = global_config.get('auto_tuner', {})
        print(f"\n🎛️ AUTO-TUNER:")
        print(f"   Habilitado: {'✅' if tuner_config.get('enabled') else '❌'}")
        print(f"   Intervalo: {tuner_config.get('adjustment_interval', 300)}s")
        
        # Ajustes por volatilidade
        vol_adj = tuner_config.get('volatility_adjustments', {})
        print("\n   📊 Ajustes por Volatilidade:")
        for vol_level, adj in vol_adj.items():
            sl = adj.get('stop_loss_mult', 1.0)
            tp = adj.get('take_profit_mult', 1.0)
            pos = adj.get('position_mult', 1.0)
            print(f"      {vol_level}: SL={sl}x, TP={tp}x, Pos={pos}x")
        
        # Ajustes por tendência
        trend_adj = tuner_config.get('trend_adjustments', {})
        print("\n   📈 Ajustes por Tendência:")
        for trend, adj in trend_adj.items():
            rsi = adj.get('rsi_buy_mult', 1.0)
            tp = adj.get('take_profit_mult', 1.0)
            print(f"      {trend}: RSI={rsi}x, TP={tp}x")
        
        return config
        
    except Exception as e:
        print(f"❌ Erro ao carregar config: {e}")
        return None


def main():
    """Executa todos os testes"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║        🧪 TESTE COMPLETO DO SISTEMA R7 TRADING BOT API       ║")
    print("║                                                              ║")
    print("║  Este teste verifica:                                        ║")
    print("║  1. Conexão com Binance                                      ║")
    print("║  2. Market Analyzer (análise de mercado)                     ║")
    print("║  3. Auto-Tuner (ajuste dinâmico)                             ║")
    print("║  4. Goal Monitor (metas mensais)                             ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # Mostra config atual
    show_current_config()
    
    # Testa conexão
    exchange = test_exchange_connection()
    if not exchange:
        print("\n❌ Falha na conexão. Abortando testes.")
        return
    
    # Testa market analyzer
    analyzer = test_market_analyzer(exchange)
    
    # Testa auto-tuner
    tuner = test_autotuner(exchange)
    
    # Testa goal monitor
    monitor = test_goal_monitor()
    
    # Resumo
    print_header("📋 RESUMO DOS TESTES")
    
    print(f"   📡 Conexão Binance: {'✅ OK' if exchange else '❌ FALHOU'}")
    print(f"   📊 Market Analyzer: {'✅ OK' if analyzer else '❌ FALHOU'}")
    print(f"   🎛️ Auto-Tuner: {'✅ OK' if tuner else '❌ FALHOU'}")
    print(f"   🎯 Goal Monitor: {'✅ OK' if monitor else '❌ FALHOU'}")
    
    if exchange and analyzer and tuner and monitor:
        print("\n" + "=" * 60)
        print("  ✅ TODOS OS COMPONENTES FUNCIONANDO!")
        print("  ")
        print("  O sistema está pronto para operar com:")
        print("  - Ajuste automático de configs baseado no mercado")
        print("  - Monitoramento de metas mensais ($60-$120)")
        print("  ")
        print("  Para iniciar: python main_multibot.py")
        print("=" * 60)
    else:
        print("\n⚠️ Alguns componentes falharam. Verifique os erros acima.")


if __name__ == "__main__":
    main()
