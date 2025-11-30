@echo off
chcp 65001 >nul
title App Leonardo - Iniciar Bot

echo ╔═══════════════════════════════════════════════════════════╗
echo ║          APP LEONARDO - TRADING BOT                       ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  Bot de Trading com Estratégia Adaptativa RSI             ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado! Por favor, instale o Python 3.9+
    echo    Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Ir para a pasta do projeto
cd /d "%~dp0"

echo 🔄 Verificando dependências...
pip install -r requirements.txt --quiet

echo.
echo 🚀 Iniciando Bot de Trading...
echo    Pressione Ctrl+C para parar
echo.

python main.py

pause
