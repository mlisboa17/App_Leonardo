"""
📊 ANÁLISE COMPLETA DOS TRADES - VERDADE NUA E CRUA
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

history_file = Path('data/multibot_history.json')
positions_file = Path('data/multibot_positions.json')
daily_stats_file = Path('data/daily_stats.json')

history = json.load(open(history_file)) if history_file.exists() else []
positions = json.load(open(positions_file)) if positions_file.exists() else {}
daily_stats = json.load(open(daily_stats_file)) if daily_stats_file.exists() else {}

CAPITAL_INICIAL = 1000.0

print("=" * 70)
print("📊 ANÁLISE COMPLETA DOS SEUS TRADES - VERDADE NUA E CRUA")
print("=" * 70)
print()

# ===== TRADES FECHADOS =====
total_trades = len(history)
print(f"📈 TRADES FECHADOS: {total_trades}")
print()

if total_trades > 0:
    wins = [t for t in history if t.get('pnl_usd', 0) > 0]
    losses = [t for t in history if t.get('pnl_usd', 0) < 0]
    breakeven = [t for t in history if t.get('pnl_usd', 0) == 0]
    
    total_pnl_realizado = sum(t.get('pnl_usd', 0) for t in history)
    avg_win = sum(t.get('pnl_usd', 0) for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t.get('pnl_usd', 0) for t in losses) / len(losses) if losses else 0
    
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
    
    print(f"   ✅ Wins: {len(wins)} ({win_rate:.1f}%)")
    print(f"   ❌ Losses: {len(losses)} ({100-win_rate:.1f}%)")
    print(f"   ➖ Breakeven: {len(breakeven)}")
    print()
    print(f"💰 PnL REALIZADO (trades fechados): ${total_pnl_realizado:+.2f}")
    print(f"   Média por WIN: ${avg_win:+.2f}")
    print(f"   Média por LOSS: ${avg_loss:+.2f}")
    
    if avg_loss != 0:
        rr_ratio = abs(avg_win / avg_loss)
        print(f"   Risk/Reward Ratio: {rr_ratio:.2f}")
        if rr_ratio < 1:
            print(f"   ⚠️ PROBLEMA: R/R < 1 significa que você perde mais do que ganha por trade!")
    print()

# ===== POR BOT =====
if total_trades > 0:
    print("📊 ANÁLISE POR BOT:")
    print("-" * 50)
    by_bot = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0, 'trades': []})
    for t in history:
        bot = t.get('bot_type', 'unknown')
        by_bot[bot]['pnl'] += t.get('pnl_usd', 0)
        by_bot[bot]['trades'].append(t)
        if t.get('pnl_usd', 0) > 0:
            by_bot[bot]['wins'] += 1
        elif t.get('pnl_usd', 0) < 0:
            by_bot[bot]['losses'] += 1
    
    for bot, data in sorted(by_bot.items()):
        total = data['wins'] + data['losses']
        wr = data['wins'] / total * 100 if total > 0 else 0
        emoji = "🟢" if data['pnl'] > 0 else "🔴"
        print(f"   {emoji} {bot}: {total} trades | WR: {wr:.0f}% | PnL: ${data['pnl']:+.2f}")
        if wr < 50:
            print(f"      ⚠️ Win rate baixo! Precisa > 50%")
    print()

# ===== POR CRYPTO =====
if total_trades > 0:
    print("📊 ANÁLISE POR CRYPTO (ordenado por PnL):")
    print("-" * 50)
    by_crypto = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0})
    for t in history:
        symbol = t.get('symbol', 'unknown')
        by_crypto[symbol]['pnl'] += t.get('pnl_usd', 0)
        if t.get('pnl_usd', 0) > 0:
            by_crypto[symbol]['wins'] += 1
        elif t.get('pnl_usd', 0) < 0:
            by_crypto[symbol]['losses'] += 1
    
    sorted_crypto = sorted(by_crypto.items(), key=lambda x: x[1]['pnl'], reverse=True)
    
    lucrativos = []
    prejuizo = []
    
    for symbol, data in sorted_crypto:
        total = data['wins'] + data['losses']
        wr = data['wins'] / total * 100 if total > 0 else 0
        emoji = "🟢" if data['pnl'] > 0 else "🔴"
        print(f"   {emoji} {symbol}: WR {wr:.0f}% | PnL: ${data['pnl']:+.2f}")
        if data['pnl'] > 0:
            lucrativos.append(symbol)
        else:
            prejuizo.append(symbol)
    
    print()
    if prejuizo:
        print(f"   ⚠️ CRYPTOS COM PREJUÍZO: {', '.join(prejuizo)}")
        print(f"   💡 SUGESTÃO: Considere REMOVER essas cryptos do portfolio")
    print()

# ===== POSIÇÕES ABERTAS =====
print("📊 POSIÇÕES ABERTAS (PnL NÃO REALIZADO):")
print("-" * 50)
total_unrealized = 0
posicoes_negativas = []

if positions:
    for pos_id, pos in positions.items():
        symbol = pos.get('symbol', '?')
        entry = pos.get('entry_price', 0)
        current = pos.get('current_price', entry)
        qty = pos.get('quantity', 0)
        pnl_pct = ((current - entry) / entry * 100) if entry > 0 else 0
        pnl_usd = (current - entry) * qty
        total_unrealized += pnl_usd
        
        emoji = "🟢" if pnl_pct > 0 else "🔴"
        print(f"   {emoji} {symbol}: {pnl_pct:+.2f}% | ${pnl_usd:+.2f}")
        
        if pnl_pct < -1:
            posicoes_negativas.append((symbol, pnl_pct, pnl_usd))
    
    print()
    print(f"   💰 PnL NÃO REALIZADO: ${total_unrealized:+.2f}")
    
    if posicoes_negativas:
        print()
        print("   ⚠️ POSIÇÕES EM PREJUÍZO SIGNIFICATIVO:")
        for s, pct, usd in posicoes_negativas:
            print(f"      {s}: {pct:.2f}% (${usd:.2f})")
else:
    print("   Nenhuma posição aberta")

print()

# ===== RESUMO FINAL =====
print("=" * 70)
print("📋 RESUMO FINAL - ONDE VOCÊ ESTÁ")
print("=" * 70)

pnl_total = total_pnl_realizado + total_unrealized if total_trades > 0 else total_unrealized
print(f"""
   💵 Capital Inicial: $1,000.00
   💰 PnL Realizado:   ${total_pnl_realizado if total_trades > 0 else 0:+.2f}
   📊 PnL Não Realiz.: ${total_unrealized:+.2f}
   ─────────────────────────────────
   📈 PnL TOTAL:       ${pnl_total:+.2f}
   💎 Saldo Estimado:  ${CAPITAL_INICIAL + pnl_total:.2f}
