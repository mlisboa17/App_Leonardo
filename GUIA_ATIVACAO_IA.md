# 🤖 GUIA DE ATIVAÇÃO DA IA - App Leonardo v3.0

## 📋 STATUS ATUAL

### ✅ Componentes Implementados:

1. **Verificador de Status da IA** (`verify_ai_status.py`)
   - Verifica operacionalidade dos sistemas
   - Ativa IA se não estiver rodando
   - Diagnostica problemas

2. **Market Monitor** (`market_monitor.py`)
   - Monitora criptomoedas em tempo real
   - Coleta dados do CoinGecko, Binance, Fear & Greed
   - Detecta oportunidades de trading

3. **Capital Manager** (`capital_manager.py`)
   - Valida sinais com R:R ≥ 2:1
   - Calcula tamanho ótimo de posição
   - Respeita limites de risco e por bot

4. **AI Orchestrator** (`ai_orchestrator.py`)
   - Orquestra todo o sistema
   - Integra monitor + capital manager
   - Gera e executa sinais de trading

---

## 🚀 INICIALIZAÇÃO RÁPIDA

### Passo 1: Verificar Status da IA

```bash
python verify_ai_status.py
```

**Esperado:**
```
🤖 STATUS DO SISTEMA DE IA - App Leonardo v3.0
==================================================
📊 COMPONENTES:
  • IA Disponível: ✅ SIM
  • Status: 🟢 OPERACIONAL

🧠 AI MANAGER:
  • Status: ACTIVE
  • Inicializado: ✅
  • Auto-Adjust: 🔵 Ativo
  ...
```

---

### Passo 2: Se IA NÃO está operacional, ativar

```bash
python verify_ai_status.py activate
```

**Esperado:**
```
🚀 Ativando IA...
🤖 ATIVANDO SISTEMA DE IA
==================================================
📍 Etapa 1: Inicializando AIManager...
✅ AIManager inicializado

📍 Etapa 2: Habilitando Auto-Adjust...
✅ Auto-Adjust habilitado

... [outras etapas]

✅ IA ATIVADA COM SUCESSO!
```

---

### Passo 3: Iniciar Market Monitor

O monitor coleta dados de criptomoedas em tempo real:

```bash
python market_monitor.py
```

**Esperado:**
```
📡 INICIANDO MARKET MONITOR
==================================================
🔄 Atualizando dados de mercado...
✅ BTCUSDT: $45,234.50 (+2.34%)
✅ ETHUSDT: $2,567.89 (+1.87%)
...

🎭 Fear & Greed: 42 (Fear)

📊 RESUMO DO MERCADO
```

---

### Passo 4: Verificar Capital Disponível

```bash
python capital_manager.py
```

**Esperado:**
```
💰 RESUMO DO CAPITAL DISPONÍVEL
==================================================
Capital Inicial:        $1,000.00
Capital Atual:          $1,050.25
PnL Total:              $50.25 (+5.03%)

Investido:              $470.65
Disponível:             $579.35
Posições Abertas:       3

📊 LIMITES DE RISCO:
  • Máx risco por trade: 2.0% (~$20.00)
  • Mínimo R:R:          2.0:1

🤖 LIMITES POR BOT:
  • bot_estavel: Máx $39.15 | 4 posições | Risco 0.5%
  • bot_medio:   Máx $39.15 | 4 posições | Risco 1.0%
  ...
```

---

### Passo 5: Iniciar AI Orchestrator

O orquestrador integra tudo e gera sinais de trading:

```bash
python ai_orchestrator.py start
```

