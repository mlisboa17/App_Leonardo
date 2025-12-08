# 🚀 Deploy na AWS - R7 Trading Bot API

## Pré-requisitos

1. Conta AWS criada
2. AWS CLI instalado e configurado
3. Par de chaves SSH criado na AWS

---

## Opção 1: EC2 (Recomendado) - $8-10/mês

### Passo 1: Criar Instância EC2

1. Acesse AWS Console → EC2 → Launch Instance
2. Configure:
   - **Nome**: `r7-trading-bot`
   - **AMI**: Ubuntu 22.04 LTS
   - **Tipo**: t3.micro (Free Tier) ou t3.small
   - **Key pair**: Selecione ou crie uma
   - **Security Group**: 
     - SSH (22) - Seu IP
     - Custom TCP (8501) - 0.0.0.0/0 (Dashboard)
   - **Storage**: 20GB gp3

### Passo 2: Conectar via SSH

```bash
ssh -i "sua-chave.pem" ubuntu@SEU_IP_PUBLICO
```

### Passo 3: Instalar Dependências

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip git

# Criar diretório
mkdir -p ~/r7-trading-bot
cd ~/r7-trading-bot
```

### Passo 4: Upload do Projeto

Do seu computador local:
```bash
# Compactar projeto (excluindo venv)
cd "c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"
tar --exclude='venv_new' --exclude='__pycache__' --exclude='.git' -czvf r7-trading-bot.tar.gz .

# Enviar para AWS
scp -i "sua-chave.pem" r7-trading-bot.tar.gz ubuntu@SEU_IP:~/r7-trading-bot/
```

No servidor AWS:
```bash
cd ~/r7-trading-bot
tar -xzvf r7-trading-bot.tar.gz
rm r7-trading-bot.tar.gz
```

### Passo 5: Configurar Ambiente

```bash
# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements_new.txt
```

### Passo 6: Configurar Variáveis de Ambiente

```bash
# Criar arquivo .env (NÃO commitar no git!)
nano .env
```

Conteúdo do .env:
```
BINANCE_API_KEY=sua_api_key_aqui
BINANCE_API_SECRET=seu_secret_aqui
```

### Passo 7: Configurar Serviços Systemd

```bash
# Copiar arquivos de serviço
sudo cp deploy/aws/r7-trading-bot.service /etc/systemd/system/
sudo cp deploy/aws/r7-trading-dashboard.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviços
sudo systemctl enable r7-trading-bot
sudo systemctl enable r7-trading-dashboard

# Iniciar serviços
sudo systemctl start r7-trading-bot
sudo systemctl start r7-trading-dashboard
```

### Passo 8: Verificar Status

```bash
# Ver status
sudo systemctl status r7-trading-bot
sudo systemctl status r7-trading-dashboard

# Ver logs
sudo journalctl -u r7-trading-bot -f
sudo journalctl -u r7-trading-dashboard -f
```

### Passo 9: Acessar Dashboard

Abra no navegador:
```
http://SEU_IP_PUBLICO:8501
```

---

## Comandos Úteis

```bash
# Reiniciar bot
sudo systemctl restart r7-trading-bot

# Parar bot
sudo systemctl stop r7-trading-bot

# Ver logs em tempo real
sudo journalctl -u r7-trading-bot -f --no-pager

# Atualizar código
cd ~/r7-trading-bot
git pull origin master  # ou re-upload manual
sudo systemctl restart r7-trading-bot
```

---

## Backup Automático para S3 (Opcional)

1. Criar bucket S3: `r7-trading-bot-backups`
2. Configurar IAM role para EC2
3. Adicionar ao crontab:

```bash
crontab -e
# Adicionar linha:
0 */6 * * * aws s3 sync ~/r7-trading-bot/data s3://r7-trading-bot-backups/data --exclude "*.pyc"
```

---

## Custos Estimados

| Recurso | Custo/mês |
|---------|-----------|
| EC2 t3.micro | $8.50 |
| EBS 20GB | $1.60 |
| Transfer (baixo) | ~$1 |
| **TOTAL** | **~$11** |

💡 **Dica**: Use Reserved Instance (1 ano) para economizar 30-40%

---

## Segurança

⚠️ **IMPORTANTE**:
1. NUNCA commite API keys no git
2. Use Security Groups restritivos
3. Mantenha o sistema atualizado
4. Configure backups automáticos
5. Use MFA na conta AWS

