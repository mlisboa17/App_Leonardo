# 📊 Estratégia de Banco de Dados

## Status Atual - v1.0 (JSON)

### ✅ Implementado
- **JSON Files** para persistência de dados (GRÁTIS!)
- Audit logs em JSONL (append-only)
- Métricas em JSON
- Configurações em YAML
- Usuários em JSON

### 📂 Estrutura de Dados Atual
```
data/
├── app_leonardo.db              # SQLite (vazio, reservado)
├── users.json                   # Usuários e senhas (hashed)
├── all_trades_history.json      # Histórico de trades
├── multibot_positions.json      # Posições atuais
├── daily_stats.json             # Estatísticas diárias
├── control_log.json             # Log de ações
├── audit/
│   └── audit_*.jsonl            # Eventos em JSONL (v1.1)
├── ai/
│   └── ai_state.json            # Estado da IA
└── backups/                     # Backups automáticos
```

### ⚡ Vantagens JSON (Atual - GRÁTIS!)
- ✅ **ZERO CUSTO** - Sem servidor externo
- ✅ Sem dependências de BD externo
- ✅ Fácil de versionar (Git)
- ✅ Simples de fazer backup (tar/zip)
- ✅ Funciona offline
- ✅ Zero overhead de infra
- ✅ Funciona perfeitamente em AWS EC2 t3.micro

### ⚠️ Limitações JSON
- ❌ Não é escalável (>1GB de dados)
- ❌ Sem queries SQL
- ❌ Sem índices
- ❌ Concorrência limitada
- ❌ Sem ACID completo
- ❌ Leitura lenta em grandes datasets

---

## 🆓 Opções GRATUITAS para v2.0

### Opção 1: SQLite (MAIS FÁCIL - GRÁTIS!)

**O que é:**
- Banco de dados leve embutido
- Já vem com Python
- Arquivo único (app_leonardo.db)
- Funciona em qualquer lugar

**Vantagens:**
- ✅ ZERO CUSTO
- ✅ Zero dependências externas
- ✅ Fácil migração de JSON
- ✅ Funciona na AWS EC2
- ✅ Perfeito para aplicações médias
- ✅ Backup simples (copiar arquivo)

**Limitações:**
- ❌ Concorrência limitada (OK para bot único)
- ❌ Não é ideal para milhões de registros

**Setup:**
```python
# Simplesmente criar conexão
import sqlite3

db = sqlite3.connect('data/app_leonardo.db')
cursor = db.cursor()

# Criar tabelas
cursor.execute('''
    CREATE TABLE trades (
        id INTEGER PRIMARY KEY,
        symbol TEXT,
        entry_price REAL,
        exit_price REAL,
        pnl REAL,
        entry_time TEXT,
        exit_time TEXT
    )
''')
db.commit()
```

**Custo:** **$0/mês** ✅

---

### Opção 2: PostgreSQL com Render.com (GRÁTIS + SEM CARTÃO!)

**O que é:**
- PostgreSQL gerenciado na nuvem
- Tier gratuito: 400 horas/mês (suficiente!)
- Sem cartão de crédito
- Banco de dados na nuvem

**Vantagens:**
- ✅ ZERO CUSTO (plano grátis)
- ✅ Sem cartão de crédito necessário
- ✅ PostgreSQL completo
- ✅ Backups automáticos
- ✅ SSL/TLS incluído
- ✅ Fácil setup

**Limitações:**
- ⚠️ Free tier: 400 horas/mês (OK para desenvolvimento)
- ⚠️ 256MB RAM
- ⚠️ Não é ideal para produção 24/7

**Setup:**
```
1. Ir para render.com
2. Sign up (GitHub grátis)
3. Create → PostgreSQL
4. Plano: Free
5. Copiar connection string
6. Usar em requirements: psycopg2
```

**Custo:** **$0/mês** ✅

---

### Opção 3: MongoDB Atlas (GRÁTIS - BANCO NÃO-SQL)

**O que é:**
- Banco NoSQL na nuvem
- 512MB de espaço gratuito
- Sem cartão de crédito

**Vantagens:**
- ✅ ZERO CUSTO
- ✅ 512MB espaço grátis
- ✅ JSON nativo
- ✅ Fácil para dados não-estruturados
- ✅ Backups automáticos

**Limitações:**
- ⚠️ Requer internet
- ⚠️ 512MB limite (você pode atingir)
- ⚠️ Menos estruturado que SQL

