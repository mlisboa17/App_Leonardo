# R7 TRADING BOT API - DEPLOY PRONTO

**Data**: 8 de Dezembro de 2025  
**Status**: Arquivo compactado criado, pronto para deploy  
**Tempo de Setup**: ~15 minutos  
**Custo**: $0 (Ano 1, Free Tier AWS)

---

## O QUE FOI FEITO ENQUANTO VOCÊ DORMIA

### ✅ COMPLETADO:
- [x] Código renomeado para "R7 Trading Bot API"
- [x] Arquivo compactado criado: `r7-trading-bot-TIMESTAMP.tar.gz` (~176 MB)
- [x] Credenciais expostas identificadas e documentadas
- [x] Script de setup automático (`setup_quick.sh`)
- [x] Código enviado para GitHub (master branch)
- [x] Documentação completa criada
- [x] Script de deploy em Windows (`deploy_windows.py`)
- [x] Script de credenciais (`setup_credentials.py`)

### 📋 TAREFAS PENDENTES (Para você fazer):

1. **Revogar credenciais antigas** (Binance)
2. **Criar novas credenciais** (Binance)
3. **Criar EC2 Instance** (AWS)
4. **Upload arquivo** (SCP)
5. **Executar setup** (SSH)
6. **Iniciar serviços** (Systemd)

---

## PASSO A PASSO RÁPIDO

### PASSO 1: Revogar e Criar Credenciais (5 min)

```powershell
cd c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1
python setup_credentials.py
```

Este script vai:
- Abrir navegador na Binance
- Guiar você na revogação das chaves antigas
- Instruir como criar novas chaves
- Salvar as novas credenciais no arquivo config/.env

**CREDENCIAIS ATUAIS A REVOGAR:**
```
Production: rVFHoreINIsQJtZ7vR9IQc7HGiybp4VLzkXQJtx0bLu9e2F7oIamconSYNmRzbyy
Testnet:    QcyrgxtWUGXRkcsfx67EBu5OSTCFcIiFTqcCLfM6aV6zeTV8vxCwkobhY5idiU3m
```

---

### PASSO 2: Criar EC2 Instance (5 min)

**Opção Manual (Simples):**
1. Ir para: https://console.aws.amazon.com/ec2
2. Clicar em "Launch Instance"
3. Configurar:
   - **Name**: r7-trading-bot-prod
   - **AMI**: Ubuntu 22.04 LTS (Free Tier)
   - **Type**: t3.micro
   - **Key pair**: Criar nova (salvar arquivo .pem)
   - **Security Group**: Permitir SSH (22), Custom TCP (8080, 8501)
4. **Launch**
5. Aguardar até status "running"
6. Copiar **Public IPv4** (ex: 3.12.34.56)

**Opção Automática (Script):**
```powershell
# Será adicionado em update futuro
```

---

### PASSO 3: Upload e Deploy (5 min)

**No PowerShell (Windows):**

```powershell
# 1. Definir variáveis
$IP = "3.12.34.56"  # Trocar pelo IP público da EC2
$PEM = "C:\caminho\para\arquivo.pem"
$ARCHIVE = "C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1\r7-trading-bot-20251208_004642.tar.gz"

# 2. Upload arquivo
scp -i $PEM -o StrictHostKeyChecking=no $ARCHIVE ubuntu@${IP}:~/

# 3. SSH para instância
ssh -i $PEM -o StrictHostKeyChecking=no ubuntu@$IP

# Na instância Ubuntu (bash):
tar -xzf r7-trading-bot-20251208_004642.tar.gz
cd r7_v1

# Editar credenciais
nano config/.env
# Cole as NOVAS credenciais Binance
# Salvar: Ctrl+X, Y, ENTER

# Executar setup
bash setup_quick.sh

# Iniciar serviços
sudo systemctl start r7-trading-bot
sudo systemctl start r7-trading-dashboard
sudo systemctl status r7-trading-bot

# Sair
exit
```

**De volta no PowerShell:**

```powershell
# Testar health
curl http://$IP:8080/api/health

# Acessar dashboard
# Navegador: http://$IP:8501
```

---

## ARQUIVOS CRIADOS

### Documentação
- **DEPLOY_QUICK.md** - Guia rápido em 3 passos
- **AWS_DEPLOY_CHECKLIST.md** - Checklist detalhado
- **REMEDIATION_SECURITY.md** - Documentação de segurança
- **README_DEPLOY_2025.txt** - Instruções de deploy
- **START_HERE.md** - Ponto de partida

