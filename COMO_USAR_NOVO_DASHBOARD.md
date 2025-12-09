# 📊 Como Acessar o Novo Dashboard PnL

## 🚀 Acesso Rápido

**URL**: http://18.230.59.118:8501

Clique na página **"04_pnl_detalhado"** no menu lateral.

---

## ✅ O que você vai ver?

### 1️⃣ KPIs Principais (4 Caixas no topo)

```
💰 Capital Atual         🟢 PnL Hoje          🟢 PnL Este Mês      🟢 PnL Geral
$1,050.25                +$12.50              +$87.45              +$50.25
Inicial: $1,000.00       5 trades             34 trades            ROI: +5.03%
```

**Cores Automáticas:**
- 🟢 **Verde** = Ganhando (lucro positivo)
- 🔴 **Vermelho** = Perdendo (prejuízo negativo)

---

### 2️⃣ Indicadores Visuais com Progress Bars

```
✅ Ganho Hoje: $12.50                    [████░░░░░░░░░░░] Meta: $2.50
✅ Ganho Mês: $87.45                     [█████████░░░░░░] Meta: $75.00
✅ Ganho Total: $50.25                   [██░░░░░░░░░░░░░] Meta: $250+
```

Se vermelho = está em prejuízo naquele período.

---

### 3️⃣ Status dos 5 Bots

```
🐢 Bot Estável      ⚖️ Bot Médio       📈 Bot Volátil      🎲 Bot Meme       🤖 Unico Bot
Status: 🟢 Ativo    Status: 🟢 Ativo   Status: 🟢 Ativo    Status: 🟢 Ativo   Status: 🟢 Ativo
Posições: 4/4       Posições: 3/4      Posições: 2/3       Posições: 1/2      Posições: 5/9
Amount: $39.15      Amount: $39.15     Amount: $39.15      Amount: $30.00     Amount: $50.00
🟢 PnL: +$15.20     🟢 PnL: +$12.10    🟢 PnL: +$8.50      🟢 PnL: +$5.20     🟢 PnL: +$9.25
```

Se algum estiver ⏹️ **Inativo**, então não está funcionando.

---

### 4️⃣ Análise: Por Que Não Está Ganhando?

**Checklist Automático:**
```
✅ Bots Ativos: 5/5          (Se < 3 = Problema!)
✅ Posições Abertas: 15      (Se = 0 = Crítico!)
✅ PnL Total Bots: +$50.25   (Se < 0 = Em prejuízo!)
✅ Total de Trades: 45       (Se = 0 = Nenhuma operação!)
✅ Taxa de Acerto: 75.6%     (Se < 40% = Estratégia ruim!)
```

**Se aparecer tudo em ✅ verde:**
- Sistema está funcionando normalmente ✨

**Se aparecer ❌ vermelho:**
- O dashboard mostra o problema específico
- Fornece comandos para corrigir

---

## 🔧 Problemas Comuns

### ❌ Problema: "CRÍTICO: Nenhum bot ativo!"

**Causa**: Os 5 bots não estão rodando.

**Solução**:
```bash
# SSH no EC2
ssh -i r7_trade_key.pem ubuntu@18.230.59.118

# Verificar se estão rodando
ps aux | grep main_multibot

# Se não tiver processo, iniciar
cd /home/ubuntu/App_Leonardo
nohup ./venv/bin/python main_multibot.py > logs/bot.log 2>&1 &

# Verificar logs
tail -f logs/bot.log
```

### ⚠️ Problema: "Poucas posições (3)"

**Causa**: Bots estão rodando mas não estão abrindo posições.

**Solução**:
1. Aguarde 5-10 minutos (leva tempo para gerar sinais)
2. Verifique se tem saldo disponível: `curl http://18.230.59.118:8080/balance`
3. Verifique logs para erros

### 🔴 Problema: "Em prejuízo: -$50.00"

**Causa**: Estratégia está gerando mais perdas que ganhos.

**Solução**:
1. Verifique se a estratégia RSI está bem configurada
2. Revise os limites de stop-loss
3. Considere pausar bots com mais de -$20

---

## 📊 Gráficos Disponíveis

### Gráfico 1: PnL por Período
Mostra barras de:
- **Hoje** (último 24h)
- **Este Mês** (do dia 1 até hoje)
- **Geral** (desde início)

Cores: Verde = lucro, Vermelho = perda

### Gráfico 2: PnL por Bot
Mostra barra para cada bot:
- 🐢 Bot Estável
- ⚖️ Bot Médio
- 📈 Bot Volátil
- 🎲 Bot Meme
- 🤖 Unico Bot

Cores: Verde = lucro, Vermelho = perda

---

## 📜 Tabela de Últimos 20 Trades

Mostra as últimas 20 operações com:

| Hora | Bot | Par | Tipo | Preço | Qtd | USD | PnL |
|------|-----|-----|------|-------|-----|-----|-----|
| 14:35:22 | bot_estavel | BTC/USDT | BUY | $40,500.25 | 0.0024 | $97.20 | +$2.50 |
| 14:22:10 | bot_medio | ETH/USDT | SELL | $2,250.00 | 0.0175 | $39.37 | +$1.20 |

---

## 🎯 Metas Diárias

O dashboard monitora 3 metas:

### Meta 1: Ganho Hoje
- **Objetivo**: $2.50 por dia
- **Cálculo**: 0.25% do capital ($1,000 × 0.0025)
- **Status**: Progress bar com meta

### Meta 2: Ganho Este Mês
- **Objetivo**: $75.00 por mês
- **Cálculo**: 7.5% do capital ($1,000 × 0.075)
- **Status**: Progress bar com meta

### Meta 3: Ganho Geral
- **Objetivo**: $250+ total
- **Cálculo**: 25%+ ROI ($1,000 × 0.25)
- **Status**: Progress bar com meta

---

## 🔄 Atualização dos Dados

Os dados atualizam a cada **3 segundos** automaticamente.

Se quiser forçar atualização: Pressione **F5** no navegador.

---

## ❓ FAQ

**P: Por que os dados não atualizam?**
R: Os bots podem estar parados. Verifique `ps aux | grep main_multibot`.

**P: Como saber se está ganhando?**
R: Se o PnL total estiver em 🟢 verde e maior que 0, está ganhando!

**P: O que significa "Taxa de Acerto"?**
R: Percentual de trades com lucro. Exemplo: 75.6% = 75.6% dos trades tiveram ganho.

**P: Como faço para parar os bots?**
R: Execute `pkill -f main_multibot` no EC2.

**P: Qual o melhor horário para checkar o dashboard?**
R: Durante o horário de abertura do mercado: 09:00 às 18:00 BRT

---

## 📱 Acesso Móvel

Você pode acessar o dashboard também do celular:
```
http://18.230.59.118:8501
```

A interface é responsiva e funciona bem em celulares.

---

## ✨ Próximos Passos

1. **Acesse o dashboard**: http://18.230.59.118:8501
2. **Clique em "04_pnl_detalhado"** no menu
3. **Verifique o status dos 5 bots**
4. **Veja o PnL do dia/mês/geral**
5. **Se houver problema, siga as recomendações**

---

**R7 Trading Bot v2.0** | Dashboard PnL Detalhado  
Última atualização: 8 de Dezembro de 2025
