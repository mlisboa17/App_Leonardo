# 🤖 App Leonardo - Bot de Trading

## ✅ Bot Criado com Sucesso!

O bot de trading automatizado está **completo e pronto para uso**.

## 📁 Arquivos Criados

- **`main.py`** - Bot principal com loop de trading
- **`src/strategies/simple_strategies_new.py`** - Estratégias de trading (Simple, Aggressive, Conservative)
- **`start_bot.bat`** - Script para iniciar o bot no Windows

## 🎯 Funcionalidades

### ✅ Sistema Completo
- ✅ Trading automático em múltiplas criptomoedas (BTC, ETH, SOL, POL)
- ✅ Estratégias baseadas em RSI + MACD + SMAs
- ✅ Gerenciamento de risco com Stop Loss (5%) e Take Profit (3%)
- ✅ Kill Switch automático (perda diária e drawdown)
- ✅ Validação de preços (anti-manipulação)
- ✅ Modo DRY RUN (simulação) e REAL
- ✅ Suporte a Testnet e Mainnet
- ✅ Dashboard web em tempo real
- ✅ Logs detalhados
- ✅ Histórico de trades em JSON e CSV

### 📊 Estratégias Disponíveis

1. **Simple** (Padrão)
   - RSI: 47 (oversold) / 56 (overbought)
   - Requer 2+ condições para operar

2. **Aggressive**
   - RSI: 40 / 60
   - Requer apenas 1 condição

3. **Conservative**
   - RSI: 25 / 75
   - Requer 3 condições

## 🚀 Como Usar

### 1. Configure as Credenciais

```bash
# Copie o arquivo de exemplo
cp config/.env.example config/.env

# Edite e adicione suas credenciais da Binance
# BINANCE_API_KEY=sua_chave_aqui
# BINANCE_API_SECRET=seu_secret_aqui
```

### 2. Inicie o Bot

**Opção 1: Script Automático (Windows)**
```bash
start_bot.bat
```

**Opção 2: Comando Direto**
```bash
python main.py
```

**Opção 3: Com ambiente virtual**
```bash
venv\Scripts\activate
python main.py
```

### 3. Modo de Operação

O bot está configurado para:
- **Testnet**: `true` (ambiente seguro de testes)
- **Dry Run**: `false` (faz operações reais na testnet)
- **Intervalo**: 5 segundos entre análises
- **Símbolos**: BTC/USDT, ETH/USDT, SOL/USDT, POL/USDT

Para alterar, edite `config/config.yaml`

## ⚙️ Configuração Recomendada

### Primeiro Teste (Seguro)
```yaml
execution:
  dry_run: true  # Apenas simula
  interval_seconds: 60  # 1 minuto

exchange:
  testnet: true  # Usa testnet
```

### Testnet (Dinheiro Falso)
```yaml
execution:
  dry_run: false  # Executa ordens reais na testnet
  interval_seconds: 30

exchange:
  testnet: true
```

### Produção (CUIDADO!)
```yaml
execution:
  dry_run: false
  interval_seconds: 10

exchange:
  testnet: false  # ⚠️ DINHEIRO REAL
```

## 📊 Monitoramento

### Dashboard Web
```bash
python manage.py runserver
```
Acesse: http://localhost:8001

### Arquivos Gerados
- **`bot_state.json`** - Estado atual do bot
- **`bot_history.json`** - Histórico de trades
- **`logs/trading_bot.log`** - Logs detalhados
- **`data/reports/trades_*.csv`** - Relatórios CSV

## 🛡️ Segurança

### Kill Switch Automático
- ✅ Para em perda diária de 100 USDT
- ✅ Para em drawdown de 20%
- ✅ Valida variações bruscas de preço (30%)
- ✅ Fecha todas posições ao parar

### Gerenciamento de Risco
- ✅ Stop Loss: -5% por trade
- ✅ Take Profit: +3% por trade
- ✅ Máximo 4 posições simultâneas
- ✅ 10 USDT por trade

## 📈 Lógica de Trading

### Sinal de COMPRA (precisa 2+)
1. RSI < 47 (oversold)
2. MACD cruzou para cima
3. Preço acima da SMA20

### Sinal de VENDA (precisa 2+)
1. RSI > 56 (overbought)
2. MACD cruzou para baixo
3. Preço abaixo da SMA20

### Fechamento Automático
- Sinal contrário detectado
- Stop Loss atingido (-5%)
- Take Profit atingido (+3%)

## 🔧 Troubleshooting

### Erro de credenciais
```
⚠️ Credenciais não encontradas - usando modo API pública
```
**Solução**: Crie `config/.env` com suas chaves

### Erro de conexão
```
❌ Conexão com exchange falhou
```
**Solução**: Verifique internet e credenciais da Binance

### Kill Switch ativado
```
⛔ KILL SWITCH: Perda diária atingida!
```
**Solução**: Aguarde reset diário ou ajuste `config.yaml`

## 📝 Próximos Passos

1. ✅ Obter credenciais da Binance Testnet
2. ✅ Configurar `config/.env`
3. ✅ Testar em DRY RUN
4. ✅ Testar na Testnet
5. ✅ Ajustar estratégia conforme resultados
6. ✅ Monitorar via dashboard
7. ⚠️ Produção apenas após validação completa

## 🎓 Estratégia Recomendada

Para iniciantes:
1. Comece com **DRY RUN** por 1 semana
2. Migre para **TESTNET** por 1 mês
3. Ajuste parâmetros baseado em resultados
4. Só vá para **MAINNET** com confiança

## ⚡ Comandos Rápidos

```bash
# Iniciar bot
python main.py

# Iniciar dashboard
python manage.py runserver

# Ver logs em tempo real
Get-Content logs/trading_bot.log -Wait -Tail 50

# Parar bot (Ctrl+C)
# O bot fecha todas posições automaticamente
```

## 📞 Suporte

O bot inclui:
- Logs detalhados em `logs/trading_bot.log`
- Estado em tempo real em `bot_state.json`
- Tratamento de erros robusto
- Parada graceful (Ctrl+C)

---

**⚠️ AVISO IMPORTANTE**: Trading de criptomoedas envolve riscos. Este bot é uma ferramenta educacional. Use por sua conta e risco. Sempre comece em modo de teste!
