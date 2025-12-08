# 📊 Integrar ServerStatus no Dashboard

## Passo 1: Importar Componente

Abra: `frontend-react/src/pages/Dashboard.tsx`

Adicione no topo do arquivo (após outros imports):
```typescript
import { ServerStatus } from '../components/ServerStatus';
```

---

## Passo 2: Adicionar no JSX

No Dashboard, encontre a seção onde estão os cards principais e adicione:

**Localizar:**
```typescript
// Procure por algo como:
<div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
  {/* Cards de resumo */}
  <StatCard title="Saldo Total" ... />
  <StatCard title="P&L Hoje" ... />
  {/* ... outros cards ... */}
</div>
```

**Adicionar após os cards:**
```typescript
{/* Status do Servidor AWS */}
<div className="mt-8 mb-6">
  <h2 className="text-xl font-bold text-white mb-4">⚙️ Sistema</h2>
  <ServerStatus apiUrl={apiUrl} />
</div>
```

---

## Passo 3: Definir `apiUrl`

No seu Dashboard.tsx, garanta que tem:

```typescript
// Se não existir, adicione:
const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8080';
```

---

## Passo 4: Testar Localmente

```bash
# Terminal - frontend-react
npm start

# Deve aparecer o card "Servidor AWS" com status
# Se estiver rodando: ✅ Online
# Se não: ❌ Offline (esperado, pois não tem backend rodando)
```

---

## Passo 5: Em Produção (AWS)

Após fazer deploy na AWS:

**Editar:** `frontend-react/.env.production`
```
REACT_APP_API_URL=http://seu-ip-publico-aws:8080
REACT_APP_WS_URL=ws://seu-ip-publico-aws:8080
```

Depois fazer build e deploy:
```bash
npm run build
# Copiar dist/ para o servidor nginx/Apache
```

---

## ✅ O que o Componente Mostra

```
┌─────────────────────────────────────────┐
│ ⚙️  Servidor AWS                         │
│ ✅ Online · v1.0.0                      │
├─────────────────────────────────────────┤
│ ⏱️  Uptime          │  💾 Disco Usado     │
│ 2h 15m              │  45%                │
├─────────────────────────────────────────┤
│ ⚙️  Status Config   │  📂 Diretório Data  │
│ ✅ OK              │  ✅ Existe          │
├─────────────────────────────────────────┤
│ Host: 0.0.0.0:8080                      │
│ Última verificação: 14:30:45             │
└─────────────────────────────────────────┘
```

---

## 🎨 Customizar Aparência

Se quiser mudar cores, edite `ServerStatus.tsx`:

```typescript
// Cores quando online (verde)
<div className="bg-gray-800 rounded-lg p-4 border border-green-700 bg-green-900/20">
// ↓ Mude para:
<div className="bg-gray-800 rounded-lg p-4 border border-blue-700 bg-blue-900/20">

// Ou ajuste o tailwind:
'border-green-700' → 'border-blue-700'
'bg-green-900/20' → 'bg-blue-900/20'
'text-green-400' → 'text-blue-400'
'text-green-300' → 'text-blue-300'
```

---

## 🔄 Auto-refresh

O componente faz verificação a cada 30 segundos. Para mudar:

```typescript
// Linha ~43
const interval = setInterval(checkHealth, 30000)  // ← Mudar aqui
// 30000 = 30 segundos
// Para 10 segundos: 10000
// Para 1 minuto: 60000
```

---

## 📱 Responsivo

Funciona em todos os tamanhos de tela (mobile, tablet, desktop).

---

## 🐛 Debug

Se não está aparecendo, verifique:

1. **Browser console** (F12 → Console)
   - Veja se tem erros
   - Procure por logs do ServerStatus

2. **Verificar API**
   ```powershell
   curl http://localhost:8080/health
   ```

3. **Verificar importação**
   ```typescript
   // Testar se o arquivo existe
   import { ServerStatus } from '../components/ServerStatus';
   ```

---

## 📊 Próximos Passos

- [ ] Integrar no Dashboard principal
- [ ] Testar em localhost
- [ ] Deploy em AWS
- [ ] Monitorar status em produção
- [ ] (v2.0) Adicionar Prometheus/Grafana para mais métricas

---

**Status**: ✅ Pronto para usar  
**Arquivo**: `frontend-react/src/components/ServerStatus.tsx`
