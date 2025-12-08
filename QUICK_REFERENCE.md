# 🚀 AWS DEPLOY - QUICK REFERENCE

**Print este documento ou deixe aberto enquanto faz o deploy!**

---

## 📋 FASES

```
Fase 1: AWS Setup          (10 min) ← FAZER HOJE
Fase 2: Preparar Código    (10 min) ← FAZER HOJE
Fase 3: Upload            (5 min)  ← FAZER HOJE
Fase 4: Deploy Automático (20 min) ← FAZER HOJE
Fase 5: Validar           (10 min) ← FAZER HOJE
```

**TOTAL**: ~55 minutos

---

## ⚡ COMANDOS RÁPIDOS

### Windows PowerShell

```powershell
# Gerar SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Compactar código
cd "c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"
tar --exclude='venv_new' --exclude='__pycache__' --exclude='.git' -czf app-leonardo.tar.gz .

# Upload para AWS
$IP = "XXX.XXX.XXX.XXX"
$KEY = "C:\Users\gabri\.ssh\app-leonardo-prod.pem"
scp -i $KEY app-leonardo.tar.gz ubuntu@${IP}:~/app-leonardo/

# Conectar SSH
ssh -i $KEY ubuntu@$IP
```

### Ubuntu Server (SSH)

```bash
# Descompactar
cd ~/app-leonardo
tar -xzf app-leonardo.tar.gz

# Deploy automático
bash deploy_auto.sh

# Verificar status
sudo systemctl status app-leonardo-api.service
sudo systemctl status app-leonardo-bot.service

# Ver logs
sudo journalctl -u app-leonardo-api.service -f

# Testar API
curl http://localhost:8080/health
```

---

## 🔐 ARQUIVOS ESSENCIAIS

### Local (seu PC)

- `app-leonardo.tar.gz` (código)
- `C:\Users\gabri\.ssh\app-leonardo-prod.pem` (SSH key)

### Servidor (AWS)

- `~/app-leonardo/.env` (credenciais)
- `~/app-leonardo/config/bots_config.yaml` (config)
- `~/logs/*.log` (logs)
- `~/app-leonardo/data/*` (dados)

---

## 📌 VALORES A SUBSTITUIR

Quando vir `XXX.XXX.XXX.XXX`, substitua por:

```
IP Público da EC2 (ex: 54.123.45.67)
```

Quando vir `seu_valor_aqui`, substitua por:

```
BINANCE_API_KEY=abc123def456...
BINANCE_API_SECRET=xyz789uvw012...
SECRET_KEY=algumTokenAleatorio...
```

---

## ✅ VERIFICATIONS

### Antes de iniciar

- [ ] AWS console acessível
- [ ] Chaves Binance disponíveis
- [ ] SSH key salva localmente
- [ ] Código local compilado (`pytest src/tests/test_e2e_restart_audit.py`)

### Durante o deploy

- [ ] EC2 criada e "Running"
- [ ] SSH conecta com sucesso
- [ ] Código descompactado
- [ ] venv criado
- [ ] .env preenchido
- [ ] Deploy script executado sem erros

### Depois do deploy

- [ ] API respondendo: `curl http://IP:8080/health`
- [ ] Logs sem erros: `sudo journalctl -u app-leonardo-api.service -n 20`
- [ ] Bots iniciando: Check status services

---

## 🆘 TROUBLESHOOTING

| Erro | Solução |
|------|---------|
| **SSH permission denied** | Recheckear `.pem` permissions: `icacls "path" /grant:r "%username%:F" /inheritance:r` |
| **ModuleNotFoundError** | `source venv/bin/activate && pip install -r requirements_new.txt` |
| **Port 8080 in use** | `sudo lsof -i :8080` e `kill` do processo |
| **Out of disk** | `df -h` e `sudo journalctl --vacuum=50M` |
| **API won't start** | Ver logs: `sudo journalctl -u app-leonardo-api.service -n 50` |
| **No response from API** | Aguarde 30s e tente de novo |
| **Tarball corruption** | Re-download ou re-create: `tar -tzf app-leonardo.tar.gz \| head` |

---

## 💡 DICAS

- **SSH lento?** Pode ser firewall. Aguarde 2-3 min após launch da EC2.
- **Disco cheio?** Delete arquivos de log antigos em `~/logs/`
- **Query lenta?** Dados JSON (v1.0). Será resolvido em v2.0 com PostgreSQL.
- **Backup?** Automático via cron para S3 (configurado no script).

---

## 📍 ARQUIVOS DOCUMENTAÇÃO

1. **DEPLOY_RESUMO_EXECUTIVO.md** - Visão geral
2. **PRE_DEPLOY_CHECKLIST.md** - Checklist detalhado
3. **AWS_DEPLOY_CHECKLIST.md** - Passo a passo (9 fases)
4. **INTEGRAR_SERVERSTATUS.md** - Dashboard updates
5. **DATABASE_STRATEGY.md** - Plano v2.0 PostgreSQL
6. **Esta arquivo** - Quick reference

**Ler nesta ordem**: 1 → 2 → 3 → Deploy → 4 → 5

---

## 🎯 URLs IMPORTANTES

| Serviço | URL | Porta |
|---------|-----|-------|
| API Docs | `http://IP:8080/docs` | 8080 |
| Health Check | `http://IP:8080/health` | 8080 |
| Dashboard | `http://IP:3000` | 3000 |
| SSH | `ssh -i KEY ubuntu@IP` | 22 |

---

## 📊 ESTRUTURA DADOS

```
~/app-leonardo/
├── venv/                # Python virtual env
├── backend/             # FastAPI
├── frontend-react/      # React dashboard
├── src/                 # Bot logic
├── config/              # YAML configs
├── data/                # JSON data
│   ├── audit/          # JSONL logs
│   └── metrics/        # Métricas
├── logs/               # Application logs
└── .env                # Credenciais (NUNCA commitar!)
```

---

## 🔄 WORKFLOW PÓS-DEPLOY

```
1. Validar por 24h
2. Monitorar logs
3. Testar restart de bots
4. Fazer backup manual
5. Documentar IP
6. (Opcional) Configurar domínio
7. (v2.0) Migrar para PostgreSQL
```

---

## 📞 CONTATOS

**Script falha?**
→ Ver output completo: `bash deploy_auto.sh 2>&1 | tee deploy.log`

**API não responde?**
→ Check logs: `sudo journalctl -u app-leonardo-api.service -f`

**Precisa de ajuda?**
→ Discord / Email / Documentação

---

## ✨ RESUMO FINAL

```
Você tem:
✅ Código testado
✅ Documentação completa
✅ Script automático
✅ Componente monitoramento

Próximo passo:
→ Ler PRE_DEPLOY_CHECKLIST.md
→ Seguir AWS_DEPLOY_CHECKLIST.md (Fase 1-2)
→ Executar deploy_auto.sh

Tempo: 1 hora
Custo: Grátis (12 meses free tier)
```

---

**🚀 BOA SORTE! 🚀**

Você está pronto para deploy em produção!