**Setup:**
```
1. Ir para mongodb.com
2. Sign up grátis
3. Create cluster (free)
4. Connect string
5. Usar pymongo
```

**Custo:** **$0/mês** ✅

---

### Opção 4: AWS RDS Free Tier (GRÁTIS - 12 MESES!)

**O que é:**
- PostgreSQL gerenciado na AWS
- Grátis por 12 meses
- db.t3.micro
- 20GB armazenamento

**Vantagens:**
- ✅ GRÁTIS os primeiros 12 meses
- ✅ PostgreSQL completo
- ✅ Mesmo datacenter que EC2 (rápido)
- ✅ Backups automáticos
- ✅ Fácil escalar depois

**Limitações:**
- ⚠️ Free tier expira em 12 meses
- ⚠️ ~$10-15/mês depois do free tier
- ⚠️ Precisa de cartão de crédito

**Setup:**
```bash
# AWS Console → RDS → Create Database
# PostgreSQL 15
# db.t3.micro (free tier)
# 20GB (free tier)

# Conectar da EC2
psql -h seu-rds-endpoint.com \
     -U admin \
     -d app_leonardo
```

**Custo:** **$0/mês (primeiros 12 meses)** → ~$15/mês depois

---

## 🎯 RECOMENDAÇÃO: Qual Usar?

### Para AGORA (v1.0):
```
✅ MANTER JSON + SQLite
- Zero custo
- Zero dependências
- Funciona perfeitamente
- Fácil backup
- Sem complicações
```

### Para v1.5 (Quando quiser BD):
```
✅ USAR SQLite
- Upgrade mínimo
- Grátis
- Sem servidor externo
- Mesmo arquivo para backup
- Ideal transição JSON → Banco de dados
```

### Para v2.0 (Quando escalar):
```
✅ USAR Render.com (PostgreSQL grátis)
ou
✅ USAR AWS RDS Free Tier (12 meses grátis)
```

---

## 💡 Estratégia de Migração (SEM CUSTO)

```
HOJE (v1.0):
├─ JSON Files (GRÁTIS)
│  ├─ users.json
│  ├─ trades.json
│  ├─ positions.json
│  └─ daily_stats.json
│
MÊS 1-2 (v1.5):
├─ Adicionar SQLite (GRÁTIS)
│  └─ app_leonardo.db (arquivo local)
│  └─ Scripts para migrar JSON → SQLite
│
MÊS 3-6 (v2.0):
├─ Adicionar PostgreSQL (GRÁTIS)
│  └─ Render.com OR AWS RDS Free Tier
│  └─ Scripts para migrar SQLite → PostgreSQL
│
DEPOIS (Quando escalar):
└─ Pagar apenas se atingir limites
   (~$15/mês PostgreSQL ou manter grátis)
```

---

## 📊 Comparação de Custo

| BD | Setup | v1.0 | v2.0 | 12m+ |
|----|----|------|------|------|
| **JSON** | 0 min | **$0** | Não | Não |
| **SQLite** | 5 min | **$0** | **$0** | **$0** |
| **Render.com** | 10 min | N/A | **$0** | **$7-10/mês** |
| **AWS RDS** | 15 min | N/A | **$0** | **$15+/mês** |
| **MongoDB Atlas** | 10 min | N/A | **$0** | **$15+/mês** |

✅ **ESCOLHA**: Manter JSON + SQLite = SEMPRE GRÁTIS!

---

## 🔄 Migração JSON → SQLite (Quando quiser)

```python
# Script simples de migração
import json
import sqlite3

# Ler JSON
with open('data/all_trades_history.json') as f:
    trades = json.load(f)

# Criar SQLite
db = sqlite3.connect('data/app_leonardo.db')
cursor = db.cursor()

# Inserir dados
for trade in trades:
    cursor.execute('''
        INSERT INTO trades 
        (symbol, entry_price, exit_price, pnl)
        VALUES (?, ?, ?, ?)
    ''', (trade['symbol'], trade['entry'], 
          trade['exit'], trade['pnl']))

db.commit()
db.close()

print(f"✅ Migrados {len(trades)} trades para SQLite")
```

---

## ✅ CONCLUSÃO

### Para AGORA (v1.0):
**✅ USE JSON - É GRÁTIS E FUNCIONA PERFEITAMENTE!**

