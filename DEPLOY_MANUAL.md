# 🚀 DEPLOY DO R7 Trading Bot API - GUIA COMPLETO

## ✅ Status Atual
- ✅ **Código compilado e pronto:** r7-trading-bot.tar.gz (29.3 MB)
- ✅ **Serviços systemd criados:** r7-trading-bot.service, r7-trading-dashboard.service
- ✅ **Scripts de setup**: deploy/aws/setup.sh
- ✅ **Documentação:** AWS_DEPLOY_CHECKLIST.md

---

## 📋 PASSOS PARA DEPLOY

### **PASSO 1: Criar Instância EC2 na AWS** (5 minutos)

1. Abra https://console.aws.amazon.com
2. Vá em **EC2 → Instances → Launch Instance**
3. Preencha:
   - **Name**: `r7-trading-bot-prod`
   - **AMI**: `Ubuntu 22.04 LTS (Free Tier eligible)`
   - **Instance type**: `t3.micro` (FREE)
   - **Key pair**: 
     - Clique em "Create new key pair"
     - Name: `r7-trading-bot-prod`
     - Salve em: `C:\Users\gabri\.ssh\r7-trading-bot-prod.pem`
   - **Network Settings:**
     - VPC: `default`
     - Public IP: Auto-assign enabled
     - Security group: Create new
       - Name: `r7-trading-bot-sg`
       - Inbound rules:
         ```
         SSH (22)        | 0.0.0.0/0
         TCP (8080)      | 0.0.0.0/0  (API Backend)
         TCP (3000)      | 0.0.0.0/0  (React Frontend)
         TCP (8501)      | 0.0.0.0/0  (Streamlit Dashboard)
         ```
   - **Storage**: 20GB `gp3`
4. Clique **"Launch instance"**
5. Aguarde status mudar para **"Running"** (1-2 min)
6. **Copie o IP público** (ex: `52.1.2.3`)

---

### **PASSO 2: Fazer Upload do Código** (3-5 minutos)

**No seu PC (PowerShell/CMD):**

```powershell
# Ir para pasta do projeto
cd "c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"

# Variáveis (ALTERE O IP PARA O DA SUA EC2)
$KEY_PATH = "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem"
$EC2_IP = "52.1.2.3"  # <<< SUBSTITUA PELO IP DA SUA EC2

# Enviar arquivo via SCP
scp -i $KEY_PATH r7-trading-bot.tar.gz ubuntu@${EC2_IP}:~/r7-trading-bot.tar.gz

# Verificar se chegou
ssh -i $KEY_PATH ubuntu@$EC2_IP "ls -lh r7-trading-bot.tar.gz"
```

---

### **PASSO 3: Setup no Servidor** (3-5 minutos)

**No seu PC (PowerShell/CMD):**

```powershell
$KEY_PATH = "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem"
$EC2_IP = "52.1.2.3"  # <<< SEU IP

# Conectar e executar setup
ssh -i $KEY_PATH ubuntu@$EC2_IP << 'BASH_SCRIPT'

set -e
echo "🚀 Iniciando Setup do R7 Trading Bot API..."

# 1. Atualizar sistema
echo "📦 Atualizando sistema..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip git curl wget

# 2. Preparar diretório
echo "📁 Criando estrutura..."
mkdir -p ~/r7-trading-bot
cd ~/r7-trading-bot

# 3. Extrair código
echo "📂 Extraindo código..."
tar -xzf ~/r7-trading-bot.tar.gz
rm ~/r7-trading-bot.tar.gz

# 4. Criar venv
echo "🔧 Criando ambiente virtual..."
python3.11 -m venv venv
source venv/bin/activate

# 5. Instalar dependências
echo "📚 Instalando Python packages..."
pip install --upgrade pip setuptools wheel
pip install -r requirements_new.txt

# 6. Criar arquivo .env
echo "⚙️  Criando .env..."
cat > .env << 'ENVEOF'
BINANCE_API_KEY=sua_chave_aqui
BINANCE_API_SECRET=seu_secret_aqui
SECRET_KEY=gerado-automaticamente
DEBUG=False
HOST=0.0.0.0
PORT=8080
DATABASE_PATH=data/app_leonardo.db
AWS_REGION=us-east-1
ENVEOF

# 7. Criar diretórios
echo "📂 Criando diretórios de dados..."
mkdir -p data/{audit,metrics,backups,ai,cache,history}
mkdir -p logs
chmod 777 data logs

# 8. Copiar serviços systemd
echo "⚙️  Instalando serviços systemd..."
sudo cp deploy/aws/r7-trading-bot.service /etc/systemd/system/
sudo cp deploy/aws/r7-trading-dashboard.service /etc/systemd/system/

# 9. Recarregar systemd
sudo systemctl daemon-reload
sudo systemctl enable r7-trading-bot.service
sudo systemctl enable r7-trading-dashboard.service

echo ""
echo "✅ Setup concluído com sucesso!"
echo ""
echo "📋 Para iniciar os serviços:"
echo "   sudo systemctl start r7-trading-bot.service"
echo "   sudo systemctl start r7-trading-dashboard.service"
echo ""
echo "📊 Para verificar status:"
echo "   sudo systemctl status r7-trading-bot.service"
echo "   sudo journalctl -u r7-trading-bot.service -f"

BASH_SCRIPT
```