""")

# ===== DIAGNÓSTICO DE PROBLEMAS =====
print("=" * 70)
print("🔍 DIAGNÓSTICO DE PROBLEMAS")
print("=" * 70)
print()

problemas = []

# 1. Win Rate
if total_trades > 0:
    if win_rate < 50:
        problemas.append({
            'problema': f"Win Rate muito baixo: {win_rate:.1f}%",
            'causa': "RSI pode estar configurado muito agressivo ou mercado lateral",
            'solucao': "Diminuir RSI oversold para 28-30, esperar sinais mais fortes"
        })

# 2. Risk/Reward
if total_trades > 0 and avg_loss != 0:
    if rr_ratio < 1:
        problemas.append({
            'problema': f"Risk/Reward negativo: {rr_ratio:.2f}",
            'causa': "Stop Loss muito longe ou Take Profit muito perto",
            'solucao': "Ajustar SL:TP para pelo menos 1:1.5 (ex: SL -1%, TP +1.5%)"
        })

# 3. Posições presas
if posicoes_negativas:
    problemas.append({
        'problema': f"{len(posicoes_negativas)} posições em prejuízo significativo",
        'causa': "Stop Loss não está sendo executado ou está muito largo",
        'solucao': "Verificar se o stop loss está ativo, considerar fechar manualmente"
    })

# 4. Cryptos com prejuízo
if total_trades > 0 and prejuizo:
    problemas.append({
        'problema': f"Cryptos dando prejuízo: {', '.join(prejuizo)}",
        'causa': "Essas cryptos podem não ser adequadas para a estratégia atual",
        'solucao': "REMOVER essas cryptos do portfolio ou ajustar parâmetros específicos"
    })

# 5. Meta 10% irreal
problemas.append({
    'problema': "Meta de 10% ao mês é MUITO agressiva",
    'causa': "Requer win rate >60% E R/R >1.5 consistentemente",
    'solucao': "Meta realista: 3-5% ao mês ($30-50). Melhor consistência."
})

for i, p in enumerate(problemas, 1):
    print(f"❌ PROBLEMA {i}: {p['problema']}")
    print(f"   Causa: {p['causa']}")
    print(f"   Solução: {p['solucao']}")
    print()

# ===== RECOMENDAÇÕES =====
print("=" * 70)
print("💡 RECOMENDAÇÕES PARA MELHORAR")
print("=" * 70)
print("""
1️⃣ AJUSTAR RSI PARA SER MAIS CONSERVADOR:
   • Bot Estável: RSI oversold 30 (não 38)
   • Bot Médio: RSI oversold 28 (não 35)
   • Bot Volátil: RSI oversold 25 (não 30)
   → Menos trades, mas trades MELHORES

2️⃣ MELHORAR RISK/REWARD (mínimo 1:1.5):
   • Se SL = -1%, então TP deve ser +1.5%
   • Se SL = -1.5%, então TP deve ser +2.25%
   → Assim mesmo com 45% de acerto, você lucra

3️⃣ USAR CONFIRMAÇÃO DE TENDÊNCIA:
   • Só comprar se preço > SMA20 (tendência de alta)
   • Evitar comprar em tendência de baixa
   → Aumenta win rate em 10-15%

4️⃣ REDUZIR TAMANHO DAS POSIÇÕES:
   • Máximo 3-5% do capital por trade (não 6%)
   • Com $1000, máximo $30-50 por trade
   → Aguenta mais losses seguidos

5️⃣ REMOVER CRYPTOS PROBLEMÁTICAS:
   • Se uma crypto dá prejuízo consistente, REMOVA
   • Foque nas que funcionam com sua estratégia

6️⃣ META REALISTA:
   • 3-5% ao mês = $30-50/mês
   • 10% ao mês = arriscado demais
   → Consistência > Ganância
""")

print("=" * 70)
print("FIM DA ANÁLISE")
print("=" * 70)
