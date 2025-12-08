# ☁️ AWS DEPLOY - Checklist Completo

## 📋 Status Atual
- ✅ Código pronto para produção
- ✅ Documentação AWS existente
- ✅ Audit + Observability implementados
- ⏳ **SGBD:** Será na v2.0 (usar JSON por enquanto)
- ⏳ **Deploy:** Precisa ser executado

---

## 🚀 FASE 1: Preparação Local (Seu PC)

### 1.1 Validar Código
```powershell
# Terminal - Windows PowerShell
cd "c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"

# Limpar arquivos temporários
Remove-Item -Path "__pycache__" -Recurse -Force
Remove-Item -Path "*.pyc" -Recurse -Force

# Teste rápido dos módulos principais
python -m pytest src/tests/test_e2e_restart_audit.py -v
```

### 1.2 Preparar Pacote para Upload
```powershell
# Criar arquivo compactado (sem venv)
tar --exclude='venv_new' `
    --exclude='__pycache__' `
    --exclude='.git' `
    --exclude='.env' `
    --exclude='data/audit/*' `
    -czf r7-trading-bot.tar.gz .

# Resultado: arquivo ~50MB
Get-Item r7-trading-bot.tar.gz | ForEach-Object {
    "Tamanho do arquivo: {0:N0} bytes" -f $_.Length
}
```

---

## ☁️ FASE 2: AWS Setup (primeira vez)

### 2.1 Criar Instância EC2
**No AWS Console:**
1. EC2 → Instances → Launch Instance
2. **Name**: `r7-trading-bot-prod`
3. **AMI**: Ubuntu 22.04 LTS (Free Tier eligible)
4. **Instance type**: `t3.micro` (FREE) ou `t3.small` (se precisar)
5. **Key pair**: Criar/Selecionar `r7-trading-bot-prod.pem`
6. **Network settings**:
   - VPC: `default`
   - Security group name: `r7-trading-bot-sg`
   - Inbound rules:
     - SSH (22): Your IP
     - Custom TCP (8080): 0.0.0.0/0 (API)
     - Custom TCP (3000): 0.0.0.0/0 (React Frontend)
7. **Storage**: 20GB `gp3` (standard)
8. **Launch**

### 2.2 Aguardar EC2 estar pronta
- Status: "Running"
- Anotar **Public IPv4**: `XXX.XXX.XXX.XXX`

### 2.3 Criar S3 Bucket (Backups)
**No AWS Console:**
1. S3 → Create bucket
2. **Name**: `r7-trading-bot-backups-123456` (único globalmente)
3. **Region**: us-east-1 (mais barato)
4. **Encryption**: SSE-S3 (padrão)
5. **Create**

---

## 🖥️ FASE 3: Configurar Servidor (SSH)

### 3.1 Conectar ao Servidor
```powershell
# Salvar PEM no seu PC (se não tiver)
# Exemplo: C:\Users\gabri\.ssh\r7-trading-bot-prod.pem

$KEY_PATH = "C:\Users\gabri\.ssh\app-leonardo-prod.pem"
$IP = "XXX.XXX.XXX.XXX"  # Substituir pelo IP da EC2

# Conectar SSH
ssh -i $KEY_PATH ubuntu@$IP
```

### 3.2 Atualizar Sistema (no servidor)
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip git curl wget
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
```

### 3.3 Preparar Diretórios
```bash
# Criar estrutura
mkdir -p ~/r7-trading-bot
mkdir -p ~/r7-trading-bot/data/{audit,metrics,backups}
mkdir -p ~/logs
chmod 755 ~/r7-trading-bot

cd ~/r7-trading-bot
```

### 3.4 Upload do Código (do seu PC, em novo PowerShell)
```powershell
$KEY_PATH = "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem"
$IP = "XXX.XXX.XXX.XXX"
$LOCAL_FILE = "C:\Users\gabri\...\r7-trading-bot.tar.gz"

# Enviar arquivo
scp -i $KEY_PATH $LOCAL_FILE ubuntu@${IP}:~/r7-trading-bot/

# Verificar
ssh -i $KEY_PATH ubuntu@$IP "ls -lh ~/r7-trading-bot/"
```

### 3.5 Descompactar no Servidor
```bash
cd ~/r7-trading-bot
tar -xzf r7-trading-bot.tar.gz
rm r7-trading-bot.tar.gz
ls -la
```

---

## 🔧 FASE 4: Configurar Aplicação