**Esperado:**
```
🎯 INICIANDO AI ORCHESTRATOR
==================================================
✅ Orquestrador iniciado com sucesso

🔄 Iniciando loop de orquestração...

⏱️ Ciclo #1
==================================================
📡 Analisando dados de mercado...
   🎭 Fear & Greed: 42 (Fear)
   📊 8 criptomoedas monitoradas
   📉 3 criptomoedas em oversold (RSI < 30)

🎯 Gerando sinais de trading...
   ⭐ BTCUSDT: OVERSOLD (Confiança: 85%)
   ⭐ ETHUSDT: EXTREME_FEAR (Confiança: 80%)

⚙️ Processando sinais de trading...
   ✅ COMPRA VALIDADA: BTCUSDT
      R:R: 2.34:1
      Tamanho: $39.15
      Risco: $18.72
      Recompensa potencial: $43.87

✅ Ciclo #1 concluído
```

---

## 📊 EXEMPLO DE FLUXO COMPLETO

### Cenário: Mercado em Extreme Fear (< 25)

```
1. MARKET MONITOR detecta:
   ✅ Fear & Greed: 20 (Extreme Fear)
   ✅ BTCUSDT RSI: 28 (Oversold)
   ✅ Queda de 24h: -5.2%
   ✅ Oportunidade: ALTA

2. AI ORCHESTRATOR gera sinal:
   ✅ Symbol: BTCUSDT
   ✅ Type: OVERSOLD
   ✅ Action: BUY_SIGNAL
   ✅ Confidence: 85%

3. CAPITAL MANAGER valida:
   ✅ Entry: $45,000
   ✅ Stop Loss: $44,775 (Risco: $225)
   ✅ Take Profit: $45,450 (Reward: $450)
   ✅ R:R: 2.0:1 ✓ (mínimo: 2:1)
   ✅ Saldo: $579.35 > $39.15 ✓
   ✅ Risco: 1.8% < 2.0% máximo ✓
   ✅ Bot limite: $39.15 = max ✓

4. RESULTADO:
   ✅ TRADE EXECUTADO
   ✅ Comprado: 1 BTC @ $45,000
   ✅ Posição aberta
   ✅ Capital disponível: $540.20
```

---

## ⚙️ CONFIGURAÇÃO DE REGRAS

### 1. Limite de Risco: 2% máximo por trade

Arquivos: `capital_manager.py` linha 47
```python
self.max_risk_per_trade = 0.02  # 2%
```

### 2. Mínimo R:R: 2:1

Arquivos: `capital_manager.py` linha 48
```python
self.min_reward_ratio = 2.0  # 2:1
```

### 3. Limites por Bot

Arquivo: `capital_manager.py` linhas 52-62
```python
self.bot_limits = {
    'bot_estavel': {'max_per_trade': 39.15, 'max_positions': 4, 'risk_pct': 0.5},
    'bot_medio': {'max_per_trade': 39.15, 'max_positions': 4, 'risk_pct': 1.0},
    'bot_volatil': {'max_per_trade': 39.15, 'max_positions': 3, 'risk_pct': 1.2},
    'bot_meme': {'max_per_trade': 30.0, 'max_positions': 2, 'risk_pct': 1.5},
    'unico_bot': {'max_per_trade': 50.0, 'max_positions': 9, 'risk_pct': 0.6},
}
```

### 4. Confiança Mínima para Trade

Arquivo: `ai_orchestrator.py` linha 39
```python
self.min_confidence_for_trade = 0.75  # 75%
```

### 5. Intervalo de Ciclo

Arquivo: `ai_orchestrator.py` linha 40
```python
self.cycle_interval = 300  # 5 minutos
```

---

## 📈 MONITORAMENTO EM TEMPO REAL

### Ver Status do Orquestrador

```bash
python ai_orchestrator.py status
```

### Gerar Relatório Completo

```bash
python ai_orchestrator.py report
```

### Histórico de Ciclos

Arquivo: `data/ai/orchestrator_state.json`
```json
{
  "running": true,
  "start_time": "2025-01-12T10:30:00",
  "cycles_completed": 12,
  "trades_executed": 3,
  "last_update": "2025-01-12T10:35:00"
}
```

---

## 🔔 ALERTAS E NOTIFICAÇÕES

### Dados de Mercado

