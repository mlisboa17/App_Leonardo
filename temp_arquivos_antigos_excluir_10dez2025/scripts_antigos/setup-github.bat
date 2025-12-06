@echo off
REM Script para configurar o repositório GitHub do App Leonardo no Windows

echo 🚀 Configurando repositório GitHub para App Leonardo Trading Bot

REM Verificar se git está instalado
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git não está instalado. Por favor, instale o Git primeiro.
    echo 🔗 Download: https://git-scm.com/download/windows
    pause
    exit /b 1
)

REM Verificar se gh CLI está instalado
gh --version >nul 2>&1
if %errorlevel% equ 0 (
    set GH_CLI_AVAILABLE=true
    echo ✅ GitHub CLI disponível
) else (
    set GH_CLI_AVAILABLE=false
    echo ⚠️  GitHub CLI não encontrado. Instale para automação completa.
    echo 🔗 Download: https://cli.github.com/
)

REM Configurar git se ainda não configurado
git config user.name >nul 2>&1
if %errorlevel% neq 0 (
    echo 📝 Configurando git...
    set /p GIT_NAME="Digite seu nome: "
    set /p GIT_EMAIL="Digite seu email: "
    git config --global user.name "%GIT_NAME%"
    git config --global user.email "%GIT_EMAIL%"
)

REM Inicializar repositório Git se não existir
if not exist ".git" (
    echo 📁 Inicializando repositório Git...
    git init
    git branch -M main
)

REM Adicionar arquivos ao Git
echo 📦 Adicionando arquivos...
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

REM Criar repositório no GitHub se GitHub CLI estiver disponível
if "%GH_CLI_AVAILABLE%"=="true" (
    set /p CREATE_REPO="Deseja criar o repositório no GitHub automaticamente? (y/n): "
    if /i "!CREATE_REPO!"=="y" (
        set /p REPO_NAME="Nome do repositório (padrão: app-leonardo-trading-bot): "
        if "!REPO_NAME!"=="" set REPO_NAME=app-leonardo-trading-bot
        
        set /p REPO_VISIBILITY="Repositório público ou privado? (pub/priv): "
        if /i "!REPO_VISIBILITY!"=="priv" (
            set VISIBILITY_FLAG=--private
        ) else (
            set VISIBILITY_FLAG=--public
        )
        
        echo 🌐 Criando repositório no GitHub...
        gh repo create "!REPO_NAME!" !VISIBILITY_FLAG! --description "🤖 Bot automatizado de trading de criptomoedas com estratégia adaptativa, dashboard em tempo real e sistema completo de análise técnica." --clone=false
        
        REM Adicionar remote
        gh repo set-default
        for /f "tokens=*" %%i in ('gh api user --jq .login') do set USERNAME=%%i
        git remote add origin "https://github.com/!USERNAME!/!REPO_NAME!.git"
        
        echo 📤 Enviando código para GitHub...
        git push -u origin main
        
        echo ✅ Repositório criado com sucesso!
        echo 🔗 URL: https://github.com/!USERNAME!/!REPO_NAME!
        
        REM Criar issues iniciais
        echo 📋 Criando issues iniciais...
        
        gh issue create --title "📚 Melhorar documentação de instalação" --body "Expandir o guia de instalação com mais detalhes sobre: Configuração do ambiente virtual, Troubleshooting comum, Exemplos de configuração, Video tutorial" --label documentation,good-first-issue
        
        gh issue create --title "🧪 Adicionar mais testes unitários" --body "Aumentar cobertura de testes para: Estratégias de trading, Indicadores técnicos, Sistema de segurança, Gestão de risco. Meta: 80%+ de cobertura" --label testing,enhancement
        
        gh issue create --title "🔔 Sistema de notificações Telegram" --body "Implementar notificações via Telegram para: Trades executados, Alertas de risco, Relatórios diários, Status do bot" --label enhancement,feature
    )
) else (
    echo 📋 Passos para criar o repositório manualmente:
    echo 1. Acesse https://github.com/new
    echo 2. Nome sugerido: app-leonardo-trading-bot
    echo 3. Descrição: 🤖 Bot automatizado de trading de criptomoedas com estratégia adaptativa
    echo 4. Escolha público ou privado
    echo 5. Não inicialize com README (já temos)
    echo 6. Execute os comandos:
    echo.
    echo    git remote add origin https://github.com/SEU_USUARIO/app-leonardo-trading-bot.git
    echo    git push -u origin main
)

echo.
echo 🎉 Configuração do GitHub concluída!
echo.
echo 📚 Próximos passos:
echo 1. Revisar e atualizar o README.md com suas informações
echo 2. Configurar secrets no GitHub (se usar CI/CD):
echo    - DOCKERHUB_USERNAME
echo    - DOCKERHUB_TOKEN  
echo    - CODECOV_TOKEN
echo 3. Revisar issues criadas
echo 4. Convidar colaboradores (se necessário)
echo 5. Configurar GitHub Pages (opcional)
echo.
echo 🔗 Links úteis:
echo - GitHub CLI: https://cli.github.com/
echo - Git for Windows: https://git-scm.com/download/windows
echo - GitHub Docs: https://docs.github.com/

pause