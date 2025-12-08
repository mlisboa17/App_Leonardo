# 🎉 R7 TRADING BOT API - PRONTO PARA DEPLOY

## ✅ STATUS: 100% PRONTO

### 📦 Arquivo de Deploy
- **Nome:** `r7-trading-bot.tar.gz`
- **Tamanho:** 29.3 MB
- **Localização:** `c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1\`
- **Status:** ✅ Criado e verificado

### 🏗️ Infraestrutura
- ✅ Aplicação Python pronta (FastAPI + Streamlit)
- ✅ Banco de dados JSON v1.0 (sem custo)
- ✅ Serviços systemd configurados
- ✅ Scripts de setup automático
- ✅ Documentação completa

### 🔑 Requisitos para Deploy
1. **AWS Account** (Free Tier suficiente)
2. **Arquivo .pem** salvo localmente
3. **EC2 t3.micro** (grátis primeiro ano)
4. **S3 Bucket** para backups (opcional)

---

## 🚀 COMO FAZER O DEPLOY (3 PASSOS)

### **PASSO 1: Criar EC2 na AWS** (5 min)
1. Acesse: https://console.aws.amazon.com/ec2
2. Launch Instance → Ubuntu 22.04 LTS
3. Instance: t3.micro
4. Key pair: r7-trading-bot-prod.pem
5. Security group: Abrir portas 22, 8080, 3000, 8501
6. Anotar IP público (ex: 52.1.2.3)

### **PASSO 2: Upload & Setup** (5 min)
Execute no seu PC:
```powershell
$IP = "52.1.2.3"  # Seu IP EC2
$KEY = "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem"

# Upload
scp -i $KEY r7-trading-bot.tar.gz ubuntu@${IP}:~/

# Setup automático (veja DEPLOY_MANUAL.md para script completo)
ssh -i $KEY ubuntu@$IP "bash setup.sh"
```

### **PASSO 3: Iniciar Serviços** (1 min)
```powershell
ssh -i $KEY ubuntu@$IP "sudo systemctl start r7-trading-bot.service"
ssh -i $KEY ubuntu@$IP "sudo systemctl start r7-trading-dashboard.service"
```

---

## 📚 DOCUMENTAÇÃO

| Arquivo | Descrição |
|---------|-----------|
| **DEPLOY_MANUAL.md** | 📋 Guia passo-a-passo completo |
| **AWS_DEPLOY_CHECKLIST.md** | ✅ Checklist detalhado |
| **deploy/aws/README_AWS.md** | 📖 Documentação AWS |
| **deploy/aws/setup.sh** | 🔧 Script setup automático |
| **RENAME_PROGRESS.md** | 📝 Histórico de renomeação |

---

## 🎯 VERIFICAÇÃO PÓS-DEPLOY

### Testar API
```bash
curl -X GET "http://52.1.2.3:8080/api/health"
# Esperado: {"status":"healthy","version":"1.0"}
```

### Ver status
```bash
ssh -i $KEY ubuntu@$IP "sudo systemctl status r7-trading-bot.service"
```

### Ver logs
```bash
ssh -i $KEY ubuntu@$IP "sudo journalctl -u r7-trading-bot.service -f"
```

---

## 💰 CUSTOS ESTIMADOS

### AWS Free Tier (1º ano)
- ✅ EC2 t3.micro: FREE (750h/mês)
- ✅ S3 storage: FREE (5GB)
- ✅ Data transfer: FREE (1GB/mês)
- **Total: $0**

### Após Free Tier
- EC2 t3.micro: ~$8-10/mês
- S3 storage: ~$0.50-1/mês
- **Total: ~$10/mês**

---

## 🔐 Segurança

### Checklist
- [ ] Salvar arquivo .pem em local seguro
- [ ] Não commitar .pem no Git
- [ ] SSH only, sem password
- [ ] Security Group: limitar IPs se possível
- [ ] Editar .env com chaves reais (não commitir)

---

## 📊 Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                     AWS EC2 (ubuntu)                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │          r7-trading-bot.service                  │   │
│  │  (FastAPI Backend @ port 8080)                   │   │
│  │  - /api/health                                   │   │
│  │  - /api/actions/*                                │   │
│  │  - /api/metrics/*                                │   │
│  └──────────────────────────────────────────────────┘   │
│                          ↓                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │    r7-trading-dashboard.service                  │   │
│  │  (Streamlit @ port 8501)                         │   │
│  │  - Dashboard interativo                          │   │
│  └──────────────────────────────────────────────────┘   │
│                          ↓                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │         JSON Database v1.0                       │   │
│  │  - data/app_leonardo.db                          │   │
│  │  - data/audit/*.json                             │   │
│  │  - data/cache/*.json                             │   │
│  └──────────────────────────────────────────────────┘   │
│                          ↓                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │        AWS S3 (Backups automáticos)              │   │
│  │  - data-backup-*.tar.gz                          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Tecnologias

- **Backend:** Python 3.11 + FastAPI
- **Frontend:** Streamlit (Python)
- **Database:** JSON v1.0 (sem custo)
- **DevOps:** Systemd + Shell scripts
- **Cloud:** AWS (EC2 + S3)
- **Monitoring:** Systemd logs + Journalctl

---

## 🎁 Próximas Melhorias

- [ ] v1.1: Renomear database para r7-trading-bot.db
- [ ] v2.0: Migrar para PostgreSQL (AWS RDS Free)
- [ ] v2.5: CI/CD com GitHub Actions
- [ ] v3.0: Kubernetes (se escalar)
- [ ] v3.5: Load balancer + multi-region

---

## 📞 Suporte

### Problemas comuns

| Problema | Solução |
|----------|---------|
| SSH connection refused | Verificar Security Group, esperar 2min após launch |
| API não responde | `sudo systemctl restart r7-trading-bot.service` |
| Falta de espaço | `df -h` e `du -sh ~/r7-trading-bot/` |
| Serviço não inicia | `sudo journalctl -u r7-trading-bot.service -e` |

---

## 🎉 Parabéns!

Você tem um sistema de trading completo, pronto para produção:
- ✅ Código profissional
- ✅ Infra escalável (AWS Free)
- ✅ Documentação completa
- ✅ Monitoramento incluído
- ✅ Backup automático

**Agora é só fazer o deploy! 🚀**

---

**Versão:** 1.0 | **Data:** 8 de Dezembro de 2025 | **Status:** PRODUÇÃO