Arquivo: `data/ai/market_data.json`
```json
{
  "timestamp": "2025-01-12T10:35:00",
  "data": {
    "FEAR_GREED": {
      "value": 42,
      "classification": "Fear"
    },
    "BTCUSDT": {
      "price": 45234.50,
      "price_change_24h": 2.34,
      "rsi": 65.3,
      "trend": "bullish",
      "confidence": 0.9
    }
  }
}
```

### Oportunidades Detectadas

Arquivo: `data/ai/market_alerts.json`
```json
{
  "timestamp": "2025-01-12T10:35:00",
  "alerts": [
    {
      "symbol": "BTCUSDT",
      "type": "OVERSOLD",
      "reason": "RSI 28 + queda 5.2%",
      "confidence": 0.85,
      "action": "BUY_SIGNAL"
    }
  ]
}
```

---

## 🛠️ TROUBLESHOOTING

### Problema: "IA não disponível"

**Solução:**
```bash
python verify_ai_status.py full
```

Isto irá:
1. Verificar status
2. Ativar se não estiver operando
3. Aguardar estabilização
4. Verificar novamente

### Problema: "Saldo insuficiente"

**Verificar:**
```bash
python capital_manager.py analyze
```

**Causas comuns:**
- Muitas posições abertas
- Capital já investido em outros trades
- Limite do bot atingido

### Problema: "R:R insuficiente"

**Significa:**
- Sinal de trading rejeitado
- Risco/Recompensa < 2:1
- Esperamos por melhor setup

### Problema: "Nenhum sinal gerado"

**Possíveis causas:**
1. Mercado neutro (sem Fear/Greed extremo)
2. RSI não em oversold/overbought
3. Confiança abaixo de 75%

**Verificar:**
```bash
python market_monitor.py
```

---

## 📊 DASHBOARDS DE ACOMPANHAMENTO

### Dashboard PnL (já existente)

Acesse no Streamlit:
```
http://localhost:8501/
```

Páginas disponíveis:
- Dashboard Multibot (Home)
- Posições
- Distribuição de Capital
- Monitoramento do Sistema
- **PnL Detalhado (com per-bot breakdown)**

---

## 🎯 PRÓXIMAS ETAPAS

### Hoje:

1. ✅ Verificar status da IA
2. ✅ Ativar se necessário
3. ✅ Iniciar Market Monitor
4. ✅ Rodar AI Orchestrator em background

### Esta Semana:

1. Analisar sinais gerados
2. Validar execução de trades
3. Monitorar desempenho
4. Ajustar confiança mínima se necessário

### Este Mês:

1. Otimizar parâmetros baseado em dados
2. Adicionar mais criptomoedas ao watchlist
3. Implementar histórico de sinais
4. Análise de taxa de acerto

---

## 📞 SUPPORT

### Arquivos de Log

```bash
# Ver logs em tempo real
tail -f data/ai/ai.log

# Buscar erros
grep ERROR data/ai/ai.log
```

### Histórico de Estado

```
data/ai/
├── orchestrator_state.json      # Estado do orquestrador
├── market_data.json              # Dados de mercado atualizados
├── market_alerts.json            # Alertas de oportunidades
├── trade_signals.json            # Sinais gerados
└── ai_state.json                 # Estado da IA
```

---

## ✅ CHECKLIST DE ATIVAÇÃO

- [ ] Executar `verify_ai_status.py`
- [ ] Verificar que IA está "OPERACIONAL"
- [ ] Se não, executar `verify_ai_status.py activate`
- [ ] Executar `market_monitor.py`
- [ ] Verificar dados de mercado
- [ ] Executar `capital_manager.py`
- [ ] Verificar capital disponível
- [ ] Iniciar `python ai_orchestrator.py start`
- [ ] Monitorar primeiros 30 minutos
- [ ] Verificar status com `ai_orchestrator.py status`
- [ ] Gerar relatório com `ai_orchestrator.py report`
- [ ] Configurar execução automática (cron/daemon)

---

**Data de Implementação:** Janeiro 2025
**Versão:** App Leonardo v3.0
**Status:** ✅ PRONTO PARA OPERAÇÃO
