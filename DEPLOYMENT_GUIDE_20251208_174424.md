# 🚀 Guia de Deployment R7 Trading Bot

## 📋 Informações do Deploy

- **Data**: 2025-12-08 17:44:25
- **Arquivo**: r7-trading-bot-20251208_174424.zip
- **Região AWS**: us-east-1
- **EC2 IP**: 18.230.59.118

## 🔑 Pré-requisitos

1. **Chave PEM (.pem)**
   - Arquivo: seu-pem-key.pem
   - Permissões: chmod 400 seu-pem-key.pem

2. **Ferramentas**
   - SSH Client
   - SCP ou WinSCP
   - Terminal/PowerShell

## 📦 Conteúdo do Deploy

```
r7-trading-bot/
├── config/                  # Configurações dos bots
├── data/                    # Dados persistentes
├── frontend/               # Dashboard Streamlit
├── requirements.txt        # Dependências Python
├── main_multibot.py       # Bot principal
├── adaptive_bot_system.py # Sistema adaptativo
├── ai_orchestrator.py     # Orquestrador IA
└── .env                   # Variáveis de ambiente
```

## 🚀 Passo a Passo

### 1. Upload do Arquivo

**Via SCP (Recomendado):**
```bash
scp -i "seu-pem-key.pem" \
    "r7-trading-bot-20251208_174424.zip" \
    ubuntu@18.230.59.118:/tmp/
```

**Via WinSCP (GUI):**
- Abra WinSCP
- New Site → SFTP
- Host: 18.230.59.118
- User: ubuntu
- Private Key: seu-pem-key.pem
- Drag & drop o arquivo

### 2. Conectar no EC2

```bash
ssh -i "seu-pem-key.pem" ubuntu@18.230.59.118
```

### 3. Descompactar

```bash
cd /tmp
unzip -q r7-trading-bot-20251208_174424.zip
cd r7-trading-bot
```

### 4. Criar Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

### 5. Configurar Credenciais

```bash
nano .env
```

Adicione:
```
BINANCE_API_KEY=seu_api_key
BINANCE_API_SECRET=seu_api_secret
TELEGRAM_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
AWS_ACCESS_KEY_ID=seu_aws_key
AWS_SECRET_ACCESS_KEY=seu_aws_secret
```

### 6. Iniciar Serviços

**Em terminais separados:**

Terminal 1 - Dashboard:
```bash
source venv/bin/activate
streamlit run frontend/dashboard_multibot.py --server.port 8501 --server.address 0.0.0.0
```

Terminal 2 - AI Orchestrator:
```bash
source venv/bin/activate
python ai_orchestrator.py
```

Terminal 3 - Main Bot:
```bash
source venv/bin/activate
python main_multibot.py
```

### 7. Acessar

- Dashboard: http://18.230.59.118:8501
- API: http://18.230.59.118:8000

## 📊 Monitoramento

```bash
# Logs em tempo real
tail -f logs/coordinator.log

# Verificar espaço em disco
df -h

# Verificar uso de memória
free -h

# Processos do bot
ps aux | grep python
```

## 🔧 Troubleshooting

### Porta já em uso
```bash
lsof -i :8501
kill -9 <PID>
```

### Erro de dependências
```bash
pip install --upgrade -r requirements.txt
```

### Problema com permissões
```bash
chmod +x *.py
```

## 🔐 Segurança

1. ✅ Mude a senha padrão do ubuntu
2. ✅ Configure firewall (allow only necessary ports)
3. ✅ Use PM2 ou Supervisor para gerenciar processos
4. ✅ Backups diários de data/
5. ✅ Monitore logs constantemente

## 📞 Suporte

- Verifique logs em `/logs/`
- Consulte `config/bots_config.yaml`
- Teste conexão com Binance antes de operar

