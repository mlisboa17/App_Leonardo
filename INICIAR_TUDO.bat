@echo off
cd /d "%~dp0"

echo ========================================
echo    APP LEONARDO - SISTEMA COMPLETO
echo ========================================
echo.

python --version
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    pause
    exit /b 1
)

echo.
echo Iniciando Bot em nova janela...
start "Bot Trading" cmd /k "cd /d "%~dp0" && python main.py"

timeout /t 3 /nobreak >nul

echo.
echo Iniciando Dashboard...
echo Acesse: http://localhost:8050
echo.

start http://localhost:8050
python frontend\dashboard_saldo.py

pause
