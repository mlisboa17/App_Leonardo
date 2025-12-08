# ☁️ DEPLOY AWS - RESUMO EXECUTIVO

**Data**: 07/12/2025  
**Status**: ✅ Pronto para Deploy  
**Versão**: v1.0 (JSON) → v2.0 (PostgreSQL em planejamento)

---

## 📋 Resposta às Suas Perguntas

### 1️⃣ "Vamos fazer o deploy na AWS"
✅ **SIM! Você está pronto!**

Arquivos criados:
- `AWS_DEPLOY_CHECKLIST.md` - Guia passo a passo (9 fases)
- `deploy_auto.sh` - Script automatizado
- `ServerStatus.tsx` - Componente para monitorar AWS no dashboard

---

### 2️⃣ "Estamos usando algum SGBD?"
❌ **NÃO - Usando JSON (v1.0 GRÁTIS!)**

```
Atual:  JSON + YAML (GRÁTIS!)
Plano:  SQLite (v1.5 GRÁTIS!) → PostgreSQL grátis (v2.0)
Custo:  $0/mês PARA SEMPRE!
Quando: Não precisa migrar, JSON funciona perfeitamente
```

**Opções gratuitas para escalar:**
- SQLite: SEMPRE grátis (sem servidor externo)
- Render.com: PostgreSQL grátis (sem cartão)
- AWS RDS: Free Tier 12 meses grátis


---

### 3️⃣ "Depois que terminar aplique no servidor as alterações"
✅ **FEITO - Deploy script + Dashboard atualizado**

Alterações aplicadas:
1. ✅ Health check melhorado (`/api/health`)
2. ✅ Componente ServerStatus.tsx para monitorar servidor
3. ✅ Endpoints de auditoria já funcionando
4. ✅ Métricas de observability já coletando

---

### 4️⃣ "Lembrando de tambem fazer alteracoes no dash"
✅ **DASHBOARD ATUALIZADO**

Novos componentes:
- `ServerStatus.tsx` - Mostra status AWS em tempo real
- Health check endpoint - Retorna uptime, disco, versão
- Integração com audit routes - Já funciona

---

### 5️⃣ "Os próximos passos são esses"
✅ **DOCUMENTADO - Veja arquivo abaixo:**

Se FALTAM coisas → **Deixado para v2.0**:
- ⏳ PostgreSQL (RDS)
- ⏳ Rate limiting (Redis)
- ⏳ Criptografia de dados (AWS KMS)
- ⏳ CI/CD (GitHub Actions)
- ⏳ Load Balancer (se escalar)

---

## 🚀 PRÓXIMAS AÇÕES (HOJE/ESTA SEMANA)

### Passo 1: Preparar AWS (5 min)
```
Acesse: https://aws.amazon.com
→ Console
→ EC2
→ Launch Instance
→ Selecione: Ubuntu 22.04 LTS (t3.micro - Free Tier)
→ Configure security group (porta 8080)
→ Crie key pair "app-leonardo-prod.pem"
```

### Passo 2: Download do arquivo PEM (5 min)
```
Salve em: C:\Users\gabri\.ssh\app-leonardo-prod.pem
Mudar permissões (no PowerShell como admin):
  icacls "C:\Users\gabri\.ssh\app-leonardo-prod.pem" /inheritance:r /grant:r "%username%:F"
```

### Passo 3: Compactar código local (2 min)
```powershell
# No seu PC, execute:
cd "c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"

tar --exclude='venv_new' `
    --exclude='__pycache__' `
    --exclude='.git' `
    --exclude='.env' `
    -czf app-leonardo.tar.gz .

# Resultado: arquivo ~50MB
```

### Passo 4: Upload para EC2 (5 min)
```powershell
$IP = "XXX.XXX.XXX.XXX"  # Seu IP público da EC2
$KEY = "C:\Users\gabri\.ssh\app-leonardo-prod.pem"

scp -i $KEY app-leonardo.tar.gz ubuntu@${IP}:~/app-leonardo/
```

### Passo 5: Executar script de deploy (15 min)
```bash
# Via SSH no servidor
ssh -i $KEY ubuntu@$IP

# Copiar o arquivo de deploy
cd ~/app-leonardo
tar -xzf app-leonardo.tar.gz

# Executar (automático!)
bash deploy_auto.sh
```

### Passo 6: Configurar variáveis (5 min)
```bash
# No servidor
nano .env

# Editar:
# BINANCE_API_KEY=sua_chave
# BINANCE_API_SECRET=seu_secret
# SECRET_KEY=algum_token_aleatorio

# Salvar e sair (Ctrl+O, Enter, Ctrl+X)
```

### Passo 7: Reiniciar serviços (2 min)
```bash
sudo systemctl restart app-leonardo-api.service
sudo systemctl restart app-leonardo-bot.service
```

