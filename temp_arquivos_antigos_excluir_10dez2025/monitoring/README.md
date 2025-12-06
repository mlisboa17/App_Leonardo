# 📊 Monitoramento com Grafana - App Leonardo

## 🚀 Início Rápido

### 1. Pré-requisitos
- Docker Desktop instalado e rodando

### 2. Iniciar Grafana + InfluxDB
```bash
# Execute o script
INICIAR_GRAFANA.bat

# Ou manualmente:
cd monitoring
docker-compose up -d
```

### 3. Acessar Dashboards

| Serviço | URL | Usuário | Senha |
|---------|-----|---------|-------|
| **Grafana** | http://localhost:3000 | admin | leonardo123 |
| **InfluxDB** | http://localhost:8086 | admin | leonardo123 |

---

## 📈 Métricas Disponíveis

### Saldo
- 💰 USDT Disponível
- 💎 Valor em Crypto
- 🏦 Patrimônio Total

### Performance
- 📈 Lucro Diário
- ✅ Win Rate
- 📊 Total de Trades
- 💹 PnL por Trade

### Criptomoedas
- 🪙 Preços em tempo real
- 📉 Variação 24h
- 🥧 Distribuição do Portfólio

---

## 🔧 Configuração

### Integração com o Bot

O bot exporta métricas automaticamente. Para habilitar:

```python
from monitoring.metrics_exporter import get_metrics_exporter, export_all_metrics

# No loop do bot:
export_all_metrics(
    balance_data={'usdt': 10000, 'crypto_value': 5000, 'total': 15000},
    stats_data={'daily_pnl': 50, 'trades': 10, 'wins': 7, 'losses': 3, 'win_rate': 70},
    prices_data={'BTC': {'price': 95000, 'change_24h': 2.5}}
)
```

### Instalar Dependência

```bash
pip install influxdb-client
```

---

## 🐳 Comandos Docker

```bash
# Iniciar
cd monitoring
docker-compose up -d

# Parar
docker-compose down

# Ver logs
docker-compose logs -f

# Reiniciar
docker-compose restart

# Remover dados (reset completo)
docker-compose down -v
```

---

## 📊 Dashboard Personalizado

O dashboard vem pré-configurado com:

1. **Painéis de Status** (topo)
   - Saldo USDT
   - Lucro Diário
   - Win Rate
   - Total Trades

2. **Gráficos de Evolução** (meio)
   - Evolução do Saldo (tempo)
   - PnL por Trade (barras)

3. **Distribuição** (baixo)
   - Pizza do Portfólio
   - Preços das Criptos (tempo)

### Personalização

Acesse o Grafana e:
1. Clique no painel desejado
2. "Edit" para modificar
3. Ajuste queries, cores, thresholds
4. "Apply" e "Save dashboard"

---

## ⚠️ Troubleshooting

### Docker não inicia
```bash
# Verifique se Docker Desktop está rodando
docker ps

# Reinicie o Docker Desktop
```

### Grafana não conecta ao InfluxDB
```bash
# Verifique se InfluxDB está rodando
docker logs leonardo_influxdb

# Teste a conexão
curl http://localhost:8086/health
```

### Métricas não aparecem
1. Verifique se o bot está exportando dados
2. Confira o token no `metrics_exporter.py`
3. Verifique logs: `docker-compose logs -f`

---

## 🔐 Segurança

Para produção, altere:
- Senhas no `docker-compose.yml`
- Token no `metrics_exporter.py`
- Habilite HTTPS no Grafana

```yaml
# docker-compose.yml
environment:
  - GF_SECURITY_ADMIN_PASSWORD=sua_senha_forte
  - DOCKER_INFLUXDB_INIT_PASSWORD=sua_senha_forte
  - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=seu_token_seguro
```
