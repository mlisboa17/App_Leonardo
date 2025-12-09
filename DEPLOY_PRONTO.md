# 🚀 DEPLOY NA AWS - PRONTO PARA EXECUTAR

## ✅ Tudo Configurado!

**Instância AWS:**
- ID: `i-0754deeabc809cdea`
- Nome: `r7_trade`
- IP Público: **18.230.59.118**
- Chave SSH: `C:\Users\gabri\Downloads\r7_trade_key.pem`

## 🎯 PASSO A PASSO (3 minutos)

### 1. Conectar ao servidor

**Opção A - Usando o script automático:**
```cmd
.\DEPLOY_AWS_CONECTAR.bat
```

**Opção B - Manual:**
```powershell
ssh -i "C:\Users\gabri\Downloads\r7_trade_key.pem" ubuntu@18.230.59.118
```

### 2. Executar deploy (COPIE E COLE após conectar)

```bash
wget https://raw.githubusercontent.com/mlisboa17/App_Leonardo/master/deploy_aws.sh
chmod +x deploy_aws.sh
./deploy_aws.sh
```

**Aguarde 5-10 minutos** - O script fará TUDO automaticamente:
- ✅ Instalar Python, Nginx, Supervisor
- ✅ Clonar código do GitHub
- ✅ Instalar dependências (Streamlit, Binance, etc)
- ✅ Configurar auto-update de saldos
- ✅ Configurar dashboard
- ✅ Iniciar serviços

### 3. Acessar Dashboard

Quando terminar, abra no navegador:

**🌐 http://18.230.59.118**

ou

**🌐 http://18.230.59.118:8503**

---

## 📊 Verificar se está funcionando

Após o deploy, no terminal SSH digite:

```bash
# Ver status
sudo supervisorctl status

# Deve mostrar:
# r7_auto_update    RUNNING
# r7_dashboard      RUNNING

# Ver logs
sudo tail -f /var/log/r7_dashboard.out.log
```

---

## 🔧 Comandos Úteis

```bash
# Atualizar código do GitHub
cd /home/ubuntu/app_r7
git pull
sudo supervisorctl restart all

# Ver logs em tempo real
sudo tail -f /var/log/r7_dashboard.out.log

# Reiniciar tudo
sudo supervisorctl restart all

# Parar tudo
sudo supervisorctl stop all
```

---

## ⚙️ Editar Credenciais Binance (se necessário)

```bash
nano /home/ubuntu/app_r7/config/.env
```

Edite as linhas:
```env
BINANCE_API_KEY=SUA_CHAVE_AQUI
BINANCE_API_SECRET=SEU_SECRET_AQUI
```

Salve (Ctrl+O, Enter, Ctrl+X) e reinicie:
```bash
sudo supervisorctl restart all
```

---

## 💰 O que vai rodar 24/7

✅ **Dashboard Streamlit** - http://18.230.59.118
✅ **Auto-update de saldos** - Atualiza quando detecta trades
✅ **Conexão Binance** - Pega preços em tempo real
✅ **Supervisor** - Reinicia se crashar

---

## 🚨 Troubleshooting

**Dashboard não abre?**
```bash
sudo supervisorctl status
sudo tail -f /var/log/r7_dashboard.err.log
```

**Saldos não atualizam?**
```bash
sudo supervisorctl status r7_auto_update
sudo tail -f /var/log/r7_auto_update.out.log
```

**Reiniciar tudo:**
```bash
sudo supervisorctl restart all
```

---

## 📱 ACESSO RÁPIDO

**Dashboard:** http://18.230.59.118

**Conectar SSH:**
```bash
.\DEPLOY_AWS_CONECTAR.bat
```

ou

```bash
ssh -i "C:\Users\gabri\Downloads\r7_trade_key.pem" ubuntu@18.230.59.118
```

---

**PRONTO PARA DEPLOY! Execute o script quando quiser! 🚀**
