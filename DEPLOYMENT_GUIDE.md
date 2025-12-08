# 🚀 GUIA DE DEPLOYMENT - RESTART AUTOMÁTICO E OBSERVABILIDADE

## PRÉ-REQUISITOS

```bash
# Dependências Python necessárias
pip install fastapi
pip install uvicorn
pip install pydantic
pip install python-dotenv
pip install pyyaml
```

## VERIFICAÇÃO PRÉ-DEPLOYMENT

### 1. Validar Estrutura de Arquivos

```bash
# Verificar arquivos criados/modificados
ls -la src/audit.py               # ✅ Novo
ls -la src/observability.py       # ✅ Novo
ls -la src/coordinator.py         # ✅ Modificado
ls -la backend/routes/audit_routes.py  # ✅ Novo
ls -la SECURITY_REVIEW.py         # ✅ Novo
ls -la COMPLETION_SUMMARY.md      # ✅ Novo
```

### 2. Validar Importações

```python
# Testar se todas as importações funcionam
python -c "from src.audit import get_audit_logger; print('✅ Auditoria OK')"
python -c "from src.observability import get_metrics; print('✅ Observabilidade OK')"
python -c "from src.coordinator import BotCoordinator; print('✅ Coordenador OK')"
```

### 3. Criar Diretórios Necessários

```bash
# Criar diretórios para auditoria
mkdir -p data/audit

# Criar diretórios para métricas
mkdir -p data/metrics

# Criar diretórios para logs
mkdir -p logs
```

### 4. Executar Testes

```bash
# Executar testes E2E
pytest src/tests/test_e2e_restart_audit.py -v

# Verificar cobertura
pytest src/tests/test_e2e_restart_audit.py --cov=src --cov-report=html
```

## VARIÁVEIS DE AMBIENTE (.env)

Verificar que o arquivo `config/.env` contém:

```bash
# Exchange (Testnet ou Produção)
BINANCE_TESTNET_API_KEY=seu_key_testnet
BINANCE_TESTNET_API_SECRET=seu_secret_testnet

BINANCE_API_KEY=seu_key_producao
BINANCE_API_SECRET=seu_secret_producao

# Logging
LOG_LEVEL=INFO

# Auditoria
AUDIT_ENABLED=true
AUDIT_DIR=data/audit

# Observabilidade
METRICS_ENABLED=true
METRICS_DIR=data/metrics
```

## INICIALIZAÇÃO DO SISTEMA

### Método 1: Python Direto

```bash
# Iniciar coordenador
python src/coordinator.py

# Esperado:
# ===========================================================
# 🎖️  COORDENADOR MULTI-BOT - R7 TRADING BOT API
# ===========================================================
# 📊 Bots ativos: 4
# ✅ Coordenador inicializado com sucesso!
```

### Método 2: FastAPI com Uvicorn

```bash
# Terminal 1 - API Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Esperado:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete

# Terminal 2 - Frontend React
cd frontend-react
npm run dev

# Esperado:
#   VITE v4.x.x  ready in xxx ms
#   ➜  Local:   http://localhost:5173/
```

### Método 3: Docker (Opcional)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build e run
docker build -t r7-bot .
docker run -p 8000:8000 -v $(pwd)/data:/app/data -v $(pwd)/config/.env:/app/config/.env r7-bot
```

## VERIFICAÇÃO PÓS-INICIALIZAÇÃO

### 1. Verificar Auditoria

```bash
# Procurar arquivo de auditoria criado
ls -la data/audit/audit_*.jsonl

# Verificar conteúdo
head -5 data/audit/audit_YYYYMMDD_HHMMSS.jsonl
# Esperado: {"timestamp": "...", "event_type": "...", "severity": "...", ...}
```

### 2. Verificar Coordenador

```bash
# Procurar arquivo de estado
ls -la data/coordinator_stats.json

# Verificar conteúdo
cat data/coordinator_stats.json | jq .
# Esperado: { "total_pnl": 0, "bots": {...}, "last_update": "..." }
```

### 3. Testar Endpoints da API

```bash
# Health check
curl http://localhost:8000/health
# Esperado: {"status": "healthy", "timestamp": "..."}

# Listar eventos de auditoria
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/audit/events?limit=10
# Esperado: {"success": true, "data": {"events": [...], "total": X}}

# Sumário de auditoria
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/audit/events/summary
# Esperado: {"success": true, "data": {"by_type": {...}, "by_severity": {...}, ...}}
```

### 4. Testar Restart via API

```bash
# Restart um bot
curl -X POST http://localhost:8000/api/actions/restart-bot \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"bot_type": "bot_estavel", "reason": "test"}'

# Esperado: {"success": true, "message": "..."}

