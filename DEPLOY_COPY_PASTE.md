# COMANDOS PRONTOS PARA DEPLOY

## 🔴 IMPORTANTE: Antes de qualquer coisa

1. Acesse Binance: https://www.binance.com/en/account/api-management
2. Delete AMBAS as chaves antigas:
   - A terminada em ...byy (production)
   - A terminada em ...m (testnet)
3. Crie NOVAS chaves com:
   - IP Whitelist: seu IP público EC2 (ex: 54.123.45.67)
   - Permissions: Spot Trading apenas
   - Salve a chave e secret com segurança

---

## 📋 CONFIGURAÇÃO DE VARIÁVEIS (customize aqui)

```powershell
# Edite estes valores com suas informações:
$EC2_IP = "seu-ip-publico-aqui"      # Ex: 54.123.45.67
$SSH_KEY = "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem"
$SSH_USER = "ubuntu"
$ARCHIVE = "r7-trading-bot.tar.gz"
```

---

## 🚀 OPÇÃO 1: DEPLOY AUTOMÁTICO (Recomendado)

Copie e cole no PowerShell (com variáveis configuradas acima):

```powershell
cd "C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"

# Execute o script automático
.\deploy_auto.ps1 -EC2_IP $EC2_IP -SSH_KEY $SSH_KEY -SSH_USER $SSH_USER -ARCHIVE $ARCHIVE

# Aguarde até ver: "Proximos passos..."
```

---

## 🚀 OPÇÃO 2: DEPLOY MANUAL (Passo a passo)

### Passo 1: Upload do arquivo
```powershell
cd "C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"

scp -i "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem" r7-trading-bot.tar.gz ubuntu@54.123.45.67:~/
```

### Passo 2: Conectar à EC2
```powershell
ssh -i "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem" ubuntu@54.123.45.67
```

### Passo 3: Extrair (já na EC2)
```bash
cd ~
tar -xzf r7-trading-bot.tar.gz
cd r7-trading-bot
chmod +x setup_quick.sh
ls -la
```

### Passo 4: Executar setup
```bash
bash setup_quick.sh

# Leva ~5-10 minutos
# Não interrompa
```

### Passo 5: Editar credenciais
```bash
nano config/.env

# Encontre e edite:
# BINANCE_API_KEY=sua-nova-chave
# BINANCE_API_SECRET=seu-novo-secret
# BINANCE_TESTNET_API_KEY=testnet-key
# BINANCE_TESTNET_API_SECRET=testnet-secret

# Salve: Ctrl+O, Enter, Ctrl+X
```

### Passo 6: Iniciar serviços
```bash
chmod +x start_services.sh
./start_services.sh

# Ou manualmente:
sudo systemctl start r7-trading-bot
sudo systemctl start r7-trading-dashboard
```

---

## ✅ VALIDAÇÃO

### Testar do Windows PowerShell:
```powershell
$EC2_IP = "seu-ip-aqui"
curl "http://${EC2_IP}:8080/api/health"

# Esperado:
# {"status":"healthy","uptime":"...","timestamp":"..."}
```

### Ver logs em tempo real:
```powershell
ssh -i "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem" ubuntu@54.123.45.67 "journalctl -u r7-trading-bot -f"
```

### Status dos serviços:
```powershell
ssh -i "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem" ubuntu@54.123.45.67 "sudo systemctl status r7-trading-bot"
```

---

## 🌐 ACESSAR A APLICAÇÃO

- **API**: http://54.123.45.67:8080
- **Dashboard**: http://54.123.45.67:8501
- **Health Check**: http://54.123.45.67:8080/api/health
- **Audit Logs**: http://54.123.45.67:8080/api/audit/events
- **Docs (Swagger)**: http://54.123.45.67:8080/docs

---

## 🔧 TROUBLESHOOTING

### SSH falha com "connection timeout"
```
Causa: IP público ou security group errado
Solução:
  1. Verificar IP é correto
  2. Checar Security Group tem porta 22 aberta
  3. Esperar 5 min para EC2 boot completar
```

### SSH falha com "Permission denied"
```
Causa: Permissões da chave incorretas
Solução (Windows):
  1. Clique direito no .pem
  2. Properties > Security > Advanced
  3. Remove all inherited permissions
  4. Add "SYSTEM" e seu usuário com "Full Control"
```

### Setup falha
```
Solução:
  1. Verificar espaço em disco: df -h
  2. Ver logs: tail -50 setup.log
  3. Reexecutar: bash setup_quick.sh
```

### Services não iniciam
```
Diagnóstico:
  sudo systemctl status r7-trading-bot
  journalctl -u r7-trading-bot -n 50
  
Causas comuns:
  1. config/.env não atualizado
  2. Credenciais Binance inválidas
  3. Porta 8080 já em uso
```

### Health check retorna erro
```
1. Verificar service está rodando:
   sudo systemctl status r7-trading-bot
   
2. Verificar logs:
   journalctl -u r7-trading-bot -f
   
3. Testar dentro da EC2:
   curl http://localhost:8080/api/health
```

---

## 📞 RESUMO FINAL

| Etapa | Tempo |
|-------|-------|
| 1. Revogar chaves Binance | 2 min |
| 2. Criar novas chaves | 2 min |
| 3. Upload arquivo | 2-3 min |
| 4. Setup automático | 5-10 min |
| 5. Atualizar credenciais | 2 min |
| 6. Iniciar serviços | 1 min |
| 7. Validar | 1 min |
| **TOTAL** | **~15-20 min** |

---

## ⚡ QUICK START (Copy-Paste)

Se seguir tudo corretamente:

```powershell
# 1. Configure variáveis acima

# 2. Execute deploy automático
cd "C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"
.\deploy_auto.ps1 -EC2_IP "seu-ip" -SSH_KEY "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem"

# 3. SSH na instância
ssh -i "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem" ubuntu@seu-ip

# 4. Na EC2: Editar credenciais
cd r7-trading-bot && nano config/.env

# 5. Na EC2: Iniciar serviços
./start_services.sh

# 6. De volta ao Windows: Validar
curl "http://seu-ip:8080/api/health"
```

Pronto! 🚀

---

## 📝 NOTES

- Arquivo está em: `c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1\r7-trading-bot.tar.gz`
- Script deploy está em: `deploy_auto.ps1`
- Setup script está em: `setup_quick.sh`
- Instruções detalhadas: `DEPLOY_INSTRUCTIONS_MORNING.md`
- Checklist: `AWS_DEPLOY_CHECKLIST.md`
