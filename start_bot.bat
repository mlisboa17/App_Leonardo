@echo off
echo ========================================
echo  🤖 App Leonardo - Bot de Trading
echo ========================================
echo.

REM Ativa ambiente virtual se existir
if exist "venv\Scripts\activate.bat" (
    echo Ativando ambiente virtual...
    call venv\Scripts\activate.bat
)

REM Verifica se .env existe
if not exist "config\.env" (
    echo ⚠️  ATENÇÃO: Arquivo .env não encontrado!
    echo.
    echo Copie config\.env.example para config\.env
    echo e preencha com suas credenciais da Binance
    echo.
    pause
    exit /b 1
)

echo 🚀 Iniciando bot de trading...
echo.
python main.py

pause
