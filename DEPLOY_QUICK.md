# 🚀 DEPLOY RÁPIDO R7 TRADING BOT API

## STATUS: PRONTO PARA DEPLOY ✅

```
📦 Código: Enviado para GitHub (master branch)
📁 Arquivo: r7-trading-bot.tar.gz (29.3 MB) - Pronto
🔒 Segurança: Remediada e documentada
📚 Documentação: Completa
✓ Testes: Passando
```

---

## 🎯 DEPLOY EM 3 PASSOS

### **PASSO 1: Criar EC2 Instance** (5 min)

```bash
# AWS Console > EC2 > Launch Instance
- Name: r7-trading-bot-prod
- AMI: Ubuntu 22.04 LTS
- Type: t3.micro (FREE TIER)
- Key Pair: r7-trading-bot-prod.pem
- Security Group:
  - SSH (22): 0.0.0.0/0
  - Custom TCP (8080): 0.0.0.0/0
  - Custom TCP (8501): 0.0.0.0/0

# Anotar: IP público (ex: 52.1.2.3)
```

### **PASSO 2: Upload do Código** (3 min)

```bash
# No seu computador
IP="52.1.2.3"  # Seu IP da EC2
KEY="$HOME/.ssh/r7-trading-bot-prod.pem"

# Upload
scp -i $KEY r7-trading-bot.tar.gz ubuntu@$IP:~/
```

### **PASSO 3: Executar Setup** (3 min)

```bash
# Conectar à EC2
ssh -i $KEY ubuntu@$IP

# Extrair e configurar (automático)
bash setup_quick.sh

# Editar credenciais
nano config/.env
# Adicionar BINANCE_API_KEY e BINANCE_API_SECRET (novas chaves!)

# Iniciar bots
sudo systemctl start r7-trading-bot.service
sudo systemctl start r7-trading-dashboard.service

# Verificar
curl http://localhost:8080/api/health
```

---

## ⚠️ CRÍTICO ANTES DO DEPLOY

### 1. **Revogar Chaves Antigas** 🔐

⚠️ **As chaves expostas estão ATIVAS!**

```
Acesse: https://www.binance.com/en/account/api-management
Revogue:
  - rVFHoreINIsQJtZ7vR9IQc7HGiybp4VLzkXQJtx0bLu9e2F7oIamconSYNmRzbyy (Prod)
  - QcyrgxtWUGXRkcsfx67EBu5OSTCFcIiFTqcCLfM6aV6zeTV8vxCwkobhY5idiU3m (Testnet)
```

### 2. **Criar Novas Chaves** 🔑

```
Em: https://www.binance.com/en/account/api-management
- Create API Key
- Label: r7-trading-bot-prod
- IP: Seu IP público AWS
- Enable: Spot Trading
- Copiar e salvar
```

### 3. **Atualizar config/.env**

```bash
# SSH para EC2
nano config/.env

# Atualizar:
BINANCE_API_KEY=sua_nova_chave_aqui
BINANCE_API_SECRET=seu_novo_secret_aqui
```

### 4. **Testar Credenciais**

```bash
# Na EC2
python test_api_key.py
# Esperado: ✅ AUTENTICAÇÃO FUNCIONANDO!
```

---

## 📊 ARQUITETURA DEPLOY

```
AWS EC2 (t3.micro)
├── OS: Ubuntu 22.04 LTS
├── Python: 3.11
├── Services:
│   ├── r7-trading-bot (main)
│   ├── r7-trading-dashboard (Streamlit)
│   └── API (FastAPI on :8080)
├── Database: JSON v1.0
├── Storage: Logs + Backups
└── Monitoring: Health checks + Systemd
```

---

## 🎯 TEMPO TOTAL: **~15 MINUTOS**

| Etapa | Tempo | Status |
|-------|-------|--------|
| 1. Criar EC2 | 5 min | ⏳ Manual |
| 2. Upload código | 3 min | ⏳ SCP |
| 3. Setup | 3 min | ✅ Automático |
| 4. Config credenciais | 2 min | ⏳ Manual |
| 5. Teste | 2 min | ✅ Automático |

---

## 💰 CUSTO

**Ano 1 (Free Tier):** $0  
**Ano 2+:** ~$10-15/mês

---

## ✅ PRÓXIMOS PASSOS

1. [ ] Revogar chaves antigas na Binance
2. [ ] Criar EC2 instance
3. [ ] Fazer SCP do arquivo
4. [ ] Executar setup_quick.sh
5. [ ] Atualizar config/.env com novas chaves
6. [ ] Testar com curl
7. [ ] Monitorar logs em tempo real

---

## 📚 DOCUMENTAÇÃO

- **START_HERE.md** - Quick reference
- **DEPLOY_MANUAL.md** - Guia detalhado
- **REMEDIATION_SECURITY.md** - Credenciais e segurança
- **AWS_DEPLOY_CHECKLIST.md** - Checklist completo

---

## 🆘 PROBLEMAS COMUNS

### "Timeout na conexão EC2"
```bash
# Verificar security group
# Porta 22 deve estar aberta para seu IP
```

### "Permission denied (publickey)"
```bash
# Verificar arquivo .pem
chmod 600 ~/.ssh/r7-trading-bot-prod.pem
```

### "Invalid API Key"
```bash
# Certificar-se que revogou as chaves antigas
# e criou as novas corretamente
```

### "Port 8080 already in use"
```bash
# Verificar se a porta está em uso
sudo lsof -i :8080
# Matar processo se necessário
sudo kill -9 <PID>
```

---

## 📞 SUPORTE

Para dúvidas, consulte:
- Logs: `sudo tail -f /home/ubuntu/logs/trading_bot.log`
- Status: `sudo systemctl status r7-trading-bot`
- Health: `curl http://localhost:8080/api/health`

