# 🌅 INSTRUÇÕES DE DEPLOY - MORNING SETUP

**Data**: 8 de Dezembro de 2025  
**Status**: Código pronto no GitHub, EC2 criada, aguardando credenciais

---

## 📋 INFORMAÇÕES A COLETAR

Você precisará de:

### 1. IP Público da EC2
```
Onde pegar: AWS Console > EC2 > Instances > [sua instância] > Public IPv4
Formato: ex. 54.123.45.67
```

### 2. Arquivo de Chave SSH (.pem)
```
Onde encontrar: C:\Users\gabri\.ssh\ (geralmente)
Nome esperado: r7-trading-bot-prod.pem
```

### 3. Usuário SSH
```
Para Ubuntu: ubuntu
Para Amazon Linux: ec2-user
```

---

## 🚀 PASSO A PASSO DE DEPLOY

### PASSO 1: Validar EC2
```powershell
# No seu Windows PowerShell, verifique:
# 1. EC2 está rodando (status "running")
# 2. Security Group tem portas abertas:
#    - Port 22 (SSH)
#    - Port 8080 (API)
#    - Port 8501 (Dashboard)
```

### PASSO 2: Preparar Ambiente Local
```powershell
# Abra PowerShell como Admin e navegue até:
cd "C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"

# Defina as variáveis:
$EC2_IP = "seu-ip-aqui"          # Ex: 54.123.45.67
$SSH_KEY = "C:\path\to\key.pem"  # Caminho completo da chave
$SSH_USER = "ubuntu"              # Geralmente ubuntu
$ARCHIVE = "r7-trading-bot.tar.gz"
```

### PASSO 3: Upload do Arquivo
```powershell
# Execute o upload (leva ~2-3 minutos para 29.3 MB):
scp -i $SSH_KEY $ARCHIVE ${SSH_USER}@${EC2_IP}:~/

# Esperado: Arquivo aparece em ~/r7-trading-bot.tar.gz na EC2
```

### PASSO 4: Conectar à EC2
```powershell
# SSH na instância:
ssh -i $SSH_KEY ${SSH_USER}@${EC2_IP}

# Você deve ver: ubuntu@ip-xxx:~$
```

### PASSO 5: Extrair e Configurar
```bash
# Na EC2, execute:
cd ~
tar -xzf r7-trading-bot.tar.gz
cd r7-trading-bot
ls -la

# Verificar: deve ver setup_quick.sh, requirements.txt, etc
```

### PASSO 6: Executar Setup Automático
```bash
# Na EC2:
bash setup_quick.sh

# Isto vai:
# ✓ Instalar Python 3.11
# ✓ Criar venv
# ✓ Instalar requirements
# ✓ Criar diretórios
# ✓ Configurar systemd services
# ✓ (NÃO inicia serviços ainda)
```

### PASSO 7: Atualizar Credenciais
```bash
# Na EC2, edite o arquivo de config:
nano config/.env

# Atualize com suas NOVAS chaves Binance:
BINANCE_API_KEY=sua-chave-nova-aqui
BINANCE_API_SECRET=seu-secret-novo-aqui
BINANCE_TESTNET_API_KEY=testnet-key-nova
BINANCE_TESTNET_API_SECRET=testnet-secret-novo

# Salve: Ctrl+O, Enter, Ctrl+X
```

### PASSO 8: Iniciar Serviços
```bash
# Na EC2, inicie os systemd services:
sudo systemctl start r7-trading-bot
sudo systemctl start r7-trading-dashboard

# Verifique status:
sudo systemctl status r7-trading-bot
sudo systemctl status r7-trading-dashboard

# Ver logs:
journalctl -u r7-trading-bot -f
```

### PASSO 9: Testar Health
```bash
# No seu Windows PowerShell:
# Health check da API
curl "http://${EC2_IP}:8080/api/health"

# Deve retornar:
# {"status":"healthy","uptime":"...","timestamp":"..."}

# Dashboard Streamlit estará em:
# http://${EC2_IP}:8501
```

