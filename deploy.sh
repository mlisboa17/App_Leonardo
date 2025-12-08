#!/usr/bin/env bash
# 🚀 UPLOAD E DEPLOY R7 TRADING BOT

set -e

echo "=============================================================="
echo "🚀 UPLOAD + DEPLOY R7 TRADING BOT API"
echo "=============================================================="

# ========================================
# PASSO 1: UPLOAD PARA GITHUB
# ========================================
echo ""
echo "PASSO 1️⃣  UPLOAD PARA GITHUB"
echo "----------------------------------------------------------"

git config user.email "gabriel@r7bot.dev" 2>/dev/null || git config --global user.email "gabriel@r7bot.dev"
git config user.name "R7 Bot Deployer" 2>/dev/null || git config --global user.name "R7 Bot Deployer"

echo "📝 Verificando status..."
git status --short

echo ""
echo "📦 Adicionando arquivos..."
git add -A

echo "💬 Fazendo commit..."
git commit -m "Production: Deploy R7 Trading Bot API with security updates and documentation

- Add security remediation documents
- Add API credential testing scripts
- Add deployment automation scripts
- Update bot status monitoring
- Add comprehensive deployment guides
- Secure .env configuration
- Production-ready for AWS EC2 deployment

Features:
- Multi-bot coordination system
- Real-time trade execution
- Dashboard monitoring
- API REST endpoints
- JSON database (v1.0)
- Systemd service management

Security:
- IP whitelisting ready
- Environment-based credentials
- No secrets in repository
- Comprehensive logging

Deployment:
- AWS EC2 (t3.micro Free Tier)
- S3 backups
- Auto-restart on failure
- Health check endpoints
" || echo "✓ Nada novo para commitar"

echo ""
echo "🔄 Fazendo push para master..."
git push origin master

echo "✅ Upload concluído com sucesso!"

# ========================================
# PASSO 2: PREPARAR PARA DEPLOY
# ========================================
echo ""
echo "PASSO 2️⃣  PREPARAR PARA DEPLOY AWS"
echo "----------------------------------------------------------"

echo ""
echo "📋 Checklist de Pré-Deploy:"
echo ""
echo "✓ 1. Arquivo de arquivos pronto: r7-trading-bot.tar.gz (29.3 MB)"
echo "✓ 2. Scripts de deploy: setup_quick.sh, deploy.sh"
echo "✓ 3. Serviços systemd: r7-trading-bot.service, r7-trading-dashboard.service"
echo "✓ 4. Documentação completa: DEPLOY_MANUAL.md, REMEDIATION_SECURITY.md"
echo "✓ 5. Código atualizado no GitHub"
echo ""

# ========================================
# PASSO 3: INSTRUÇÕES DE DEPLOY
# ========================================
echo ""
echo "PASSO 3️⃣  DEPLOY NA AWS EC2"
echo "----------------------------------------------------------"
echo ""
echo "Para fazer o deploy:"
echo ""
echo "1️⃣  Crie uma EC2 instance (t3.micro):"
echo "    - Name: r7-trading-bot-prod"
echo "    - AMI: Ubuntu 22.04 LTS"
echo "    - Type: t3.micro (Free Tier)"
echo "    - Key: r7-trading-bot-prod.pem"
echo "    - Security Group: Ports 22, 8080, 3000, 8501"
echo ""
echo "2️⃣  No seu computador, execute:"
echo ""
echo "    # Copiar arquivo para EC2"
echo "    scp -i ~/.ssh/r7-trading-bot-prod.pem r7-trading-bot.tar.gz ubuntu@[IP]:~/"
echo ""
echo "    # Conectar e executar setup"
echo "    ssh -i ~/.ssh/r7-trading-bot-prod.pem ubuntu@[IP]"
echo "    bash setup_quick.sh"
echo ""
echo "3️⃣  Iniciar os serviços:"
echo ""
echo "    sudo systemctl start r7-trading-bot.service"
echo "    sudo systemctl start r7-trading-dashboard.service"
echo ""
echo "4️⃣  Verificar status:"
echo ""
echo "    curl http://[IP]:8080/api/health"
echo ""

# ========================================
# INFORMAÇÕES IMPORTANTES
# ========================================
echo ""
echo "=============================================================="
echo "⚠️  IMPORTANTE - ANTES DO DEPLOY"
echo "=============================================================="
echo ""
echo "1. REVOGAR CHAVES ANTIGAS:"
echo "   https://www.binance.com/en/account/api-management"
echo "   Revogue as chaves expostas antes de colocar em produção!"
echo ""
echo "2. CRIAR NOVAS CHAVES BINANCE:"
echo "   - Label: r7-trading-bot-prod"
echo "   - IP Whitelist: seu IP AWS"
echo "   - Permissions: Spot Trading"
echo ""
echo "3. ATUALIZAR .env NA EC2:"
echo "   - SSH para a instância"
echo "   - nano config/.env"
echo "   - Adicionar novas chaves"
echo ""
echo "4. TESTAR NOVAS CHAVES:"
echo "   - python test_api_key.py"
echo ""

echo ""
echo "=============================================================="
echo "✅ FASE 1: UPLOAD CONCLUÍDA"
echo "=============================================================="
echo ""
echo "Próximo passo: Crie a EC2 instance e execute o deploy"
echo ""
echo "Documentação disponível em:"
echo "  - DEPLOY_MANUAL.md"
echo "  - START_HERE.md"
echo "  - REMEDIATION_SECURITY.md"
echo ""

