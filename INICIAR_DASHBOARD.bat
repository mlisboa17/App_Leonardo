@echo off
chcp 65001 >nul
title App Leonardo - Dashboard

echo ╔═══════════════════════════════════════════════════════════╗
echo ║          APP LEONARDO - DASHBOARD                         ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  Dashboard Web em Tempo Real                              ║
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
echo 🚀 Iniciando Dashboard...
echo    Acesse: http://localhost:8050
echo    Pressione Ctrl+C para parar
echo.

python frontend/dashboard_saldo.py

pause
