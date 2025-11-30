# 📜 HISTÓRICO COMPLETO DO PROJETO APP LEONARDO

## 🎯 Objetivo Principal
**Meta: $100/dia** através de trading automatizado de criptomoedas, comprando barato e vendendo quando a tendência virar de queda.

---

## 📅 Linha do Tempo das Implementações

### 🔹 FASE 1: Estratégia Inicial
- Implementação de scalping básico com RSI fixo (35/65)
- Problema identificado: Muitas moedas nunca chegam ao RSI 35

### 🔹 FASE 2: RSI Adaptativo por Moeda
- **Solução**: Analisar histórico de cada moeda para descobrir seus níveis reais de RSI
- Criado `quick_analysis.py` para análise histórica
- Gerado `crypto_profiles.json` com thresholds específicos:

```
BTC/USDT: compra<40.3, venda>63.2
ETH/USDT: compra<39.9, venda>60.8
SOL/USDT: compra<39.6, venda>62.9
BNB/USDT: compra<40.1, venda>60.2
XRP/USDT: compra<40.9, venda>63.1
LINK/USDT: compra<41.2, venda>62.2
DOGE/USDT: compra<39.8, venda>60.9
LTC/USDT: compra<39.4, venda>59.8
```

### 🔹 FASE 3: Lógica "Segurar até Virar Queda"
- **Conceito**: Não vender só porque subiu, esperar a tendência VIRAR
- Implementado sistema de detecção de tendência com 4 indicadores:
  1. MACD (acima/abaixo do sinal)
  2. EMA9 vs EMA21 (cruzamento)
  3. Preço vs SMA20
  4. Direção do RSI

### 🔹 FASE 4: Biblioteca Profissional TA
- Integrado biblioteca `ta` (Technical Analysis Library)
- Indicadores disponíveis: RSI, MACD, SMA, EMA, Bollinger, ATR, ADX

### 🔹 FASE 5: SmartStrategy Completa
- Criado `smart_strategy.py` com toda a lógica integrada
- Sistema de urgência: relaxa RSI se ficar sem trades por muito tempo

---

## 🏗️ Arquitetura do Sistema

```
App_Leonardo/
├── main.py                      # Bot principal (síncrono)
├── config/
│   └── config.yaml              # Configurações (8 cryptos, $50/trade)
├── data/
│   ├── crypto_profiles.json     # Perfis RSI por moeda
│   ├── cache/                   # Cache de dados
│   └── reports/                 # Relatórios de trades
├── src/
│   ├── core/
│   │   ├── exchange_client.py   # Cliente Binance (REST)
│   │   ├── websocket_client.py  # Cliente WebSocket (NOVO)
│   │   ├── dashboard.py         # Dashboard web
│   │   └── utils.py             # Utilidades
│   ├── indicators/
│   │   └── technical_indicators.py
│   ├── strategies/
│   │   ├── smart_strategy.py    # ⭐ Estratégia principal
│   │   ├── simple_strategies.py
│   │   └── quick_analysis.py    # Análise histórica
│   └── safety/
│       └── safety_manager.py    # Gerenciador de risco
├── bot_dashboard/               # Django admin
└── dashboard_web/               # Django settings
```

---

## 🧠 SmartStrategy - Lógica Detalhada

### Entrada (Compra)
```python
# Condições para COMPRAR:
1. RSI < threshold_adaptativo (ex: BTC < 40.3)
2. MACD cruzando para cima
3. Preço próximo ou abaixo da SMA20

# Sistema de Urgência:
- 5+ min sem trade: RSI threshold +1
- 10+ min sem trade: RSI threshold +2
- 30+ min sem trade: RSI threshold +4
```

### Manter Posição
```python
# SEGURA enquanto tendência for ALTA:
- MACD > Sinal ✓
- EMA9 > EMA21 ✓
- Preço > SMA20 ✓
- RSI subindo ✓

# Se 3+ sinais de ALTA → SEGURA
```

### Saída (Venda)
```python
# Condições para VENDER:

1. STOP LOSS: -1.5% (SEMPRE ativo)
2. TAKE PROFIT MAX: +5%
3. TEMPO MÁXIMO: 15 minutos
4. RSI OVERBOUGHT: RSI > sell_threshold (ex: 63)
5. TENDÊNCIA VIROU: 3+ sinais de QUEDA
```

