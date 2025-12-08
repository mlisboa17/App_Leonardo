@echo off
setlocal EnableDelayedExpansion

set KEY=C:\Users\gabri\Downloads\r7_trade_key.pem
set HOST=ubuntu@18.230.59.118
set APP=~/r7-trading-bot

if "%1"=="" goto menu
if "%1"=="1" goto check_cryptos
if "%1"=="2" goto sell_extra
if "%1"=="3" goto upload_config
if "%1"=="4" goto restart_bot
if "%1"=="5" goto logs
if "%1"=="6" goto status
if "%1"=="7" goto positions
goto menu

:menu
echo.
echo ========================================
echo    AWS BOT CONTROL - Menu Rapido
echo ========================================
echo.
echo  1 - Ver cryptos para VENDER
echo  2 - VENDER cryptos fora do portfolio
echo  3 - Upload config atualizado
echo  4 - Reiniciar bot
echo  5 - Ver logs (ultimas 50 linhas)
echo  6 - Status do bot
echo  7 - Ver posicoes atuais
echo.
echo  Use: aws_cmd.bat [numero]
echo ========================================
echo.
goto end

:check_cryptos
echo.
echo === Verificando cryptos para vender ===
ssh -i "%KEY%" %HOST% "cd %APP% && ./venv/bin/python -c \"import ccxt,yaml; cfg=yaml.safe_load(open('config/config.yaml')); ex=ccxt.binance({'apiKey':cfg['api']['binance']['api_key'],'secret':cfg['api']['binance']['api_secret']}); keep=['BTC','ETH','BNB','SOL','DOT','UNI','AAVE','XRP','DOGE','USDT']; bal=ex.fetch_balance(); print('\\n=== CRYPTOS FORA DO PORTFOLIO ==='); [print(f'{c}: {v:.6f}') for c,v in bal['total'].items() if v>0.0001 and c not in keep]\""
goto end

:sell_extra
echo.
echo === Vendendo cryptos fora do portfolio ===
ssh -i "%KEY%" %HOST% "cd %APP% && ./venv/bin/python -c \"
import ccxt, yaml, time

cfg = yaml.safe_load(open('config/config.yaml'))
ex = ccxt.binance({
    'apiKey': cfg['api']['binance']['api_key'],
    'secret': cfg['api']['binance']['api_secret']
})

keep = ['BTC','ETH','BNB','SOL','DOT','UNI','AAVE','XRP','DOGE','USDT','USD','BRL']
bal = ex.fetch_balance()

for coin, amount in bal['total'].items():
    if amount > 0.0001 and coin not in keep:
        try:
            symbol = f'{coin}/USDT'
            market = ex.market(symbol)
            qty = ex.amount_to_precision(symbol, amount * 0.999)
            if float(qty) > 0:
                order = ex.create_market_sell_order(symbol, qty)
                print(f'VENDIDO: {coin} - {qty}')
                time.sleep(0.5)
        except Exception as e:
            print(f'Erro {coin}: {e}')
print('\\nConcluido!')
\""
goto end

:upload_config
echo.
echo === Enviando config atualizado ===
scp -i "%KEY%" "c:\Users\gabri\OneDrive\Area de Trabalho\Projetos\ScanKripto\r7_v1\config\unico_bot_config.yaml" %HOST%:%APP%/config/
echo Config enviado!
goto end

:restart_bot
echo.
echo === Reiniciando bot ===
ssh -i "%KEY%" %HOST% "pkill -f main_multibot.py; sleep 2; cd %APP% && nohup ./venv/bin/python main_multibot.py > logs/bot.log 2>&1 & sleep 2; ps aux | grep main_multibot | grep -v grep"
echo Bot reiniciado!
goto end

:logs
echo.
echo === Ultimas 50 linhas do log ===
ssh -i "%KEY%" %HOST% "tail -50 %APP%/logs/bot.log"
goto end

:status
echo.
echo === Status do bot ===
ssh -i "%KEY%" %HOST% "ps aux | grep -E 'main_multibot|streamlit' | grep -v grep"
goto end

:positions
echo.
echo === Posicoes atuais ===
ssh -i "%KEY%" %HOST% "cd %APP% && ./venv/bin/python -c \"import json; d=json.load(open('data/multibot_positions.json')); print(f'Total: {len(d)} posicoes'); [print(f'  {k}') for k in d.keys()]\""
goto end

:end
echo.
