# 📘 Manual Completo do GitHub - App Leonardo

Este guia contém todas as instruções para configurar e gerenciar o repositório GitHub do App Leonardo Trading Bot.

## 🎯 Passo a Passo Completo

### 1️⃣ Preparação Inicial

#### Instalar Ferramentas Necessárias
```bash
# Git (obrigatório)
# Windows: https://git-scm.com/download/windows
# Ubuntu: sudo apt install git
# macOS: brew install git

# GitHub CLI (recomendado)
# Windows: winget install GitHub.cli
# Ubuntu: sudo snap install gh
# macOS: brew install gh

# Verificar instalação
git --version
gh --version
```

#### Configurar Git
```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@exemplo.com"
git config --global init.defaultBranch main
```

### 2️⃣ Configuração Automática (Recomendado)

#### Windows
```cmd
# Execute o script automático
setup-github.bat
```

#### Linux/Mac
```bash
# Dar permissão e executar
chmod +x setup-github.sh
./setup-github.sh
```

### 3️⃣ Configuração Manual

#### Passo 1: Inicializar Repositório Local
```bash
# Se ainda não foi inicializado
git init
git branch -M main

# Adicionar arquivos
git add .
git commit -m "feat: initial commit - App Leonardo Trading Bot"
```

#### Passo 2: Criar Repositório no GitHub
1. Acesse [github.com/new](https://github.com/new)
2. **Repository name**: `app-leonardo-trading-bot`
3. **Description**: `🤖 Bot automatizado de trading de criptomoedas com estratégia adaptativa`
4. **Visibility**: Público ou Privado (sua escolha)
5. **NÃO** marque "Add a README file" (já temos)
6. **NÃO** marque "Add .gitignore" (já temos)
7. **Escolha licença**: MIT (recomendado)
8. Clique "Create repository"

#### Passo 3: Conectar Local com GitHub
```bash
# Adicionar remote (substitua SEU_USUARIO)
git remote add origin https://github.com/SEU_USUARIO/app-leonardo-trading-bot.git

# Push inicial
git push -u origin main
```

### 4️⃣ Configurações Avançadas do Repositório

#### Configurar Branch Protection
1. Vá em **Settings** → **Branches**
2. Clique "Add rule" para `main`
3. Configure:
   - ☑️ Require a pull request before merging
   - ☑️ Require approvals (1 mínimo)
   - ☑️ Dismiss stale PR approvals when new commits are pushed
   - ☑️ Require status checks to pass before merging
   - ☑️ Require branches to be up to date before merging
   - ☑️ Include administrators

#### Configurar GitHub Pages (Opcional)
1. Vá em **Settings** → **Pages**
2. **Source**: Deploy from a branch
3. **Branch**: `main` / `docs` (se tiver documentação)
4. **Folder**: `/ (root)` ou `/docs`

#### Configurar Issues Templates
Os templates já estão criados em `.github/ISSUE_TEMPLATE/`:
- `bug_report.yml` - Para reportar bugs
- `feature_request.yml` - Para solicitar features

#### Configurar Labels
```bash
# Usando GitHub CLI
gh label create "bug" --description "Algo não está funcionando" --color "d73a4a"
gh label create "enhancement" --description "Nova funcionalidade ou melhoria" --color "a2eeef"
gh label create "documentation" --description "Melhorias na documentação" --color "0075ca"
gh label create "good first issue" --description "Bom para iniciantes" --color "7057ff"
gh label create "help wanted" --description "Procuramos ajuda da comunidade" --color "008672"
gh label create "security" --description "Questão de segurança" --color "b60205"
gh label create "performance" --description "Melhoria de performance" --color "fbca04"
gh label create "testing" --description "Relacionado a testes" --color "1d76db"
```

### 5️⃣ Secrets e Variáveis (Para CI/CD)

#### GitHub Secrets
Vá em **Settings** → **Secrets and variables** → **Actions**

**Secrets obrigatórios para CI/CD:**
- `DOCKERHUB_USERNAME` - Usuário Docker Hub
- `DOCKERHUB_TOKEN` - Token Docker Hub
- `CODECOV_TOKEN` - Token Codecov (opcional)

**Como adicionar:**
1. Clique "New repository secret"
2. Digite o nome do secret
3. Cole o valor
4. Clique "Add secret"

### 6️⃣ Configurar CI/CD

O workflow já está em `.github/workflows/ci.yml` e inclui:
- ✅ Testes automatizados
- ✅ Verificação de código (linting)
- ✅ Verificação de segurança
- ✅ Build Docker
- ✅ Deploy automático

**Para ativar:**
1. Os workflows são ativados automaticamente no push
2. Configure os secrets necessários
3. Faça um push para testar

### 7️⃣ Colaboração

#### Convidar Colaboradores
1. **Settings** → **Manage access**
2. Clique "Invite a collaborator"
3. Digite username/email
4. Escolha permissão:
   - **Read**: Apenas visualizar
   - **Triage**: Gerenciar issues/PRs
   - **Write**: Push direto (não recomendado)
   - **Maintain**: Configurar repositório
   - **Admin**: Controle total

#### Workflow de Contribuição
```bash
# 1. Fork do repositório (via interface web)

# 2. Clone do fork
git clone https://github.com/SEU_USUARIO/app-leonardo-trading-bot.git

# 3. Criar branch para feature
git checkout -b feature/nova-funcionalidade

# 4. Fazer mudanças e commit
git add .
git commit -m "feat: add nova funcionalidade"

# 5. Push da branch
git push origin feature/nova-funcionalidade

# 6. Criar Pull Request via interface web
```

### 8️⃣ Releases e Versionamento

#### Criar Release Manual
1. **Code** → **Releases** → **Create a new release**
2. **Tag version**: `v2.1.0` (seguir semântico)
3. **Release title**: `Release v2.1.0 - Nova estratégia adaptativa`
4. **Description**: Descrever mudanças
5. **Attach binaries**: Executáveis (opcional)

#### Release Automático
O workflow CI/CD cria releases automaticamente quando:
- Push na `main` contém "release:" no commit
- Tag é criada seguindo padrão `v*.*.*`

### 9️⃣ Documentação

#### README.md
- ✅ Já criado com badges, instalação e uso
- 🔄 Personalize com suas informações
- 📸 Adicione screenshots reais
- 🔗 Atualize links com seu usuário

#### Wiki (Opcional)
1. **Wiki** tab → **Create the first page**
2. Páginas sugeridas:
   - Installation Guide
   - Configuration Reference
   - API Documentation
   - Troubleshooting
   - FAQ

#### GitHub Pages
Para documentação mais avançada:
1. Criar pasta `docs/`
2. Usar Jekyll, MkDocs ou Sphinx
3. Configurar em Settings → Pages

### 🔟 Monitoramento e Analytics

#### GitHub Insights
- **Traffic**: Visualizações e clones
- **Commits**: Atividade de desenvolvimento
- **Dependency graph**: Dependências vulneráveis
- **Security**: Alertas de segurança

#### Badges para README
```markdown
![GitHub stars](https://img.shields.io/github/stars/SEU_USUARIO/app-leonardo-trading-bot)
![GitHub forks](https://img.shields.io/github/forks/SEU_USUARIO/app-leonardo-trading-bot)
![GitHub issues](https://img.shields.io/github/issues/SEU_USUARIO/app-leonardo-trading-bot)
![GitHub license](https://img.shields.io/github/license/SEU_USUARIO/app-leonardo-trading-bot)
![Build Status](https://img.shields.io/github/workflow/status/SEU_USUARIO/app-leonardo-trading-bot/CI)
```

### 🛡️ Segurança

#### Dependabot (Automático)
- Atualiza dependências automaticamente
- Cria PRs para vulnerabilidades
- Configurável em `.github/dependabot.yml`

#### Code Scanning
1. **Security** → **Code scanning alerts**
2. **Set up code scanning**
3. Escolher **CodeQL Analysis**

#### Secret Scanning
- Detecta secrets commitados acidentalmente
- Ativado automaticamente em repositórios públicos
- Configurável para repositórios privados

### 📊 Métricas e KPIs

#### Issues e PRs
- Tempo médio de resposta
- Taxa de fechamento
- Qualidade dos reports

#### Código
- Cobertura de testes
- Complexidade ciclomática
- Duplicação de código
- Vulnerabilidades

#### Comunidade
- Contributors ativos
- Stars e forks
- Discussões e feedback

### 🚀 Promoção do Projeto

#### Marketing
- 🐦 Twitter/X com hashtags #CryptoBot #TradingBot
- 📱 LinkedIn para comunidade profissional
- 🎥 YouTube com demos e tutoriais
- 📝 Medium/Dev.to com artigos técnicos

#### Comunidades
- Reddit: r/algotrading, r/cryptocurrency
- Discord: Servidores de trading
- Telegram: Grupos de crypto
- Stack Overflow: Responder questões relacionadas

### 🆘 Troubleshooting

#### Problemas Comuns

**Push rejeitado:**
```bash
git pull origin main --rebase
git push origin main
```

**Conflitos de merge:**
```bash
git status  # Ver arquivos em conflito
# Editar arquivos manualmente
git add .
git commit -m "resolve merge conflicts"
```

**Reverter commit:**
```bash
git revert <commit-hash>
git push origin main
```

**Limpar cache git:**
```bash
git rm -r --cached .
git add .
git commit -m "fix: update gitignore"
```

### 📞 Suporte

- 📧 Email: leonardo.trading@email.com
- 💬 Discord: [Link do servidor]
- 🐛 Issues: Use os templates do GitHub
- 📚 Wiki: Documentação detalhada

---

## ✅ Checklist Final

Após configurar tudo:

- [ ] ✅ Repositório criado no GitHub
- [ ] ✅ Código pushed para main
- [ ] ✅ README.md personalizado
- [ ] ✅ .gitignore configurado
- [ ] ✅ Secrets configurados (se usar CI/CD)
- [ ] ✅ Branch protection habilitada
- [ ] ✅ Issues templates ativos
- [ ] ✅ Labels criadas
- [ ] ✅ Colaboradores convidados (se necessário)
- [ ] ✅ Release inicial criada
- [ ] ✅ License adicionada
- [ ] ✅ Descrição e tópicos configurados
- [ ] ✅ GitHub Pages configurado (opcional)
- [ ] ✅ Wiki criada (opcional)

**🎉 Parabéns! Seu repositório GitHub está profissionalmente configurado!**