# ✅ PRÉ-DEPLOY CHECKLIST

**Versão**: v1.0  
**Data**: 07/12/2025  
**Tipo**: Deploy em AWS EC2

---

## 🎯 ANTES DE INICIAR O DEPLOY

### ✔️ Verificações Obrigatórias

- [ ] Conta AWS criada e ativa
- [ ] Cartão de crédito vinculado (Free Tier precisa)
- [ ] Você tem as chaves da Binance:
  - [ ] API Key
  - [ ] API Secret
  - [ ] IP whitelist configurado na Binance
- [ ] Computador com:
  - [ ] Git instalado
  - [ ] Python 3.11+
  - [ ] PowerShell (Windows) ou Terminal (Mac/Linux)
  - [ ] ~200MB de espaço livre

### ✔️ Código Local

- [ ] Executar testes locais:
  ```powershell
  cd "c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"
  pytest src/tests/test_e2e_restart_audit.py -v
  # Deve passar todos os testes
  ```

- [ ] Limpar arquivos temporários:
  ```powershell
  Remove-Item -Path "__pycache__" -Recurse -Force
  Get-ChildItem -Path . -Include "*.pyc" -Recurse | Remove-Item -Force
  ```

- [ ] Verificar se tem arquivo .env (não deve ter no git):
  ```powershell
  # Não deve existir (ou deve estar em .gitignore)
  Test-Path .\.env
  ```

### ✔️ Documentação

- [ ] Ler: `DEPLOY_RESUMO_EXECUTIVO.md`
- [ ] Ler: `AWS_DEPLOY_CHECKLIST.md` (Fase 1 e 2)
- [ ] Ler: `DATABASE_STRATEGY.md` (entender JSON vs PostgreSQL)

---

## 🔧 CONFIGURAÇÃO PRÉ-DEPLOY

### Passo 1: Gerar SECRET_KEY

Será necessário para o .env do servidor:

```powershell
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copiar o output (ex: "SomeRandomString...")
```

### Passo 2: Preparar Credenciais

Ter em mãos:

```
BINANCE_API_KEY=seu_valor_aqui
BINANCE_API_SECRET=seu_valor_aqui
SECRET_KEY=copiar_do_passo_1
```

⚠️ **Importante**: Não commitar essas credenciais no Git!

### Passo 3: Preparar Chave SSH

Salvar no PC o arquivo `.pem`:

```powershell
# Caminho esperado
C:\Users\gabri\.ssh\app-leonardo-prod.pem

# Se não existir, criar pasta
mkdir C:\Users\gabri\.ssh

# Colocar o arquivo lá
# Depois ajustar permissões (como admin):
icacls "C:\Users\gabri\.ssh\app-leonardo-prod.pem" /grant:r "%username%:F" /inheritance:r
```

### Passo 4: Testar Conectividade SSH

```powershell
$IP = "XXX.XXX.XXX.XXX"  # Seu IP público AWS
$KEY = "C:\Users\gabri\.ssh\app-leonardo-prod.pem"

# Testar conexão (SEM arquivo .pem é erro esperado)
ssh -i $KEY ubuntu@$IP "echo 'SSH OK'"

# Esperado:
# SSH OK
```

---

## 📦 PREPARAR PACOTE PARA UPLOAD

### Passo 1: Navegar para o diretório do projeto

```powershell
cd "c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"
```

### Passo 2: Validar estrutura

```powershell
# Verificar arquivos críticos existem
Test-Path .\backend\main.py         # Deve ser TRUE
Test-Path .\src\coordinator.py      # Deve ser TRUE
Test-Path .\requirements_new.txt    # Deve ser TRUE
Test-Path .\config\bots_config_template.yaml  # Deve ser TRUE
```

### Passo 3: Compactar código

```powershell
# ⚠️ Excluir venv, cache, git, .env
tar --exclude='venv_new' `
    --exclude='__pycache__' `
    --exclude='.git' `
    --exclude='.env' `
    --exclude='*.pyc' `
    --exclude='node_modules' `
    --exclude='.pytest_cache' `
    -czf app-leonardo.tar.gz .

# Verificar tamanho
(Get-Item app-leonardo.tar.gz).Length / 1MB  # Deve ser ~40-60MB
```

### Passo 4: Preparar para upload

```powershell
# Copiar para local acessível
Copy-Item app-leonardo.tar.gz $env:USERPROFILE\Desktop\

