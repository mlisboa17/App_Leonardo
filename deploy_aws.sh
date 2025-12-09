#!/bin/bash

echo "============================================================"
echo "🚀 DEPLOY AWS - APP R7 TRADING BOT"
echo "============================================================"
echo ""

# Configurações
APP_DIR="/home/ubuntu/app_r7"
REPO_URL="https://github.com/mlisboa17/App_Leonardo.git"
BRANCH="master"

echo "📋 Configurações:"
echo "  • Diretório: $APP_DIR"
echo "  • Repositório: $REPO_URL"
echo "  • Branch: $BRANCH"
echo ""

# Atualizar sistema
echo "[1/8] Atualizando sistema..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# Instalar dependências
echo "[2/8] Instalando dependências do sistema..."
sudo apt-get install -y python3-pip python3-venv git htop supervisor nginx -qq

# Clonar ou atualizar repositório
if [ -d "$APP_DIR" ]; then
    echo "[3/8] Atualizando repositório existente..."
    cd $APP_DIR
    git fetch origin
    git reset --hard origin/$BRANCH
    git pull origin $BRANCH
else
    echo "[3/8] Clonando repositório..."
    git clone -b $BRANCH $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# Criar ambiente virtual
echo "[4/8] Configurando ambiente virtual..."
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências Python
echo "[5/8] Instalando pacotes Python..."
pip install --upgrade pip -q
pip install -r requirements_new.txt -q
pip install python-binance watchdog streamlit -q

# Configurar credenciais
echo "[6/8] Configurando credenciais..."
if [ ! -f "config/.env" ]; then
    echo "⚠️ Criando arquivo .env - EDITE COM SUAS CREDENCIAIS!"
    cat > config/.env << 'EOF'
# Binance API
BINANCE_API_KEY=R4So8k98GeMLDhNoMmAedjXjYnUBpxCVZKH9bNbMrM6lfbJzFlY9m3okEbXRuJqR
BINANCE_API_SECRET=n00KKGAVD7QXbOd3fkCRLXKWFK3PuVS8WUk6wtfpRT0UJG9qRYsay9Qt6LoUKwCN

# PostgreSQL
POSTGRES_USER=leonardo
POSTGRES_PASSWORD=trading123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trading_bot
EOF
fi

# Configurar Supervisor (gerenciamento de processos)
echo "[7/8] Configurando Supervisor..."
sudo tee /etc/supervisor/conf.d/app_r7.conf > /dev/null << EOF
[program:r7_auto_update]
command=$APP_DIR/.venv/bin/python $APP_DIR/auto_update_balances.py
directory=$APP_DIR
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/r7_auto_update.err.log
stdout_logfile=/var/log/r7_auto_update.out.log

[program:r7_dashboard]
command=$APP_DIR/.venv/bin/streamlit run $APP_DIR/frontend/dashboard_multibot_v2.py --server.port 8503 --server.address 0.0.0.0
directory=$APP_DIR
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/r7_dashboard.err.log
stdout_logfile=/var/log/r7_dashboard.out.log
EOF

# Configurar Nginx (proxy reverso)
echo "[8/8] Configurando Nginx..."
sudo tee /etc/nginx/sites-available/r7_trading > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8503;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/r7_trading /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Reiniciar serviços
echo ""
echo "🔄 Reiniciando serviços..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

echo ""
echo "============================================================"
echo "✅ DEPLOY COMPLETO!"
echo "============================================================"
echo ""
echo "📊 Status dos serviços:"
sudo supervisorctl status

echo ""
echo "🌐 Acessos:"
echo "  • Dashboard: http://$(curl -s ifconfig.me):80"
echo "  • Dashboard direto: http://$(curl -s ifconfig.me):8503"
echo ""
echo "📋 Comandos úteis:"
echo "  • Ver logs dashboard: sudo tail -f /var/log/r7_dashboard.out.log"
echo "  • Ver logs auto-update: sudo tail -f /var/log/r7_auto_update.out.log"
echo "  • Status: sudo supervisorctl status"
echo "  • Reiniciar: sudo supervisorctl restart all"
echo ""
echo "============================================================"
