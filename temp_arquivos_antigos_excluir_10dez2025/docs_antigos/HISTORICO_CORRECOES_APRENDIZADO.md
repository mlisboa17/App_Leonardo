# 📚 Histórico de Correções e Aprendizados - App Leonardo

> **Data:** 30 de Novembro de 2025  
> **Projeto:** Bot de Trading de Criptomoedas com Dashboard em Tempo Real  
> **Objetivo:** Documentar todas as correções realizadas para servir de aprendizado

---

## 🎯 Resumo do Projeto

Bot de trading automatizado para criptomoedas com:
- Estratégia adaptativa com RSI, MACD e SMA
- Meta diária de $100
- Dashboard em tempo real com Dash/Plotly
- Persistência completa (SQLite, JSON, CSV)
- Modo Testnet da Binance

---

## 🐛 CORREÇÕES IMPORTANTES

### 1. ❌ Erro: Atributos Faltando no Bot (`trade_amount`, `daily_goal`)

**Problema:**
```
'TradingBot' object has no attribute 'trade_amount'
'TradingBot' object has no attribute 'daily_goal'
```

**Causa:** Os atributos eram usados em funções de histórico mas não foram inicializados no `__init__`.

**Solução:** Adicionar os atributos no construtor:
```python
# No __init__ da classe TradingBot
self.trade_amount = self.amount_per_trade  # Valor por trade
self.daily_goal = self.stats.get('daily_target', 100.0)  # Meta diária
```

**Aprendizado:** 
> ⚠️ Sempre inicializar TODOS os atributos usados na classe no `__init__`, mesmo que sejam derivados de outros valores.

---

### 2. ❌ Erro: JSON Não Serializável (`bool`)

**Problema:**
```
Object of type bool is not JSON serializable
```

**Causa:** Valores booleanos do NumPy/Pandas não são serializáveis diretamente.

**Solução:** Converter explicitamente para tipos nativos Python:
```python
stats_to_save = {
    'total_pnl': float(self.stats['total_pnl']),  # Converte para float
    'daily_pnl': float(self.stats['daily_pnl']),
    'target_reached': bool(self.stats['daily_pnl'] >= target),  # Converte para bool
}

# E usar default=str no json.dump
json.dump(stats_to_save, f, indent=2, default=str)
```

**Aprendizado:**
> ⚠️ Ao salvar dados em JSON, sempre converter tipos NumPy/Pandas para tipos nativos Python. Use `default=str` como fallback.

---

### 3. ❌ Erro: Dashboard Não Atualizava (Exchange Reinicializando)

**Problema:** Dashboard mostrava $0.00 em todos os campos e não atualizava.

**Causa:** A cada callback (10s), o código criava uma NOVA conexão com a exchange e carregava todos os mercados novamente. Isso levava muito tempo e causava timeout.

**Código Problemático:**
```python
def get_exchange():
    return ccxt.binance({...})  # Nova instância a cada chamada

def get_balances():
    exchange = get_exchange()
    exchange.load_markets()  # LENTO! Carrega ~1000 mercados
    return exchange.fetch_balance()
```

**Solução:** Usar padrão Singleton para manter uma única conexão:
```python
# Exchange global (SINGLETON)
_exchange_instance = None
_exchange_last_init = None

def get_exchange():
    global _exchange_instance, _exchange_last_init
    
    current_time = time.time()
    
    # Reinicializa apenas a cada 5 minutos
    if _exchange_instance is None or (current_time - _exchange_last_init > 300):
        _exchange_instance = ccxt.binance({...})
        _exchange_instance.load_markets()
        _exchange_last_init = current_time
    
    return _exchange_instance
```

**Aprendizado:**
> ⚠️ NUNCA criar novas conexões de API dentro de callbacks frequentes. Use SINGLETON para reutilizar conexões. O `load_markets()` da Binance carrega ~1000 pares e leva vários segundos.

---

### 4. ❌ Erro: Parâmetro Inválido na API (`timeout` no fetch_ohlcv)

**Problema:**
```
binance {"code":-1104,"msg":"Not all sent parameters were read; read '3' parameter(s) but was sent '4'."}
```

**Causa:** Passar `timeout` como parâmetro para a API da Binance (que não aceita):
```python
# ERRADO
ohlcv = exchange.fetch_ohlcv(pair, '1h', limit=50, params={"timeout": 5000})
```

**Solução:** O timeout deve ser configurado na instância da exchange, não na chamada:
```python
# CORRETO - timeout na instância
exchange = ccxt.binance({
    'timeout': 15000,  # Timeout aqui
    ...
})

# Chamada sem params extras
ohlcv = exchange.fetch_ohlcv(pair, '1h', limit=50)
```

**Aprendizado:**
> ⚠️ Parâmetros de conexão (timeout, recvWindow) vão na configuração da exchange, NÃO nas chamadas individuais. Consulte a documentação do CCXT.

---

### 5. ❌ Erro: Imports Não Encontrados (Pylance)

**Problema:**
```
Import "core.utils" could not be resolved
Import "core.exchange_client" could not be resolved
```

**Causa:** O Pylance (IDE) não reconhece o `sys.path.insert()` em runtime.

**Solução:** O código funciona em runtime, mas para o Pylance reconhecer:

Opção 1 - Adicionar `pyrightconfig.json`:
```json
{
    "extraPaths": ["src"]
}
```

