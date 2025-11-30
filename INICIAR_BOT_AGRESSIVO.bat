@echo off
cls
echo ========================================
echo   🤖 BOT AGRESSIVO - APP LEONARDO
echo ========================================
echo.
echo 📊 CONFIGURAÇÃO ATIVA:
echo    Modo: AGRESSIVO (1 condição)
echo    Criptos: BTC, ETH, SOL, POL
echo    Testnet: SIM (dinheiro virtual)
echo    Intervalo: 10 segundos
echo    Stop Loss: -3%%
echo    Take Profit: +2%%
echo    RSI: 40/60 (mais sensível)
echo    Posições simultâneas: 4
echo.
echo ⚠️  O bot vai COMPRAR e VENDER AUTOMATICAMENTE
echo.
pause

echo.
echo 🚀 Iniciando bot...
echo.

REM Ativa ambiente virtual se existir
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python main.py

pause