### 4.1 Criar Virtual Environment
```bash
cd ~/r7-trading-bot
python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements_new.txt
```

### 4.2 Configurar Variáveis de Ambiente
```bash
# Criar arquivo .env
cat > .env << 'EOF'
# 🔐 Chaves da Binance (seu IP trader)
BINANCE_API_KEY=sua_api_key_aqui
BINANCE_API_SECRET=seu_secret_aqui

# 🔑 Segurança
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
DEBUG=False

# 📍 Servidor
HOST=0.0.0.0
PORT=8080

# 📊 Banco de Dados (JSON - v1.0)
DATABASE_PATH=data/app_leonardo.db

# ☁️ AWS
AWS_REGION=us-east-1
AWS_BUCKET=r7-trading-bot-backups-123456
AWS_ACCESS_KEY_ID=sua_aws_key
AWS_SECRET_ACCESS_KEY=sua_aws_secret

EOF

cat .env
```

### 4.3 Criar Diretórios de Dados
```bash
# Garantir que existem
mkdir -p data/{audit,metrics,backups,ai,cache,history}
mkdir -p logs
mkdir -p config
chmod 777 data logs

# Copiar configurações
cp config/bots_config_template.yaml config/bots_config.yaml
```

---

## ⚙️ FASE 5: Configurar Systemd Services

### 5.1 Service - API Backend
```bash
sudo tee /etc/systemd/system/r7-trading-bot-api.service > /dev/null << 'EOF'
[Unit]
Description=R7 Trading Bot API - Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/r7-trading-bot
Environment="PATH=/home/ubuntu/r7-trading-bot/venv/bin"
ExecStart=/home/ubuntu/r7-trading-bot/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/logs/api.log
StandardError=append:/home/ubuntu/logs/api_error.log

[Install]
WantedBy=multi-user.target
EOF
```

### 5.2 Service - Main Bot
```bash
sudo tee /etc/systemd/system/r7-trading-bot.service > /dev/null << 'EOF'
[Unit]
Description=R7 Trading Bot API - Main Process
After=network.target r7-trading-bot-api.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/r7-trading-bot
Environment="PATH=/home/ubuntu/r7-trading-bot/venv/bin"
ExecStart=/home/ubuntu/r7-trading-bot/venv/bin/python main_multibot.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/logs/bot.log
StandardError=append:/home/ubuntu/logs/bot_error.log

[Install]
WantedBy=multi-user.target
EOF
```

### 5.3 Service - React Frontend
```bash
sudo tee /etc/systemd/system/r7-trading-bot-frontend.service > /dev/null << 'EOF'
[Unit]
Description=R7 Trading Bot - React Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/r7-trading-bot/frontend-react
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/logs/frontend.log
StandardError=append:/home/ubuntu/logs/frontend_error.log
Environment="NODE_ENV=production"
Environment="REACT_APP_API_URL=http://XXXX:8080"

[Install]
WantedBy=multi-user.target
EOF
```

### 5.4 Carregar Serviços
```bash
sudo systemctl daemon-reload
sudo systemctl enable r7-trading-bot-api.service
sudo systemctl enable r7-trading-bot.service
sudo systemctl enable r7-trading-bot-frontend.service

# Verificar status
sudo systemctl status r7-trading-bot-api.service
```

---

## ▶️ FASE 6: Iniciar Serviços

### 6.1 Iniciar na Ordem Certa
```bash
# 1. API primeiro
sudo systemctl start r7-trading-bot-api.service
sleep 5

# 2. Bot em seguida
sudo systemctl start r7-trading-bot.service
sleep 5

# 3. Frontend por último (se tiver Node instalado)
# sudo systemctl start r7-trading-bot-frontend.service

# Verificar todos
sudo systemctl status r7-trading-bot-api.service
sudo systemctl status r7-trading-bot.service

# Ver logs em tempo real
sudo journalctl -u r7-trading-bot-api.service -f
```

---

## 📊 FASE 7: Configurar Dashboard (Alterações)

### 7.1 Atualizar URL da API no Frontend
**Arquivo: `frontend-react/.env.production`**
```
REACT_APP_API_URL=http://SEU_IP_PUBLICO:8080
REACT_APP_WS_URL=ws://SEU_IP_PUBLICO:8080
```

### 7.2 Adicionar Monitoramento de Status
**Arquivo: `frontend-react/src/pages/Dashboard.tsx`** - Adicionar status do servidor:

