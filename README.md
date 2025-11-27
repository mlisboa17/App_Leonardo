# 🤖 App Leonardo - Trading Bot

Bot de trading automatizado para criptomoedas com interface web em tempo real.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Características

- ✅ **Conexão com Binance** via CCXT (suporte para 100+ exchanges)
- ✅ **Indicadores Técnicos** nativos (RSI, MACD, SMAs, EMA, Bollinger Bands)
- ✅ **Dashboard Web em Tempo Real** com Django
- ✅ **Gráfico de Candlestick Profissional** com Lightweight Charts
- ✅ **Sistema de Segurança Anti-Alucinação:**
  - Kill Switch (perda máxima diária e drawdown)
  - Validação de preços (detecção de anomalias)
  - Confirmação de ordens
- ✅ **Modo Testnet** para testes seguros
- ✅ **Configuração Interativa** via terminal ou web
- ✅ **Estratégias Prontas:** RSI, Cruzamento de SMAs

## 📊 Dashboard

Interface web moderna mostrando em tempo real:

- Saldo e PnL (diário e total)
- Preço atual e posição
- Taxa de acerto (wins/losses)
- Indicadores técnicos (RSI, MACD, SMAs)
- Gráfico de preços com candlesticks
- Log de atividades

## 🛠️ Tecnologias

- **Python 3.14**
- **Django 5.2.7** + Channels (WebSocket)
- **CCXT 4.5.22** (API de exchanges)
- **Pandas 2.3.3** + NumPy (análise de dados)
- **Lightweight Charts** (gráficos profissionais)
- **Bootstrap 5** (interface responsiva)

## 📁 Estrutura do Projeto

```
App_Leonardo/
├── bot_dashboard/          # App Django do dashboard
│   ├── templates/          # Templates HTML
│   ├── views.py           # Views e APIs
│   └── urls.py            # Rotas do dashboard
├── dashboard_web/          # Projeto Django
│   ├── settings.py        # Configurações Django
│   ├── urls.py           # URLs principais
│   └── asgi.py           # ASGI config
├── config/                 # Configurações
│   ├── config.yaml        # Configuração do bot
│   └── .env              # Credenciais (não versionado)
├── src/
│   ├── core/              # Núcleo do bot
│   │   ├── exchange_client.py
│   │   └── __init__.py
│   ├── indicators/        # Indicadores técnicos
│   │   └── technical_indicators.py
│   ├── safety/            # Sistema de segurança
│   │   └── safety_manager.py
│   └── strategies/        # Estratégias de trading
│       └── simple_strategies.py
├── logs/                  # Logs do bot
├── data/                  # Dados históricos
├── main.py               # Execução principal do bot
├── configure_bot.py      # Configurador interativo
├── manage.py             # Django management
└── requirements.txt      # Dependências
```

## 📦 Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/SEU_USUARIO/App_Leonardo.git
cd App_Leonardo
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure as credenciais:**
Crie o arquivo `config/.env`:
```env
BINANCE_API_KEY=sua_api_key
BINANCE_SECRET=sua_secret_key
```

5. **Configure o bot:**
```bash
python configure_bot.py
```

6. **Execute as migrações do Django:**
```bash
python manage.py migrate
```

## 🚀 Uso

### Iniciar o Dashboard Web

```bash
python manage.py runserver
```

Acesse: **http://127.0.0.1:8000/**

### Executar o Bot

```bash
python main.py
```

### Testar Conexão

```bash
python test_connection.py
```

## 🛡️ Segurança (Anti-Alucinação)

O bot possui múltiplas camadas de proteção:

1. **Kill Switch**: Para automaticamente se:
   - Perda diária exceder limite configurado
   - Drawdown exceder % máximo

2. **Validação de Preços**: Rejeita preços com variação anormal

3. **Confirmação de Ordens**: Sempre verifica status na exchange após envio

4. **Logs Completos**: Registra todas decisões e operações

5. **Modo Testnet Obrigatório**: Teste antes de usar dinheiro real

## 📊 Estratégias Disponíveis

### 1. RSI Strategy (Padrão)
- Compra: RSI < 30 (sobrevenda)
- Venda: RSI > 70 (sobrecompra)

### 2. SMA Cross Strategy
- Compra: SMA rápida cruza SMA lenta para cima
- Venda: SMA rápida cruza SMA lenta para baixo

## 📝 TODO

- [ ] Integrar bot engine com dashboard (dados reais)
- [ ] WebSocket para atualizações em tempo real
- [ ] Backtesting com dados históricos
- [ ] Mais estratégias (Bandas de Bollinger, etc.)
- [ ] Notificações (email, Telegram)
- [ ] Stop loss e take profit automáticos
- [ ] Multi-pares simultâneos

## 📄 Licença

MIT License - sinta-se livre para usar e modificar!

## ⚠️ Disclaimer

Este bot é para fins **educacionais**. Trading de criptomoedas envolve risco. Use por sua conta e risco. Sempre teste em ambiente testnet antes de usar fundos reais.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

---

**Desenvolvido com ❤️ usando Python e Django**
