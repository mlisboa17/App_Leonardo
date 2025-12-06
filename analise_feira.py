"""
ANÁLISE: QUAIS CRYPTOS SE BENEFICIAM DA ESTRATÉGIA DE FEIRA?
============================================================

Critérios para aplicar Estratégia de Feira:
1. ALTA VOLATILIDADE (>0.5%) - preço oscila muito, precisa vender rápido
2. VOLUME MÉDIO/BAIXO - menos liquidez, mais difícil vender depois
3. MEME COINS - muito especulativo, melhor realizar lucro rápido
4. ALTCOINS MENORES - mais arriscado segurar

Critérios para NÃO aplicar (Estratégia HOLD):
1. BAIXA VOLATILIDADE (<0.5%) - BTC, ETH - preço estável
2. ALTO VOLUME - muita liquidez, pode esperar
3. BLUE CHIPS - BTC, ETH - mais seguro segurar
4. TENDÊNCIA CLARA DE ALTA - melhor segurar
"""

import json

# Carregar dados
profiles = json.load(open('data/crypto_profiles.json'))
history = json.load(open('data/multibot_history.json'))

print("="*70)
print("🔍 ANÁLISE: ESTRATÉGIA FEIRA vs HOLD POR CRYPTO")
print("="*70)
print()

# Analisar cada crypto
crypto_analysis = {}

for symbol, profile in profiles.items():
    volatility = profile.get('volatility_pct', 0.5)
    volume = profile.get('volume_usd', 0)
    rsi_range = profile.get('rsi_max', 70) - profile.get('rsi_min', 30)
    
    # Calcular performance nos trades
    trades = [t for t in history if t['symbol'] == symbol]
    wins = [t for t in trades if t['pnl_usd'] > 0]
    losses = [t for t in trades if t['pnl_usd'] < 0]
    
    avg_duration = sum(t.get('duration_min', 0) for t in trades) / len(trades) if trades else 0
    total_pnl = sum(t.get('pnl_usd', 0) for t in trades)
    
    # Classificar
    is_meme = symbol in ['DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT']
    is_bluechip = symbol in ['BTCUSDT', 'ETHUSDT']
    is_high_vol = volatility > 0.55
    is_low_volume = volume < 1000000
    
    # Decidir estratégia
    if is_bluechip:
        strategy = "HOLD"
        reason = "Blue chip - mais seguro segurar"
        feira_factor = 0.3  # Pouca redução com tempo
    elif is_meme:
        strategy = "FEIRA_AGRESSIVA"
        reason = "Meme coin - realizar lucro rápido"
        feira_factor = 0.9  # Muita redução com tempo
    elif is_high_vol and is_low_volume:
        strategy = "FEIRA"
        reason = "Alta volatilidade + baixo volume"
        feira_factor = 0.7
    elif is_high_vol:
        strategy = "FEIRA_MODERADA"
        reason = "Alta volatilidade"
        feira_factor = 0.5
    else:
        strategy = "HOLD_MODERADO"
        reason = "Volatilidade normal"
        feira_factor = 0.4
    
    crypto_analysis[symbol] = {
        'strategy': strategy,
        'reason': reason,
        'feira_factor': feira_factor,
        'volatility': volatility,
        'volume': volume,
        'trades': len(trades),
        'wins': len(wins),
        'avg_duration': avg_duration,
        'total_pnl': total_pnl
    }

# Mostrar resultados
print(f"{'CRYPTO':<12} {'ESTRATÉGIA':<18} {'FATOR':<8} {'VOL%':<8} {'MOTIVO'}")
print("-"*70)

for symbol, data in sorted(crypto_analysis.items(), key=lambda x: x[1]['feira_factor'], reverse=True):
    emoji = "🏪" if "FEIRA" in data['strategy'] else "🔒"
    print(f"{emoji} {symbol:<10} {data['strategy']:<18} {data['feira_factor']:<8.1f} {data['volatility']:<8.2f} {data['reason']}")

print()
print("="*70)
print("📋 RESUMO DA ESTRATÉGIA")
print("="*70)
print("""
🏪 FEIRA (vende mais rápido com o tempo):
   - DOGEUSDT, SHIBUSDT, PEPEUSDT (memes)
   - LINKUSDT, XRPUSDT (alta volatilidade)
   - Altcoins com baixo volume

🔒 HOLD (segura mais tempo):
   - BTCUSDT, ETHUSDT (blue chips)
   - Cryptos com tendência clara de alta
   - Alto volume = mais liquidez

⚙️ FATOR FEIRA:
   0.9 = Muito agressivo (reduz TP 90% com o tempo)
   0.5 = Moderado (reduz TP 50% com o tempo)
   0.3 = Conservador (reduz TP 30% com o tempo)
""")

# Salvar configuração
config_feira = {
    'enabled': True,
    'description': 'Estratégia de Feira - TP dinâmico por crypto',
    'cryptos': crypto_analysis
}

with open('data/feira_strategy_config.json', 'w') as f:
    json.dump(config_feira, f, indent=2)

print("✅ Configuração salva em data/feira_strategy_config.json")
