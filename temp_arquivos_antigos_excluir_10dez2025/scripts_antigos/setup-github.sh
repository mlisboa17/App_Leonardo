#!/bin/bash
# Script para configurar o repositório GitHub do App Leonardo

echo "🚀 Configurando repositório GitHub para App Leonardo Trading Bot"

# Verificar se git está instalado
if ! command -v git &> /dev/null; then
    echo "❌ Git não está instalado. Por favor, instale o Git primeiro."
    exit 1
fi

# Verificar se gh CLI está instalado (opcional)
if command -v gh &> /dev/null; then
    GH_CLI_AVAILABLE=true
    echo "✅ GitHub CLI disponível"
else
    GH_CLI_AVAILABLE=false
    echo "⚠️  GitHub CLI não encontrado. Você precisará criar o repositório manualmente."
fi

# Configurar git se ainda não configurado
if ! git config user.name &> /dev/null; then
    echo "📝 Configurando git..."
    read -p "Digite seu nome: " GIT_NAME
    read -p "Digite seu email: " GIT_EMAIL
    git config --global user.name "$GIT_NAME"
    git config --global user.email "$GIT_EMAIL"
fi

# Inicializar repositório Git se não existir
if [ ! -d ".git" ]; then
    echo "📁 Inicializando repositório Git..."
    git init
    git branch -M main
fi

# Adicionar arquivos ao Git
echo "📦 Adicionando arquivos..."
git add .
git commit -m "feat: initial commit - App Leonardo Trading Bot

- Complete trading bot with adaptive strategy
- Real-time dashboard with Dash/Plotly
- Risk management system
- SQLite persistence
- Comprehensive documentation
- Docker support
- CI/CD pipeline
- Security features"

# Criar repositório no GitHub se GitHub CLI estiver disponível
if [ "$GH_CLI_AVAILABLE" = true ]; then
    read -p "Deseja criar o repositório no GitHub automaticamente? (y/n): " CREATE_REPO
    if [ "$CREATE_REPO" = "y" ] || [ "$CREATE_REPO" = "Y" ]; then
        read -p "Nome do repositório (default: app-leonardo-trading-bot): " REPO_NAME
        REPO_NAME=${REPO_NAME:-app-leonardo-trading-bot}
        
        read -p "Repositório público ou privado? (pub/priv): " REPO_VISIBILITY
        if [ "$REPO_VISIBILITY" = "priv" ]; then
            VISIBILITY_FLAG="--private"
        else
            VISIBILITY_FLAG="--public"
        fi
        
        echo "🌐 Criando repositório no GitHub..."
        gh repo create "$REPO_NAME" $VISIBILITY_FLAG --description "🤖 Bot automatizado de trading de criptomoedas com estratégia adaptativa, dashboard em tempo real e sistema completo de análise técnica." --clone=false
        
        # Adicionar remote
        gh repo set-default
        git remote add origin "https://github.com/$(gh api user --jq .login)/$REPO_NAME.git"
        
        echo "📤 Enviando código para GitHub..."
        git push -u origin main
        
        echo "✅ Repositório criado com sucesso!"
        echo "🔗 URL: https://github.com/$(gh api user --jq .login)/$REPO_NAME"
    fi
else
    echo "📋 Passos para criar o repositório manualmente:"
    echo "1. Acesse https://github.com/new"
    echo "2. Nome sugerido: app-leonardo-trading-bot"
    echo "3. Descrição: 🤖 Bot automatizado de trading de criptomoedas com estratégia adaptativa"
    echo "4. Escolha público ou privado"
    echo "5. Não inicialize com README (já temos)"
    echo "6. Execute os comandos:"
    echo ""
    echo "   git remote add origin https://github.com/SEU_USUARIO/app-leonardo-trading-bot.git"
    echo "   git push -u origin main"
fi

# Configurar branch protection (se GitHub CLI disponível)
if [ "$GH_CLI_AVAILABLE" = true ] && [ "$CREATE_REPO" = "y" ] || [ "$CREATE_REPO" = "Y" ]; then
    echo "🛡️  Configurando proteções da branch main..."
    gh api repos/:owner/:repo/branches/main/protection \
        --method PUT \
        --field required_status_checks='{"strict":true,"contexts":["test"]}' \
        --field enforce_admins=true \
        --field required_pull_request_reviews='{"required_approving_review_count":1}' \
        --field restrictions=null 2>/dev/null || echo "⚠️  Não foi possível configurar proteções (conta pode ser gratuita)"
fi

# Criar issues iniciais
if [ "$GH_CLI_AVAILABLE" = true ] && [ "$CREATE_REPO" = "y" ] || [ "$CREATE_REPO" = "Y" ]; then
    echo "📋 Criando issues iniciais..."
    
    gh issue create --title "📚 Melhorar documentação de instalação" \
                   --body "Expandir o guia de instalação com mais detalhes sobre:
- Configuração do ambiente virtual
- Troubleshooting comum
- Exemplos de configuração
- Video tutorial" \
                   --label documentation,good-first-issue
    
    gh issue create --title "🧪 Adicionar mais testes unitários" \
                   --body "Aumentar cobertura de testes para:
- Estratégias de trading
- Indicadores técnicos
- Sistema de segurança
- Gestão de risco

Meta: 80%+ de cobertura" \
                   --label testing,enhancement
    
    gh issue create --title "🔔 Sistema de notificações Telegram" \
                   --body "Implementar notificações via Telegram para:
- Trades executados
- Alertas de risco
- Relatórios diários
- Status do bot" \
                   --label enhancement,feature
fi

echo ""
echo "🎉 Configuração do GitHub concluída!"
echo ""
echo "📚 Próximos passos:"
echo "1. Revisar e atualizar o README.md com suas informações"
echo "2. Configurar secrets no GitHub (se usar CI/CD):"
echo "   - DOCKERHUB_USERNAME"
echo "   - DOCKERHUB_TOKEN"
echo "   - CODECOV_TOKEN"
echo "3. Revisar issues criadas"
echo "4. Convidar colaboradores (se necessário)"
echo "5. Configurar GitHub Pages (opcional)"
echo ""
echo "🔗 Links úteis:"
echo "- Configurar secrets: https://github.com/SEU_USUARIO/REPO_NAME/settings/secrets"
echo "- Configurar Pages: https://github.com/SEU_USUARIO/REPO_NAME/settings/pages"
echo "- Manage access: https://github.com/SEU_USUARIO/REPO_NAME/settings/access"