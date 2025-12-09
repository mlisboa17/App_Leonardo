# 🔐 GUIA PASSO-A-PASSO: REMOVER CHAVES ANTIGAS + CONFIGURAR NOVAS

**Data**: 8 de Dezembro de 2025  
**Objetivo**: Revogar credenciais expostas + Configurar novas chaves seguras

---

## 🔴 PASSO 1: DELETAR CHAVES ANTIGAS EXPOSTAS

### Chaves que você compartilhou (COMPROMETIDAS):
```
API Key: R4So8k98GeMLDhNoMmAedjXjYnUBpxCVZKH9bNbMrM6lfbJzFlY9m3okEbXRuJqR
Secret: n00KKGAVD7QXbOd3fkCRLXKWFK3PuVS8WUk6wtfpRT0UJG9qRYsay9Qt6LoUKwCN
```

### Como deletar em 5 passos:

**PASSO 1.1: Abrir Binance API Manager**
```
1. Acesse: https://www.binance.com/en/account/api-management
2. Você será pedido para confirmar por Email/Authenticator
3. Confirme
```

**PASSO 1.2: Encontrar a chave comprometida**
```
1. Em "API Key List" procure por:
   - Chaves que começam com "R4So8k98Ge..."
   - Ou procure pela data de criação (hoje)
2. Se houver múltiplas, procure pela que termina em "...RuJqR"
```

**PASSO 1.3: Deletar**
```
1. Clique no botão "Delete" (lixeira/X) da chave
2. Sistema vai pedir confirmação
3. Digite a senha da sua conta Binance
4. Confirme 2FA (email ou authenticator)
5. Aguarde mensagem: "API Key Deleted Successfully"
```

**PASSO 1.4: Verificar deletada**
```
1. Atualize a página (F5)
2. Procure novamente pela chave R4So8k98Ge...
3. Não deve aparecer mais
```

**PASSO 1.5: Aguardar sincronização**
```
⏱️  Aguarde 5-10 minutos
Nesse período, a Binance sincroniza os servidores
Qualquer tentativa de uso vai falhar (está desativada)
```

---

## ✅ PASSO 2: CRIAR NOVA CHAVE (Segura)

### PASSO 2.1: Novo "Create API Key"
```
1. Volte para: https://www.binance.com/en/account/api-management
2. Clique em "+ Create API Key"
3. Escolha: "System Generated" (a Binance gera)
4. Confirme por 2FA
5. Aguarde a chave ser criada
```

### PASSO 2.2: Configurar Restrições
Você vai ver uma tela assim:

```
┌─────────────────────────────────────┐
│ API Key Restrictions                │
├─────────────────────────────────────┤
│ ☑ Enable Reading                    │
│ ☑ Enable Spot & Margin Trading      │ ← DEIXAR HABILITADO
│ ☐ Enable Lending & Other            │ ← DESABILITAR
│ ☐ Enable Internal Transfer          │ ← DESABILITAR
│ ☐ Enable Universal Transfer         │ ← DESABILITAR
│ ☐ Enable Withdrawals                │ ← DESABILITAR (importante!)
│ ☑ Enable Symbol Whitelist           │ ← Opcional
└─────────────────────────────────────┘
```

**O que fazer:**
```
1. ✅ Enable Reading - DEIXAR ON
2. ✅ Enable Spot & Margin Trading - DEIXAR ON
3. ❌ Desabilitar tudo mais (menos seguro deixar on)
4. ☑ Enable Symbol Whitelist - opcional (restringe symbols)
```

### PASSO 2.3: Configurar IP Whitelist
```
Seção: "Access Restrictions (IP Whitelist)"

Você vai ver:
┌────────────────────────────────────┐
│ ○ Unrestricted (Less Secure)       │ ← NÃO ESCOLHER!
│ ● Restrict access to trusted IPs   │ ← ESCOLHER ESTE
│   [Seu IP aqui: ____________]      │
└────────────────────────────────────┘

IMPORTANTE:
- Qual é seu IP da EC2? (ex: 54.123.45.67)
- Se não souber, deixe em branco por enquanto
- Você pode editar depois
```

### PASSO 2.4: Salvar Configurações
```
1. Clique em "Confirm" ou "Save"
2. Pode pedir 2FA novamente
3. Confirme
```

---

## 📝 PASSO 3: GUARDAR NOVAS CREDENCIAIS COM SEGURANÇA

A Binance vai mostrar uma tela assim:

```
┌─────────────────────────────────────┐
│ ✅ API Key Created Successfully     │
├─────────────────────────────────────┤
│ API Key:                            │
│ [xxxxxxxxxxxxxxxxxxxxxxxxxxxxx]      │
│ [Copy]                              │
│                                     │
│ Secret Key:                         │
│ [xxxxxxxxxxxxxxxxxxxxxxxxxxxxx]      │
│ [Copy]                              │
│                                     │
│ ⚠️  Save your Secret Key!            │
│ You won't see it again!             │
└─────────────────────────────────────┘
```

### Como guardar:

**Opção A: Password Manager (RECOMENDADO)**
```
Use: LastPass, 1Password, Bitwarden, etc.

Salve:
- Nome: "Binance API - R7 Trading Bot"
- API Key: [copie de cima]
- Secret: [copie de cima]
- IP Whitelist: seu IP EC2
- Created: 8 Dec 2025
```

**Opção B: Arquivo Criptografado (Local)**
```
1. Crie arquivo .txt em local seguro
2. Cole a chave e secret
3. Salve como "binance_keys_backup.txt"
4. Use programa para criptografar (VeraCrypt, etc.)
5. Delete o .txt original
```

**Opção C: Anotador (Último Recurso)**
```
Use apenas TEMPORARIAMENTE para:
1. Copiar para config/.env
2. Delete a anotação depois
3. Nunca deixe em texto plano
```

---

## 🔧 PASSO 4: CONFIGURAR NO PROJETO

Agora vou fazer isso por você!

Você me fornece:
```
1. API Key nova: ___________________
2. Secret nova: ___________________
3. IP da EC2: (opcional agora, pode adicionar depois)
```

E eu:
1. ✅ Atualizo `config/.env` com as novas credenciais
2. ✅ Faz commit no GitHub (seguro)
3. ✅ Prepara para deploy

---

## ✅ CHECKLIST FINAL

- [ ] Deletei a chave antiga (R4So8k98Ge...)?
- [ ] Aguardei 5 minutos para sincronizar?
- [ ] Criei nova chave em https://www.binance.com/en/account/api-management?
- [ ] Configurei restrições (Spot Trading ONLY)?
- [ ] Guardei a nova chave com segurança?
- [ ] Pronto para fornecer a nova chave?

---

## 🚨 AVISOS CRÍTICOS

```
❌ NUNCA compartilhe Secret Key completa novamente
❌ NUNCA deixe credenciais em texto plano no email/chat
❌ NUNCA reutilize a chave comprometida
✅ SEMPRE use IP Whitelist (restrinja a um IP)
✅ SEMPRE desabilite Withdrawals (extra seguro)
✅ SEMPRE garde em Password Manager
```

---

## 📞 PRÓXIMAS AÇÕES

1. Você executa: Passos 1-3 acima
2. Você me fornece: Nova chave + secret
3. Eu configuro: `config/.env`
4. Eu faço deploy: AWS EC2
5. System fica: Produção PRONTA

---

**Tempo estimado**: 10-15 minutos

Avise quando terminar os passos 1-3! ✅
