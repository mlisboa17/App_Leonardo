@echo off
echo ========================================
echo CORRIGINDO BOT NA AWS
echo ========================================

echo.
echo [1/5] Parando o bot...
ssh -i "C:\Users\gabri\Downloads\r7_trade_key.pem" ubuntu@18.230.59.118 "pkill -f main_multibot"
timeout /t 2 > nul

echo.
echo [2/5] Executando fix_positions.py...
ssh -i "C:\Users\gabri\Downloads\r7_trade_key.pem" ubuntu@18.230.59.118 "cd ~/App_Leonardo && ./venv/bin/python fix_positions.py"

echo.
echo [3/5] Verificando posicoes...
ssh -i "C:\Users\gabri\Downloads\r7_trade_key.pem" ubuntu@18.230.59.118 "cd ~/App_Leonardo && cat data/multibot_positions.json"

echo.
echo [4/5] Reiniciando o bot...
ssh -i "C:\Users\gabri\Downloads\r7_trade_key.pem" ubuntu@18.230.59.118 "cd ~/App_Leonardo && nohup ./venv/bin/python main_multibot.py > logs/bot.log 2>&1 &"
timeout /t 10 > nul

echo.
echo [5/5] Verificando logs...
ssh -i "C:\Users\gabri\Downloads\r7_trade_key.pem" ubuntu@18.230.59.118 "tail -30 ~/App_Leonardo/logs/bot.log"

echo.
echo ========================================
echo CONCLUIDO! Verifique se ha erros acima.
echo ========================================
pause
