# ⚡ Bot Único - Modos de Operação

## 📋 Resumo

O **Bot Único** agora possui **2 MODOS** de operação que você pode escolher:

---

## 🎯 MODO SOLO (Recomendado)

**Como funciona:**
- Bot Único assume **TODAS as cryptos**
- Bot Único gerencia **TODO o capital**
- Os 4 bots (Estável, Médio, Volátil, Meme) ficam **PAUSADOS automaticamente**
- Estratégia unificada e centralizada

**Quando usar:**
- ✅ Você quer **máxima eficiência** e controle centralizado
- ✅ Quer evitar conflitos entre bots
- ✅ Prefere uma estratégia adaptativa única

**Configuração:**
```yaml
enabled: true
operation_mode: SOLO
```

**Comportamento:**
1. Ao ativar Bot Único em MODO SOLO → Pausa os 4 bots
2. Bot Único opera sozinho com todas as cryptos
3. Ao desativar Bot Único → Você pode reativar os 4 bots manualmente

---

## 🔄 MODO HÍBRIDO (Experimental)

**Como funciona:**
- Bot Único trabalha **JUNTO** com os 4 bots especializados
- Cada bot tem sua **própria carteira** separada
- Bot Único **NÃO assume** as cryptos dos outros
- Bot Único opera apenas com **suas próprias cryptos** (ou as que adquirir)
- Total: **5 bots trabalhando simultaneamente** (+1 bot no sistema)

**Quando usar:**
- ✅ Você quer **máxima diversificação**
- ✅ Quer testar estratégias diferentes simultaneamente
- ✅ Prefere distribuir risco entre múltiplos bots

**Configuração:**
```yaml
enabled: true
operation_mode: HYBRID
```

**Comportamento:**
1. Ao ativar Bot Único em MODO HÍBRIDO → NÃO pausa os 4 bots
2. Bot Único opera com sua própria carteira
3. Os 4 bots continuam com suas carteiras
4. Cada bot é independente

---

## 🎮 Como Ativar/Trocar Modo

### Via Dashboard (Recomendado)

1. Acesse: **🎮 Bot Control** (no menu lateral)
2. Seção **⚡ UnicoBot**
3. Se desativado:
   - Escolha o modo: SOLO ou HÍBRIDO
   - Clique em **⚡ ATIVAR UnicoBot**
4. Se ativado:
   - Use os botões **🎯 Mudar para MODO SOLO** ou **🔄 Mudar para MODO HÍBRIDO**

### Via Arquivo YAML

Edite `config/unico_bot_config.yaml`:

```yaml
enabled: true
operation_mode: SOLO  # ou HYBRID
```

---

## 📊 Comparação

| Característica | MODO SOLO | MODO HÍBRIDO |
|----------------|-----------|--------------|
| **Bots ativos** | 1 (só Bot Único) | 5 (Bot Único + 4 bots) |
| **Carteiras** | 1 compartilhada | 5 separadas |
| **Capital por bot** | Todo o capital | Capital dividido |
| **Complexidade** | Baixa | Alta |
| **Conflitos** | Zero | Possíveis |
| **Diversificação** | Moderada | Máxima |
| **Recomendado para** | Iniciantes | Avançados |

---

## ⚠️ Avisos Importantes

### MODO SOLO:
- ✅ Mais estável e previsível
- ✅ Evita competição entre bots
- ⚠️ Concentra todo capital em um só bot

### MODO HÍBRIDO:
- ✅ Máxima diversificação
- ✅ Permite comparar estratégias
- ⚠️ Requer mais capital para operar bem
- ⚠️ Possíveis conflitos se bots tentarem comprar mesma crypto
- ⚠️ Mais complexo de monitorar

---

## 🚀 Exemplos de Uso

### Exemplo 1: Usuário Conservador
```
Capital: $1000
Escolha: MODO SOLO
Bot Único: $1000 (gerencia tudo)
4 bots: Pausados
```

### Exemplo 2: Usuário Agressivo
```
Capital: $2000
Escolha: MODO HÍBRIDO
Bot Único: $400
Bot Estável: $400
Bot Médio: $400
Bot Volátil: $300
Bot Meme: $300
Reserve: $200
```

---

## 📝 Configuração Recomendada por Capital

| Capital Total | Modo Recomendado | Distribuição |
|---------------|------------------|--------------|
| < $1000 | SOLO | Bot Único: 100% |
| $1000 - $2000 | SOLO | Bot Único: 100% |
| $2000 - $5000 | HÍBRIDO | Cada bot: ~20% |
| > $5000 | HÍBRIDO | Personalizado |

---

## 🔧 Troubleshooting

**Problema:** Bot Único ativado mas outros bots também ativos (MODO SOLO)
**Solução:** Vá em Bot Control → Pausar TODOS → Ative só Bot Único

**Problema:** Bot Único não compra nada (MODO HÍBRIDO)
**Solução:** Verifique se tem capital alocado para ele

**Problema:** Conflito entre bots (MODO HÍBRIDO)
**Solução:** Mude para MODO SOLO ou ajuste carteiras

---

## 📚 Arquivos Relacionados

- `config/unico_bot_config.yaml` - Configuração do Bot Único
- `frontend/pages/06_bot_control.py` - Interface de controle
- `config/bots_config.yaml` - Configuração dos 4 bots

---

**Última atualização:** 08/12/2024
