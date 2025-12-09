# 🚀 DEPLOY AWS - Guia Completo

## Pré-requisitos

- Conta AWS ativa
- Par de chaves SSH criado
- Security Group configurado (portas 22, 80, 8503)

## Passo 1: Criar Instância EC2

### Console AWS:

1. **EC2 Dashboard** → Launch Instance
2. **Name:** `app-r7-trading-bot`
3. **AMI:** Ubuntu Server 22.04 LTS (Free tier eligible)
4. **Instance type:** t2.small ou superior (mínimo 2GB RAM)
5. **Key pair:** Selecione ou crie uma
6. **Security Group:** Configure as regras:
   - SSH (22) - Seu IP
   - HTTP (80) - 0.0.0.0/0
   - Custom TCP (8503) - 0.0.0.0/0

7. **Storage:** 20 GB gp3

8. **Launch instance**

## Passo 2: Conectar à Instância

```bash
# Windows (PowerShell)
ssh -i "sua-chave.pem" ubuntu@SEU-IP-PUBLICO

# Exemplo
ssh -i "C:\Users\gabriel\.ssh\r7-key.pem" ubuntu@54.123.45.67
```

Se der erro de permissões no Windows:
```powershell
icacls "sua-chave.pem" /inheritance:r
icacls "sua-chave.pem" /grant:r "%USERNAME%:R"
```

## Passo 3: Deploy Automático

Após conectar via SSH, execute:

```bash
# Download do script de deploy
wget https://raw.githubusercontent.com/mlisboa17/App_Leonardo/master/deploy_aws.sh

# Dar permissão de execução
chmod +x deploy_aws.sh

# Executar deploy
./deploy_aws.sh
```

O script irá:
- ✅ Atualizar sistema Ubuntu
- ✅ Instalar Python 3, Git, Nginx, Supervisor
- ✅ Clonar repositório GitHub
- ✅ Criar ambiente virtual
- ✅ Instalar dependências (Streamlit, Binance, etc)
- ✅ Configurar auto-update de saldos
- ✅ Configurar Dashboard na porta 8503
- ✅ Configurar Nginx como proxy (porta 80)
- ✅ Iniciar serviços automaticamente

**Tempo estimado:** 5-10 minutos

## Passo 4: Verificar Instalação

```bash
# Ver status dos serviços
sudo supervisorctl status

# Deve mostrar:
# r7_auto_update    RUNNING
# r7_dashboard      RUNNING

# Ver logs do dashboard
sudo tail -f /var/log/r7_dashboard.out.log

# Ver logs do auto-update
sudo tail -f /var/log/r7_auto_update.out.log
```

## Passo 5: Acessar Dashboard

**Opção 1 - Via Nginx (Porta 80):**
```
http://SEU-IP-PUBLICO
```

**Opção 2 - Direto Streamlit (Porta 8503):**
```
http://SEU-IP-PUBLICO:8503
```

## Comandos Úteis

### Gerenciar Serviços

```bash
# Ver status
sudo supervisorctl status

# Reiniciar todos
sudo supervisorctl restart all

# Reiniciar apenas dashboard
sudo supervisorctl restart r7_dashboard

# Reiniciar apenas auto-update
sudo supervisorctl restart r7_auto_update

# Parar todos
sudo supervisorctl stop all

# Iniciar todos
sudo supervisorctl start all
```

### Ver Logs

```bash
# Dashboard (tempo real)
sudo tail -f /var/log/r7_dashboard.out.log

# Auto-update (tempo real)
sudo tail -f /var/log/r7_auto_update.out.log

# Erros dashboard
sudo tail -f /var/log/r7_dashboard.err.log

# Últimas 100 linhas
sudo tail -n 100 /var/log/r7_dashboard.out.log
```

### Atualizar Código

```bash
cd /home/ubuntu/app_r7
git pull origin master
sudo supervisorctl restart all
```

### Monitorar Recursos

