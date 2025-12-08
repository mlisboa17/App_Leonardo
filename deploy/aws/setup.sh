#!/bin/bash
# ==============================================
# Script de Setup para AWS EC2 - R7 Trading Bot API
# ==============================================

set -e

echo "🚀 Iniciando setup do R7 Trading Bot API na AWS..."

# Atualizar sistema
echo "📦 Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependências
echo "🐍 Instalando Python e dependências..."
sudo apt install -y python3.11 python3.11-venv python3-pip git htop

# Criar diretório
echo "📁 Criando diretório..."
mkdir -p ~/r7-trading-bot
cd ~/r7-trading-bot

# Criar ambiente virtual
echo "🔧 Criando ambiente virtual..."
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências Python
echo "📚 Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements_new.txt

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "⚠️ Criando arquivo .env (CONFIGURE SUAS CHAVES!)..."
    cat > .env << EOF
BINANCE_API_KEY=sua_api_key_aqui
BINANCE_API_SECRET=seu_secret_aqui
EOF
    echo "⚠️ IMPORTANTE: Edite o arquivo .env com suas chaves da Binance!"
fi

# Instalar serviços systemd
echo "⚙️ Configurando serviços systemd..."
sudo cp deploy/aws/r7-trading-bot.service /etc/systemd/system/
sudo cp deploy/aws/r7-trading-dashboard.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviços
sudo systemctl enable r7-trading-bot
sudo systemctl enable r7-trading-dashboard

echo ""
echo "✅ Setup concluído!"
echo ""
echo "📋 Próximos passos:"
echo "   1. Edite o arquivo .env com suas chaves da Binance:"
echo "      nano .env"
echo ""
echo "   2. Inicie os serviços:"
echo "      sudo systemctl start r7-trading-bot"
echo "      sudo systemctl start r7-trading-dashboard"
echo ""
echo "   3. Verifique o status:"
echo "      sudo systemctl status r7-trading-bot"
echo ""
echo "   4. Acesse o dashboard:"
echo "      http://SEU_IP:8501"
echo ""
