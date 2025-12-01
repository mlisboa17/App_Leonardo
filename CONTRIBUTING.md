# Contribuindo para App Leonardo Trading Bot

Obrigado pelo seu interesse em contribuir! Este documento fornece diretrizes para contribuições.

## 🚀 Como Contribuir

### Reportando Bugs
1. Use o [sistema de issues](https://github.com/SEU_USUARIO/app-leonardo-trading-bot/issues)
2. Verifique se o bug já foi reportado
3. Use o template de bug report
4. Inclua logs, screenshots e passos para reproduzir

### Sugerindo Features
1. Abra uma issue com tag `enhancement`
2. Descreva detalhadamente a funcionalidade
3. Explique o caso de uso
4. Discuta a implementação se possível

### Pull Requests
1. **Fork** o repositório
2. Crie uma **branch** para sua feature: `git checkout -b feature/nome-da-feature`
3. **Commit** suas mudanças: `git commit -m 'Add: nova funcionalidade'`
4. **Push** para a branch: `git push origin feature/nome-da-feature`
5. Abra um **Pull Request**

## 📋 Checklist para PRs

- [ ] Código segue os padrões do projeto
- [ ] Testes foram adicionados/atualizados
- [ ] Documentação foi atualizada
- [ ] Logs foram testados
- [ ] PR está linkado a uma issue
- [ ] Descrição clara das mudanças

## 🧪 Executando Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-cov

# Executar testes
python -m pytest tests/

# Com coverage
python -m pytest tests/ --cov=src
```

## 📝 Padrões de Código

### Python (PEP 8)
- Use 4 espaços para indentação
- Linhas máximo 88 caracteres
- Snake_case para variáveis e funções
- PascalCase para classes
- Use type hints quando possível

```python
def calculate_rsi(prices: list[float], period: int = 14) -> float:
    """Calcula RSI para lista de preços."""
    pass
```

### Commits
Use o padrão Conventional Commits:
- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` mudanças na documentação
- `style:` formatação, sem mudança de código
- `refactor:` refatoração de código
- `test:` adição/correção de testes
- `chore:` tarefas de manutenção

Exemplo:
```
feat: add telegram notifications for trade alerts

- Add telegram bot integration
- Configure webhook for real-time alerts
- Update config.yaml with telegram settings

Closes #123
```

## 🎯 Áreas Prioritárias

### 🔥 Alta Prioridade
- [ ] Testes unitários para estratégias
- [ ] Sistema de notificações (Telegram/Discord)
- [ ] Melhorias na interface do dashboard
- [ ] Documentação de APIs

### 🟡 Média Prioridade
- [ ] Novos indicadores técnicos
- [ ] Backtesting mais robusto
- [ ] Sistema de plugins
- [ ] App mobile

### 🟢 Baixa Prioridade
- [ ] Suporte a outras exchanges
- [ ] Machine Learning integration
- [ ] Social trading features
- [ ] Advanced charting

## 🏗️ Arquitetura

### Estrutura de Pastas
```
src/
├── core/           # Motor principal do bot
├── strategies/     # Estratégias de trading
├── indicators/     # Indicadores técnicos
├── safety/        # Sistemas de segurança
└── utils/         # Utilidades gerais
```

### Adicionando Nova Estratégia
1. Crie arquivo em `src/strategies/`
2. Herde de `BaseStrategy`
3. Implemente `should_buy()` e `should_sell()`
4. Adicione testes em `tests/strategies/`
5. Documente no README

```python
from src.strategies.base_strategy import BaseStrategy

class MinhaEstrategia(BaseStrategy):
    def should_buy(self, data: dict) -> bool:
        # Sua lógica aqui
        return False
    
    def should_sell(self, data: dict) -> bool:
        # Sua lógica aqui
        return False
```

## 🔧 Setup de Desenvolvimento

### 1. Clone e Configure
```bash
git clone https://github.com/SEU_USUARIO/app-leonardo-trading-bot.git
cd app-leonardo-trading-bot
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dependências de desenvolvimento
```

### 2. Configure Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
```

### 3. Configure IDE
Para VS Code, instale extensões:
- Python
- Pylint
- Black Formatter
- GitLens

## 🧪 Guidelines de Teste

### Estrutura de Testes
```
tests/
├── conftest.py          # Fixtures compartilhadas
├── test_strategies/     # Testes de estratégias
├── test_indicators/     # Testes de indicadores
├── test_core/          # Testes do core
└── integration/        # Testes de integração
```

### Escrevendo Testes
```python
import pytest
from src.strategies.smart_strategy import SmartStrategy

class TestSmartStrategy:
    def test_should_buy_with_oversold_rsi(self):
        strategy = SmartStrategy()
        data = {
            'rsi': 25,
            'price': 50000,
            'volume': 1000000
        }
        assert strategy.should_buy(data) == True
    
    def test_should_sell_with_overbought_rsi(self):
        strategy = SmartStrategy()
        data = {
            'rsi': 75,
            'price': 55000,
            'volume': 1000000
        }
        assert strategy.should_sell(data) == True
```

## 📚 Recursos Úteis

### Trading
- [Investopedia](https://www.investopedia.com/)
- [TradingView](https://www.tradingview.com/)
- [Binance API Docs](https://binance-docs.github.io/apidocs/)

### Python
- [PEP 8](https://peps.python.org/pep-0008/)
- [Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Docs](https://docs.pytest.org/)

### Git
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)

## ❓ Dúvidas?

- Abra uma issue com tag `question`
- Entre no nosso Discord: [Link do Discord]
- Email: leonardo.trading@email.com

## 🙏 Reconhecimento

Contribuidores são listados no arquivo [CONTRIBUTORS.md](CONTRIBUTORS.md).

Obrigado por ajudar a tornar este projeto melhor! 🚀