#!/bin/bash

# Script para sincronizar dashboards atualizados para EC2

REMOTE_USER="ubuntu"
REMOTE_HOST="18.230.59.118"
SSH_KEY="/home/ubuntu/r7_trade_key.pem"
REMOTE_PATH="/home/ubuntu/App_Leonardo"

echo "🔄 Sincronizando dashboards para EC2..."

# Sincronizar arquivo PnL detalhado
echo "📤 Enviando 04_pnl_detalhado.py..."
scp -i "$SSH_KEY" \
    frontend/pages/04_pnl_detalhado.py \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/frontend/pages/"

echo "✅ Dashboard PnL sincronizado!"
echo "📊 Acesse: http://18.230.59.118:8501"
echo ""
echo "Páginas disponíveis:"
echo "  - 04_pnl_detalhado.py (Nova!) - PnL Dia/Mês/Geral com diagnóstico"
echo "  - 01_positions_dashboard.py - Posições com gráficos"
echo "  - 02_capital_distribution.py - Distribuição de capital"
echo "  - 03_system_monitoring.py - Monitoramento do sistema"