```typescript
// Na seção de cards, adicionar:
<StatusCard 
  title="Servidor AWS"
  subtitle={`${serverStatus.status}`}
  value={serverStatus.uptime || '0h'}
  icon="☁️"
/>

// Implementar fetch de status:
useEffect(() => {
  const checkServerStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/health`)
      setServerStatus({
        status: response.ok ? 'Online' : 'Offline',
        uptime: '...'
      })
    } catch (e) {
      setServerStatus({ status: 'Offline', uptime: 'N/A' })
    }
  }
  checkServerStatus()
  const interval = setInterval(checkServerStatus, 30000)
  return () => clearInterval(interval)
}, [])
```

### 7.3 Adicionar Endpoint de Health Check
**Arquivo: `backend/main.py`** - Adicionar antes de `app.include_router`:

```python
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint para monitoramento"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.VERSION,
        "uptime_seconds": int((datetime.now() - app.startup_time).total_seconds())
    }

# No FastAPI startup:
app.startup_time = datetime.now()
```

### 7.4 Adicionar Logs de Acesso
**Arquivo: `backend/main.py`** - Adicionar middleware:

```python
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response
```

---

## 🔒 FASE 8: Segurança em Produção

### 8.1 Configurar Firewall
```bash
# UFW (Uncomplicated Firewall)
sudo ufw enable
sudo ufw allow 22/tcp        # SSH
sudo ufw allow 8080/tcp      # API
sudo ufw allow 3000/tcp      # Frontend
sudo ufw status verbose
```

### 8.2 Gerar HTTPS com Let's Encrypt
```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Gerar certificado (se tiver domínio)
sudo certbot certonly --standalone -d seu-dominio.com

# Configurar renovação automática
sudo systemctl enable certbot.timer
```

### 8.3 Backup Automático para S3
```bash
# Instalar AWS CLI
sudo apt install -y awscli

# Criar script de backup
cat > ~/backup.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
tar -czf ~/backup_${TIMESTAMP}.tar.gz ~/r7-trading-bot/data/
aws s3 cp ~/backup_${TIMESTAMP}.tar.gz s3://r7-trading-bot-backups-123456/
rm ~/backup_${TIMESTAMP}.tar.gz
EOF

chmod +x ~/backup.sh

# Agendar cron (executar a cada 6 horas)
crontab -e
# Adicionar: 0 */6 * * * ~/backup.sh
```

---

## ✅ FASE 9: Verificação Final

### 9.1 Testar Conectividade
```powershell
# Do seu PC
$IP = "XXX.XXX.XXX.XXX"

# Teste 1: API
curl -X GET "http://${IP}:8080/api/health"
# Esperado: {"status": "healthy", ...}

# Teste 2: Dashboard
# Abrir browser: http://${IP}:3000
```

### 9.2 Verificar Logs
```bash
# Terminal do servidor
sudo journalctl -u r7-trading-bot-api.service -n 50
sudo journalctl -u r7-trading-bot.service -n 50

# Ou arquivos
tail -f ~/logs/api.log
tail -f ~/logs/bot.log
```

### 9.3 Testar Reinicio de Bots
```powershell
# Via dashboard ou API
curl -X POST "http://${IP}:8080/api/actions/restart-bot" `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"bot_type":"feira"}'

# Verificar nos logs
# sudo journalctl -u r7-trading-bot.service -f
```

---

## 🎯 Próximos Passos (v2.0)

- [ ] Migrar dados JSON → PostgreSQL na AWS RDS
- [ ] Configurar CloudWatch para métricas
- [ ] Implementar CI/CD (GitHub Actions)
- [ ] Adicionar Rate Limiting (Redis)
- [ ] Criptografia de dados sensíveis (AWS KMS)
- [ ] Load Balancer (se escalar)

---

## 📞 Troubleshooting

### API não responde
```bash
sudo systemctl restart r7-trading-bot-api.service
sudo journalctl -u r7-trading-bot-api.service -e
```

### Bot não inicia
```bash
sudo systemctl restart r7-trading-bot.service
tail -f ~/logs/bot_error.log
```

### Sem espaço em disco
```bash
df -h
# Limpar logs antigos
sudo journalctl --vacuum=50M
```

### SSH timeout
```bash
# No seu PC
ssh -i $KEY -v ubuntu@$IP  # Modo verbose para debug
```

---

**Status**: ☁️ Pronto para deploy  
**Última atualização**: 07/12/2025  
**Tempo estimado**: 1-2 horas
