# ✅ CHECKLIST EXECUTIVO - DEPLOY PARA PRODUÇÃO

**Data**: 8 de Dezembro de 2025  
**Situação**: Código pronto + EC2 existente + Aguardando credenciais

---

## 📋 PRÉ-DEPLOY (Antes de começar)

- [ ] **EC2 está rodando** (status "running" no console AWS)
- [ ] **IP público anotado** (ex: 54.123.45.67)
- [ ] **Arquivo .pem está em** `C:\Users\gabri\.ssh\`
- [ ] **Arquivo r7-trading-bot.tar.gz existe** (29.3 MB)
- [ ] **Você está com acesso ao console Binance**

---

## 🔴 SEGURANÇA CRÍTICA

### ⚠️ REVOGAR CREDENCIAIS ANTIGAS (PASSO 1)

```
IMPORTANTE: As credenciais atuais estão EXPOSTAS no GitHub!
Devem ser revogadas IMEDIATAMENTE antes de qualquer coisa.
```

**Local**: https://www.binance.com/en/account/api-management

- [ ] Acesso ao console Binance ok
- [ ] Encontrou as 2 chaves antigas:
  - [ ] ...byy (production - DELETE)
  - [ ] ...m (testnet - DELETE)
- [ ] **Clicou DELETE em ambas** (CONFIRMAR)
- [ ] Aguardou confirmação (1-5 min)
- [ ] Verificou que sumiram da lista

**Status**: CRÍTICO - Não prosseguir sem isso ✋

---

## 🔑 CRIAR NOVAS CREDENCIAIS BINANCE (PASSO 2)

**Local**: https://www.binance.com/en/account/api-management

- [ ] Clicou "+ Create API Key"
- [ ] Escolheu "System generated"
- [ ] Confirmou por email/2FA
- [ ] **Chave PRODUCTION criada:**
  - [ ] API Key: `[COPIE E COLE AQUI: ___________________]`
  - [ ] Secret: `[COPIE E COLE AQUI: ___________________]`
  - [ ] ⚠️ Guardou em local seguro (NÃO compartilhe)

- [ ] **Chave TESTNET criada** (http://testnet.binancefuture.com):
  - [ ] API Key: `[COPIE E COLE AQUI: ___________________]`
  - [ ] Secret: `[COPIE E COLE AQUI: ___________________]`

- [ ] **Configurou IP Whitelist**:
  - [ ] IP da EC2 adicionado: `[seu-ip-aqui: ___________]`
  - [ ] Removeu 0.0.0.0/0 (aceita só seu IP)

- [ ] **Permissions configuradas**:
  - [ ] [x] Spot Trading
  - [ ] [ ] Margin Trading (DESABILITAR)
  - [ ] [ ] Futures (DESABILITAR)

**Status**: OK - Só continue quando tiver as novas chaves ✅

---

## 🚀 DEPLOY (PASSO 3)

### OPÇÃO A: Deploy Automático (Recomendado)

- [ ] Abriu PowerShell como Administrator
- [ ] Navegou até: `C:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1`
- [ ] Editou variáveis em `deploy_auto.ps1`:
  ```powershell
  $EC2_IP = "seu-ip-aqui"
  $SSH_KEY = "C:\Users\gabri\.ssh\r7-trading-bot-prod.pem"
  ```
- [ ] Executou: `.\deploy_auto.ps1 -EC2_IP "IP" -SSH_KEY "caminho"`
- [ ] ✅ Viu mensagem: "Deploy Preparado"

### OPÇÃO B: Deploy Manual

- [ ] Executou SCP (upload):
  ```powershell
  scp -i "path\key.pem" r7-trading-bot.tar.gz ubuntu@IP:~/
  ```
- [ ] Conectou SSH:
  ```powershell
  ssh -i "path\key.pem" ubuntu@IP
  ```
- [ ] Extraiu arquivo (na EC2):
  ```bash
  cd ~ && tar -xzf r7-trading-bot.tar.gz && cd r7-trading-bot
  ```
- [ ] Executou setup (na EC2):
  ```bash
  chmod +x setup_quick.sh && bash setup_quick.sh
  ```

**Status**: Upload + Setup completado ✅

---

## 🔐 CONFIGURAR CREDENCIAIS (PASSO 4)

- [ ] SSH conectado na EC2:
  ```powershell
  ssh -i "path\key.pem" ubuntu@IP
  ```
- [ ] Abriu arquivo de config:
  ```bash
  cd ~/r7-trading-bot && nano config/.env
  ```
- [ ] Atualizou **TODAS** as 4 credenciais:
  - [ ] `BINANCE_API_KEY=` (nova chave production)
  - [ ] `BINANCE_API_SECRET=` (novo secret production)
  - [ ] `BINANCE_TESTNET_API_KEY=` (nova chave testnet)
  - [ ] `BINANCE_TESTNET_API_SECRET=` (novo secret testnet)
- [ ] ⚠️ **Não deixou vazios** (erro se vazio)
- [ ] Salvou arquivo (Ctrl+O, Enter, Ctrl+X)
- [ ] Verificou que foi salvo:
  ```bash
  cat config/.env | grep BINANCE
  ```

**Status**: Credenciais configuradas ✅

---

## ⚡ INICIAR SERVIÇOS (PASSO 5)

- [ ] Na EC2, executou:
  ```bash
  chmod +x start_services.sh
  ./start_services.sh
  ```
- [ ] Ou manualmente:
  ```bash
  sudo systemctl start r7-trading-bot
  sudo systemctl start r7-trading-dashboard
  ```
- [ ] Viu mensagens de sucesso ✓
- [ ] Verificou status:
  ```bash
  sudo systemctl status r7-trading-bot
  ```

**Status**: Serviços iniciados ✅

---

## 🧪 VALIDAR DEPLOY (PASSO 6)

### Health Check
- [ ] Executou no PowerShell:
  ```powershell
  curl "http://seu-ip:8080/api/health"
  ```
- [ ] Recebeu resposta: `{"status":"healthy",...}`

### Acessar Dashboard
- [ ] Abriu browser em: `http://seu-ip:8501`
- [ ] Viu página do Streamlit
- [ ] Navegou pelos gráficos

