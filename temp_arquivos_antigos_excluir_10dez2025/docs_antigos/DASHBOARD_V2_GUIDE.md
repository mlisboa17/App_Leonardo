# 📊 DASHBOARD v2.0 - Guia Completo

## 🎯 O Que Foi Implementado

### ✅ Integração CCXT com Binance
- Conexão real com API da Binance (Testnet)
- Busca de preços ao vivo
- Dados OHLCV (candlestick) em tempo real
- Suporte a 8 criptomoedas simultâneas

### ✅ Estatísticas Completas

#### 1. Saldos Detalhados
```yaml
Saldo USD: $1000.00
  - Dinheiro líquido disponível para trades
  
Valor Total: $1500.00
  - USD + valor de todas as criptos
  
Valor em Criptos: $500.00
  - Soma de todas as posições
```

#### 2. Trades do Dia
```yaml
Trades Hoje: 12
  - Quantidade de trades executados hoje
  
Posições Abertas: 3
  - BTC/USDT, ETH/USDT, SOL/USDT abertas
  
Total Trades: 145
  - Histórico completo desde início
```

#### 3. Performance
```yaml
PnL Total: +$125.50
  - Lucro/Perda acumulado total
  
PnL Hoje: +$23.40
  - Lucro/Perda do dia atual
  
Win Rate: 62.5%
  - Taxa de acerto (trades ganhos / total)
```

---

## 🪙 Cards de Criptomoedas (8 Cards)

Cada cripto tem seu próprio card com:

### 📈 Mini-Gráfico Candlestick
- Últimos 50 candles de 5 minutos
- Cores: Verde (alta) / Vermelho (baixa)
- Atualização automática a cada 5 segundos

### 💰 Estatísticas Financeiras
```
BTC Card Example:
┌─────────────────────────────┐
│ BTC 📈                      │
│ $95,234.50                  │
├─────────────────────────────┤
│ [Mini Candlestick Chart]    │
├─────────────────────────────┤
│ Investido:    $50.00        │
│ Valor Atual:  $52.30        │
│ PnL:          +$2.30        │
│ PnL %:        +4.6%         │
│ Win Rate:     65.0%         │
│ Tendência:    BULLISH       │
└─────────────────────────────┘
```

### 🎯 Informações Por Card

| Campo | Descrição |
|-------|-----------|
| **Símbolo** | BTC, ETH, SOL, BNB, XRP, LINK, DOGE, LTC |
| **Preço Atual** | Último preço da Binance |
| **Mini-Gráfico** | Candlestick 5m (50 velas) |
| **Investido USD** | Quanto você investiu nesta cripto |
| **Valor Atual USD** | Valor atual do investimento |
| **PnL USD** | Lucro/Perda em dólares |
| **PnL %** | Lucro/Perda em porcentagem |
| **Win Rate** | Taxa de acerto só desta cripto |
| **Tendência** | BULLISH 📈 / BEARISH 📉 / NEUTRAL ➡️ |

---

## 📋 Tabela de Trades Recentes

Últimos 10 trades executados:

| Coluna | Exemplo | Descrição |
|--------|---------|-----------|
| Símbolo | BTC/USDT | Qual cripto |
| Lado | BUY/SELL | Compra ou venda |
| Entrada | $95,234.50 | Preço de entrada |
| Saída | $95,678.20 | Preço de saída |
| PnL USD | +$8.87 | Lucro em USD |
| PnL % | +0.93% | Lucro em % |
| Hora | 14:32:15 | Horário do trade |

**Cores:**
- Verde: Trades lucrativos
- Vermelho: Trades com perda

---

## 🔄 Atualização Automática

### Intervalo: 5 segundos
- Todos os dados são atualizados
- Mini-gráficos recarregam
- Estatísticas recalculadas
- Sem necessidade de refresh manual

---

## 🎨 API Endpoints Criados

