# 🤖 R7 Trading Bot

> Sistema de trading automatizado multi-bot com orquestração de IA para criptomoedas

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📋 Sobre o Projeto

R7 Trading Bot é um sistema sofisticado de trading automatizado que opera **4+ bots especializados simultaneamente**, cada um focado em diferentes categorias de criptomoedas (stablecoins, voláteis, médias, memecoins). O sistema utiliza aprendizado adaptativo de IA para otimizar estratégias em tempo real com base no histórico de trades.

### ✨ Principais Funcionalidades

- 🤖 **Multi-Bot Coordination**: 4+ bots operando em paralelo com capital distribuído inteligentemente
- 🧠 **AI Orchestration**: Orquestrador de IA monitora mercado e gera sinais de trade
- 📊 **Gestão de Capital Avançada**: Risk/Reward mínimo de 2:1 e máximo 2% do portfólio por trade
- 🎯 **Estratégias Múltiplas**: Smart, Adaptive, Scalping, e bot único especializado
- 📈 **Dashboards em Tempo Real**: Interface Streamlit + React para monitoramento
- 🔄 **Aprendizado Adaptativo**: IA aprende com histórico e ajusta parâmetros automaticamente
- 🛡️ **Segurança Robusta**: Limites diários de perda, proteção de desvio de preço, audit logging

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.8 ou superior
- Conta Binance (testnet ou produção)
- Git

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/app_r7.git
cd app_r7

# Crie ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instale dependências
pip install -r requirements.txt

# Configure credenciais
copy config\.env.example config\.env
# Edite config\.env com suas API keys
```

### Configuração Inicial

1. **Configure suas credenciais** em `config/.env`:
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_TESTNET=true  # true para testnet, false para produção
```

2. **Revise configurações dos bots** em `config/bots_config.yaml`

3. **Verifique configurações de segurança** em `config/config.yaml`

### Executar o Sistema

```bash
# Iniciar sistema completo (4 bots + AI)
python main_multibot.py

# Em outro terminal - Dashboard
streamlit run frontend/dashboard_multibot.py --server.port 8501

# API Backend (opcional)
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Acesse:
- 📊 Dashboard: http://localhost:8501
- 🔌 API: http://localhost:8000/docs

## 📂 Estrutura do Projeto

```
app_r7/
├── 🤖 main_multibot.py          # Orquestrador principal
├── 🧠 ai_orchestrator.py        # Motor de IA
├── 💰 capital_manager.py        # Gestão de capital e risco
├── config/                      # Configurações
│   ├── config.yaml             # Config principal
│   ├── bots_config.yaml        # Config dos bots
│   └── .env                    # Credenciais (não comitado)
├── src/                         # Código fonte
│   ├── coordinator.py          # Coordenador de bots
│   ├── strategies/             # Estratégias de trading
│   ├── ai/                     # Componentes de IA
│   ├── core/                   # Exchange, websocket
│   └── audit.py                # Sistema de auditoria
├── frontend/                    # Dashboard Streamlit
├── frontend-react/              # Interface React
├── backend/                     # API FastAPI
├── aws-management/              # Ferramentas AWS
│   ├── scripts/                # Scripts de manutenção
│   ├── deployment/             # Deploy AWS
│   └── monitoring/             # Monitoramento EC2
├── data/                        # Dados persistidos (não comitado)
└── logs/                        # Logs do sistema (não comitado)
```

## 🎯 Arquitetura

### Fluxo de Decisão de Trade

```
┌─────────────────┐
│  Market Data    │ (ccxt → Binance)
└────────┬────────┘
         ↓
┌─────────────────┐
│ AI Orchestrator │ (análise sentimento + tendências)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Capital Manager │ (valida R:R ≥ 2:1)
└────────┬────────┘
         ↓
┌─────────────────┐
│   Coordinator   │ (seleciona bot e executa)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Adaptive Engine │ (aprende com resultado)
└─────────────────┘
```

### Categorias de Bots

| Bot | Categoria | Exemplos | Estratégia |
|-----|-----------|----------|------------|
| Bot 1 | Stable | USDT, BUSD, DAI | Baixa volatilidade |
| Bot 2 | Volatile | BTC, ETH, BNB | Alta volatilidade |
| Bot 3 | Medium | ADA, DOT, LINK | Volatilidade média |
| Bot 4 | Meme | DOGE, SHIB | Oportunística |

## 🛠️ Funcionalidades Avançadas

### AI Learning
- Análise de mercado em tempo real
- Aprendizado a partir do histórico de trades
- Ajuste dinâmico de parâmetros (stop loss, take profit)
- Modo oportunístico para aproveitar volatilidade

### Gestão de Risco
- **R:R mínimo de 2:1** (forçado pelo `capital_manager`)
- **Máximo 2% do portfólio** por trade
- **Limites diários de perda** configuráveis
- **Proteção de desvio de preço** para evitar slippage

### Monitoramento
- Dashboard em tempo real com métricas de desempenho
- Logs estruturados com auditoria completa
- Alertas de posições e P&L por bot
- Visualizações de distribuição de capital

## ☁️ Deploy em AWS

O projeto inclui ferramentas completas para deploy em AWS EC2:

```bash
# Menu interativo AWS
aws-management\aws-menu.bat

# Ou deploy direto
bash aws-management/deployment/deploy_aws.sh
```

Veja [`aws-management/README.md`](aws-management/README.md) para guia completo.

## 📚 Documentação

- 📖 [`INDEX.md`](INDEX.md) - Índice completo da documentação
- 🚀 [`SETUP_COMPLETO_08_DEC.md`](SETUP_COMPLETO_08_DEC.md) - Guia de setup detalhado
- ☁️ [`aws-management/`](aws-management/) - Documentação AWS
- 📊 [`DATABASE_STRATEGY.md`](DATABASE_STRATEGY.md) - Estratégia de migração para DB
- 🔒 [`REMEDIATION_SECURITY.md`](REMEDIATION_SECURITY.md) - Guia de segurança

## 🧪 Testes

```bash
# Verificar sistema
python test_sistema.py

# Testar conexão exchange
python test_api.py

# Testar dashboard
python test_dashboard.py

# Testar modo oportunístico
python test_opportunistic.py
```

## ⚠️ Avisos Importantes

### Segurança
- ⚠️ **NUNCA comite** arquivos `.env` ou com credenciais
- 🔐 Use **testnet** primeiro antes de produção
- 🛡️ Configure `exchange.testnet: false` apenas após validação completa

### Trading
- 📉 **Trading envolve risco** significativo de perda financeira
- 🧪 **Teste em testnet** extensivamente antes de usar capital real
- 📊 **Monitore constantemente** o comportamento dos bots
- 🚨 **Configure limites de perda** apropriados para seu perfil de risco

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Distribuído sob a licença MIT. Veja [`LICENSE`](LICENSE) para mais informações.

## 🔗 Links Úteis

- [Binance API Documentation](https://binance-docs.github.io/apidocs/)
- [CCXT Documentation](https://docs.ccxt.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 📧 Contato

Leonardo - [@seu_twitter](https://twitter.com/seu_twitter)

Project Link: [https://github.com/seu-usuario/app_r7](https://github.com/seu-usuario/app_r7)

---

**⚡ Desenvolvido com Python, IA e muita cafeína ☕**