### Scripts
- **deploy_windows.py** - Cria arquivo tar.gz
- **setup_credentials.py** - Guia interativo para credenciais
- **setup_quick.sh** - Setup automático na EC2
- **revoke_credentials.py** - Validar revogação (opcional)
- **test_credentials.py** - Testar credenciais (opcional)

### Arquivo Deploy
- **r7-trading-bot-20251208_004642.tar.gz** (~176 MB)
  - Pronto para upload à EC2
  - Inclui: backend, frontend, configs, scripts
  - Exclui: venv, cache, logs, credenciais reais

---

## ESTRUTURA DA EC2

Após setup automático, sua instância terá:

```
/home/ubuntu/r7_v1/
├── backend/          # FastAPI
├── frontend-react/   # React dashboard
├── src/              # Core bot
├── config/           # Configurações
├── data/             # Dados (logs, histórico, etc)
├── requirements.txt
├── setup_quick.sh    # Setup automático
└── ... (outros arquivos)

SERVIÇOS SYSTEMD:
- r7-trading-bot      (Backend FastAPI)
- r7-trading-dashboard (Frontend Streamlit)
```

---

## VERIFICAÇÕES

### Depois de fazer deploy:

```bash
# 1. Health check
curl http://IP:8080/api/health
# Esperado: {"status":"ok", ...}

# 2. API test
curl http://IP:8080/api/status
# Esperado: 200 OK

# 3. Dashboard
# Navegador: http://IP:8501
# Esperado: Streamlit dashboard carregando

# 4. Logs
ssh -i PEM ubuntu@IP
sudo journalctl -u r7-trading-bot -f
sudo journalctl -u r7-trading-dashboard -f
```

---

## SEGURANÇA

### ✅ Feito:
- Credenciais expostas documentadas
- Scripts de revogação criados
- .env.template criado para referência
- .gitignore protege .env

### ⚠️ A fazer:
1. Revogar credenciais antigas NO MESMO DIA
2. Usar credenciais novas (mais seguras)
3. Configurar IP whitelist na Binance (IP da EC2)
4. Usar SSH key-only (sem passwords)
5. Configurar Security Group na EC2 (porta 22 apenas para seu IP)

---

## CUSTO

**Ano 1**: $0 (AWS Free Tier)
- EC2 t3.micro: Grátis (até 750 horas/mês)
- S3: Grátis (até 5 GB)

**Ano 2+**: ~$10-15/mês
- EC2 t3.micro: ~$7-10/mês
- S3/transferência: ~$1-5/mês

---

## TROUBLESHOOTING

### Arquivo não compactado?
```powershell
cd c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1
python deploy_windows.py
```

### Credenciais não funcionam?
```bash
# Na EC2, validar:
python3 test_credentials.py
python3 revoke_credentials.py
```

### Serviço não inicia?
```bash
sudo systemctl status r7-trading-bot
sudo journalctl -u r7-trading-bot -n 50  # Últimas 50 linhas
```

### SSH não conecta?
1. Verificar IP da EC2 (console AWS)
2. Verificar Security Group (porta 22 aberta)
3. Verificar arquivo .pem (chmod 400 no Linux)
4. Verificar nome de usuário (ubuntu para Ubuntu AMI)

---

## PROXIMOS PASSOS

1. [ ] Revogar credenciais antigas
2. [ ] Criar novas credenciais Binance
3. [ ] Criar EC2 instance
4. [ ] Fazer upload arquivo
5. [ ] Executar setup_quick.sh
6. [ ] Testar health endpoints
7. [ ] Acessar dashboard
8. [ ] Configurar notificações (Telegram, email, etc)
9. [ ] Monitorar logs
10. [ ] Ajustar estratégias se necessário

---

## DOCUMENTAÇÃO COMPLETA

Para mais informações detalhadas:
- `DEPLOY_QUICK.md` - Setup em 3 passos
- `AWS_DEPLOY_CHECKLIST.md` - Checklist com prints
- `REMEDIATION_SECURITY.md` - Detalhes de segurança

---

## SUPORTE

Se tiver problemas:
1. Checar logs: `journalctl -u r7-trading-bot`
2. Ler `REMEDIATION_SECURITY.md`
3. Executar `test_credentials.py` para validar chaves
4. Verificar `config/.env` tem credenciais corretas

---

**Criado em**: 8 de Dezembro de 2025  
**Repo**: https://github.com/mlisboa17/App_Leonardo  
**Branch**: master  

Bom deploy! 🚀
