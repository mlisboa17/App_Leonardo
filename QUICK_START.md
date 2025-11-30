# 🚀 Quick Start - App Leonardo v2.0

## 🎯 Sistema Configurado

- ✅ Backend FastAPI (assíncrono)
- ✅ Frontend Plotly Dash (gráficos profissionais)
- ✅ PostgreSQL (banco de dados)
- ✅ Redis (cache)
- ✅ **8 criptomoedas de alta liquidez**: BTC, ETH, SOL, BNB, XRP, LINK, DOGE, LTC

---

## Opção 1: Com Docker (Mais Fácil)

### 1. Instale Docker Desktop
https://www.docker.com/products/docker-desktop/

### 2. Execute o setup
```powershell
.\SETUP_DOCKER.bat
```

### 3. Inicie o sistema
```powershell
.\START_V2.bat
```

### 4. Acesse
- **Dashboard**: http://localhost:8050
- **API Docs**: http://localhost:8001/docs

---

## Opção 2: Sem Docker (Manual)

### 1. Instale PostgreSQL
```powershell
choco install postgresql
```

Configure:
- User: leonardo
- Password: trading123
- Database: trading_bot

### 2. Instale Redis
```powershell
choco install redis-64
```

### 3. Instale dependências Python
```powershell
pip install -r requirements_new.txt
```

### 4. Inicie o sistema
```powershell
.\START_V2.bat
```

---

## ⚠️ Solução de Problemas

### PostgreSQL não conecta
```powershell
# Verifique se está rodando
docker ps

# Reinicie
docker restart postgres-trading
```

### Redis não conecta
```powershell
# Verifique
docker ps

# Reinicie
docker restart redis-trading
```

### Erro de importação
```powershell
# Reinstale dependências
pip install --upgrade -r requirements_new.txt
```

---

## 📊 Monitoramento

### Ver logs do backend
Acompanhe o terminal do FastAPI

### Ver banco de dados
```powershell
# Conecte ao PostgreSQL
docker exec -it postgres-trading psql -U leonardo -d trading_bot

# Ver trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;
```

### Ver Redis
```powershell
# Conecte ao Redis
docker exec -it redis-trading redis-cli

# Ver chaves
KEYS *

# Ver status
GET bot:status
```

---

**🎯 Sistema pronto para operar!**
