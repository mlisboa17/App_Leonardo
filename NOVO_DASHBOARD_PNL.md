# 📊 Dashboard PnL Detalhado - Novo

**Data**: 8 de Dezembro de 2025  
**Versão**: 1.0

## 🎯 O que foi criado?

Um novo dashboard **04_pnl_detalhado.py** que mostra:

### ✅ KPIs Principais com Cores
- 💰 Capital Atual (vs. inicial $1,000 USDT)
- 🟢 PnL Hoje com número de trades
- 🟢 PnL Este Mês com número de trades  
- 🟢 PnL Geral com ROI %
- **Cores automáticas**: Verde para lucro, Vermelho para perda

### 🎯 Indicadores Visuais
- Progress bars para metas:
  - Meta Dia: $2.50
  - Meta Mês: $75.00
  - Meta Geral: $250+
- Status visual com checkmarks

### 🤖 Status dos 5 Bots
Mostra cada bot com:
- Status (Ativo 🟢 ou Inativo ⏹️)
- Número de posições abertas
- Amount por trade
- PnL de cada bot (verde/vermelho)

### 🔍 Análise: Por Que Não Está Ganhando?

**Checklist Automático:**
1. Número de bots ativos (0/5, 1-2/5, 3-5/5)
2. Número de posições abertas
3. PnL total dos bots
4. Total de trades realizados
5. Taxa de acerto dos trades

**Diagnósticos:**
- ❌ Se 0 bots ativos → CRÍTICO: Nenhum bot rodando
- ⚠️ Se < 3 bots → Baixa diversificação
- ❌ Se 0 posições → Sem operações ativas
- ⚠️ Se < 5 posições → Poucas operações
- ❌ Se PnL negativo → Estratégia gerando perdas
- ⚠️ Se taxa de acerto < 40% → Revisar estratégia

### 🚀 Recomendações Imediatas

Se problemas são encontrados, o dashboard mostra:
1. Comando para verificar se bots estão rodando
2. Comando para iniciar os bots
3. Comando para verificar logs
4. Avisos específicos sobre o que corrigir

### 📈 Gráficos
- Gráfico de barras PnL por período (Hoje/Mês/Geral)
- Gráfico de barras PnL por bot
- Ambos com cores automáticas (verde/vermelho)

### 📜 Tabela de Últimos 20 Trades
Mostra:
- Hora exata
- Bot responsável
- Par de criptomoedas
- Tipo de trade (BUY/SELL)
- Preço de entrada
- Quantidade
- Valor em USD
- PnL do trade

## 🌐 Como Acessar?

Todos os 4 dashboards agora estão disponíveis no Streamlit:

**URL**: http://18.230.59.118:8501

**Páginas:**
1. 📊 **dashboard_multibot.py** (Principal) - Visão geral de todos os bots
2. 📈 **01_positions_dashboard.py** - Posições com gráficos detalhados
3. 💵 **02_capital_distribution.py** - Distribuição de capital pelos 5 bots
4. 🔧 **03_system_monitoring.py** - Saúde do sistema e logs
5. **04_pnl_detalhado.py** (NOVO!) - PnL Dia/Mês/Geral com diagnóstico

## 📊 Dados que Alimentam o Dashboard

O dashboard lê os seguintes arquivos JSON em tempo real (cache 3 segundos):

```
data/
  ├── all_trades_history.json        ← Histórico completo de trades
  ├── coordinator_stats.json          ← Status dos 5 bots
  ├── dashboard_balances.json         ← Saldos atuais
  ├── multibot_positions.json         ← Posições abertas
  └── initial_capital.json            ← Capital inicial ($1,000)
```

## 🔧 Para Sincronizar para EC2

Se estiver desenvolvendo localmente e quer enviar para EC2:

```bash
# Linux/Mac
./sync_dashboards.sh

# Windows (PowerShell)
python sync_dashboards.py
```

## ✅ Checklist de Verificação

Após acessar o dashboard, verifique:

- [ ] Todos os 5 bots aparecem na listagem
- [ ] Status de cada bot (Ativo/Inativo) está correto
- [ ] PnL está em cores (verde/vermelho)
- [ ] Metas diárias/mensais aparecem com progress bars
- [ ] Gráficos carregam sem erros
- [ ] Últimos trades aparecem na tabela
- [ ] Diagnóstico mostra status do sistema

## 📈 Exemplo de Output Esperado

### Se Tudo OK (Ganhando):
```
✅ Capital Atual: $1,050.25 (+$50.25, +5.03%)
✅ PnL Hoje: +$12.50 (5 trades)
✅ PnL Este Mês: +$87.45 (34 trades)
✅ PnL Geral: +$50.25 (ROI: +5.03%)

🤖 Status dos 5 Bots:
  🟢 Bot Estável: Ativo, 4/4 posições, PnL +$15.20
  🟢 Bot Médio: Ativo, 3/4 posições, PnL +$12.10
  🟢 Bot Volátil: Ativo, 2/3 posições, PnL +$8.50
  🟢 Bot Meme: Ativo, 1/2 posições, PnL +$5.20
  🟢 Unico Bot: Ativo, 5/9 posições, PnL +$9.25

✅ Sistema Operando Normalmente!
```

### Se Tudo ERRADO (Sem Ganho):
```
🔴 Capital Atual: $950.00 (-$50.00, -5.00%)
🔴 PnL Hoje: -$2.50 (1 trade)
🔴 PnL Este Mês: -$25.00 (12 trades)
🔴 PnL Geral: -$50.00 (ROI: -5.00%)

🤖 Status dos 5 Bots:
  ⏹️ Bot Estável: Inativo
  ⏹️ Bot Médio: Inativo
  ⏹️ Bot Volátil: Inativo
  ⏹️ Bot Meme: Inativo
  ⏹️ Unico Bot: Inativo

❌ CRÍTICO: Nenhum bot está rodando!
Nenhum trade realizado - verifique a conexão com Binance.

🚀 Ações Corretivas:
1. Verificar se bots estão rodando:
   ps aux | grep main_multibot
2. Se não tiver processo, iniciar:
   cd /home/ubuntu/App_Leonardo
   nohup ./venv/bin/python main_multibot.py > logs/bot.log 2>&1 &
3. Verificar logs:
   tail -f logs/bot.log
```

## 📝 Notas Importantes

1. **Capital Inicial**: Definido como $1,000 USDT na primeira execução
2. **Atualização**: Dados atualizam a cada 3 segundos (cache)
3. **Período do Mês**: De 01/mês até hoje
4. **Diagnóstico Automático**: Detecta problemas comuns e sugere soluções
5. **Cores**: Verde para lucro, Vermelho para perda (automático)

## 🎯 Objetivos Diários

- **Meta Dia**: $2.50 (0.25% do capital inicial)
- **Meta Mês**: $75.00 (7.5% do capital)
- **Meta Geral**: $250+ (25%+ ROI)

---

**Desenvolvido por**: GitHub Copilot  
**Sistema**: R7 Trading Bot v2.0  
**Data**: 8 de Dezembro de 2025