### 1. `/api/status`
**Retorna:**
```json
{
  "balance_usd": 1000.00,
  "balance_crypto": {
    "BTC/USDT": {
      "amount": 0.000524,
      "invested_usd": 50.00,
      "current_value_usd": 52.30,
      "pnl_usd": 2.30,
      "pnl_pct": 4.6,
      "trend": "BULLISH",
      "win_rate": 65.0
    }
  },
  "total_trades_today": 12,
  "open_positions": 3,
  "win_rate": 62.5
}
```

### 2. `/api/crypto/{symbol}/stats`
**Exemplo: `/api/crypto/BTC/USDT/stats`**
```json
{
  "symbol": "BTC/USDT",
  "invested_usd": 50.00,
  "current_value_usd": 52.30,
  "pnl_usd": 2.30,
  "total_trades": 45,
  "win_rate": 65.0,
  "trend": "BULLISH",
  "recent_trades": [...]
}
```

### 3. `/api/crypto/{symbol}/chart`
**Exemplo: `/api/crypto/BTC/USDT/chart?timeframe=5m&limit=50`**
```json
{
  "symbol": "BTC/USDT",
  "timeframe": "5m",
  "candles": [
    {
      "timestamp": "2025-11-29T14:30:00",
      "open": 95234.50,
      "high": 95456.78,
      "low": 95123.45,
      "close": 95345.67,
      "volume": 1234.56,
      "rsi": 65.4,
      "macd": 123.45
    }
  ]
}
```

### 4. `/api/prices/live`
**Retorna preços ao vivo de todas as 8 criptos:**
```json
{
  "BTC/USDT": {
    "price": 95234.50,
    "change_24h": 2.34,
    "high_24h": 96000.00,
    "low_24h": 94500.00,
    "volume_24h": 45678901.23
  },
  "ETH/USDT": {...},
  ...
}
```

### 5. `/api/trades/recent`
**Últimos 20 trades:**
```json
[
  {
    "id": 145,
    "timestamp": "2025-11-29T14:32:15",
    "symbol": "BTC/USDT",
    "side": "SELL",
    "entry_price": 95234.50,
    "exit_price": 95678.20,
    "pnl": 8.87,
    "pnl_pct": 0.93,
    "duration_minutes": 15.5
  }
]
```

### 6. `/api/summary`
**Resumo geral do dashboard:**
```json
{
  "balance_usd": 1000.00,
  "total_value_usd": 1500.00,
  "total_trades_today": 12,
  "open_positions": 3,
  "win_rate": 62.5,
  "cryptos": [
    {
      "symbol": "BTC",
      "invested_usd": 50.00,
      "trend": "BULLISH",
      ...
    }
  ]
}
```

---

## 💾 Banco de Dados Atualizado

### Nova Tabela: `crypto_balances`
```sql
CREATE TABLE crypto_balances (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE,
    
    -- Saldos
    amount FLOAT DEFAULT 0.0,
    invested_usd FLOAT DEFAULT 0.0,
    current_value_usd FLOAT DEFAULT 0.0,
    pnl_usd FLOAT DEFAULT 0.0,
    pnl_pct FLOAT DEFAULT 0.0,
    
    -- Estatísticas
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate FLOAT DEFAULT 0.0,
    
    -- Tendência
    trend VARCHAR(20) DEFAULT 'NEUTRAL',
    trend_strength FLOAT DEFAULT 0.0,
    
    last_update TIMESTAMP
);
```

### Tabela `bot_status` Atualizada
```sql
CREATE TABLE bot_status (
    id SERIAL PRIMARY KEY,
    
    -- Saldos
    balance_usd FLOAT DEFAULT 1000.0,
    initial_balance FLOAT DEFAULT 1000.0,
    
    -- Trades
    total_trades INTEGER DEFAULT 0,
    total_trades_today INTEGER DEFAULT 0,  -- NOVO
    open_positions INTEGER DEFAULT 0,      -- NOVO
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    
    -- Timestamps
    last_trade_time TIMESTAMP              -- NOVO
);
```

---

## 🚀 Como Usar

### 1. Iniciar Sistema
```powershell
.\START_V2.bat
```

### 2. Aguardar Inicialização
- Backend: http://localhost:8001 (3s)
- Frontend: http://localhost:8050 (5s)

