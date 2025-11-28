# 🚀 Como Publicar no GitHub

## Passo 1: Criar Repositório no GitHub

1. Acesse: https://github.com/new
2. Preencha:
   - **Repository name:** `App_Leonardo`
   - **Description:** `Bot de trading automatizado com dashboard Django em tempo real`
   - **Public** ou **Private** (sua escolha)
   - ❌ **NÃO** marque "Initialize with README" (já temos um)
3. Clique em **Create repository**

## Passo 2: Conectar Repositório Local ao GitHub

Copie a URL do seu repositório (vai aparecer algo como):
```
https://github.com/SEU_USUARIO/App_Leonardo.git
```

Execute no terminal:

```bash
git remote add origin https://github.com/SEU_USUARIO/App_Leonardo.git
git branch -M main
git push -u origin main
```

## Passo 3: Configurar Git (se ainda não configurou)

Se for sua primeira vez usando Git, configure seu nome e email:

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@example.com"
```

## ✅ Pronto!

Seu repositório está publicado! Acesse:
```
https://github.com/SEU_USUARIO/App_Leonardo
```

## 📋 Comandos Git Úteis

### Ver status dos arquivos
```bash
git status
```

### Adicionar alterações
```bash
git add .
```

### Fazer commit
```bash
git commit -m "Descrição das alterações"
```

### Enviar para GitHub
```bash
git push
```

### Atualizar do GitHub
```bash
git pull
```

### Ver histórico
```bash
git log --oneline
```

### Criar nova branch
```bash
git checkout -b nome-da-branch
```

## 🔒 Segurança

✅ Arquivos protegidos no `.gitignore`:
- `config/.env` - Suas credenciais API
- `db.sqlite3` - Banco de dados local
- `__pycache__/` - Cache Python
- `venv/` - Ambiente virtual
- `logs/` - Logs do bot

⚠️ **NUNCA** faça commit de:
- API Keys
- Senhas
- Tokens de acesso
- Dados sensíveis

## 📝 Próximos Commits

Sempre que fizer alterações:

```bash
git add .
git commit -m "Descrição clara do que mudou"
git push
```

Exemplos de mensagens:
- `git commit -m "Adiciona estratégia de Bollinger Bands"`
- `git commit -m "Corrige bug no cálculo de RSI"`
- `git commit -m "Melhora performance do dashboard"`
- `git commit -m "Adiciona testes unitários"`

## 🎯 Boas Práticas

1. **Commits frequentes e pequenos** - É melhor vários commits pequenos do que um gigante
2. **Mensagens descritivas** - Explique o QUE mudou e POR QUÊ
3. **Teste antes de commitar** - Certifique-se que o código funciona
4. **Use branches** - Para features grandes, crie branches separadas
5. **Pull antes de Push** - Sempre `git pull` antes de `git push` para evitar conflitos

## 📖 Recursos

- Guia Git: https://git-scm.com/book/pt-br/v2
- GitHub Docs: https://docs.github.com/pt
- Git Cheat Sheet: https://training.github.com/downloads/pt_BR/github-git-cheat-sheet/

---

**Seu código está salvo e versionado! 🎉**
