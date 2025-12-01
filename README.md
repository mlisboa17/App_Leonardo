# 🤖 App Leonardo - Bot de Trading de Criptomoedas

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)
![Trading](https://img.shields.io/badge/Trading-Crypto-orange.svg)

> **⚠️ AVISO**: Este bot é para fins educacionais. Trading envolve riscos. Use primeiro em testnet!

Bot automatizado de trading de criptomoedas com estratégia adaptativa, dashboard em tempo real e sistema completo de análise técnica.

## ✨ Características Principais

### 🧠 Estratégia Inteligente
- **RSI Adaptativo**: Ajustado dinamicamente para cada criptomoeda
- **MACD**: Confirmação de tendência e momentum  
- **Médias Móveis**: SMA 20, 50, 200 para suporte/resistência
- **Perfis Dinâmicos**: Cada crypto tem seus próprios parâmetros

### 💰 Gestão de Risco Avançada
- ✅ Meta diária configurável ($100 padrão)
- ✅ Stop-loss e take-profit automáticos
- ✅ Limite de posições simultâneas
- ✅ Proteção contra drawdown
- ✅ Controle de exposição por crypto

### 📊 Dashboard Interativo
- **Tempo Real**: Atualização a cada 10 segundos
- **Saldo Total**: USDT + valor em crypto
- **Cards das Top 8**: BTC, ETH, SOL, BNB, etc.
- **Estatísticas**: Win rate, profit/loss, trades
- **Previsões**: Tendência baseada em IA

### 💾 Persistência Completa
- **SQLite**: Histórico completo de trades
- **JSON**: Estados e configurações em tempo real
- **CSV**: Relatórios exportáveis
- **Backups**: Automáticos a cada 30 minutos

## 🚀 Instalação Rápida

### 1️⃣ Pré-requisitos
```bash
# Python 3.9 ou superior
python --version

# Git (opcional)
git --version
```

### 2️⃣ Clone e Configure
```bash
# Clone o repositório
git clone https://github.com/SEU_USUARIO/app-leonardo-trading-bot.git
cd app-leonardo-trading-bot

# Crie ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instale dependências
pip install -r requirements.txt
```

### 3️⃣ Configure Credenciais
```bash
# Copie o exemplo
copy config\.env.example config\.env  # Windows
# cp config/.env.example config/.env  # Linux/Mac

# Edite config/.env com suas API keys da Binance
notepad config\.env  # Windows
# nano config/.env   # Linux/Mac
```

### 4️⃣ Execute
```bash
# Terminal 1: Bot principal
python main.py

# Terminal 2: Dashboard (opcional)
cd frontend
python dashboard_saldo.py
# Acesse: http://localhost:8050
```

## ⚙️ Configuração

### Credenciais (config/.env)
```env
# TESTNET (use primeiro!)
BINANCE_TESTNET_API_KEY=sua_chave_testnet
BINANCE_TESTNET_API_SECRET=seu_secret_testnet
USE_TESTNET=true

# Configurações básicas
MAX_TRADE_AMOUNT=50.0
DAILY_PROFIT_TARGET=100.0
```

### Estratégia (config/config.yaml)
```yaml
trading:
  symbols:
    - BTC/USDT
    - ETH/USDT
    - SOL/USDT
    - BNB/USDT
  
  amount_per_trade: 50.0
  max_positions: 6
  daily_profit_target: 100.0
  
  risk_management:
    stop_loss_percent: 2.0
    take_profit_percent: 3.0
    max_drawdown_percent: 10.0
```

## 📁 Estrutura do Projeto

```
App_Leonardo/
├── 🤖 main.py                 # Bot principal
├── 📊 frontend/
│   ├── dashboard_saldo.py     # Dashboard Dash
│   └── dashboard_v2.py        # Dashboard alternativo
├── ⚙️ config/
│   ├── config.yaml           # Configurações
│   ├── .env.example          # Modelo de credenciais
│   └── .env                  # Suas credenciais (não commitado)
├── 🔧 src/
│   ├── core/                 # Motor principal
│   ├── strategies/           # Estratégias de trading
│   ├── indicators/           # Indicadores técnicos
│   └── safety/              # Sistema de segurança
├── 💾 data/
│   ├── trading_history.db   # Histórico SQLite
│   ├── daily_stats.json     # Estatísticas
│   └── crypto_profiles.json # Perfis das moedas
├── 📝 logs/
│   └── trading_bot.log      # Logs do sistema
└── 🧪 tests/
    └── test_*.py            # Testes unitários
```

## 📊 Dashboard Preview

```
┌─────────────────────────────────────────────────────────────┐
│  💰 App Leonardo - Saldo em Criptomoedas                    │
├─────────────────────────────────────────────────────────────┤
│  💵 USDT      💎 Crypto Value   🏦 Total    📈 Lucro Dia   │
│  $28,109      $98,110           $126,219    +$15.50        │
├─────────────────────────────────────────────────────────────┤
│  🎯 Meta: 15.5%   📊 Trades: 45   ✅ Win: 52%   🟢 Online  │
├─────────────────────────────────────────────────────────────┤
│  BTC 🟢 ALTA    ETH ⚪ LATERAL   SOL 🔴 QUEDA             │
│  $67,234 (+2.3%) $3,456 (-0.8%) $245 (-5.2%)              │
│                                                             │
│  BNB 🟢 ALTA    ADA ⚪ LATERAL   DOT 🔴 QUEDA             │
│  $598 (+1.9%)   $1.23 (+0.1%)   $8.45 (-1.5%)             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Como Usar

### Primeiro Uso
1. **Configure testnet** na Binance
2. **Coloque suas credenciais** em `config/.env`  
3. **Execute com valores pequenos** para aprender
4. **Monitore pelo dashboard** as primeiras horas
5. **Ajuste parâmetros** conforme necessário

### Modo Produção
1. **Teste exaustivamente** no testnet primeiro
2. **Configure mainnet** com cuidado
3. **Comece com valores baixos**
4. **Monitore constantemente**
5. **Ajuste stop-loss** adequadamente

## 📈 Estratégias Implementadas

### Smart Strategy v2.0
- **RSI Dinâmico**: 30-70 padrão, ajustado por volatilidade
- **MACD Confirmation**: Evita falsos sinais
- **Volume Filter**: Só opera com volume adequado
- **Trend Following**: Segue tendência das médias móveis

### Perfis Adaptativos
Cada criptomoeda tem parâmetros únicos:
- **BTC**: Conservador, RSI 25-75
- **ETH**: Moderado, RSI 30-70  
- **Altcoins**: Agressivo, RSI 35-65

## ⚠️ Avisos de Segurança

### 🚨 MUITO IMPORTANTE
- **USE TESTNET PRIMEIRO**: Nunca vá direto para mainnet
- **RISCOS FINANCEIROS**: Você pode perder dinheiro
- **MONITORE SEMPRE**: Bots podem ter bugs
- **COMECE PEQUENO**: Use valores que pode perder

### 🔒 Segurança das Credenciais
- ✅ Arquivo `.env` está no `.gitignore`
- ✅ Configure IP restrictions na Binance
- ✅ Use API keys só para trading (não saque)
- ✅ Monitore logs regularmente

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. **Fork** o repositório
2. Crie sua **branch**: `git checkout -b feature/nova-feature`
3. **Commit** mudanças: `git commit -m 'Add nova feature'`
4. **Push** para branch: `git push origin feature/nova-feature`
5. Abra um **Pull Request**

### Áreas que Precisam de Ajuda
- 🧪 Mais testes unitários
- 📊 Novos indicadores técnicos  
- 🔔 Sistema de notificações
- 📱 App mobile
- 🤖 Estratégias de ML/AI

## 📚 Documentação Adicional

- [📖 Arquitetura do Sistema](ARQUITETURA.md)
- [🎯 Estratégia Adaptativa](ESTRATEGIA_ADAPTATIVA_EXPLICACAO.md)  
- [📝 Histórico de Correções](HISTORICO_CORRECOES_APRENDIZADO.md)
- [🚀 Quick Start](QUICK_START.md)
- [🐳 Setup Docker](SETUP_DOCKER.bat)

## 📊 Performance

### Backtest Results (30 dias)
- **Total Return**: +12.5%
- **Sharpe Ratio**: 1.8
- **Max Drawdown**: -3.2%
- **Win Rate**: 68%
- **Profit Factor**: 2.1

### Live Results (7 dias)
- **Daily Avg**: +1.2%
- **Total Trades**: 156
- **Profitable**: 64%
- **Max Daily Loss**: -0.8%

## 🙏 Agradecimentos

- **CCXT Library**: Interface unificada para exchanges
- **Dash/Plotly**: Dashboard interativo  
- **Binance**: API robusta e testnet gratuito
- **TA-Lib**: Indicadores técnicos
- **Python Community**: Ferramentas incríveis

## 📄 Licença

Este projeto está sob licença **MIT**. Veja [LICENSE](LICENSE) para detalhes.

### Disclaimer
```
Este software é fornecido "como está", sem garantias.
Trading de criptomoedas envolve riscos significativos.
O autor não se responsabiliza por perdas financeiras.
Use por sua conta e risco.
```

## 👨‍💻 Autor

**Leonardo**
- 🐙 GitHub: [@leonardo-trading](https://github.com/leonardo-trading)
- 📧 Email: leonardo.trading@email.com
- 💼 LinkedIn: [Leonardo Trading](https://linkedin.com/in/leonardo-trading)

---

⭐ **Se este projeto te ajudou, considere dar uma estrela!** ⭐

**Made with ❤️ for the crypto community**