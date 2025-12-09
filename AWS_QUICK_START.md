# 🚀 DEPLOY AWS - INÍCIO RÁPIDO (5 minutos)

## Passo 1: Criar EC2 na AWS (2 min)

1. Acesse: https://console.aws.amazon.com/ec2/
2. Clique: **Launch Instance**
3. Configure:
   - **Name:** `app-r7-trading`
   - **AMI:** Ubuntu 22.04 LTS
   - **Type:** t2.small ou t3.small
   - **Key pair:** Crie uma nova ou use existente
   - **Security Group - Inbound rules:**
     - SSH (22) - Seu IP
     - HTTP (80) - 0.0.0.0/0
     - Custom TCP (8503) - 0.0.0.0/0
   - **Storage:** 20 GB
4. Clique: **Launch instance**
5. Anote o **IP público** da instância

## Passo 2: Conectar via SSH (1 min)

```powershell
# Windows PowerShell
ssh -i "C:\caminho\para\sua-chave.pem" ubuntu@SEU_IP_AQUI

# Exemplo:
ssh -i "C:\Users\gabri\.ssh\r7-key.pem" ubuntu@54.123.45.67
```

## Passo 3: Deploy Automático (2 min)

Após conectar, cole estes comandos:

```bash
wget https://raw.githubusercontent.com/mlisboa17/App_Leonardo/master/deploy_aws.sh
chmod +x deploy_aws.sh
./deploy_aws.sh
```

**Aguarde 5-10 minutos** enquanto o script:
- Instala tudo automaticamente
- Configura serviços
- Inicia dashboard

## Passo 4: Acessar Dashboard

Abra no navegador:
```
http://SEU_IP_AQUI
```

Ou direto na porta 8503:
```
http://SEU_IP_AQUI:8503
```

**PRONTO! Sistema rodando na AWS! 🎉**

---

## Comandos Úteis

```bash
# Ver status
sudo supervisorctl status

# Ver logs
sudo tail -f /var/log/r7_dashboard.out.log

# Reiniciar
sudo supervisorctl restart all

# Atualizar código
cd /home/ubuntu/app_r7
git pull
sudo supervisorctl restart all
```

## Custos

- **EC2 t3.small:** ~$15/mês
- **Storage 20GB:** ~$2/mês
- **Total:** ~$17/mês

## Problemas?

Veja o guia completo: `DEPLOY_AWS_GUIA.md`
