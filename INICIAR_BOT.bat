@echo off
cd /d "%~dp0"

echo ========================================
echo       APP LEONARDO - BOT TRADING
echo ========================================
echo.

python --version
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    pause
    exit /b 1
)

echo.
echo Iniciando Bot de Trading...
echo Pressione Ctrl+C para parar
echo.

python main.py

pause
