# 🔧 Sistema de Configurações Avançadas - App Leonardo

## 📋 Resumo da Implementação

Implementei um sistema completo de gestão avançada de portfólio com interface web dedicada, conforme solicitado. O sistema implementa a regra específica: **quando o bot tiver 40% do valor total em crypto, ele deve parar de comprar e apenas vender**.

## 🎯 Principais Funcionalidades

### 1. **Interface Web Separada (http://localhost:8051)**
- Página dedicada para configurações avançadas
- Design responsivo com tema escuro
- Navegação entre dashboard principal e configurações
- Controles visuais para todas as regras

### 2. **Regra Principal de Exposição**
- ✅ **Limite de 40% de exposição em crypto**
- ✅ **Ação configurável**: Parar compras, Rebalancear ou Vender tudo
- ✅ **Exceção para portfólio vazio**: Até 5 posições permitidas
- ✅ **Status visual em tempo real**

### 3. **Sistema de Exceções**
- 🔄 **Portfólio Vazio**: Permite até 5 posições se não há crypto
- 🎯 **Alta Confiança**: Ignora limite para sinais > 80% de confiança
- 📉 **DCA**: Permite compras em posições perdendo (Dollar Cost Average)
- 🌅 **Horário Matinal**: Exceção nas primeiras 2 horas do dia

### 4. **Configurações de Timing**
- ⚡ **Horário Agressivo**: 09:00-11:00 (compras mais ativas)
- 🛑 **Apenas Vendas**: 15:00-17:00 (não permite compras)
- ⏰ **Controle temporal** das operações

## 📊 Dashboard de Status

### Monitoramento em Tempo Real:
- 💵 **Saldo USDT atual**
- 💎 **Valor total em crypto**
- 📊 **Percentual de exposição**
- 🎯 **Status da regra** (OK/Atenção/Limite Atingido)

## 🛠️ Arquivos Criados/Modificados

### Novos Arquivos:
1. **`frontend/config_avancado.py`** - Interface web de configurações
2. **`src/core/portfolio_manager.py`** - Lógica de gestão de portfólio
3. **`config/portfolio_rules.json`** - Configurações persistentes
4. **`INICIAR_CONFIG_AVANCADO.bat`** - Script de inicialização

### Modificações:
1. **`main.py`** - Integração do Portfolio Manager
   - Import e inicialização
   - Verificações antes de cada compra
   - Vendas forçadas quando necessário
   - Status de portfólio no resumo

## 🚀 Como Usar

### 1. **Iniciar Interface de Configurações:**
```batch
# Execute o arquivo:
INICIAR_CONFIG_AVANCADO.bat

# Ou manualmente:
python frontend/config_avancado.py
```

### 2. **Acessar Interface:**
- **Configurações Avançadas**: http://localhost:8051
- **Dashboard Principal**: http://localhost:8050

### 3. **Configurar Regras:**
1. Definir **percentual máximo de exposição** (padrão: 40%)
2. Escolher **ação ao atingir limite**
3. Ativar **exceções desejadas**
4. Configurar **horários especiais**
5. **Salvar configurações**

## ⚙️ Regra Principal em Funcionamento

### ✅ **Condição Normal (< 40% exposição)**
```
💰 Saldo: $113.92 USDT
💎 Crypto: $25.00 (18.0% do portfólio)
🟢 Status: OK - Pode comprar normalmente
```

### ⚠️ **Aproximando do Limite (32-40%)**
```
💰 Saldo: $113.92 USDT
💎 Crypto: $48.00 (35.0% do portfólio)
🟡 Status: PRÓXIMO DO LIMITE - Atenção
```

### 🛑 **Limite Atingido (≥ 40%)**
```
💰 Saldo: $113.92 USDT
💎 Crypto: $55.00 (42.0% do portfólio)
🔴 Status: LIMITE ATINGIDO - Apenas vendas
```

## 🔧 Exceções Automáticas

### 1. **Portfólio Vazio**
```
Situação: 0 posições abertas
Ação: Permite até 5 compras independente do limite
Motivo: "Exceção: Portfólio com poucas posições (0) - permitida compra"
```

### 2. **Sinal de Alta Confiança**
```
Situação: Sinal com >80% de confiança
Ação: Ignora limite de exposição
Motivo: "Exceção: Sinal de alta confiança (85.2%) - permitida compra"
```

## 📈 Integração com o Bot

O sistema está **totalmente integrado** ao bot principal:

### ✅ **Verificações Automáticas:**
- Antes de cada compra: verifica exposição e regras
- A cada ciclo: monitora necessidade de vendas forçadas
- No resumo: exibe status completo do portfólio

### 📝 **Logs Detalhados:**
```
2025-11-30 20:11:05 - INFO - 💼 Portfolio Manager inicializado - Regras de exposição ativas
2025-11-30 20:11:07 - INFO - ✅ BTC/USDT: Compra permitida - Exposição: 18.5% (máx: 40%)
2025-11-30 20:11:10 - WARNING - 🚫 ETH/USDT: Limite de exposição atingido: 41.2% (máx: 40%)
```

## 🎮 Controles da Interface

### Botões Principais:
- **💾 Salvar Configurações**: Persiste regras em arquivo
- **🧪 Testar Regras**: Simula aplicação das regras
- **🔄 Aplicar Agora**: Força aplicação imediata

### Navegação:
- **📊 Dashboard Principal**: Volta para http://localhost:8050
- **🔧 Configurações**: Interface atual (localhost:8051)
- **📈 Backtesting**: Futuro módulo de testes

## 🔄 Status de Funcionamento

### ✅ **Testado e Funcionando:**
- ✅ Bot carregando Portfolio Manager automaticamente
- ✅ Verificações de exposição antes de cada compra
- ✅ Interface web rodando em paralelo
- ✅ Persistência de configurações em JSON
- ✅ Status em tempo real no resumo

### 📊 **Resultados Observados:**
```
Portfolio Manager inicializado - Regras de exposição ativas
Saldo USDT: 113.92 USDT
Exposição: 18.5% (máx: 40%)
Status Portfólio: 🟢 OK
Posições: 2/6 | Pode comprar: Sim
```

## 🎯 Conclusão

O sistema implementa **exatamente** a regra solicitada:
- ✅ **40% de exposição máxima** em crypto
- ✅ **Para de comprar** quando limite atingido
- ✅ **Exceção para portfólio vazio** (até 5 posições)
- ✅ **Interface dedicada** para configurações
- ✅ **Integração completa** com o bot

O bot agora opera com **gestão inteligente de risco**, protegendo contra super-exposição em crypto enquanto mantém flexibilidade para situações especiais.

---

**📱 Acesso Rápido:**
- **Dashboard**: http://localhost:8050
- **Configurações**: http://localhost:8051

**🚀 Inicialização:**
- Bot: `python main.py`
- Configurações: `INICIAR_CONFIG_AVANCADO.bat`