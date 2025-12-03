@echo off
cd /d "%~dp0"

echo ========================================
echo      APP LEONARDO - DASHBOARD
echo ========================================
echo.

python --version
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    pause
    exit /b 1
)

echo.
echo Iniciando Dashboard...
echo Acesse: http://localhost:8050
echo Pressione Ctrl+C para parar
echo.

start http://localhost:8050
python frontend\dashboard_saldo.py

pause
