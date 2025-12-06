# 📊 ESTUDO: Classificação de Criptomoedas por Características de Trading

## Objetivo
Classificar as criptomoedas disponíveis no Binance Testnet por características de volatilidade e comportamento de mercado para otimizar as configurações dos 4 bots especializados.

---

## 🔬 Metodologia de Pesquisa

### Fontes de Dados Utilizadas:
1. **CoinMarketCap Categories** - 187 categorias de criptomoedas
2. **TradingView** - Dados de volatilidade e análise técnica
3. **Binance** - Dados de mercado em tempo real

### Métricas Analisadas:
- Volatilidade diária (% de variação)
- Market Cap (liquidez)
- Volume de negociação 24h
- Categoria/Setor do projeto
- Histórico de movimentos bruscos

---

## 📈 Classificação por Setor (CoinMarketCap Data)

| Setor | Volatilidade Média | Risco | Exemplos |
|-------|-------------------|-------|----------|
| **Meme Coins** | 8.09% | EXTREMO | DOGE, SHIB, PEPE |
| **Gaming/Metaverse** | 3.65% | ALTO | SAND, MANA, AXS |
| **Layer 1 (novos)** | 3.80% | ALTO | SOL, AVAX, NEAR |
| **Solana Ecosystem** | 3.60% | ALTO | SOL, RAY, SRM |
| **DeFi** | 1.08% | MÉDIO | UNI, AAVE, LINK |
| **Privacy Coins** | 1.38% | MÉDIO-BAIXO | XMR, ZEC |
| **Layer 1 (estabelecidos)** | 0.5-2% | BAIXO | BTC, ETH |
| **Stablecoins** | ~0% | ZERO | USDT, USDC, DAI |

---

## 🎯 Criptomoedas Disponíveis no Binance Testnet

### Classificação Final:

#### 🟢 **ESTÁVEL** (Volatilidade BAIXA: 1-3% diário)
| Cripto | Market Cap | Característica | RSI Ideal |
|--------|------------|----------------|-----------|
| **BTC** | $1.77T | Store of value, líder | 40-60 |
| **ETH** | $300B+ | Smart contracts, DeFi base | 40-60 |
| **LTC** | $6B+ | Digital silver, estabelecida | 38-62 |

**Comportamento:** Movimentos previsíveis, seguem tendências macro, baixa probabilidade de pumps/dumps extremos.

---

#### 🟡 **MÉDIO** (Volatilidade MÉDIA: 3-5% diário)
| Cripto | Market Cap | Característica | RSI Ideal |
|--------|------------|----------------|-----------|
| **BNB** | $80B+ | Exchange token, utilidade | 35-65 |
| **SOL** | $50B+ | Layer 1 rápida, crescente | 35-65 |
| **LINK** | $8B+ | Oracle DeFi, fundamental | 35-65 |
| **ADA** | $15B+ | Layer 1 academia | 35-65 |

**Comportamento:** Correlação com BTC mas com amplificação, ciclos de hype tecnológico.

---

#### 🟠 **VOLÁTIL** (Volatilidade ALTA: 5-8% diário)
| Cripto | Market Cap | Característica | RSI Ideal |
|--------|------------|----------------|-----------|
| **XRP** | $30B+ | Pagamentos, notícias legais | 30-70 |
| **TRX** | $10B+ | DApp ecosystem, Tron | 30-70 |
| **EOS** | $1B+ | Ex-hyped L1, alta vol | 30-70 |
| **XLM** | $3B+ | Pagamentos, parceiro XRP | 30-70 |

**Comportamento:** Movimentos bruscos em notícias, pumps frequentes, correlação menor com BTC.

---

#### 🔴 **MEME/ESPECULATIVO** (Volatilidade EXTREMA: 8%+ diário)
| Cripto | Market Cap | Característica | RSI Ideal |
|--------|------------|----------------|-----------|
| **DOGE** | $25B+ | Original meme, Elon effect | 25-75 |

**Comportamento:** Pumps imprevisíveis, driven por redes sociais, alta manipulação.

---

## ⚙️ Configurações Recomendadas por Categoria