```
Custo: $0/mês
Banco: JSON Files (já funciona)
Quando escalar: Migrar para SQLite
Depois: Opções gratuitas (Render, AWS RDS Free)
```

### Seu Stack Gratuito:
```
Frontend:     React (grátis)
Backend:      FastAPI (grátis)
Database:     JSON (grátis) → SQLite (grátis)
Servidor:     AWS EC2 t3.micro ($0/12m, depois $5-8/mês)
Armazenamento: S3 Backup (~$0.03/mês)
────────────────────────────────────
TOTAL:        $1-5/mês por 12 meses!
```

Não precisa gastar NADA com banco de dados! 🎉

---

## 🚀 Próximos Passos

### Agora:
- ✅ Deploy em AWS com JSON (já pronto)
- ✅ Usar arquivos JSON que já tem

### v1.5 (Quando quiser melhorar):
- ⏳ Adicionar SQLite (100% grátis)
- ⏳ Migrar dados quando atingir ~100MB

### v2.0+ (Quando escalar muito):
- ⏳ PostgreSQL Render.com OU AWS RDS
- ⏳ Ambos com opções gratuitas!

**Bottom line**: Seu bot pode rodar SEM CUSTO por TEMPO ILIMITADO! 🎯

### 📋 Plano de Migração (v2.0)

#### Fase 1: Preparar BD
```sql
-- Criar database
CREATE DATABASE app_leonardo;

-- Criar schemas
CREATE SCHEMA trading;
CREATE SCHEMA audit;
CREATE SCHEMA metrics;

-- Tabelas principais
CREATE TABLE trading.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE TABLE trading.bots (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    bot_type VARCHAR(50),
    enabled BOOLEAN DEFAULT FALSE,
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE trading.positions (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES trading.bots(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10),
    entry_price DECIMAL(20,8),
    quantity DECIMAL(20,8),
    entry_time TIMESTAMP,
    current_price DECIMAL(20,8),
    pnl DECIMAL(20,8),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE trading.trades (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES trading.bots(id),
    symbol VARCHAR(20) NOT NULL,
    entry_price DECIMAL(20,8),
    exit_price DECIMAL(20,8),
    quantity DECIMAL(20,8),
    pnl DECIMAL(20,8),
    pnl_percent DECIMAL(10,4),
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabelas de Audit
CREATE TABLE audit.events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20),
    source VARCHAR(100),
    target VARCHAR(100),
    action VARCHAR(255),
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    user_id INTEGER REFERENCES trading.users(id)
);

-- Tabelas de Métricas
CREATE TABLE metrics.performance (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES trading.bots(id),
    metric_name VARCHAR(100),
    metric_value FLOAT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_positions_bot_id ON trading.positions(bot_id);
CREATE INDEX idx_positions_symbol ON trading.positions(symbol);
CREATE INDEX idx_trades_bot_id ON trading.trades(bot_id);
CREATE INDEX idx_trades_entry_time ON trading.trades(entry_time);
CREATE INDEX idx_audit_timestamp ON audit.events(timestamp);
CREATE INDEX idx_audit_event_type ON audit.events(event_type);
```

#### Fase 2: Setup da API
```python
# requirements_db.txt (novo)
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
python-dotenv==1.0.0

# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://user:password@localhost:5432/app_leonardo"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# backend/models.py
from sqlalchemy import Column, Integer, String, Float, JSONB, Timestamp, Boolean
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String)
    password_hash = Column(String)
    created_at = Column(Timestamp, default=datetime.utcnow)

class Bot(Base):
    __tablename__ = "bots"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    bot_type = Column(String)
    enabled = Column(Boolean, default=False)
    config = Column(JSONB)
    created_at = Column(Timestamp, default=datetime.utcnow)

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    bot_id = Column(Integer)
    symbol = Column(String, index=True)
    entry_price = Column(Float)
    exit_price = Column(Float)
    pnl = Column(Float)
    entry_time = Column(Timestamp, index=True)
    exit_time = Column(Timestamp)
```

#### Fase 3: Migrar Dados
```bash
# Script para migrar JSON → PostgreSQL
python migrate_json_to_postgres.py

# Verificar integridade
python validate_migration.py

# Backup do JSON (manter como backup)
tar -czf data_backup_json.tar.gz data/
```

