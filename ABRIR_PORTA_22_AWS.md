# 🔓 ABRIR PORTA 22 (SSH) NA AWS

## Passo a Passo Rápido

### 1. Acesse o Console AWS
- Abra: https://console.aws.amazon.com/ec2/
- Faça login com suas credenciais

### 2. Vá para Security Groups
- No menu lateral esquerdo, clique em **"Security Groups"** (ou "Grupos de Segurança")
- Ou use a barra de busca: digite "Security Groups"

### 3. Encontre o Security Group da sua Instância
- Procure pelo grupo associado à instância **i-0754deeabc809cdea**
- Ou procure pelo nome que contenha "r7" ou "trade"
- Clique no **ID do Security Group** para abrir

### 4. Editar Regras de Entrada (Inbound Rules)
1. Clique na aba **"Inbound rules"** (Regras de entrada)
2. Clique no botão **"Edit inbound rules"** (Editar regras de entrada)
3. Clique em **"Add rule"** (Adicionar regra)

### 5. Configurar Regra SSH (Porta 22)
Preencha os campos:
- **Type**: SSH
- **Protocol**: TCP
- **Port Range**: 22
- **Source**: 0.0.0.0/0 (ou seu IP para mais segurança)
- **Description**: SSH access

### 6. Adicionar Outras Portas Necessárias
Adicione mais 2 regras:

**Regra 2 - HTTP:**
- **Type**: HTTP
- **Protocol**: TCP
- **Port Range**: 80
- **Source**: 0.0.0.0/0
- **Description**: Dashboard HTTP

**Regra 3 - Custom TCP (Streamlit):**
- **Type**: Custom TCP
- **Protocol**: TCP
- **Port Range**: 8503
- **Source**: 0.0.0.0/0
- **Description**: Streamlit Dashboard

### 7. Salvar
- Clique em **"Save rules"** (Salvar regras)
- Aguarde alguns segundos para aplicar

---

## ✅ Verificar se Funcionou

Após salvar, execute no PowerShell:

```powershell
ssh -i "C:\Users\gabri\Downloads\r7_trade_key.pem" -o StrictHostKeyChecking=no ubuntu@18.230.59.118 "echo 'SSH OK!'"
```

**Deve aparecer:** `SSH OK!`

---

## 🎯 Configuração Completa de Security Group

Suas regras devem ficar assim:

| Type       | Protocol | Port Range | Source      | Description        |
|------------|----------|------------|-------------|--------------------|
| SSH        | TCP      | 22         | 0.0.0.0/0   | SSH access         |
| HTTP       | TCP      | 80         | 0.0.0.0/0   | Dashboard HTTP     |
| Custom TCP | TCP      | 8503       | 0.0.0.0/0   | Streamlit Dashboard|

---

## 🔒 Segurança (Opcional - Recomendado)

Para mais segurança, em vez de `0.0.0.0/0`, use **seu IP específico**:

1. Descubra seu IP: https://www.whatismyip.com/
2. Use: `SEU_IP/32` (exemplo: `177.45.123.89/32`)

Isso permitirá acesso apenas do seu IP.

---

## 📸 Onde Encontrar no Console AWS

**Caminho completo:**
```
AWS Console → EC2 Dashboard → Network & Security → Security Groups → [Selecionar Security Group] → Inbound rules → Edit inbound rules
```

---

## ⚡ Após Abrir as Portas

Execute o deploy:

```bash
ssh -i "C:\Users\gabri\Downloads\r7_trade_key.pem" ubuntu@18.230.59.118
wget https://raw.githubusercontent.com/mlisboa17/App_Leonardo/master/deploy_aws.sh
chmod +x deploy_aws.sh
./deploy_aws.sh
```

---

## 🆘 Problemas Comuns

### Erro: "Connection timed out"
- Porta 22 ainda não está aberta
- Verifique se salvou as regras
- Aguarde 30-60 segundos e tente novamente

### Erro: "Permission denied (publickey)"
- A porta está aberta, mas a chave SSH está incorreta
- Verifique se o arquivo `r7_trade_key.pem` está correto

### Erro: "No supported authentication methods available"
- Execute: `icacls "C:\Users\gabri\Downloads\r7_trade_key.pem" /inheritance:r /grant:r "%username%:R"`

---

**Qualquer dúvida, me avise!** 🚀
