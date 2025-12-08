#!/bin/bash
# Script de Deploy Automatizado para AWS EC2
# Executar no servidor: bash deploy_auto.sh

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════╗"
echo "║     App Leonardo - Automated AWS Deploy Script      ║"
echo "║     Por favor, confirme que está no servidor EC2   ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para log
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================
# 1. VERIFICAR PRÉ-REQUISITOS
# ============================================
log_info "Verificando pré-requisitos..."

if ! command -v python3.11 &> /dev/null; then
    log_error "Python 3.11 não encontrado. Instalando..."
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3-pip
fi

if ! command -v git &> /dev/null; then
    log_error "Git não encontrado. Instalando..."
    sudo apt install -y git
fi

log_info "✅ Python 3.11: $(python3.11 --version)"
log_info "✅ Git: $(git --version)"

# ============================================
# 2. ESTRUTURA DE DIRETÓRIOS
# ============================================
log_info "Criando estrutura de diretórios..."

mkdir -p ~/app-leonardo/data/{audit,metrics,backups,ai,cache,history}
mkdir -p ~/logs
mkdir -p ~/backup_json

cd ~/app-leonardo
log_info "✅ Diretórios criados"

# ============================================
# 3. VIRTUAL ENVIRONMENT
# ============================================
log_info "Criando virtual environment..."

if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    log_info "✅ VEnv criado"
else
    log_warn "VEnv já existe, pulando..."
fi

source venv/bin/activate
pip install --upgrade pip setuptools wheel
log_info "✅ Pip atualizado"

# ============================================
# 4. INSTALAR DEPENDÊNCIAS
# ============================================
log_info "Instalando dependências Python..."

if [ -f "requirements_new.txt" ]; then
    pip install -r requirements_new.txt
    log_info "✅ Dependências instaladas"
else
    log_warn "requirements_new.txt não encontrado"
fi

# ============================================
# 5. CONFIGURAR VARIÁVEIS DE AMBIENTE
# ============================================
log_info "Configurando .env..."

if [ ! -f ".env" ]; then
    log_warn "Arquivo .env não encontrado"
    echo ""
    echo "ℹ️  Criar arquivo .env manualmente com:"
    echo "    BINANCE_API_KEY=sua_chave"
    echo "    BINANCE_API_SECRET=seu_secret"
    echo "    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
    echo ""
    
    # Criar .env padrão (sem secrets)
    cat > .env << 'EOF'
# 🔐 Binance API (EDITAR COM SUAS CHAVES)
BINANCE_API_KEY=seu_api_key_aqui
BINANCE_API_SECRET=seu_api_secret_aqui

# 🔑 Segurança
SECRET_KEY=gerar_com_comando_abaixo
DEBUG=False

# 📍 Servidor
HOST=0.0.0.0
PORT=8080

# 📊 Banco de Dados
DATABASE_PATH=data/app_leonardo.db

# ☁️ AWS (Opcional, para v2.0)
AWS_REGION=us-east-1
AWS_BUCKET=seu-bucket
AWS_ACCESS_KEY_ID=seu_aws_key
AWS_SECRET_ACCESS_KEY=seu_aws_secret

# Gerar SECRET_KEY com:
# python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
EOF
    
    log_warn "⚠️  EDITAR .env com suas credenciais Binance!"
    log_warn "    nano .env"
else
    log_info "✅ .env já existe"
fi

# ============================================
# 6. CRIAR CONFIGS
# ============================================
log_info "Copiando configurações..."

cp config/bots_config_template.yaml config/bots_config.yaml
cp config/config.yaml config/config.yaml.bak

log_info "✅ Configs criadas"

# ============================================
# 7. CONFIGURAR SYSTEMD SERVICES
# ============================================
log_info "Configurando Systemd services..."

# API Service
sudo tee /etc/systemd/system/app-leonardo-api.service > /dev/null << 'SVCEOF'
[Unit]
Description=App Leonardo Trading Bot - API
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/app-leonardo
Environment="PATH=/home/ubuntu/app-leonardo/venv/bin"
ExecStart=/home/ubuntu/app-leonardo/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/logs/api.log
StandardError=append:/home/ubuntu/logs/api_error.log

