#!/bin/bash
# Script para iniciar o dashboard no EC2

echo "🔄 Parando processos antigos..."
pkill -9 -f streamlit
sleep 2

echo "🚀 Iniciando APP R7 Dashboard..."
cd ~/App_Leonardo
source venv/bin/activate

# Inicia dashboard
nohup streamlit run frontend/dashboard_multibot.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    > logs/dashboard.log 2>&1 &

sleep 3

# Verifica se está rodando
if pgrep -f streamlit > /dev/null; then
    echo "✅ Dashboard iniciado com sucesso!"
    echo "📊 Acesse: http://18.230.59.118:8501"
    ps aux | grep streamlit | grep -v grep
else
    echo "❌ Erro ao iniciar dashboard"
    echo "📋 Últimas linhas do log:"
    tail -20 logs/dashboard.log
fi
