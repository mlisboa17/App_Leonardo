"""
DIAGNÓSTICO REAL DO PROBLEMA
"""
import json

positions = json.load(open('data/multibot_positions.json'))
history = json.load(open('data/multibot_history.json'))

print("="*70)
print("🔍 DIAGNÓSTICO REAL - ONDE ESTÁ O PROBLEMA")
print("="*70)
print()

# Capital investido em posições
total_invested = 0
print("📊 POSIÇÕES ABERTAS:")
print("-"*50)
for sym, pos in positions.items():
    invested = pos.get('amount_usd', 0)
    total_invested += invested
    bot = pos.get('bot_type', '?')
    entry = pos.get('entry_price', 0)
    print(f"   {sym}: ${invested} ({bot})")

print()
print(f"   💰 TOTAL EM CRYPTO: ${total_invested}")
print()

# Resumo
usdt_livre = 371.86  # Do dashboard
poupanca = 104.50

print("📋 RESUMO DO CAPITAL:")
print("-"*50)
print(f"   USDT Livre:     ${usdt_livre:.2f}")
print(f"   Em Crypto:      ${total_invested:.2f}")
print(f"   Poupança:       ${poupanca:.2f}")
print(f"   ─────────────────────────")
total_atual = usdt_livre + total_invested + poupanca
print(f"   TOTAL ATUAL:    ${total_atual:.2f}")
print()

capital_inicial = 1000.0
diferenca = total_atual - capital_inicial

print(f"   Capital Inicial: $1,000.00")
print(f"   Capital Atual:   ${total_atual:.2f}")
print(f"   ─────────────────────────")
print(f"   DIFERENÇA:       ${diferenca:+.2f}")
print()

# Onde está a diferença?
print("="*70)
print("🔍 ONDE FOI PARAR O DINHEIRO?")
print("="*70)
print()

# Trades realizados
total_pnl_realizado = sum(t.get('pnl_usd', 0) for t in history)
print(f"1. PnL dos trades fechados: ${total_pnl_realizado:+.2f}")
print(f"   (14 trades, 85% win rate, mas lucros MINÚSCULOS)")
print()

# Taxas
# Binance cobra ~0.1% por trade (compra + venda = 0.2%)
num_trades_abertos = len(positions)
num_trades_fechados = len(history)
total_trades = num_trades_abertos + num_trades_fechados

# Estimativa de taxas pagas
# Cada posição aberta pagou ~0.1% na compra
taxas_abertura = total_invested * 0.001
# Cada trade fechado pagou ~0.2% (compra + venda)
volume_fechado = sum(50 for _ in history)  # Estimativa de $50 por trade
taxas_fechamento = volume_fechado * 0.002

taxas_totais = taxas_abertura + taxas_fechamento

print(f"2. TAXAS ESTIMADAS:")
print(f"   Posições abertas ({num_trades_abertos}): ${taxas_abertura:.2f}")
print(f"   Trades fechados ({num_trades_fechados}): ${taxas_fechamento:.2f}")
print(f"   TOTAL TAXAS: ${taxas_totais:.2f}")
print()

# PnL não realizado (posições abertas podem estar em prejuízo)
print(f"3. PnL NÃO REALIZADO:")
print(f"   As posições abertas podem estar com prejuízo")
print(f"   Isso explica a diferença entre o que você investiu e o valor atual")
print()

print("="*70)
print("⚠️ O GRANDE PROBLEMA")
print("="*70)
print("""
Os trades estão sendo FECHADOS COM LUCROS MINÚSCULOS!

Média de lucro por trade: $0.07 (7 centavos!)

Para ganhar $100/mês com $0.07/trade, você precisaria de:
→ $100 / $0.07 = 1,428 trades por mês!
→ 48 trades POR DIA!

Isso é IMPOSSÍVEL de manter.

O PROBLEMA REAL:
1. Take Profit muito baixo (0.5-0.6%)
2. Stop Loss muito perto (quando bate, perde mais do que ganha)
3. As posições ficam abertas por muito tempo esperando o TP
4. Enquanto isso, o dinheiro está PARADO, não trabalhando

SOLUÇÃO:
1. AUMENTAR Take Profit para pelo menos 1.5-2%
2. Fazer MENOS trades, mas com MAIS lucro cada
3. Usar confirmação de tendência para entrar MELHOR
4. Aceitar que 10%/mês é IRREAL com $1000 em Spot
""")

print("="*70)
print("📊 CONFIGURAÇÃO ATUAL vs RECOMENDADA")
print("="*70)
print("""
                    ATUAL           RECOMENDADO
Bot Estável:
  RSI Oversold:     38              28-30
  Stop Loss:        -1.0%           -1.5%
  Take Profit:      +0.6%           +1.5%  ← PROBLEMA!
  
Bot Médio:  
  RSI Oversold:     35              28
  Stop Loss:        -1.5%           -2.0%
  Take Profit:      +1.2%           +2.5%  ← PRECISA MAIS
  
Bot Volátil:
  RSI Oversold:     30              25
  Stop Loss:        -2.0%           -2.5%
  Take Profit:      +1.5%           +3.0%  ← PRECISA MAIS

REGRA DE OURO:
→ Take Profit deve ser NO MÍNIMO 1.5x o Stop Loss
→ Se SL = -1.5%, então TP >= +2.25%
""")

print("="*70)
print("🎯 META REALISTA")
print("="*70)
print("""
Com $1000 em Spot trading:

META REALISTA: 3-5% ao mês = $30-50/mês

Para isso:
- 2-3 bons trades por dia
- Take Profit de 1.5-2%
- Win rate de 55-60%
- Risk/Reward de 1:1.5

NÃO 10%! Isso requer:
- Alavancagem (Futuros)
- OU Capital muito maior
- OU Risco de perder tudo
""")
