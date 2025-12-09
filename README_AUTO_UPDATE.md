# 🔄 Sistema de Auto-Update de Saldos

## O que faz?

O sistema monitora **automaticamente** os arquivos de posições e histórico de trades, atualizando os saldos no dashboard **em tempo real** sempre que:

- ✅ Uma nova posição é aberta
- ✅ Uma posição é fechada (trade finalizado)
- ✅ Os preços das cryptos mudam significativamente

## Como funciona?

### 1. Monitor de Arquivos (`auto_update_balances.py`)

Monitora continuamente:
- `data/multibot_positions.json` - Posições abertas
- `data/multibot_history.json` - Histórico de trades

Quando detecta mudança:
1. Conecta com Binance para pegar preços atuais
2. Calcula valor atual de cada posição
3. Calcula PnL (lucro/prejuízo) de cada crypto
4. Atualiza `data/dashboard_balances.json` com:
   - Saldo USDT livre
   - Valor total em cryptos
   - Saldo total (USDT + Cryptos)
   - PnL diário
   - Detalhes de cada posição

### 2. Dashboard Streamlit

Lê `dashboard_balances.json` e exibe:
- 💵 Saldo USDT
- 🪙 Saldo em Cryptos (valor atual no mercado)
- 💎 Saldo Total
- 📈 PnL (lucro ou prejuízo)
- 🎯 Progresso da meta diária

## Como usar?

### Opção 1: Iniciar tudo de uma vez (RECOMENDADO)

```bash
INICIAR_SISTEMA_COMPLETO.bat
```

Isso inicia:
1. Auto-update de saldos (em background)
2. Dashboard Streamlit (http://localhost:8503)

### Opção 2: Iniciar separadamente

**Terminal 1 - Auto-update:**
```bash
.venv\Scripts\activate
python auto_update_balances.py
```

**Terminal 2 - Dashboard:**
```bash
.venv\Scripts\activate
streamlit run frontend/dashboard_multibot_v2.py --server.port 8503
```

### Opção 3: Update manual

Se quiser atualizar manualmente uma vez:
```bash
python update_balances.py
```

## Arquivos envolvidos

```
📁 r7_v1/
├── 🔄 auto_update_balances.py    # Monitor automático (roda em background)
├── 📊 update_balances.py         # Update manual (roda uma vez)
├── 🚀 INICIAR_SISTEMA_COMPLETO.bat   # Inicia tudo automaticamente
│
├── 📂 data/
│   ├── multibot_positions.json   # Posições abertas (MONITORADO)
│   ├── multibot_history.json     # Histórico trades (MONITORADO)
│   └── dashboard_balances.json   # Saldos calculados (ATUALIZADO)
│
└── 📂 frontend/
    └── dashboard_multibot_v2.py  # Dashboard Streamlit
```

## Exemplo de funcionamento

```
[01:05:30] 🔄 Monitor iniciado
[01:05:31] ✅ Saldos atualizados - $1007.22

[01:10:45] 🔄 multibot_positions.json modificado
[01:10:46] 📊 Buscando preços atuais...
[01:10:47] ✅ Saldos atualizados - $1008.15

[01:15:20] 🔄 multibot_history.json modificado (novo trade)
[01:15:21] 📊 Calculando PnL diário...
[01:15:22] ✅ Saldos atualizados - $1009.50
```

## Vantagens

✅ **Automático** - Sem necessidade de atualizar manualmente
✅ **Tempo real** - Saldos sempre atualizados
✅ **Preços reais** - Conecta com Binance para pegar cotações atuais
✅ **PnL preciso** - Calcula lucro/prejuízo baseado em preços reais
✅ **Background** - Roda em segundo plano sem interferir
✅ **Eficiente** - Só atualiza quando há mudanças nos arquivos

## Troubleshooting

**Monitor não está rodando:**
- Verifique se `auto_update_balances.py` está em execução
- Rode `INICIAR_SISTEMA_COMPLETO.bat` para garantir

**Saldos não atualizam:**
- Aguarde 2-3 segundos após uma transação (há cooldown)
- Verifique se os arquivos JSON em `data/` estão sendo modificados

**Erro de conexão Binance:**
- Verifique credenciais em `config/.env`
- Ou edite API_KEY e API_SECRET em `auto_update_balances.py`

## Credenciais

As credenciais da Binance estão configuradas em:
- `config/.env` (preferencial)
- Hardcoded em `auto_update_balances.py` (fallback)

**Nunca commite o arquivo .env com credenciais reais!**