### Ver Logs
- [ ] Executou:
  ```powershell
  ssh -i "key.pem" ubuntu@IP "journalctl -u r7-trading-bot -n 50"
  ```
- [ ] Procurou por erros (ERROR, EXCEPTION)
- [ ] Se houver erros:
  - [ ] Verificou credenciais em config/.env
  - [ ] Verificou chaves Binance são válidas
  - [ ] Reexecutou start_services.sh

**Status**: Validação completa ✅

---

## 📊 APÓS ESTAR RODANDO

### Acessos
- [ ] API: `http://seu-ip:8080`
- [ ] Dashboard: `http://seu-ip:8501`
- [ ] Docs: `http://seu-ip:8080/docs`
- [ ] Health: `http://seu-ip:8080/api/health`

### Monitoramento
- [ ] Habilitou auto-start (systemd)
- [ ] Logs estão sendo coletados
- [ ] Backup automático configurado
- [ ] Bots começaram a tradar (ou estão em standby se mercado fechado)

### Segurança
- [ ] Credenciais antigas foram deletadas ✓
- [ ] Novas credenciais IP-whitelist só seu IP ✓
- [ ] .env no servidor (não no GitHub) ✓
- [ ] Logs estão em `/var/log/r7-trading-bot/`

**Status**: Produção OK ✅

---

## 🆘 PROBLEMAS?

### Se SSH não conecta:
```
1. Verificar IP: correto?
2. Verificar .pem: está em C:\Users\gabri\.ssh\?
3. Permissões da chave: Properties > Security
4. Esperar 5 min: EC2 leva tempo pra boot
5. Testar: ping seu-ip (consegue chegar?)
```

### Se upload falha (SCP):
```
1. Arquivo existe? ls r7-trading-bot.tar.gz
2. Caminho correto? pwd
3. Permissões SSH? Conecta com ssh?
4. Espaço em disco na EC2? ssh ... "df -h"
```

### Se setup falha:
```
1. Viu qual erro exato?
2. Espaço disco? ssh ... "df -h"
3. Python? ssh ... "python3 --version"
4. Reexecutar: cd r7-trading-bot && bash setup_quick.sh
```

### Se services não iniciam:
```
1. Status: sudo systemctl status r7-trading-bot
2. Logs: journalctl -u r7-trading-bot -n 50
3. Credenciais ok? cat config/.env | grep BINANCE
4. Porta aberta? sudo netstat -tlnp | grep 8080
```

### Se health check falha:
```
1. Service rodando? sudo systemctl status
2. Porta aberta? curl localhost:8080 (de dentro EC2)
3. Logs? journalctl -u r7-trading-bot -f
4. Binance online? Teste credenciais manualmente
```

---

## 📝 NOTAS IMPORTANTES

1. **Não reutilize credenciais antigas** - Elas foram expostas no GitHub
2. **Guarde novas chaves com segurança** - Nunca compartilhe
3. **IP Whitelist está configurado** - Só você pode usar
4. **Auto-restart habilitado** - Service reinicia se cair
5. **Backups automáticos** - Dados salvos em S3
6. **Logs persistem** - Pode debugar depois

---

## ✨ SE TUDO DEU CERTO

```
✅ Código rodando em produção
✅ Dashboard acessível
✅ Bots operando
✅ Logs centralizados
✅ Auto-restart ativo
✅ Backups automáticos
✅ Segurança implementada
```

**Parabéns! Seu sistema está em produção!** 🎉

---

## 🎯 PRÓXIMOS PASSOS (Dia 2+)

- [ ] Monitorar logs diariamente: `journalctl -u r7-trading-bot -f`
- [ ] Revisar trades históricos no dashboard
- [ ] Configurar alertas (emails, SMS, Discord)
- [ ] Escalabilidade: adicionar mais bots conforme mercado aquece
- [ ] Database: migrar para PostgreSQL quando volume crescer
- [ ] Load Balancer: distribuir tráfego se demanda aumentar

---

**Última atualização**: 8 de Dezembro de 2025  
**Status**: Pronto para Deploy  
**Tempo estimado**: 15-20 minutos
