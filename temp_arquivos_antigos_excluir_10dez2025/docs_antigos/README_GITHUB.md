# 🤖 App Leonardo - Bot de Trading de Criptomoedas

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

Bot automatizado de trading de criptomoedas com estratégia adaptativa, dashboard em tempo real e sistema completo de persistência.

## 🌟 Features

- 📊 **Estratégia Inteligente (Smart Strategy v2.0)**
  - RSI adaptativo baseado no perfil de cada moeda
  - MACD para confirmação de tendência
  - SMA (20, 50, 200) para identificar suportes/resistências

- 💰 **Gestão de Risco**
  - Meta diária configurável ($100 default)
  - Stop-loss e take-profit automáticos
  - Limite máximo de posições abertas
  - Sistema de segurança contra drawdown

- 📈 **Dashboard em Tempo Real**
  - Saldo e patrimônio total
  - Cards das 8 principais criptos com previsões
  - Win rate e estatísticas de trades
  - Atualização a cada 10 segundos

- 💾 **Persistência Completa**
  - SQLite para histórico de trades
  - JSON para estados e estatísticas
  - CSV para relatórios diários
  - Backup automático a cada 30 minutos

## 📸 Screenshot

```
┌─────────────────────────────────────────────────────────────┐
│  💰 App Leonardo - Saldo em Criptomoedas                    │
├─────────────────────────────────────────────────────────────┤
│  💵 USDT      💎 Crypto Value   🏦 Total    📈 Lucro Dia   │
│  $28,109      $98,110           $126,219    +$15.50        │
├─────────────────────────────────────────────────────────────┤
│  🎯 Meta: 15.5%   📊 Trades: 45   ✅ Win: 52%   🟢 Online  │
├─────────────────────────────────────────────────────────────┤
│  BTC 🟢 ALTA    ETH ⚪ LATERAL   SOL 🔴 QUEDA   ...        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.9+
- Conta na Binance (Testnet para testes)

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/SEU_USUARIO/app-leonardo-trading-bot.git
cd app-leonardo-trading-bot
```

2. **Crie o ambiente virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as credenciais**
```bash
cp config/.env.example config/.env
# Edite config/.env com suas API keys
```

5. **Execute o bot**
```bash
python main.py
```

6. **Execute o dashboard** (em outro terminal)
```bash
cd frontend
python dashboard_saldo.py
# Acesse: http://localhost:8050
```

## ⚙️ Configuração

### config/config.yaml

```yaml
exchange:
  name: binance
  testnet: true  # Use false para conta real

trading:
  symbols:
    - BTC/USDT
    - ETH/USDT
    - SOL/USDT
    # ...
  amount_per_trade: 50.0
  max_positions: 6
  daily_profit_target: 100.0

execution:
  interval_seconds: 3  # Intervalo entre análises
  dry_run: false
```

### config/.env

```env
BINANCE_TESTNET_API_KEY=sua_api_key_aqui
BINANCE_TESTNET_API_SECRET=seu_secret_aqui
```

## 📁 Estrutura do Projeto

```
App_Leonardo/
├── main.py                    # Bot principal
├── config/
│   ├── config.yaml           # Configurações
│   └── .env                  # Credenciais (não comitar!)
├── frontend/
│   └── dashboard_saldo.py    # Dashboard Dash/Plotly
├── src/
│   ├── core/
│   │   ├── exchange_client.py
│   │   └── utils.py
│   ├── indicators/
│   │   └── technical_indicators.py
│   ├── strategies/
│   │   ├── smart_strategy.py
│   │   └── simple_strategies.py
│   └── safety/
│       └── safety_manager.py
├── data/
│   ├── trading_history.db    # SQLite
│   └── daily_stats.json
├── logs/
│   └── trading_bot.log
└── tests/
```

## 📖 Documentação

- [Histórico de Correções e Aprendizados](HISTORICO_CORRECOES_APRENDIZADO.md)
- [Arquitetura do Sistema](ARQUITETURA.md)
- [Estratégia Adaptativa](ESTRATEGIA_ADAPTATIVA_EXPLICACAO.md)
- [Quick Start](QUICK_START.md)

## ⚠️ Avisos Importantes

1. **USE PRIMEIRO EM TESTNET** - Teste exaustivamente antes de usar dinheiro real
2. **NUNCA COMITE SUAS CREDENCIAIS** - O `.env` está no `.gitignore`
3. **TRADING ENVOLVE RISCOS** - Você pode perder dinheiro
4. **MONITORE CONSTANTEMENTE** - Bots podem ter bugs

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/NovaFeature`)
3. Commit suas mudanças (`git commit -m 'Add NovaFeature'`)
4. Push para a branch (`git push origin feature/NovaFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja [LICENSE](LICENSE) para mais detalhes.

## 👤 Autor

**Leonardo**

- GitHub: [@seu_usuario](https://github.com/seu_usuario)

## 🙏 Agradecimentos

- CCXT Library
- Dash/Plotly
- Binance API

---

⭐ Se este projeto te ajudou, considere dar uma estrela!
