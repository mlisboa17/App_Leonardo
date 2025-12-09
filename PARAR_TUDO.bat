@echo off
REM Script para parar todos os processos no EC2

echo ========================================
echo   PARANDO TODOS OS PROCESSOS
echo ========================================
echo.

ssh -i "C:\Users\gabri\Downloads\r7_trade_key.pem" ubuntu@18.230.59.118 "pkill -9 -f streamlit && pkill -9 -f main_multibot && pkill -9 -f python && echo 'Todos os processos parados!'"

echo.
echo ========================================
echo   Sistema parado!
echo ========================================
echo.
pause