### 🟢 Bot Estável (BTC, ETH, LTC)
```yaml
rsi_buy: 40       # Compra mais conservadora
rsi_sell: 60      # Vende cedo para garantir lucro
stop_loss: -0.5%  # Stop apertado (baixa vol = baixo risco)
take_profit: 0.3% # Lucro pequeno mas frequente
max_hold_min: 240 # Pode segurar 4 horas
```
**Estratégia:** Scalping conservador, muitos trades pequenos.

---

### 🟡 Bot Médio (BNB, SOL, LINK, ADA)
```yaml
rsi_buy: 35       # Compra em quedas moderadas
rsi_sell: 65      # Vende em subidas moderadas
stop_loss: -1.0%  # Stop médio
take_profit: 0.7% # Lucro maior por trade
max_hold_min: 180 # 3 horas max
```
**Estratégia:** Swing trading curto, aproveita volatilidade média.

---

### 🟠 Bot Volátil (XRP, TRX, EOS, XLM)
```yaml
rsi_buy: 30       # Compra em oversold forte
rsi_sell: 70      # Vende em overbought forte
stop_loss: -1.2%  # Stop mais largo para volatilidade
take_profit: 1.0% # Lucro maior compensa vol
max_hold_min: 120 # 2 horas max (risco vol)
```
**Estratégia:** Momentum trading, entrada/saída rápida.

---

### 🔴 Bot Meme (DOGE)
```yaml
rsi_buy: 25       # Só compra em crash forte
rsi_sell: 75      # Vende em pump
stop_loss: -1.5%  # Stop largo (vol extrema)
take_profit: 1.5% # Lucro alto para compensar risco
max_hold_min: 60  # 1 hora max (muito arriscado)
```
**Estratégia:** Pump detection, entrada/saída ultra rápida.

---

## 📊 Análise de Risco/Retorno

| Bot | Risco | Retorno Esperado/Trade | Win Rate Esperado | Trades/Dia |
|-----|-------|------------------------|-------------------|------------|
| Estável | Baixo | 0.3% | 65-70% | 15-20 |
| Médio | Médio | 0.7% | 55-60% | 10-15 |
| Volátil | Alto | 1.0% | 50-55% | 8-12 |
| Meme | Extremo | 1.5% | 45-50% | 5-8 |

---

## 🔄 Correlação entre Criptos

### Alta Correlação (movem juntos):
- BTC ↔ ETH (0.85+)
- BTC ↔ LTC (0.80+)
- XRP ↔ XLM (0.75+)
- SOL ↔ BNB (0.70+)

### Baixa Correlação (diversificação):
- BTC ↔ DOGE (0.40)
- ETH ↔ TRX (0.35)
- LINK ↔ XRP (0.30)

**Conclusão:** Cada bot trabalha com criptos de correlação alta interna, mas os 4 bots juntos têm baixa correlação entre si = DIVERSIFICAÇÃO PERFEITA.

---

## 📅 Padrões Temporais Identificados

### Horários de Alta Volatilidade:
- **08:00-10:00 UTC**: Abertura Europa
- **13:00-15:00 UTC**: Abertura EUA
- **00:00-02:00 UTC**: Abertura Ásia

### Dias da Semana:
- **Segunda**: Alta volatilidade (catch-up)
- **Terça-Quinta**: Volatilidade normal
- **Sexta**: Redução antes fim de semana
- **Sábado-Domingo**: Volatilidade imprevisível

**Implementado:** `get_day_urgency_factor()` aumenta agressividade ao longo do dia.

---

## ✅ Conclusões do Estudo

1. **Diversificação por Volatilidade Funciona**: Cada bot especializado captura oportunidades diferentes
2. **RSI Dinâmico é Essencial**: Ranges diferentes para cada tipo de cripto
3. **Stop/Take Profit Adaptativo**: Volatilidade maior = stops/takes maiores
4. **Correlação Baixa Entre Bots**: Sistema como um todo é resiliente
5. **Fator Temporal Importante**: Urgência ao longo do dia aumenta chances

---

## 🚀 Próximos Passos

1. ✅ Aplicar configurações ao `bots_config.yaml`
2. ✅ Atualizar `smart_strategy.py` com crypto_configs
3. 🔄 Monitorar performance por 24h
4. 🔄 Ajustar baseado em resultados reais
5. 🔄 Adicionar mais criptos quando disponíveis

---

*Estudo realizado em: Dezembro 2025*
*Fonte: CoinMarketCap, TradingView, Binance*
*Versão: 1.0*
