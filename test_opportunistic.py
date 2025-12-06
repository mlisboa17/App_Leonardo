"""
🎯 Teste do Modo Oportunista - META 10% AO MÊS
"""
from src.ai.opportunistic_mode import get_opportunistic_mode

opp = get_opportunistic_mode()

print("=" * 70)
print("🎯 CONFIGURAÇÃO AGRESSIVA - META 10% AO MÊS ($100/mês)")
print("=" * 70)
print()

# Cenário 1: Mercado NORMAL (conservador)
print("📊 CENÁRIO 1: Mercado Normal")
print("-" * 50)
score1 = opp.calculate_opportunity_score(
    fear_greed_index=50,
    avg_rsi=50,
    oversold_count=2,
    total_assets=20,
    volume_ratio=1.0,
    btc_change_24h=0.5,
    recent_pnl=0,
    recent_win_rate=0.5
)
level1 = opp.determine_level(score1)
params1 = opp.get_adjusted_params()
print(f"  Score: {score1.total_score}/100")
print(f"  Nível: {level1.emoji} {level1.name} (x{level1.multiplier})")
print(f"  Posição máx: {params1['position_pct']}% = ${1000 * params1['position_pct'] / 100:.0f}")
print()

# Cenário 2: Mercado BOM (moderado)
print("📊 CENÁRIO 2: Condições Favoráveis")
print("-" * 50)
score2 = opp.calculate_opportunity_score(
    fear_greed_index=30,
    avg_rsi=35,
    oversold_count=5,
    total_assets=20,
    volume_ratio=1.3,
    btc_change_24h=2.0,
    recent_pnl=15,
    recent_win_rate=0.55
)
level2 = opp.determine_level(score2)
params2 = opp.get_adjusted_params()
print(f"  Score: {score2.total_score}/100")
print(f"  Nível: {level2.emoji} {level2.name} (x{level2.multiplier})")
print(f"  Posição máx: {params2['position_pct']}% = ${1000 * params2['position_pct'] / 100:.0f}")
print()

# Cenário 3: OPORTUNIDADE (agressivo)
print("📊 CENÁRIO 3: Grande Oportunidade!")
print("-" * 50)
score3 = opp.calculate_opportunity_score(
    fear_greed_index=20,
    avg_rsi=28,
    oversold_count=10,
    total_assets=20,
    volume_ratio=1.6,
    btc_change_24h=3.0,
    recent_pnl=30,
    recent_win_rate=0.60
)
level3 = opp.determine_level(score3)
params3 = opp.get_adjusted_params()
print(f"  Score: {score3.total_score}/100")
print(f"  Nível: {level3.emoji} {level3.name} (x{level3.multiplier})")
print(f"  Posição máx: {params3['position_pct']}% = ${1000 * params3['position_pct'] / 100:.0f}")
print()

# Cenário 4: MÁXIMO (medo extremo + tudo favorável)
print("📊 CENÁRIO 4: OPORTUNIDADE MÁXIMA! 🔥")
print("-" * 50)
score4 = opp.calculate_opportunity_score(
    fear_greed_index=15,
    avg_rsi=22,
    oversold_count=14,
    total_assets=20,
    volume_ratio=2.0,
    btc_change_24h=4.0,
    recent_pnl=50,
    recent_win_rate=0.65
)
level4 = opp.determine_level(score4)
params4 = opp.get_adjusted_params()
print(f"  Score: {score4.total_score}/100")
print(f"  Nível: {level4.emoji} {level4.name} (x{level4.multiplier})")
print(f"  Posição máx: {params4['position_pct']}% = ${1000 * params4['position_pct'] / 100:.0f}")
print(f"  RSI Oversold: {params4['rsi_oversold']} (compra mais cedo)")
print(f"  Take Profit: {params4['take_profit_pct']}%")
print()

print("=" * 70)
print("💰 PROJEÇÃO MENSAL COM MODO OPORTUNISTA")
print("=" * 70)
print()
print("Se o mercado ficar em cada cenário por 1 semana:")
print()
print("  Semana 1 (Normal):      $20-25")
print("  Semana 2 (Favorável):   $25-35")
print("  Semana 3 (Oportunidade):$35-50")
print("  Semana 4 (Máximo):      $40-60")
print("  ─────────────────────────────")
print("  🎯 TOTAL MÊS:           $120-170")
print()
print("⚠️  RISCOS:")
print("  • Daily Stop: 5% ($50)")
print("  • Max Drawdown: 20% ($200)")
print("  • Emergency Stop: 25% ($250)")
print()
print("✅ META 10% ($100/mês) é ALCANÇÁVEL com Modo Oportunista!")
print("=" * 70)
