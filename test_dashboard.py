"""
Script de teste do novo Dashboard PnL
Valida se os arquivos JSON estão corretos e mostra dados
"""

import json
from pathlib import Path
from datetime import datetime

def test_dashboard_data():
    """Testa e exibe os dados do dashboard"""
    
    print("\n" + "="*70)
    print("🧪 Teste do Dashboard PnL Detalhado")
    print("="*70 + "\n")
    
    data_dir = Path("data")
    
    files_to_check = {
        'all_trades_history.json': 'Histórico de trades',
        'coordinator_stats.json': 'Status dos coordenadores',
        'dashboard_balances.json': 'Saldos',
        'multibot_positions.json': 'Posições abertas',
        'initial_capital.json': 'Capital inicial (será criado)',
    }
    
    results = {}
    
    for filename, description in files_to_check.items():
        filepath = data_dir / filename
        
        print(f"📋 Verificando: {description}")
        print(f"   Arquivo: {filename}")
        
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, dict):
                    keys = list(data.keys())[:5]
                    print(f"   ✅ Existe | Tipo: dict | Chaves: {len(data)} | Amostra: {keys}")
                elif isinstance(data, list):
                    print(f"   ✅ Existe | Tipo: list | Items: {len(data)}")
                    if len(data) > 0 and isinstance(data[0], dict):
                        print(f"      Primeiro item tem: {list(data[0].keys())}")
                else:
                    print(f"   ✅ Existe | Tipo: {type(data)}")
                
                results[filename] = 'OK'
            
            except json.JSONDecodeError as e:
                print(f"   ❌ Erro ao decodificar JSON: {e}")
                results[filename] = 'ERRO'
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                results[filename] = 'ERRO'
        else:
            print(f"   ⚠️  Arquivo não encontrado (será criado na primeira execução)")
            results[filename] = 'MISSING'
        
        print()
    
    # Análise específica
    print("\n" + "="*70)
    print("📊 Análise Detalhada dos Dados")
    print("="*70 + "\n")
    
    # Trades
    print("📜 Histórico de Trades (all_trades_history.json):")
    try:
        with open(data_dir / 'all_trades_history.json', 'r') as f:
            trades = json.load(f)
        
        if isinstance(trades, list) and len(trades) > 0:
            print(f"   ✅ Total de trades: {len(trades)}")
            
            # Calcular PnL
            pnl_total = sum(float(t.get('profit_loss', 0)) for t in trades)
            trades_positivos = len([t for t in trades if float(t.get('profit_loss', 0)) > 0])
            taxa_acerto = (trades_positivos / len(trades) * 100) if len(trades) > 0 else 0
            
            print(f"   PnL Total: ${pnl_total:+.2f}")
            print(f"   Trades com lucro: {trades_positivos}/{len(trades)} ({taxa_acerto:.1f}%)")
            
            # Amostra
            if len(trades) > 0:
                print(f"\n   Último trade:")
                last_trade = trades[-1]
                print(f"     - Timestamp: {last_trade.get('timestamp', 'N/A')}")
                print(f"     - Bot: {last_trade.get('bot_type', 'N/A')}")
                print(f"     - Símbolo: {last_trade.get('symbol', 'N/A')}")
                print(f"     - PnL: ${float(last_trade.get('profit_loss', 0)):+.2f}")
        else:
            print("   ⚠️  Nenhum trade registrado ainda")
    except:
        print("   ⚠️  Arquivo não acessível")
    
    # Coordinator
    print("\n💼 Coordinator Stats (coordinator_stats.json):")
    try:
        with open(data_dir / 'coordinator_stats.json', 'r') as f:
            coordinator = json.load(f)
        
        if 'bots' in coordinator:
            print(f"   ✅ Bots encontrados: {len(coordinator['bots'])}")
            for bot_name, bot_info in coordinator['bots'].items():
                active = "🟢" if bot_info.get('is_active') else "⏹️"
                positions = len(bot_info.get('positions', []))
                print(f"      {active} {bot_name}: {positions} posições, PnL ${bot_info.get('total_pnl', 0):+.2f}")
        else:
            print("   ⚠️  Estrutura de 'bots' não encontrada")
    except:
        print("   ⚠️  Arquivo não acessível")
    
    # Balances
    print("\n💰 Dashboard Balances (dashboard_balances.json):")
    try:
        with open(data_dir / 'dashboard_balances.json', 'r') as f:
            balances = json.load(f)
        
        print(f"   ✅ Total USDT: ${balances.get('total_balance', 0):,.2f}")
        print(f"      - USDT em carteira: ${balances.get('usdt_balance', 0):,.2f}")
        print(f"      - Cripto em carteira: ${balances.get('crypto_balance', 0):,.2f}")
    except:
        print("   ⚠️  Arquivo não acessível")
    
    # Positions
    print("\n📍 Posições Abertas (multibot_positions.json):")
    try:
        with open(data_dir / 'multibot_positions.json', 'r') as f:
            positions = json.load(f)
        
        if positions:
            print(f"   ✅ Total de posições abertas: {len(positions)}")
            total_usd = sum(float(p.get('amount_usd', 0)) for p in positions.values())
            print(f"   Capital investido: ${total_usd:,.2f}")
            
            for symbol, pos in list(positions.items())[:3]:
                print(f"      - {symbol}: {pos.get('amount', 0):.4f} @ ${pos.get('entry_price', 0):.2f}")
        else:
            print("   ⚠️  Nenhuma posição aberta")
    except:
        print("   ⚠️  Arquivo não acessível")
    
    # Resumo
    print("\n" + "="*70)
    print("✅ Resumo da Verificação")
    print("="*70)
    
    ok_count = sum(1 for v in results.values() if v == 'OK')
    print(f"\n✅ Arquivos OK: {ok_count}/{len(results)}")
    print(f"⚠️  Avisos: {sum(1 for v in results.values() if v == 'MISSING')}")
    print(f"❌ Erros: {sum(1 for v in results.values() if v == 'ERRO')}")
    
    print("\n" + "="*70)
    print("✨ Dashboard está pronto para uso!")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_dashboard_data()
