# ✅ PORTA ALTERADA - 8000 → 8001

## 🔄 Mudança Realizada

A porta do backend FastAPI foi alterada de **8000** para **8001** para evitar conflitos.

---

## 📝 Arquivos Atualizados

### ✅ Código
1. **`backend/config.py`**
   - `API_PORT: int = 8001` (era 8000)

2. **`frontend/dashboard_v2.py`**
   - `BACKEND_URL = "http://localhost:8001"` (era 8000)

3. **`frontend/dashboard.py`**
   - `API_URL = "http://localhost:8001"` (era 8000)
   - `WS_URL = "ws://localhost:8001/ws"` (era 8000)

### ✅ Scripts
4. **`START_V2.bat`**
   - Documentação atualizada com porta 8001

### ✅ Documentação (10 arquivos)
5. **`README_v2.md`**
6. **`QUICK_START.md`**
7. **`RESUMO_V2.txt`**
8. **`LIMPEZA.md`**
9. **`DASHBOARD_V2_GUIDE.md`**
10. **`BOT_README.md`**
11. **`RESUMO_EXECUTIVO.md`**
12. **`ARQUITETURA.md`**

---

## 🚀 Novas URLs

### Backend (FastAPI)
- **API**: http://localhost:8001
- **Docs**: http://localhost:8001/docs
- **WebSocket**: ws://localhost:8001/ws

### Frontend (Plotly Dash)
- **Dashboard**: http://localhost:8050 (sem mudança)

---

## 🎯 Como Usar

### 1. Iniciar Sistema
```powershell
.\START_V2.bat
```

### 2. Acessos
- **Dashboard**: http://localhost:8050
- **API Docs**: http://localhost:8001/docs
- **API Status**: http://localhost:8001/api/status

---

## 🔍 Verificação

### Testar Backend
```powershell
# Abra navegador em:
http://localhost:8001/docs
```

### Testar Conexão do Frontend
```powershell
# Dashboard deve conectar automaticamente
http://localhost:8050
```

Se o dashboard mostrar dados, significa que está conectado com sucesso ao backend na porta 8001!

---

## ⚙️ Configuração Manual (se necessário)

### Mudar para Outra Porta

Se precisar usar outra porta diferente, edite:

**backend/config.py:**
```python
API_PORT: int = 8001  # Mude para porta desejada
```

**frontend/dashboard_v2.py:**
```python
BACKEND_URL = "http://localhost:8001"  # Mude aqui também
```

---

## ✅ Checklist

- [x] Porta alterada em `backend/config.py`
- [x] URL atualizada em `frontend/dashboard_v2.py`
- [x] URL atualizada em `frontend/dashboard.py`
- [x] WebSocket URL atualizada
- [x] START_V2.bat atualizado
- [x] Toda documentação atualizada (10 arquivos)
- [x] Diagramas de arquitetura atualizados

---

## 🎉 PRONTO!

O sistema agora usa a porta **8001** para o backend.

Execute `.\START_V2.bat` e tudo funcionará normalmente! 🚀
