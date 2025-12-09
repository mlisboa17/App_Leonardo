#!/bin/bash
# Script para iniciar os bots de trading no EC2

echo "🔄 Parando processos antigos..."
pkill -9 -f main_multibot
sleep 2

echo "🤖 Iniciando Trading Bots..."
cd ~/App_Leonardo
source venv/bin/activate

# Inicia bot
nohup python main_multibot.py > logs/bot.log 2>&1 &

sleep 3

# Verifica se está rodando
if pgrep -f main_multibot > /dev/null; then
    echo "✅ Bots iniciados com sucesso!"
    ps aux | grep main_multibot | grep -v grep
else
    echo "❌ Erro ao iniciar bots"
    echo "📋 Últimas linhas do log:"
    tail -20 logs/bot.log
fi
