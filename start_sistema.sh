#!/bin/bash
# Script para iniciar o sistema completo com 5 bots

cd /home/ubuntu/App_Leonardo

echo "========================================"
echo "🚀 INICIANDO SISTEMA COMPLETO"
echo "========================================"

# Parar qualquer instância anterior
echo "Parando instâncias anteriores..."
pkill -f main_multibot.py 2>/dev/null
sleep 2

# Limpar nohup
rm -f nohup.out

# Iniciar bot
echo "Iniciando bot principal..."
nohup ./venv/bin/python main_multibot.py > logs/bot.log 2>&1 &
BOT_PID=$!

sleep 3

# Verificar
if ps -p $BOT_PID > /dev/null; then
    echo "✅ Bot iniciado com sucesso (PID: $BOT_PID)"
else
    echo "❌ Erro ao iniciar bot"
    tail -20 logs/bot.log
    exit 1
fi

# Reiniciar Streamlit se necessário
pkill -f "streamlit run" 2>/dev/null
sleep 2

echo "Iniciando Streamlit..."
nohup ./venv/bin/streamlit run frontend/dashboard_multibot.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    > logs/streamlit.log 2>&1 &

sleep 3

echo ""
echo "========================================"
echo "✅ SISTEMA INICIADO"
echo "========================================"
echo ""
echo "📊 Bots ativos:"
echo "  ✅ Bot Estável - \$39.15/trade"
echo "  ✅ Bot Médio - \$39.15/trade"
echo "  ✅ Bot Volátil - \$39.15/trade"
echo "  ✅ Bot Meme - \$30.00/trade"
echo "  ✅ Unico Bot - \$50.00/trade"
echo ""
echo "📈 Dashboard: http://18.230.59.118:8501"
echo "📍 Bot PID: $BOT_PID"
echo ""
echo "Ver logs:"
echo "  tail -f logs/bot.log"
echo "  tail -f logs/streamlit.log"
echo ""
