# 🚀 Deploy na AWS - App Leonardo Bot

## Pré-requisitos

1. Conta AWS criada
2. AWS CLI instalado e configurado
3. Par de chaves SSH criado na AWS

---

## Opção 1: EC2 (Recomendado) - $8-10/mês

### Passo 1: Criar Instância EC2

1. Acesse AWS Console → EC2 → Launch Instance
2. Configure:
   - **Nome**: `app-leonardo-bot`
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
mkdir -p ~/app-leonardo
cd ~/app-leonardo
```

### Passo 4: Upload do Projeto

Do seu computador local:
```bash
# Compactar projeto (excluindo venv)
cd "c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\ScanKripto\r7_v1"
tar --exclude='venv_new' --exclude='__pycache__' --exclude='.git' -czvf app-leonardo.tar.gz .

# Enviar para AWS
scp -i "sua-chave.pem" app-leonardo.tar.gz ubuntu@SEU_IP:~/app-leonardo/
```

No servidor AWS:
```bash
cd ~/app-leonardo
tar -xzvf app-leonardo.tar.gz
rm app-leonardo.tar.gz
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
sudo cp deploy/aws/app-leonardo-bot.service /etc/systemd/system/
sudo cp deploy/aws/app-leonardo-dashboard.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviços
sudo systemctl enable app-leonardo-bot
sudo systemctl enable app-leonardo-dashboard

# Iniciar serviços
sudo systemctl start app-leonardo-bot
sudo systemctl start app-leonardo-dashboard
```

### Passo 8: Verificar Status

```bash
# Ver status
sudo systemctl status app-leonardo-bot
sudo systemctl status app-leonardo-dashboard

# Ver logs
sudo journalctl -u app-leonardo-bot -f
sudo journalctl -u app-leonardo-dashboard -f
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
sudo systemctl restart app-leonardo-bot

# Parar bot
sudo systemctl stop app-leonardo-bot

# Ver logs em tempo real
sudo journalctl -u app-leonardo-bot -f --no-pager

# Atualizar código
cd ~/app-leonardo
git pull origin master  # ou re-upload manual
sudo systemctl restart app-leonardo-bot
```

---

## Backup Automático para S3 (Opcional)

1. Criar bucket S3: `app-leonardo-backups`
2. Configurar IAM role para EC2
3. Adicionar ao crontab:

```bash
crontab -e
# Adicionar linha:
0 */6 * * * aws s3 sync ~/app-leonardo/data s3://app-leonardo-backups/data --exclude "*.pyc"
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