---

## 📊 Configurações Atuais (config.yaml)

```yaml
trading:
  symbols:
    - BTC/USDT
    - ETH/USDT
    - SOL/USDT
    - BNB/USDT
    - XRP/USDT
    - LINK/USDT
    - DOGE/USDT
    - LTC/USDT
  timeframe: 1m
  amount_per_trade: 50      # $50 por trade
  max_positions: 4          # Máx 4 posições simultâneas

strategy:
  type: smart_hold
  daily_profit_target: 100  # Meta $100/dia
  stop_loss_pct: 1.5
  take_profit_pct: 5.0

safety:
  max_daily_loss: 50        # Máx perda diária $50
  min_balance: 100          # Saldo mínimo para operar

execution:
  interval_seconds: 10
  dry_run: false

exchange:
  name: binance
  testnet: true
```

---

## 🔌 WebSocket - Implementação

### Por que WebSocket?
- **REST API**: Polling a cada X segundos (mais lento, mais requests)
- **WebSocket**: Dados em tempo real instantâneos

### Streams Disponíveis na Binance:
```
btcusdt@kline_1m     # Candles 1 minuto
btcusdt@trade        # Trades em tempo real
btcusdt@ticker       # Ticker 24h
btcusdt@depth        # Order book
```

---

## 📁 Arquivos Criados/Modificados

| Arquivo | Ação | Descrição |
|---------|------|-----------|
| `src/strategies/smart_strategy.py` | CRIADO | Estratégia principal |
| `src/strategies/quick_analysis.py` | CRIADO | Análise histórica |
| `data/crypto_profiles.json` | GERADO | Perfis RSI por moeda |
| `src/strategies/__init__.py` | MODIFICADO | Export SmartStrategy |
| `main.py` | MODIFICADO | Integração SmartStrategy |
| `config/config.yaml` | MODIFICADO | 8 cryptos, smart_hold |
| `ESTRATEGIA_SCALPING.md` | CRIADO | Documentação estratégia |
| `src/core/websocket_client.py` | CRIADO | Cliente WebSocket |

---

## 🚀 Como Executar

### Modo Normal (REST API):
```bash
cd App_Leonardo
python main.py
```

### Modo WebSocket (Tempo Real):
```bash
cd App_Leonardo
python main_websocket.py
```

### Testar SmartStrategy:
```bash
cd App_Leonardo
python test_smart_strategy.py
```

### Gerar Novos Perfis RSI:
```bash
cd App_Leonardo
python src/strategies/quick_analysis.py
```

---

## 📈 Métricas de Sucesso

Para atingir $100/dia com $50/trade:
- **Opção A**: 2 trades com +100% cada (improvável)
- **Opção B**: 10 trades com +20% cada (difícil)
- **Opção C**: 50 trades com +4% cada (possível!)
- **Opção D**: 100 trades com +2% cada (scalping clássico)

### Cálculo Real:
```
$50 por trade × 2% lucro médio = $1 por trade
$100 meta ÷ $1 = 100 trades/dia necessários
100 trades ÷ 8 moedas = ~12 trades por moeda
24 horas ÷ 12 trades = 1 trade a cada 2 horas por moeda
```

---

## 🔧 Próximos Passos Sugeridos

1. [ ] Implementar WebSocket para dados em tempo real
2. [ ] Dashboard web com gráficos de performance
3. [ ] Backtesting com dados históricos
4. [ ] Notificações via Telegram
5. [ ] Múltiplas exchanges (Bybit, KuCoin)
6. [ ] Machine Learning para otimizar thresholds

---

## 📞 Comandos Úteis

```bash
# Ver logs em tempo real
tail -f logs/trading.log

# Verificar posições abertas
python -c "from main import TradingBot; b = TradingBot(); print(b.positions)"

# Atualizar perfis RSI
python src/strategies/quick_analysis.py

# Testar conexão
python test_connection.py
```

---

*Última atualização: 30 de Novembro de 2025*