### PASSO 10: Verificar Logs
```bash
# Na EC2:
# Ver últimos logs:
journalctl -u r7-trading-bot -n 50

# Ver logs em tempo real:
journalctl -u r7-trading-bot -f

# Ver logs do dashboard:
journalctl -u r7-trading-dashboard -f
```

---

## ⚠️ ANTES DE COMEÇAR

### Credenciais Antigas (IMPORTANTE!)

As credenciais antigas estão ainda ATIVAS. Você deve:

```
1. Acessar: https://www.binance.com/en/account/api-management
2. Encontrar as chaves antigas (de desenvolvimento)
3. Deletar AMBAS:
   - API Key terminando em ...byy (production)
   - API Key terminando em ...m (testnet)
4. CONFIRMAR delete
5. Criar NOVAS chaves com:
   - IP Whitelist: seu IP público da EC2
   - Permissions: Spot Trading apenas
```

---

## 🔍 TROUBLESHOOTING

### SSH falha com "Permission denied"
```
Causa: Permissões da chave incorretas
Solução: 
  chmod 600 $SSH_KEY  (Linux/Mac)
  No Windows: Configure permissões na propriedade do arquivo
```

### SCP: "No such file"
```
Causa: Arquivo .tar.gz não existe ou caminho errado
Solução:
  ls r7-trading-bot.tar.gz  (verifique existência)
  Certifique-se que está no diretório correto
```

### Setup falha com "Permission denied"
```
Causa: Falta permissão de execução
Solução: chmod +x setup_quick.sh
```

### Services não iniciam
```
Verificar:
  sudo systemctl status r7-trading-bot
  journalctl -u r7-trading-bot -n 20
  Logs detalhados em /var/log/r7-trading-bot/
```

### Health endpoint retorna erro
```
Verificar:
  1. curl "http://${EC2_IP}:8080/api/health"
  2. Se falhar, checar logs: journalctl -u r7-trading-bot -f
  3. Verificar config/.env está correto
  4. Verificar credenciais Binance são válidas
```

---

## 📞 RESUMO RÁPIDO

| Passo | Comando | Tempo |
|-------|---------|-------|
| 1 | Upload via SCP | 2-3 min |
| 2 | SSH para EC2 | 1 min |
| 3 | Extrair arquivo | 1 min |
| 4 | Executar setup_quick.sh | 5-10 min |
| 5 | Atualizar credenciais | 2 min |
| 6 | Iniciar serviços | 1 min |
| 7 | Testar health | 1 min |
| **TOTAL** | **~15-20 minutos** | |

---

## ✅ CHECKLIST FINAL

- [ ] EC2 está em estado "running"
- [ ] Security Groups têm portas abertas (22, 8080, 8501)
- [ ] Arquivo .pem tem permissões corretas
- [ ] Credenciais antigas foram deletadas do Binance
- [ ] Novas chaves Binance foram criadas
- [ ] Arquivo r7-trading-bot.tar.gz existe localmente
- [ ] IP público da EC2 está anotado
- [ ] SSH consegue conectar: `ssh -i KEY ubuntu@IP`
- [ ] Upload completou sem erros
- [ ] Setup executou sem erros críticos
- [ ] config/.env foi atualizado com novas credenciais
- [ ] Serviços iniciaram sem erros
- [ ] curl /api/health retorna 200 OK
- [ ] Dashboard Streamlit está acessível

---

## 🎉 DEPOIS QUE ESTIVER RODANDO

Sua aplicação estará:

- **API**: `http://seu-ip:8080` (FastAPI)
- **Dashboard**: `http://seu-ip:8501` (Streamlit)
- **Health Check**: `curl http://seu-ip:8080/api/health`
- **Logs**: `ssh -i KEY ubuntu@IP` + `journalctl -u r7-trading-bot -f`
- **Auto-restart**: Habilitado (systemd)
- **Backup**: Automático (cron job)

---

Bom deploy! 🚀