---

### **PASSO 4: Iniciar Serviços** (1 minuto)

**No seu PC (PowerShell/CMD):**

```powershell
$KEY_PATH = "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem"
$EC2_IP = "52.1.2.3"  # <<< SEU IP

# Iniciar API
ssh -i $KEY_PATH ubuntu@$EC2_IP "sudo systemctl start r7-trading-bot.service"
Start-Sleep -Seconds 3

# Iniciar Dashboard
ssh -i $KEY_PATH ubuntu@$EC2_IP "sudo systemctl start r7-trading-dashboard.service"
Start-Sleep -Seconds 3

# Ver status
ssh -i $KEY_PATH ubuntu@$EC2_IP "sudo systemctl status r7-trading-bot.service"

# Ver logs
ssh -i $KEY_PATH ubuntu@$EC2_IP "sudo journalctl -u r7-trading-bot.service -n 20"
```

---

### **PASSO 5: Verificar Deploy** (1 minuto)

**No seu navegador:**

1. **API Health Check:**
   ```
   http://52.1.2.3:8080/api/health
   ```
   Esperado: `{"status":"healthy","version":"1.0"}`

2. **Dashboard (se Streamlit configurado):**
   ```
   http://52.1.2.3:8501
   ```

---

## 🎯 Comandos Úteis (no servidor)

```bash
# Ver status dos serviços
sudo systemctl status r7-trading-bot.service
sudo systemctl status r7-trading-dashboard.service

# Ver logs em tempo real
sudo journalctl -u r7-trading-bot.service -f
sudo journalctl -u r7-trading-dashboard.service -f

# Parar serviços
sudo systemctl stop r7-trading-bot.service
sudo systemctl stop r7-trading-dashboard.service

# Reiniciar serviços
sudo systemctl restart r7-trading-bot.service
sudo systemctl restart r7-trading-dashboard.service

# Ver últimas 50 linhas de log
sudo journalctl -u r7-trading-bot.service -n 50

# Conectar ao servidor
ssh -i "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem" ubuntu@52.1.2.3
```

---

## 🆘 Troubleshooting

### API não responde
```bash
ssh -i "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem" ubuntu@EC2_IP
sudo systemctl restart r7-trading-bot.service
sudo journalctl -u r7-trading-bot.service -e
```

### Erro de permissão
```bash
ssh -i "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem" ubuntu@EC2_IP
chmod 600 ~/.ssh/r7-trading-bot-prod.pem
sudo systemctl daemon-reload
```

### Ver espaço em disco
```bash
df -h
du -sh ~/r7-trading-bot/
```

---

## 💾 Backup e Restauração

### Fazer backup
```bash
cd ~/r7-trading-bot
tar -czf ~/backup-$(date +%Y%m%d-%H%M%S).tar.gz data/
```

### Restaurar backup
```bash
tar -xzf backup-20251208.tar.gz
```

---

## 📧 Resumo Final

✅ **Arquivo pronto:** `r7-trading-bot.tar.gz` (29.3 MB)
✅ **Chave SSH:** `C:\Users\gabri\.ssh\r7-trading-bot-prod.pem`
✅ **Serviços:** Systemd configurados e prontos
✅ **Scripts:** Deploy automático incluído

**Tempo total estimado:** 15 minutos

---

**Próximas versões:**
- v1.1: Renomear banco para `r7-trading-bot.db`
- v2.0: Migrar para PostgreSQL AWS RDS
- v2.5: Implementar CI/CD com GitHub Actions

