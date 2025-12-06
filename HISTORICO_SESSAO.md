# 📋 Histórico de Desenvolvimento - App Leonardo Bot
## Sessão: 5 de Dezembro de 2025

---

## 🎯 Resumo Executivo

Sessão focada em **otimização da estratégia de trading**, **controle usuário vs IA**, e **preparação para deploy na AWS**.

---

## 📊 1. Diagnóstico Inicial

### Problema Identificado:
- PnL por trade muito baixo (~$0.07)
- Take Profit configurado em apenas 0.6%
- Bot "ansioso" tentando comprar sem saldo suficiente

### Solução Aplicada:
- Aumentado TP para meta de **7.5% ao mês**
- Ajustados RSI thresholds para compras mais seletivas

---

## 🛒 2. Estratégia de Feira Implementada

### Conceito:
Estratégia inspirada em vendedor de feira - **preço dinâmico que diminui com o tempo**.

### Configuração por Crypto:

| Tipo | Cryptos | Fator Feira | Estratégia |
|------|---------|-------------|------------|
| Blue Chips | BTC, ETH | 0.3 | HOLD - Esperar TP cheio |
| Estáveis | BNB, LTC, SOL | 0.4-0.5 | Moderado |
| Médias | LINK, AVAX, DOT | 0.6-0.7 | Flexível |
| Meme Coins | DOGE, SHIB, PEPE | 0.9 | Agressivo - Vender rápido |

### Lógica de Venda:
```
TP Dinâmico = TP Base × (1 - fator_feira × tempo_decorrido)
```

### Arquivo Criado:
- `data/feira_strategy_config.json`

### Código Modificado:
- `src/strategies/smart_strategy.py` - Função `should_sell()` com lógica de feira

---

## 💰 3. Poupança Desativada

### Motivo:
Liberar mais capital para trades ativos

### Alterações:
- `config/bots_config.yaml`: `poupanca.enabled: false`
- `data/poupanca.json`: Todos valores zerados

### Resultado:
+$100 liberados para trading

---

## 🤖 4. Controle Usuário vs IA

### Nova Seção no Config:
```yaml
user_control:
  locked_params:
    - "stop_loss"
    - "take_profit"
    - "amount_per_trade"
    - "max_positions"
  
  ai_permissions:
    can_adjust_rsi: true
    can_adjust_trailing: true
    can_enable_disable_bots: false
    can_change_portfolio: false
  
  manual_override_enabled: true
  override_cooldown_hours: 24
```

### Código Modificado:
- `src/ai/auto_config.py` - Métodos de verificação de permissões:
  - `can_ai_modify_param()`
  - `_is_param_locked()`
  - `_is_param_in_cooldown()`
  - `register_manual_edit()`

### Resultado:
- IA **NÃO pode** alterar: stop_loss, take_profit, amount_per_trade, max_positions
- IA **pode** ajustar: RSI, trailing stop, urgência (com limites)
- Edições manuais têm **24h de cooldown** antes da IA poder sugerir mudanças

---

## 📈 5. Aumento de Valor por Trade

### Justificativa:
Com win rate de 62%+, melhor aumentar valor por trade do que número de posições

### Alterações:

| Bot | Antes | Depois | Aumento |
|-----|-------|--------|---------|
| Bot Estável | $60 | **$70** | +17% |
| Bot Médio | $55 | **$65** | +18% |
| Bot Volátil | $45 | $45 | - |
| Bot Meme | $25 | $25 | - |

### Nova Exposição Máxima:
- Antes: $645
- Depois: **$725** (+12%)

---

## ☁️ 6. Preparação Deploy AWS

### Conta AWS:
- **Nome da conta**: `logos`
- **Status**: Verificando Free Tier

### Arquivos Criados:
```
deploy/aws/
├── README_AWS.md              # Guia completo
├── app-leonardo-bot.service   # Serviço systemd do bot
├── app-leonardo-dashboard.service  # Serviço do dashboard
├── setup.sh                   # Script de instalação
├── deploy.sh                  # Script de update
└── .gitignore                 # Ignorar arquivos sensíveis
```

### Opções de Hospedagem:

| Opção | Custo/mês | Status |
|-------|-----------|--------|
| EC2 t3.micro (Free Tier) | $0 (1º ano) | ⏳ Verificando |
| EC2 t3.micro (pago) | ~$10 | Backup |
| Lightsail | $5 | Alternativa |

---

## 🗄️ 7. Banco de Dados

### Tipo: SQLite
### Arquivo: `data/app_leonardo.db`

### Features:
- Transações ACID
- Thread-safe
- Backup automático
- Verificação de integridade
- WAL mode para performance

---

## 📊 8. Status Final do Bot

### Configuração Atual:

| Bot | TP | SL | $/Trade | Max Pos |
|-----|----|----|---------|---------|
| Estável | 1.8% | -1.2% | $70 | 4 |
| Médio | 2.3% | -1.5% | $65 | 4 |
| Volátil | 3.0% | -2.0% | $45 | 3 |
| Meme | 4.0% | -2.5% | $25 | 2 |

### Métricas da Sessão:
- PnL Dia: +$0.36
- Trades: 3
- Win Rate: 66.7%
- Posições Abertas: 10

---

## 📁 Arquivos Modificados

### Configuração:
- `config/bots_config.yaml` - TP, valores por trade, user_control

### Estratégias:
- `src/strategies/smart_strategy.py` - Lógica de feira

### IA:
- `src/ai/auto_config.py` - Controle de permissões

### Dados:
- `data/poupanca.json` - Zerado
- `data/feira_strategy_config.json` - Criado

### Deploy:
- `deploy/aws/*` - Arquivos de deploy AWS

---

## 🔜 Próximos Passos

1. [ ] Finalizar acesso AWS (Free Tier ou Lightsail)
2. [ ] Deploy do bot na nuvem
3. [ ] Configurar backups automáticos
4. [ ] Monitorar performance da estratégia de feira
5. [ ] Ajustar fatores de feira baseado em resultados

---

## 💡 Lições Aprendidas

1. **TP muito baixo = lucros insignificantes** - Mínimo 1.5%+ para valer a pena
2. **Diferentes cryptos precisam de estratégias diferentes** - Blue chips vs meme coins
3. **Usuário deve manter controle sobre parâmetros críticos** - IA como assistente, não dono
4. **Aumentar valor por trade > mais posições** - Menos fragmentação do capital

---

*Documento gerado em 05/12/2025 às 22:50*
