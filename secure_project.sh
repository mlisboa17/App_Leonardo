#!/usr/bin/env bash

# ========================================
# 🚨 SCRIPT DE SEGURANÇA - REVOGAÇÃO
# ========================================
# Este script ajuda a revogar credenciais expostas
# e preparar o projeto para novas chaves
# ========================================

set -e

echo "==============================================="
echo "🔐 SECURITY REMEDIATION SCRIPT"
echo "==============================================="
echo ""
echo "Este script vai:"
echo "  1. Remover config/.env do histórico Git"
echo "  2. Adicionar .env ao .gitignore"
echo "  3. Criar template de .env seguro"
echo "  4. Exibir instruções para revogar chaves"
echo ""

# ========================================
# 1. Verificar se .env existe
# ========================================
echo "1️⃣  Verificando arquivo .env..."
if [ -f "config/.env" ]; then
    echo "   ✅ config/.env encontrado"
else
    echo "   ⚠️  config/.env não encontrado"
fi

# ========================================
# 2. Adicionar ao .gitignore
# ========================================
echo ""
echo "2️⃣  Adicionando .env ao .gitignore..."

# Verificar se .gitignore existe
if [ ! -f ".gitignore" ]; then
    echo "# Environment variables" > .gitignore
    echo ".env" >> .gitignore
    echo "config/.env" >> .gitignore
    echo "   ✅ .gitignore criado"
else
    if grep -q "^config/.env$" .gitignore; then
        echo "   ℹ️  config/.env já está no .gitignore"
    else
        echo "" >> .gitignore
        echo "# Environment variables (confidential)" >> .gitignore
        echo ".env" >> .gitignore
        echo "config/.env" >> .gitignore
        echo "   ✅ Adicionado ao .gitignore"
    fi
fi

# ========================================
# 3. Remover .env do histórico Git
# ========================================
echo ""
echo "3️⃣  Removendo .env do histórico Git..."

if git log --all --full-history -- "config/.env" | grep -q "commit"; then
    echo "   ⚠️  Arquivo .env encontrado no histórico!"
    echo "   Para remover completamente do histórico, use:"
    echo "   $ git filter-branch --tree-filter 'rm -f config/.env' HEAD"
    echo "   ou (melhor):"
    echo "   $ bfg --delete-files config/.env"
    echo "   ⚠️  AVISO: Isso reescreve todo o histórico do Git!"
else
    echo "   ✅ .env não está no histórico"
fi

# ========================================
# 4. Criar template .env seguro
# ========================================
echo ""
echo "4️⃣  Criando template seguro .env.template..."

cat > config/.env.template << 'EOF'
# ========================================
# R7 TRADING BOT API - CONFIGURAÇÃO
# ========================================
# NUNCA COMMITAR ESTE ARQUIVO COM DADOS REAIS!
# Copie para config/.env e preencha com suas credenciais

# ========================================
# BINANCE (Production) - NOVAS CHAVES
# ========================================
# Gere em: https://www.binance.com/api-management
# IP Whitelist: RECOMENDADO (seu IP público ou AWS)
BINANCE_API_KEY=SUA_NOVA_API_KEY_AQUI
BINANCE_API_SECRET=SUA_NOVA_API_SECRET_AQUI

# ========================================
# BINANCE TESTNET (Desenvolvimento)
# ========================================
BINANCE_TESTNET_API_KEY=SUA_NOVA_TESTNET_KEY_AQUI
BINANCE_TESTNET_API_SECRET=SUA_NOVA_TESTNET_SECRET_AQUI

# ========================================
# BANCO DE DADOS (se usarPRODUCTION v2.0)
# ========================================
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha_forte
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trading_bot

# ========================================
# AWS (Backups em S3)
# ========================================
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_REGION=us-east-1
AWS_BUCKET=seu-bucket-backup

# ========================================
# APLICAÇÃO
# ========================================
SECRET_KEY=gerado-automaticamente
ENVIRONMENT=production
DEBUG=false
EOF

echo "   ✅ Template criado: config/.env.template"

# ========================================
# 5. Exibir instruções
# ========================================
echo ""
echo "==============================================="
echo "📋 PRÓXIMOS PASSOS - REVOGAÇÃO MANUAL"
echo "==============================================="
echo ""
echo "1️⃣  REVOGAR CHAVES ANTIGAS:"
echo "   https://www.binance.com/en/account/api-management"
echo ""
echo "   Procure por:"
echo "   • API Key: rVFHoreINIsQJtZ7vR9IQc7HGiybp4VLzkXQJtx0bLu9e2F7oIamconSYNmRzbyy"
echo "   • Testnet: QcyrgxtWUGXRkcsfx67EBu5OSTCFcIiFTqcCLfM6aV6zeTV8vxCwkobhY5idiU3m"
echo ""
echo "   Clique em 'Delete' para cada uma"
echo "   Confirme com 2FA/Email"
echo ""
echo "2️⃣  CRIAR NOVAS CHAVES:"
echo "   • Clique em 'Create API Key'"
echo "   • Enable Spot Trading"
echo "   • IP Whitelist (seu IP ou deixe em branco para AWS)"
echo "   • Copiar e guardar em local seguro"
echo ""
echo "3️⃣  ATUALIZAR config/.env:"
echo "   $ cp config/.env.template config/.env"
echo "   $ nano config/.env  # adicionar novas chaves"
echo ""
echo "4️⃣  TESTAR NOVAS CHAVES:"
echo "   $ python test_api_key.py"
echo ""
echo "5️⃣  FAZER COMMIT:"
echo "   $ git add .gitignore"
echo "   $ git commit -m 'Security: Remove exposed credentials and add gitignore'"
echo "   $ git push origin master"
echo ""
echo "==============================================="
echo "✅ SCRIPT CONCLUÍDO"
echo "==============================================="