# Verificar logs
tail -f logs/coordinator.log
# Esperado: 
# [RESTART] Solicitado reinício do bot bot_estavel (razão: test)
# [WATCHER] Ação detectada: restart target=bot_estavel
# [RESTART] Bot bot_estavel reiniciado com sucesso
```

## MONITORAMENTO CONTÍNUO

### Logs em Tempo Real

```bash
# Terminal 1 - Logs do Coordenador
tail -f logs/coordinator.log

# Terminal 2 - Logs de Auditoria
tail -f data/audit/audit_*.jsonl | jq .

# Terminal 3 - Logs da API
tail -f logs/api.log
```

### Métricas

```python
# Script de monitoramento
from src.observability import get_metrics
import json
import time

metrics = get_metrics()

while True:
    summary = metrics.get_summary()
    print("\n" + "="*60)
    print(f"Timestamp: {summary['timestamp']}")
    print(f"Restarts: {summary['restarts']['successful']}/{summary['restarts']['total']} "
          f"({summary['restarts']['success_rate']:.1f}%)")
    print(f"Avg Restart Duration: {summary['restarts']['avg_duration_ms']:.0f}ms")
    print(f"Total Errors: {summary['errors']['total']}")
    print("="*60)
    time.sleep(60)
```

## TROUBLESHOOTING

### Problema: Auditoria não está sendo registrada

**Solução:**
```bash
# Verificar se diretório existe
mkdir -p data/audit

# Verificar permissões
chmod 755 data/audit

# Reiniciar coordenador
# Verificar logs
tail logs/coordinator.log | grep -i audit
```

### Problema: Restart lento

**Análise:**
```python
from src.observability import get_metrics

metrics = get_metrics()
summary = metrics.get_summary()

# Verificar duração média
print(f"Avg duration: {summary['restarts']['avg_duration_ms']}ms")

# Se > 3000ms, verificar:
# 1. Recarregamento de config
# 2. Reinicialização de estratégia
# 3. Latência de disco
```

### Problema: Memory leak

**Solução:**
```bash
# Monitorar uso de memória
watch -n 1 'ps aux | grep coordinator'

# Se crescer continuamente:
# 1. Limitar tamanho do cache de auditoria
# 2. Implementar rotação de logs
# 3. Adicionar garbage collection
```

### Problema: Conflitos de port

**Solução:**
```bash
# Encontrar processo usando port 8000
lsof -i :8000
# Matar processo
kill -9 <PID>

# Usar port diferente
uvicorn backend.main:app --port 8001
```

## BACKUP E RECOVERY

### Backup Regular

```bash
#!/bin/bash
# backup.sh - Executar diariamente via cron

BACKUP_DIR="data/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup de auditoria
cp -r data/audit $BACKUP_DIR/

# Backup de estado
cp data/coordinator_stats.json $BACKUP_DIR/

# Backup de configuração
cp -r config $BACKUP_DIR/

# Comprimir
tar -czf "data/backups/backup_$(date +%Y%m%d_%H%M%S).tar.gz" $BACKUP_DIR

# Limpar backups antigos (>30 dias)
find data/backups -name "backup_*.tar.gz" -mtime +30 -delete
```

### Recovery

```bash
# Restaurar de backup
tar -xzf data/backups/backup_YYYYMMDD_HHMMSS.tar.gz -C data/

# Reiniciar sistema
python src/coordinator.py
```

## CHECKLIST PRÉ-PRODUÇÃO

- [ ] Todos os arquivos criados/modificados estão em lugar
- [ ] Importações validadas
- [ ] Diretórios necessários criados
- [ ] Testes E2E passando
- [ ] .env configurado corretamente
- [ ] Auditoria funcional
- [ ] Métricas sendo coletadas
- [ ] UI funcionando
- [ ] Endpoints API testados
- [ ] Rate limiting implementado
- [ ] Backup/recovery testado
- [ ] Logs sendo rotacionados
- [ ] Alertas configurados

## ESCALABILIDADE FUTURA

Para lidar com maior volume:

1. **Auditoria:**
   - Mover para banco de dados (PostgreSQL)
   - Implementar índices
   - Arquivar eventos antigos

2. **Métricas:**
   - Integrar com Prometheus
   - Adicionar Grafana para visualização
   - Usar InfluxDB para series temporais

3. **API:**
   - Adicionar cache com Redis
   - Rate limiting com FastAPI-limiter
   - Load balancing com Nginx

4. **Logging:**
   - Stack ELK (Elasticsearch, Logstash, Kibana)
   - Splunk ou CloudWatch

---

**Criado:** 7 de Dezembro de 2025  
**Última atualização:** 2025-12-07
