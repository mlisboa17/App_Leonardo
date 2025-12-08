#!/bin/bash
# 🚀 R7 Trading Bot - Deploy Rápido
# Execute este script no servidor Ubuntu após upload do arquivo tar.gz

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🚀 R7 Trading Bot API - Deploy Rápido                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar arquivo
if [ ! -f "r7-trading-bot.tar.gz" ]; then
    echo -e "${RED}❌ Arquivo r7-trading-bot.tar.gz não encontrado!${NC}"
    echo "   Baixe o arquivo: scp -i chave.pem arquivo.tar.gz ubuntu@IP:~/"
    exit 1
fi

echo -e "${GREEN}✅ Arquivo encontrado${NC}"

# 1. Atualizar sistema
echo -e "${BLUE}[1/8]${NC} Atualizando sistema..."
sudo apt update && sudo apt upgrade -y > /dev/null 2>&1

# 2. Instalar dependências
echo -e "${BLUE}[2/8]${NC} Instalando Python e dependências..."
sudo apt install -y python3.11 python3.11-venv python3-pip git curl wget > /dev/null 2>&1

# 3. Criar estrutura
echo -e "${BLUE}[3/8]${NC} Criando diretório de aplicação..."
mkdir -p ~/r7-trading-bot
cd ~/r7-trading-bot

# 4. Extrair código
echo -e "${BLUE}[4/8]${NC} Extraindo código da aplicação..."
tar -xzf ~/r7-trading-bot.tar.gz
rm ~/r7-trading-bot.tar.gz

# 5. Criar venv
echo -e "${BLUE}[5/8]${NC} Criando ambiente virtual Python..."
python3.11 -m venv venv > /dev/null 2>&1
source venv/bin/activate

# 6. Instalar dependências Python
echo -e "${BLUE}[6/8]${NC} Instalando pacotes Python..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements_new.txt > /dev/null 2>&1

# 7. Preparar configuração
echo -e "${BLUE}[7/8]${NC} Preparando configuração..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
BINANCE_API_KEY=sua_chave_api
BINANCE_API_SECRET=seu_secret
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
DEBUG=False
HOST=0.0.0.0
PORT=8080
DATABASE_PATH=data/app_leonardo.db
AWS_REGION=us-east-1
EOF
fi

mkdir -p data/{audit,metrics,backups,ai,cache,history}
mkdir -p logs
chmod 777 data logs

# 8. Instalar serviços
echo -e "${BLUE}[8/8]${NC} Configurando serviços systemd..."
sudo cp deploy/aws/r7-trading-bot.service /etc/systemd/system/ 2>/dev/null || true
sudo cp deploy/aws/r7-trading-dashboard.service /etc/systemd/system/ 2>/dev/null || true
sudo systemctl daemon-reload

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ SETUP CONCLUÍDO COM SUCESSO!                            ║"
echo "╚════════════════════════════════════════════════════════════╝${NC}"

echo ""
echo -e "${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo ""
echo "1️⃣  Editar configuração (opcional):"
echo "   nano .env"
echo ""
echo "2️⃣  Iniciar serviços:"
echo "   sudo systemctl start r7-trading-bot.service"
echo "   sudo systemctl start r7-trading-dashboard.service"
echo ""
echo "3️⃣  Verificar status:"
echo "   sudo systemctl status r7-trading-bot.service"
echo "   sudo journalctl -u r7-trading-bot.service -f"
echo ""
echo "4️⃣  Acessar aplicação:"
echo "   API:       http://localhost:8080/api/health"
echo "   Dashboard: http://localhost:8501"
echo ""
echo -e "${GREEN}✨ Sistema pronto para produção!${NC}"
