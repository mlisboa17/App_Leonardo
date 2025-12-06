# 📜 HISTÓRICO DE DESENVOLVIMENTO - APP LEONARDO

> **Bot de Trading de Criptomoedas com Estratégia Inteligente**  
> Última atualização: 30/11/2025

---

## 📋 ÍNDICE

1. [Visão Geral do Projeto](#-visão-geral-do-projeto)
2. [Cronologia de Desenvolvimento](#-cronologia-de-desenvolvimento)
3. [Arquitetura do Sistema](#-arquitetura-do-sistema)
4. [Estratégia de Trading](#-estratégia-de-trading)
5. [Arquivos Criados/Modificados](#-arquivos-criadosmodificados)
6. [Configurações](#-configurações)
7. [Como Executar](#-como-executar)
8. [Próximos Passos](#-próximos-passos)

---

## 🎯 VISÃO GERAL DO PROJETO

### Objetivo Principal
Criar um bot de trading automatizado para criptomoedas com meta de **$100/dia** de lucro, utilizando uma estratégia inteligente que:
- Compra quando o preço está barato (RSI adaptativo por moeda)
- **SEGURA** enquanto a tendência for de ALTA
- Vende **APENAS** quando a tendência virar de QUEDA

### Tecnologias Utilizadas
- **Linguagem**: Python 3.10+
- **Backend API**: FastAPI (porta 8001)
- **Dashboard**: Plotly Dash (porta 8050)
- **Banco de Dados**: SQLite (local), PostgreSQL (produção)
- **Exchange**: Binance (Testnet para desenvolvimento)
- **Biblioteca TA**: `ta` (Technical Analysis Library)

---

## 📅 CRONOLOGIA DE DESENVOLVIMENTO

### 🗓️ 30/11/2025 - Sessão Principal

#### 1. Definição da Meta e Estratégia Inicial
- **Requisito**: Meta de $100/dia através de múltiplas operações
- **Decisão**: Estratégia scalping com compra/venda frequente
- **Problema identificado**: RSI fixo de 35 não funciona para todas as moedas

#### 2. Análise de RSI por Moeda
- **Descoberta**: Cada criptomoeda tem comportamento diferente
- **Solução**: Analisar histórico de cada moeda para determinar RSI adaptativo
- **Implementação**: Script `quick_analysis.py` para análise automatizada

#### 3. Integração da Biblioteca TA (Technical Analysis)
- **Motivo**: Cálculos profissionais de indicadores
- **Indicadores implementados**:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - SMA (Simple Moving Average) - 20 e 50 períodos
  - EMA (Exponential Moving Average) - 9 e 21 períodos
  - Bollinger Bands
  - ATR (Average True Range)
  - ADX (Average Directional Index)

#### 4. Criação da Smart Strategy
- **Lógica principal**: "Comprar barato, segurar enquanto ALTA, vender quando virar QUEDA"
- **Arquivo**: `src/strategies/smart_strategy.py`
- **Features**:
  - RSI adaptativo por moeda
  - Sistema de urgência (relaxa RSI se ficar sem trades)
  - Detecção de tendência (4 indicadores)
  - Stop loss (-1.5%) e take profit máximo (+5%)

#### 5. Geração dos Perfis de Criptomoedas
- **Script executado**: `quick_analysis.py`
- **Dados coletados**: 10 dias de candles de 15 minutos
- **Output**: `data/crypto_profiles.json`
- **8 moedas analisadas**: BTC, ETH, SOL, BNB, XRP, LINK, DOGE, LTC

#### 6. Integração com Main.py
- **Modificações**:
  - Import do SmartStrategy com fallback
  - `_initialize_components()` usa SmartStrategy
  - `process_symbol()` usa lógica inteligente de venda
  - Atualização de estatísticas diárias

#### 7. Atualização do Config.yaml
- **Mudanças**:
  - 8 símbolos configurados
  - Estratégia: `smart_hold`
  - Valor por trade: $50
  - Meta diária: $100

#### 8. Testes de Validação
- **Teste criado**: `test_smart_strategy.py`
- **Resultado**: ✅ Todos os métodos disponíveis e funcionando
- **Perfis carregados**: 8 moedas com RSI adaptativo

---

## 🏗️ ARQUITETURA DO SISTEMA

```
App_Leonardo/
│
├── main.py                    # 🤖 Bot principal (síncrono)
├── main_websocket.py          # 🔌 Bot com WebSocket (tempo real) [PENDENTE]
│
├── config/
│   └── config.yaml            # ⚙️ Configurações gerais
│
├── data/
│   ├── crypto_profiles.json   # 📊 Perfis RSI por moeda
│   ├── cache/                 # Cache de dados
│   └── reports/               # Relatórios de trades
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── exchange_client.py # 🔗 Cliente da Binance
│   │   ├── utils.py           # 🛠️ Utilitários
│   │   └── dashboard.py       # 📈 Dashboard Dash
│   │
│   ├── indicators/
│   │   └── technical_indicators.py  # 📉 Indicadores técnicos
│   │
│   ├── safety/
│   │   └── safety_manager.py  # 🛡️ Gerenciador de segurança
│   │
│   └── strategies/
│       ├── __init__.py
│       ├── smart_strategy.py      # 🧠 Estratégia inteligente (PRINCIPAL)
│       ├── quick_analysis.py      # 📊 Análise de histórico
│       ├── simple_strategies.py   # 📋 Estratégias simples
│       └── adaptive_strategy.py   # 🔄 Estratégia adaptativa
│
├── bot_dashboard/             # 🌐 Dashboard Django
│   └── templates/
│
└── logs/                      # 📝 Arquivos de log
```

---

## 🧠 ESTRATÉGIA DE TRADING

### Smart Strategy v2.0

#### Lógica de COMPRA
```
SE (RSI < RSI_adaptativo_da_moeda + ajuste_urgência)
   E (MACD > MACD_Signal)
   E (Preço próximo da SMA20)
ENTÃO → COMPRAR
```

#### Sistema de Urgência
| Tempo sem trades | Ajuste RSI |
|------------------|------------|
| > 5 minutos      | +1         |
| > 10 minutos     | +2         |
| > 20 minutos     | +3         |
| > 30 minutos     | +4         |
| > 60 minutos     | +5         |

#### Lógica de SEGURAR
```
ENQUANTO tendência == ALTA:
    - MACD > MACD_Signal ✓
    - EMA9 > EMA21 ✓
    - Preço > SMA20 ✓
    - RSI subindo ✓
→ MANTER POSIÇÃO
```

#### Lógica de VENDA
```
SE (Stop Loss -1.5%) → VENDER IMEDIATAMENTE
SE (Take Profit +5%) → VENDER
SE (Tempo > 15 min E lucro > 0.3%) → VENDER
SE (RSI > RSI_venda E lucro > 0.3%) → VENDER
SE (Tendência == QUEDA com 3+ sinais) → VENDER
```

#### Detecção de Tendência (4 indicadores)
| Indicador | ALTA | QUEDA |
|-----------|------|-------|
| MACD      | MACD > Signal | MACD < Signal |
| Preço/SMA | Preço > SMA20 | Preço < SMA20 |
| RSI       | RSI subindo | RSI descendo |
| EMA       | EMA9 > EMA21 | EMA9 < EMA21 |

- **ALTA**: 3-4 indicadores positivos
- **QUEDA**: 3-4 indicadores negativos
- **LATERAL**: 2 ou menos

---

## 📁 ARQUIVOS CRIADOS/MODIFICADOS

### ✅ Criados Nesta Sessão

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `src/strategies/smart_strategy.py` | Novo | Estratégia inteligente principal |
| `src/strategies/quick_analysis.py` | Novo | Script de análise histórica |
| `data/crypto_profiles.json` | Novo | Perfis RSI das 8 moedas |
| `src/core/websocket_client.py` | Novo | Cliente WebSocket para Binance |
| `main_websocket.py` | Novo | Bot com dados em tempo real |
| `test_smart_strategy.py` | Novo | Script de teste |
| `HISTORICO_DE_DESENVOLVIMENTO.md` | Novo | Este arquivo |

### ✏️ Modificados Nesta Sessão

| Arquivo | Modificação |
|---------|-------------|
| `main.py` | Import SmartStrategy, lógica de venda inteligente |
| `config/config.yaml` | 8 símbolos, smart_hold, $50/trade |
| `src/strategies/__init__.py` | Export SmartStrategy |

---

## ⚙️ CONFIGURAÇÕES

### config.yaml (Atual)
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
  timeframe: "15m"
  amount_per_trade: 50
  max_positions: 3

strategy:
  type: "smart_hold"
  daily_profit_target: 100
  stop_loss_pct: -1.5
  take_profit_pct: 5.0

exchange:
  name: "binance"
  testnet: true

execution:
  dry_run: true
  interval_seconds: 60
```

### crypto_profiles.json (Gerado)
```json
{
  "BTCUSDT": {"buy_rsi": 40.3, "sell_rsi": 63.2, "rsi_mean": 51.7},
  "ETHUSDT": {"buy_rsi": 39.9, "sell_rsi": 60.8, "rsi_mean": 50.4},
  "SOLUSDT": {"buy_rsi": 39.6, "sell_rsi": 62.9, "rsi_mean": 51.2},
  "BNBUSDT": {"buy_rsi": 40.1, "sell_rsi": 60.2, "rsi_mean": 50.2},
  "XRPUSDT": {"buy_rsi": 40.9, "sell_rsi": 63.1, "rsi_mean": 52.0},
  "LINKUSDT": {"buy_rsi": 41.2, "sell_rsi": 62.2, "rsi_mean": 51.7},
  "DOGEUSDT": {"buy_rsi": 39.8, "sell_rsi": 60.9, "rsi_mean": 50.3},
  "LTCUSDT": {"buy_rsi": 39.4, "sell_rsi": 59.8, "rsi_mean": 49.6}
}
```

---

## 🚀 COMO EXECUTAR

### Pré-requisitos
```bash
pip install ccxt pandas numpy ta pyyaml python-dotenv
```

### Executar Bot Principal
```bash
cd App_Leonardo
python main.py
```

### Executar Teste da Estratégia
```bash
cd App_Leonardo
python test_smart_strategy.py
```

### Executar Análise de Perfis (gerar novo crypto_profiles.json)
```bash
cd App_Leonardo
python src/strategies/quick_analysis.py
```

---

## 📝 PRÓXIMOS PASSOS

### 🔌 WebSocket (✅ CONCLUÍDO)
- [x] Criar `src/core/websocket_client.py`
- [x] Criar `main_websocket.py` - versão com dados em tempo real
- [x] Implementar reconexão automática
- [ ] Cache local de dados persistente

### 📊 Dashboard (Prioridade Média)
- [ ] Gráficos em tempo real
- [ ] Histórico de trades
- [ ] Indicadores visuais de tendência
- [ ] Progresso da meta diária

### 🛡️ Segurança (Prioridade Alta)
- [ ] Limites de perda diária
- [ ] Alertas por Telegram/Discord
- [ ] Backup de posições

### 📈 Otimização (Prioridade Baixa)
- [ ] Backtesting com dados históricos
- [ ] Machine Learning para otimização de parâmetros
- [ ] Múltiplas estratégias simultâneas

---

## 📊 ESTATÍSTICAS DO PROJETO

| Métrica | Valor |
|---------|-------|
| Moedas configuradas | 8 |
| Meta diária | $100 |
| Valor por trade | $50 |
| Stop Loss | -1.5% |
| Take Profit máx | +5% |
| Tempo máx posição | 15 min |

---

## 🔄 LOG DE ATUALIZAÇÕES

### 30/11/2025 - Parte 3 (Dashboard de Saldo)
- ✅ Criado `frontend/dashboard_saldo.py` - Dashboard com saldo em criptomoedas
- ✅ Verificação de credenciais OK (API Key configurada)
- ✅ Conexão com Binance Testnet funcionando
- ✅ Saldo disponível: **$30,055.19 USDT** + várias criptos
- ✅ Dashboard mostra:
  - USDT disponível
  - Valor total em crypto
  - Patrimônio total
  - 8 principais criptos (BTC, ETH, SOL, BNB, XRP, LINK, DOGE, LTC)
  - Gráfico de pizza do portfólio
  - Lista de todas as moedas com saldo

### 30/11/2025 - Parte 2 (WebSocket)
- ✅ Criado `src/core/websocket_client.py` - Cliente WebSocket para Binance
- ✅ Criado `main_websocket.py` - Versão do bot com dados em tempo real
- ✅ Instalada biblioteca `websockets`
- ✅ Testado conexão WebSocket (mainnet para dados públicos)
- ✅ Criado `HISTORICO_DE_DESENVOLVIMENTO.md`

### 30/11/2025 - Parte 1 (Smart Strategy)
- ✅ Criação inicial do projeto
- ✅ Implementação da Smart Strategy
- ✅ Análise de RSI adaptativo
- ✅ Integração com main.py
- ✅ Testes validados
- ✅ Documentação criada

---

> **Nota**: Este arquivo deve ser atualizado a cada nova feature ou modificação significativa no projeto.