Opção 2 - Usar imports relativos:
```python
from src.core.utils import load_config
```

**Aprendizado:**
> ⚠️ `sys.path.insert()` funciona em runtime mas IDEs não reconhecem. Use arquivos de configuração do Pylance ou imports absolutos com prefixo do pacote.

---

### 6. ❌ Erro: Intervalo de Análise Muito Longo

**Problema:** Bot analisava a cada 10 segundos, perdendo oportunidades.

**Causa:** Configuração padrão conservadora.

**Solução:** Alterar `config.yaml`:
```yaml
execution:
  interval_seconds: 3  # Era 10
```

**Aprendizado:**
> ⚠️ Em scalping/day trading, intervalos menores = mais oportunidades. Mas cuidado com rate limits da API!

---

## 📊 Métricas Finais do Sistema

| Métrica | Valor |
|---------|-------|
| Saldo USDT | ~$28,100 |
| Posições Máximas | 6 |
| Intervalo de Análise | 3 segundos |
| Criptos Monitoradas | 8 (BTC, ETH, SOL, BNB, XRP, LINK, DOGE, LTC) |
| Dashboard Update | 10 segundos |
| Win Rate | ~45-50% |

---

## 🏗️ Arquitetura Final

```
App_Leonardo/
├── main.py                    # Bot principal
├── config/
│   └── config.yaml           # Configurações
├── frontend/
│   └── dashboard_saldo.py    # Dashboard Dash
├── src/
│   ├── core/
│   │   ├── exchange_client.py
│   │   └── utils.py
│   ├── indicators/
│   │   └── technical_indicators.py
│   ├── strategies/
│   │   └── smart_strategy.py
│   └── safety/
│       └── safety_manager.py
├── data/
│   ├── trading_history.db    # SQLite
│   ├── daily_stats.json      # Stats diários
│   └── backups/              # Backups automáticos
└── logs/
    └── trading_bot.log
```

---

## ✅ Checklist de Boas Práticas

- [x] Usar SINGLETON para conexões de API
- [x] Converter tipos antes de serializar JSON
- [x] Inicializar TODOS os atributos no `__init__`
- [x] Não passar parâmetros de conexão em chamadas de API
- [x] Adicionar logs de debug para troubleshooting
- [x] Usar `default=str` em `json.dump()` como fallback
- [x] Configurar timeouts adequados (10-15s para APIs)
- [x] Implementar rate limiting (`enableRateLimit: True`)

---

## 🚀 Próximos Passos Concluídos

### ✅ 1. GitHub - Versionamento
- Repositório Git inicializado
- Commits organizados por versão
- `.gitignore` configurado para ignorar:
  - `venv/`, `__pycache__/`, `build/`, `dist/`
  - `*.sqlite3`, `*.db`, `*.log`
  - `.env` (segurança)

### ✅ 2. Scripts de Inicialização
Criados scripts `.bat` para facilitar uso:

| Script | Função |
|--------|--------|
| `INICIAR_BOT.bat` | Inicia apenas o bot |
| `INICIAR_DASHBOARD.bat` | Inicia apenas o dashboard |
| `INICIAR_TUDO.bat` | Inicia bot + dashboard + abre navegador |
| `INSTALAR_NOVA_MAQUINA.bat` | Instala dependências automaticamente |

### ✅ 3. Portabilidade - ZIP para Outra Máquina

**Problema:** Projeto original tinha ~21MB devido a pastas desnecessárias.

**Solução:** Criar ZIP limpo excluindo:
- `venv/` - Ambiente virtual (7MB+) - reinstalado via pip
- `build/`, `dist/` - Arquivos do PyInstaller
- `__pycache__/` - Cache do Python
- `.git/` - Histórico do Git
- `*.sqlite3`, `*.db` - Bancos de dados (recriados)
- `logs/` - Logs antigos

**Resultado:** ZIP de **513 KB** vs 21MB original (redução de 97%)

**Comando PowerShell usado:**
```powershell
Get-ChildItem $src -Exclude @("build","dist","logs","__pycache__",".git","venv") | 
    Copy-Item -Destination $temp -Recurse
Compress-Archive -Path "$temp\*" -DestinationPath $zip
```

**Aprendizado:**
> ⚠️ Nunca incluir `venv/` em ZIPs ou Git! As dependências são reinstaladas via `pip install -r requirements.txt`. Isso reduz drasticamente o tamanho.

---

## 📋 Histórico de Versões (Git)

| Versão | Commit | Descrição |
|--------|--------|-----------|
| v2.1 | `5454e4e` | Scripts de inicialização e portabilidade |
| v2.0 | `6c8c7ef` | Bot completo com dashboard e correções |
| v1.1 | `e670493` | Sistema adaptativo com múltiplas compras |
| v1.0 | `a9bd9a4` | Initial commit |

---

## 🖥️ Instruções para Nova Máquina

### Pré-requisito:
- **Python 3.9+** instalado com **"Add to PATH"** marcado

### Passos:
1. Extrair `App_Leonardo_PORTATIL.zip`
2. Executar `INSTALAR_NOVA_MAQUINA.bat` (instala dependências)
3. Executar `INICIAR_TUDO.bat` (inicia o sistema)
4. Acessar `http://localhost:8050` no navegador

---

*Documento atualizado em 30/11/2025 - App Leonardo v2.1*