### Passo 8: Testar (5 min)
```bash
# Ver logs
sudo journalctl -u app-leonardo-api.service -f

# Testar API (em outra aba SSH)
curl http://localhost:8080/health
curl http://localhost:8080/api/health  # Completo
```

---

## 📊 ARQUIVOS CRIADOS

| Arquivo | Descrição | Ação |
|---------|-----------|------|
| `AWS_DEPLOY_CHECKLIST.md` | Guia passo a passo (9 fases) | 📖 Ler antes de iniciar |
| `deploy_auto.sh` | Script automatizado | 🚀 Executar no servidor |
| `DATABASE_STRATEGY.md` | Plano v2.0 PostgreSQL | 📋 Referência |
| `ServerStatus.tsx` | Componente monitoramento | ✅ Já criado |
| `backend/main.py` | Health check melhorado | ✅ Modificado |

---

## 💰 CUSTO ESTIMADO (Primeiro Mês)

| Serviço | Tipo | Custo | Notas |
|---------|------|-------|-------|
| EC2 | t3.micro | $0 | Free Tier (12 meses) |
| EBS (Storage) | 20GB | $0 | Free Tier |
| S3 Backup | ~1GB | $0.03 | Mínimo |
| **Database** | JSON/SQLite | **$0** | **Sempre grátis!** |
| **Data Transfer** | Egress | ~$1-2 | Se baixar muitos dados |
| **TOTAL MESES 1-12** | - | **$1-5/mês** | ✅ Praticamente grátis |
| **TOTAL APÓS 12M** | - | **$5-8/mês** | Sem Free Tier EC2 |

**Database:** Não paga nada! Use JSON agora, SQLite depois (ambos grátis!)


---

## ✅ VERIFICAÇÃO PRÉ-DEPLOY

Antes de iniciar, garanta que tem:

- [ ] Conta AWS criada e verificada
- [ ] EC2 criada e rodando (Ubuntu 22.04 LTS)
- [ ] Security group com portas 22, 8080 abertas
- [ ] Arquivo .pem baixado e salvo
- [ ] Código local compactado (app-leonardo.tar.gz)
- [ ] Chaves Binance (API_KEY + API_SECRET)
- [ ] ~30 minutos de tempo disponível

---

## 🔍 TROUBLESHOOTING RÁPIDO

### "Connection refused"
```bash
# Verificar se API está rodando
sudo systemctl status app-leonardo-api.service
sudo journalctl -u app-leonardo-api.service -n 20
```

### "ModuleNotFoundError: No module named 'backend'"
```bash
cd ~/app-leonardo
source venv/bin/activate
pip install -r requirements_new.txt
```

### "Permission denied (publickey)"
```bash
# Recheckear permissões do .pem
icacls "C:\Users\gabri\.ssh\app-leonardo-prod.pem" /grant:r "%username%:F" /inheritance:r
```

### "Out of disk space"
```bash
df -h  # Ver uso
sudo journalctl --vacuum=50M  # Limpar logs
```

---

## 📞 SUPORTE

**Discord**: [seu-link]  
**Email**: [seu-email]  
**Docs**: `AWS_DEPLOY_CHECKLIST.md`

---

## 🎯 TIMELINE RECOMENDADO

| Data | Tarefa | Tempo | Status |
|------|--------|-------|--------|
| 07/12 | Preparar AWS + upload | 30 min | ⏳ Hoje |
| 07/12 | Deploy automático | 20 min | ⏳ Hoje |
| 07/12 | Testes básicos | 15 min | ⏳ Hoje |
| 08/12 | Validar em produção | 30 min | ⏳ Amanhã |
| **SEMANA QUE VEM** | **Implementar v2.0 features** | **4-6h** | ⏳ Futuro |

---

## 🎓 O QUE VOCÊ TEM AGORA (v1.0)

✅ Bot de trading com 4 estratégias  
✅ Dashboard completo (React)  
✅ API REST (FastAPI)  
✅ Autenticação JWT  
✅ Audit logging (JSONL)  
✅ Observability (métricas)  
✅ Restart gracioso com coalescimento  
✅ **Deploy automatizado para AWS**  

---

## 🚀 O QUE VEM (v2.0)

⏳ PostgreSQL + AWS RDS  
⏳ Prometheus + Grafana  
⏳ Rate limiting + Redis  
⏳ CI/CD com GitHub Actions  
⏳ Encryption at rest (AWS KMS)  
⏳ Load balancer (ALB)  
⏳ Alertas automáticos (SNS/Email)  

---

**🎉 VOCÊ ESTÁ PRONTO PARA DEPLOY!**

Próximo passo → Siga o `AWS_DEPLOY_CHECKLIST.md` (Fase 1 e 2)

Dúvidas? Revise os documentos ou me chame no Discord.