# Verificar
Test-Path $env:USERPROFILE\Desktop\app-leonardo.tar.gz
```

---

## 🌐 AWS SETUP

### Passo 1: Criar Instância EC2

**No AWS Console:**

1. Ir para: https://console.aws.amazon.com
2. Serviço: EC2
3. Botão: "Launch Instance"

**Configurações:**
- Name: `app-leonardo-bot-prod`
- AMI: **Ubuntu 22.04 LTS** (free-tier eligible)
- Instance Type: **t3.micro** (free tier)
- Key pair: **Criar nova** → `app-leonardo-prod`
- Network: Default VPC
- Security Group: **Create new**
  - Name: `app-leonardo-sg`
  - Inbound rules:
    - SSH (22): Seu IP (RESTRITAR!)
    - Custom TCP 8080: 0.0.0.0/0 (API)
- Storage: **20GB** gp3 (free tier)
- Launch!

### Passo 2: Anotar informações

Após launch, pegar:

```
Public IPv4 Address: XXX.XXX.XXX.XXX
Instance ID: i-xxxxxxxxxx
Security Group: sg-xxxxxxxxxx
```

Guardar essas informações!

### Passo 3: Aguardar instância estar pronta

Status deve ser "Running" (pode levar 2-3 minutos)

### Passo 4: Download do arquivo .pem

AWS Console → Key Pairs → Download `app-leonardo-prod.pem`

Salvar em: `C:\Users\gabri\.ssh\app-leonardo-prod.pem`

---

## 🚀 DEPLOY (ORDEM CORRETA)

### ✅ Checklist de Execução

- [ ] Pré-requisitos OK
- [ ] Código compilado e testado
- [ ] Pacote compactado (`app-leonardo.tar.gz`)
- [ ] EC2 criada e rodando
- [ ] SSH key salva e com permissões corretas
- [ ] Credenciais Binance a mão
- [ ] Tempo disponível: 30-45 minutos

### ✅ Durante o Deploy

1. [ ] Conectar via SSH
2. [ ] Descompactar código
3. [ ] Criar venv
4. [ ] Instalar dependências
5. [ ] Criar .env com credenciais
6. [ ] Rodar script de deploy automático
7. [ ] Verificar logs
8. [ ] Testar endpoints

### ✅ Pós-Deploy

- [ ] API respondendo: `curl http://IP:8080/health`
- [ ] Dashboard carregando: `http://IP:3000`
- [ ] Bots iniciando: Check logs
- [ ] Backup automático: Cronjob criado
- [ ] Firewall: Aberto para conexões

---

## 🐛 POSSÍVEIS PROBLEMAS

### Problema: "Permission denied (publickey)"

**Solução:**
```powershell
# Recheckear permissões
icacls "C:\Users\gabri\.ssh\app-leonardo-prod.pem" /grant:r "%username%:F" /inheritance:r

# Ou copiar para um local sem espaços
copy "C:\Users\gabri\.ssh\app-leonardo-prod.pem" $env:TEMP\key.pem
ssh -i $env:TEMP\key.pem ubuntu@$IP
```

### Problema: "Connection refused"

**Solução:**
```powershell
# Verificar se EC2 está realmente rodando
# AWS Console → EC2 → Instances → Status check

# Aguarde 2-3 minutos após launch
# Tente de novo
```

### Problema: "ModuleNotFoundError"

**Solução:**
```bash
# No servidor
source venv/bin/activate
pip install -r requirements_new.txt -v
```

### Problema: Script de deploy falha

**Solução:**
```bash
# Ver erro exato
bash deploy_auto.sh 2>&1 | tee deploy.log
tail -100 deploy.log
```

---

## 📞 SUPORTE

Se ficar preso:

1. **Revisar**: `AWS_DEPLOY_CHECKLIST.md`
2. **Verificar logs**: `sudo journalctl -u app-leonardo-api.service -n 50`
3. **Testar conectividade**: `curl http://localhost:8080/health`
4. **Discord**: [seu-link]

---

## 🎓 DEPOIS DO DEPLOY

Próximas ações:

- [ ] Validar em produção por 24h
- [ ] Monitorar logs e métricas
- [ ] Testar restart de bots
- [ ] Fazer backup dos dados
- [ ] Documentar IP e configurações
- [ ] (Opcional) Configurar domínio + SSL

---

## 📊 VERSÕES SUPORTADAS

| Componente | Versão | Status |
|------------|--------|--------|
| Python | 3.11+ | ✅ |
| FastAPI | 0.109+ | ✅ |
| React | 18+ | ✅ |
| Node | 18+ | ✅ |
| Ubuntu | 22.04 LTS | ✅ |
| AWS | Qualquer region | ✅ |

---

**🎯 Objetivo**: Deploy em AWS com sucesso  
**Tempo estimado**: 45-60 minutos  
**Custo**: ~$1-5 primeiro mês (free tier)

Boa sorte! 🚀
