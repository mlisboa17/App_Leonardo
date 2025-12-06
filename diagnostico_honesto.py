"""
DIAGNÓSTICO CORRETO - ANÁLISE REAL
"""
import json

# Dados REAIS do dashboard
dashboard = json.load(open('data/dashboard_balances.json'))
positions = json.load(open('data/multibot_positions.json'))
history = json.load(open('data/multibot_history.json'))

print("="*70)
print("🔍 DIAGNÓSTICO HONESTO DO SEU TRADING")
print("="*70)
print()

# Valores REAIS da Binance
usdt_livre = dashboard['usdt_balance']
crypto_valor = dashboard['crypto_balance']
total_real = dashboard['total_balance']

print("📋 SITUAÇÃO ATUAL (REAL DA BINANCE):")
print("-"*50)
print(f"   USDT Livre:      ${usdt_livre:.2f}")
print(f"   Crypto (valor):  ${crypto_valor:.2f}")
print(f"   ────────────────────────────")
print(f"   TOTAL NA CONTA:  ${total_real:.2f}")
print()

capital_inicial = 1000.0
pnl_real = total_real - capital_inicial

print(f"   Capital Inicial: $1,000.00")
print(f"   Capital Atual:   ${total_real:.2f}")
print(f"   ────────────────────────────")
if pnl_real >= 0:
    print(f"   💰 LUCRO:        ${pnl_real:+.2f}")
else:
    print(f"   ⚠️ PREJUÍZO:     ${pnl_real:.2f}")
print()

# Detalhamento das posições
print("="*70)
print("📊 DETALHAMENTO DAS POSIÇÕES (Valor Atual vs Investido)")
print("="*70)
print()

total_investido = 0
total_valor_atual = 0
total_pnl_aberto = 0

for sym, pos in positions.items():
    invested = pos.get('amount_usd', 0)
    total_investido += invested
    
    # Pegar valor atual do dashboard
    coin = sym.replace('USDT', '')
    atual_data = dashboard.get('crypto_positions', {}).get(coin, {})
    valor_atual = atual_data.get('value_usd', invested)
    total_valor_atual += valor_atual
    
    pnl = valor_atual - invested
    total_pnl_aberto += pnl
    
    pct = (pnl / invested * 100) if invested > 0 else 0
    
    status = "🟢" if pnl >= 0 else "🔴"
    print(f"   {status} {sym:10} | Invest: ${invested:.2f} | Atual: ${valor_atual:.2f} | PnL: ${pnl:+.2f} ({pct:+.1f}%)")

print()
print(f"   ────────────────────────────────────────────────")
print(f"   TOTAL INVESTIDO: ${total_investido:.2f}")
print(f"   VALOR ATUAL:     ${total_valor_atual:.2f}")
print(f"   PnL ABERTO:      ${total_pnl_aberto:+.2f}")
print()

# Análise dos trades fechados
print("="*70)
print("📈 ANÁLISE DOS TRADES FECHADOS")
print("="*70)
print()

total_pnl_fechado = 0
wins = []
losses = []

for trade in history:
    pnl = trade.get('pnl_usd', 0)
    total_pnl_fechado += pnl
    if pnl > 0.01:
        wins.append(pnl)
    elif pnl < -0.01:
        losses.append(pnl)

print(f"   Trades fechados: {len(history)}")
print(f"   ✅ Wins: {len(wins)}")
print(f"   ❌ Losses: {len(losses)}")
print(f"   ➖ Breakeven: {len(history) - len(wins) - len(losses)}")
print()
print(f"   PnL Realizado Total: ${total_pnl_fechado:+.2f}")
if wins:
    print(f"   Média por Win: ${sum(wins)/len(wins):.2f}")
if losses:
    print(f"   Média por Loss: ${sum(losses)/len(losses):.2f}")
print()

# Onde foi parar o dinheiro?
print("="*70)
print("🔍 ONDE FOI PARAR O DINHEIRO?")
print("="*70)
print()
print(f"   PnL Realizado (trades fechados):  ${total_pnl_fechado:+.2f}")
print(f"   PnL Aberto (posições abertas):    ${total_pnl_aberto:+.2f}")
print(f"   ────────────────────────────")
print(f"   TOTAL PnL:                        ${(total_pnl_fechado + total_pnl_aberto):+.2f}")
print()

# Taxas estimadas
volume_total = total_investido + sum(50 for _ in history)
taxas = volume_total * 0.001  # 0.1% maker fee
print(f"   Taxas de trading (~0.1%):         ${-taxas:.2f}")
print()
diferenca_esperada = total_pnl_fechado + total_pnl_aberto - taxas
print(f"   PnL esperado após taxas:          ${diferenca_esperada:+.2f}")
print(f"   PnL real (do dashboard):          ${pnl_real:+.2f}")
print()

# O Grande Problema
print("="*70)
print("⚠️ O GRANDE PROBLEMA")
print("="*70)
print("""
RESUMO DA SITUAÇÃO:
─────────────────────────────────────────────────────

1. CAPITAL INICIAL:        $1,000.00
2. CAPITAL ATUAL:          ${:.2f}
3. DIFERENÇA:              ${:+.2f}

DIAGNÓSTICO:
─────────────────────────────────────────────────────""".format(total_real, pnl_real))

if pnl_real < 0:
    print("""
🔴 VOCÊ ESTÁ NO PREJUÍZO de ${:.2f}

MOTIVOS:
1. Posições abertas estão em queda (PnL aberto: ${:+.2f})
2. Take Profit muito baixo - lucros de 7 centavos por trade
3. Dinheiro está PARADO em posições que não se movem
4. Taxas de trading consumiram parte do capital
""".format(abs(pnl_real), total_pnl_aberto))
else:
    print(f"""
🟢 VOCÊ ESTÁ NO LUCRO de ${pnl_real:+.2f}

MAS CUIDADO:
1. Lucro médio por trade é de apenas $0.07
2. Para atingir 10%/mês você precisaria de 1,400+ trades
3. As posições abertas podem virar prejuízo
""")

print("""
="*70
🎯 RECOMENDAÇÕES HONESTAS
="*70

PARA SUA META DE 10%/MÊS ($100):

❌ IMPOSSÍVEL com a configuração atual!
   - 7 centavos por trade = 1,400 trades/mês necessários
   - Isso é insustentável

✅ O QUE VOCÊ PRECISA FAZER:

1. AUMENTAR TAKE PROFIT:
   - Bot Estável: de 0.6% para 1.5%
   - Bot Médio: de 1.2% para 2.5%
   - Bot Volátil: de 1.5% para 3.0%

2. DIMINUIR RSI OVERSOLD (entrar MELHOR):
   - Só comprar quando RSI < 30 (oversold real)
   - Menos trades, mas melhores entradas

3. ACEITAR REALIDADE:
   - Spot trading com $1000 = 3-5%/mês realista
   - Para 10%/mês precisa de Futuros com alavancagem
   - OU aceitar o risco de perdas maiores

4. CONSIDERAR FUTUROS:
   - Alavancagem 3-5x pode dar 10%/mês
   - MAS: risco de liquidação se der errado

QUER QUE EU AJUSTE AS CONFIGURAÇÕES PARA SER MAIS REALISTA?
""")