```bash
# CPU e RAM em tempo real
htop

# Espaço em disco
df -h

# Processos Python
ps aux | grep python
```

## Configurações Avançadas

### Editar Credenciais Binance

```bash
nano /home/ubuntu/app_r7/config/.env
```

Edite as linhas:
```env
BINANCE_API_KEY=SUA_CHAVE_AQUI
BINANCE_API_SECRET=SEU_SECRET_AQUI
```

Salve (Ctrl+O) e saia (Ctrl+X), depois:
```bash
sudo supervisorctl restart all
```

### Configurar Domínio Próprio

Edite o Nginx:
```bash
sudo nano /etc/nginx/sites-available/r7_trading
```

Mude a linha:
```nginx
server_name _;
```

Para:
```nginx
server_name seudominio.com;
```

Reinicie Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### SSL/HTTPS com Let's Encrypt

```bash
# Instalar Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Obter certificado (substitua seu domínio)
sudo certbot --nginx -d seudominio.com

# Renovação automática já está configurada
```

## Troubleshooting

### Dashboard não abre

```bash
# Verificar se está rodando
sudo supervisorctl status

# Se não estiver, iniciar
sudo supervisorctl start r7_dashboard

# Ver erro nos logs
sudo tail -f /var/log/r7_dashboard.err.log
```

### Porta 80 não acessível

```bash
# Verificar Security Group no AWS Console
# Deve ter regra: HTTP (80) - 0.0.0.0/0

# Verificar Nginx
sudo systemctl status nginx
sudo nginx -t
```

### Saldos não atualizam

```bash
# Verificar auto-update
sudo supervisorctl status r7_auto_update

# Ver logs
sudo tail -f /var/log/r7_auto_update.out.log

# Reiniciar
sudo supervisorctl restart r7_auto_update
```

### Sem espaço em disco

```bash
# Limpar logs antigos
sudo truncate -s 0 /var/log/r7_*.log

# Limpar cache apt
sudo apt-get clean
```

## Backup e Restore

### Backup dos dados

```bash
# Criar backup
cd /home/ubuntu/app_r7
tar -czf backup-$(date +%Y%m%d).tar.gz data/ config/.env

# Download para seu PC
# No seu PC (PowerShell):
scp -i "sua-chave.pem" ubuntu@SEU-IP:/home/ubuntu/app_r7/backup-*.tar.gz .
```

### Restore

```bash
# Upload do backup (no seu PC)
scp -i "sua-chave.pem" backup-*.tar.gz ubuntu@SEU-IP:/home/ubuntu/app_r7/

# Na AWS
cd /home/ubuntu/app_r7
tar -xzf backup-*.tar.gz
sudo supervisorctl restart all
```

## Segurança

### Firewall UFW

```bash
# Ativar firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 8503/tcp
sudo ufw enable
sudo ufw status
```

### Atualizar Sistema

```bash
# Semanalmente
sudo apt-get update
sudo apt-get upgrade -y
sudo reboot
```

## Custos Estimados (AWS)

- **t2.small:** ~$17/mês
- **t2.medium:** ~$34/mês
- **t3.small:** ~$15/mês (melhor custo-benefício)
- **Storage (20GB):** ~$2/mês
- **Transfer:** Free tier 100GB/mês

**Total estimado:** $17-36/mês

## Checklist de Deploy

- [ ] Instância EC2 criada
- [ ] Security Group configurado (22, 80, 8503)
- [ ] Conectado via SSH
- [ ] Script deploy_aws.sh executado
- [ ] Serviços rodando (supervisorctl status)
- [ ] Dashboard acessível via IP público
- [ ] Credenciais Binance configuradas
- [ ] Auto-update funcionando
- [ ] Logs sem erros

## Suporte

Se precisar de ajuda:
1. Verifique logs: `sudo tail -f /var/log/r7_*.log`
2. Status serviços: `sudo supervisorctl status`
3. Recursos: `htop`
4. GitHub Issues: https://github.com/mlisboa17/App_Leonardo/issues