[Install]
WantedBy=multi-user.target
SVCEOF

# Bot Service
sudo tee /etc/systemd/system/app-leonardo-bot.service > /dev/null << 'SVCEOF'
[Unit]
Description=App Leonardo Trading Bot - Main Process
After=network.target app-leonardo-api.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/app-leonardo
Environment="PATH=/home/ubuntu/app-leonardo/venv/bin"
ExecStart=/home/ubuntu/app-leonardo/venv/bin/python main_multibot.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/logs/bot.log
StandardError=append:/home/ubuntu/logs/bot_error.log

[Install]
WantedBy=multi-user.target
SVCEOF

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl enable app-leonardo-api.service
sudo systemctl enable app-leonardo-bot.service

log_info "✅ Services configurados"

# ============================================
# 8. VALIDAR CÓDIGO
# ============================================
log_info "Validando código Python..."

python3 -m py_compile backend/main.py
python3 -m py_compile src/coordinator.py

log_info "✅ Código validado"

# ============================================
# 9. INICIAR SERVIÇOS
# ============================================
log_info "Iniciando serviços..."

sudo systemctl start app-leonardo-api.service
sleep 5

log_info "Aguardando API ficar pronta..."
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        log_info "✅ API respondendo"
        break
    fi
    sleep 1
    echo -n "."
done

sudo systemctl start app-leonardo-bot.service

# Aguardar um pouco para que os serviços iniciem
sleep 5

# ============================================
# 10. VERIFICAR STATUS
# ============================================
log_info "Verificando status dos serviços..."

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 STATUS DOS SERVIÇOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sudo systemctl status app-leonardo-api.service --no-pager
echo ""
sudo systemctl status app-leonardo-bot.service --no-pager
echo ""

# ============================================
# 11. CRIAR BACKUP CRON
# ============================================
log_info "Configurando backup automático..."

CRON_CMD="0 2 * * * /home/ubuntu/app-leonardo/backup.sh"
(crontab -l 2>/dev/null | grep -v "app-leonardo"; echo "$CRON_CMD") | crontab -

# Criar script de backup
cat > ~/app-leonardo/backup.sh << 'BACKEOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
tar -czf ~/backup_json/data_${TIMESTAMP}.tar.gz ~/app-leonardo/data/ 2>/dev/null
# Manter apenas últimos 7 dias
find ~/backup_json -name "data_*.tar.gz" -mtime +7 -delete
BACKEOF

chmod +x ~/app-leonardo/backup.sh

log_info "✅ Backup automático configurado (2h da manhã)"

# ============================================
# 12. RESUMO FINAL
# ============================================
echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║          ✅ DEPLOY COMPLETADO COM SUCESSO          ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "📍 Próximas ações:"
echo ""
echo "1. EDITAR .env com suas credenciais Binance:"
echo "   nano .env"
echo ""
echo "2. Parar e reiniciar com novas credenciais:"
echo "   sudo systemctl restart app-leonardo-api.service"
echo "   sudo systemctl restart app-leonardo-bot.service"
echo ""
echo "3. Verificar logs em tempo real:"
echo "   sudo journalctl -u app-leonardo-api.service -f"
echo "   tail -f ~/logs/bot.log"
echo ""
echo "4. Acessar API:"
echo "   http://SEU_IP:8080/docs"
echo "   http://SEU_IP:8080/health"
echo ""
echo "5. Verificar bots:"
echo "   curl http://localhost:8080/api/health"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Diretórios:"
echo "   Data:  ~/app-leonardo/data/"
echo "   Logs:  ~/logs/"
echo "   Backup: ~/backup_json/"
echo ""
echo "🔧 Comandos úteis:"
echo "   Ver status:    sudo systemctl status app-leonardo-api.service"
echo "   Logs:          sudo journalctl -u app-leonardo-api.service -n 50"
echo "   Parar:         sudo systemctl stop app-leonardo-api.service"
echo "   Iniciar:       sudo systemctl start app-leonardo-api.service"
echo "   Reiniciar:     sudo systemctl restart app-leonardo-api.service"
echo ""
echo "📧 Discord: https://discord.gg/..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