### 3. Acessar Dashboard
Abra navegador em: **http://localhost:8050**

### 4. Visualizar Dados
- **Cards superiores**: Estatísticas gerais
- **Grid 8 criptos**: Investimento por moeda
- **Tabela inferior**: Trades recentes

---

## 📊 Layout do Dashboard

```
┌──────────────────────────────────────────────────────────────┐
│  🚀 App Leonardo Trading Bot v2.0                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                    │
│  │ USD  │  │Total │  │Trades│  │ Open │                    │
│  │$1000 │  │$1500 │  │  12  │  │  3   │                    │
│  └──────┘  └──────┘  └──────┘  └──────┘                    │
│                                                               │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                    │
│  │ PnL  │  │ PnL  │  │ Win  │  │Total │                    │
│  │+$125 │  │ +$23 │  │ 62%  │  │ 145  │                    │
│  └──────┘  └──────┘  └──────┘  └──────┘                    │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│  🪙 Portfólio de Criptomoedas                                │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                    │
│  │ BTC  │  │ ETH  │  │ SOL  │  │ BNB  │                    │
│  │ 📈   │  │ 📈   │  │ ➡️   │  │ 📉   │                    │
│  │[Graf]│  │[Graf]│  │[Graf]│  │[Graf]│                    │
│  │$50   │  │$45   │  │$30   │  │$25   │                    │
│  └──────┘  └──────┘  └──────┘  └──────┘                    │
│                                                               │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                    │
│  │ XRP  │  │LINK  │  │DOGE  │  │ LTC  │                    │
│  │ 📈   │  │ ➡️   │  │ 📉   │  │ 📈   │                    │
│  │[Graf]│  │[Graf]│  │[Graf]│  │[Graf]│                    │
│  │$20   │  │$15   │  │$10   │  │$5    │                    │
│  └──────┘  └──────┘  └──────┘  └──────┘                    │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│  📋 Trades Recentes                                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Símbolo | Lado | Entrada | Saída | PnL | PnL% | Hora       │
│  ──────────────────────────────────────────────────────────  │
│  BTC     | SELL | $95234  |$95678 |+$8.87|+0.93%| 14:32:15  │
│  ETH     | BUY  | $3456   |$3478  |+$4.40|+0.64%| 14:28:43  │
│  ...                                                          │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 Próximos Passos

### Para Testar:
1. Execute `.\SETUP_DOCKER.bat` (PostgreSQL + Redis)
2. Execute `.\START_V2.bat`
3. Acesse http://localhost:8050
4. Veja os dados carregarem em tempo real

### Para Iniciar Trading:
1. No backend, endpoint `/api/bot/start`
2. O bot começará a:
   - Buscar preços da Binance
   - Calcular indicadores (RSI, MACD)
   - Abrir/fechar posições
   - Salvar tudo no PostgreSQL
   - Atualizar dashboard via WebSocket

---

## ✅ Checklist Implementado

- [x] Integração CCXT com Binance
- [x] Endpoint `/api/status` com saldos USD + Crypto
- [x] Endpoint `/api/crypto/{symbol}/stats` por moeda
- [x] Endpoint `/api/crypto/{symbol}/chart` com OHLCV
- [x] Endpoint `/api/prices/live` todas as 8 criptos
- [x] Endpoint `/api/trades/recent` histórico
- [x] Endpoint `/api/summary` resumo dashboard
- [x] Tabela `crypto_balances` no PostgreSQL
- [x] Tabela `bot_status` atualizada
- [x] Dashboard v2.0 com 8 cards de criptos
- [x] Mini-gráficos candlestick por cripto
- [x] Estatísticas: Investido, Valor Atual, PnL
- [x] Tendências: BULLISH/BEARISH/NEUTRAL
- [x] Win Rate por cripto
- [x] Tabela de trades recentes
- [x] Atualização automática a cada 5s

---

## 🔥 SISTEMA COMPLETO E FUNCIONAL!

Execute `.\START_V2.bat` e veja a mágica acontecer! 🚀
