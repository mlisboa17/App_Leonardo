#!/bin/bash
# ==============================================
# Script de Deploy/Update - App Leonardo
# ==============================================

set -e

echo "🔄 Atualizando App Leonardo..."

cd ~/app-leonardo

# Ativar venv
source venv/bin/activate

# Parar serviços
echo "⏹️ Parando serviços..."
sudo systemctl stop app-leonardo-bot || true
sudo systemctl stop app-leonardo-dashboard || true

# Backup de dados
echo "💾 Fazendo backup..."
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r data $BACKUP_DIR/ 2>/dev/null || true
cp config/bots_config.yaml $BACKUP_DIR/ 2>/dev/null || true

# Atualizar dependências se necessário
if [ -f requirements_new.txt ]; then
    echo "📚 Atualizando dependências..."
    pip install -r requirements_new.txt --quiet
fi

# Reiniciar serviços
echo "▶️ Iniciando serviços..."
sudo systemctl start app-leonardo-bot
sudo systemctl start app-leonardo-dashboard

# Verificar status
sleep 3
echo ""
echo "📊 Status dos serviços:"
sudo systemctl status app-leonardo-bot --no-pager -l | head -20
echo ""
sudo systemctl status app-leonardo-dashboard --no-pager -l | head -10

echo ""
echo "✅ Deploy concluído!"