#### Fase 4: Implementar Queries Otimizadas
```python
# Exemplo: listar trades do mês
@app.get("/api/trades/monthly")
async def get_monthly_trades(db: Session = Depends(get_db)):
    trades = db.query(Trade).filter(
        Trade.exit_time >= datetime(2025, 1, 1),
        Trade.exit_time < datetime(2025, 2, 1)
    ).order_by(Trade.exit_time.desc()).all()
    return trades

# Exemplo: listar posições ativas
@app.get("/api/positions/active")
async def get_active_positions(db: Session = Depends(get_db)):
    positions = db.query(Position).filter(
        Position.status == 'open'
    ).all()
    return positions
```

---

## ☁️ AWS RDS - Setup para v2.0

### Opção 1: RDS PostgreSQL (Recomendado)
```bash
# AWS Console
# RDS → Create Database → PostgreSQL 15

# Configuração
- Engine: PostgreSQL 15.x
- DB instance class: db.t3.micro (Free tier)
- Storage: 20GB gp3
- Multi-AZ: No (para economizar)
- Backup retention: 7 days
- Encryption: Enabled

# Custo mensal
- Compute: ~$10-15/mês
- Storage: ~$2-3/mês
- Data transfer: Grátis (VPC)
- TOTAL: ~$12-18/mês
```

### Opção 2: Aurora PostgreSQL (Mais caro, mas melhor)
```
Custo: ~$50-100/mês
Vantagens: Auto-scaling, read replicas, mais uptime
```

### Conexão da EC2 ao RDS
```bash
# .env na EC2
DATABASE_URL=postgresql://admin:senha_segura@app-leonardo-db.xxxxx.us-east-1.rds.amazonaws.com:5432/app_leonardo

# Testar conexão
psql -h app-leonardo-db.xxxxx.us-east-1.rds.amazonaws.com \
     -U admin \
     -d app_leonardo
```

---

## 🔒 Backup e Recuperação

### Backup JSON (Atual)
```bash
# Diário
0 2 * * * tar -czf ~/backups/data_$(date +\%Y\%m\%d).tar.gz ~/app-leonardo/data/
aws s3 sync ~/backups s3://app-leonardo-backups/
```

### Backup PostgreSQL (v2.0)
```bash
# RDS faz backup automático
# Manual backup (via AWS CLI)
aws rds create-db-snapshot \
  --db-instance-identifier app-leonardo-db \
  --db-snapshot-identifier app-leonardo-snapshot-$(date +%Y%m%d)
```

---

## 📊 Monitoramento

### Métricas Atuais (JSON)
- Tamanho dos arquivos
- Número de trades
- Posições ativas
- Uptime do bot

### Métricas Futuras (PostgreSQL + Prometheus)
```python
# Coletar métricas do PostgreSQL
query_count = "SELECT COUNT(*) FROM trades"
table_size = "SELECT pg_size_pretty(pg_total_relation_size('trades'))"
active_queries = "SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'"

# Expor em Prometheus
@app.get("/metrics")
async def metrics():
    return f"""
# HELP trades_total Total de trades
# TYPE trades_total counter
trades_total {trade_count}

# HELP db_size_bytes Tamanho da database
# TYPE db_size_bytes gauge
db_size_bytes {db_size_bytes}

# HELP active_connections Conexões ativas
# TYPE active_connections gauge
active_connections {active_conns}
"""
```

---

## 🎯 Timeline

| Fase | Tarefa | v1.0 | v1.1 | v2.0 |
|------|--------|------|------|------|
| Setup | Prod deploy | ✅ | ✅ | - |
| DB | JSON | ✅ | ✅ | - |
| Audit | JSONL logs | - | ✅ | Migrar → PostgreSQL |
| Observability | Métricas | - | ✅ | + Prometheus/Grafana |
| Backup | S3 automático | - | - | ✅ |
| Security | Rate limiting | - | - | ✅ |
| Replication | Read replicas | - | - | ✅ (Aurora) |

---

## 📞 Suporte

**v1.0 - Atual (JSON)**
- Consultar arquivos em `data/`
- Backups automáticos
- Sem queries SQL

**v2.0 - Planejado (PostgreSQL)**
- Queries SQL completas
- Índices automáticos
- Dashboards com Grafana
- Alertas baseados em thresholds

---

**Próximo passo**: Deploy atual em AWS (v1.0 com JSON)  
**Quando migrar**: Quando atingir 1GB de dados ou precisar de queries complexas  
**Sem urgência**: Sistema funciona bem com JSON por enquanto
