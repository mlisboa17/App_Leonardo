@echo off
chcp 65001 >nul
title App Leonardo - Sistema Completo

echo ╔═══════════════════════════════════════════════════════════╗
echo ║          APP LEONARDO - SISTEMA COMPLETO                  ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  Inicia Bot + Dashboard automaticamente                   ║
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
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  🚀 INICIANDO SISTEMA                                     ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  Bot será iniciado em uma nova janela                     ║
echo ║  Dashboard será iniciado nesta janela                     ║
echo ║                                                           ║
echo ║  📊 Dashboard: http://localhost:8050                      ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:: Iniciar Bot em nova janela
echo 🤖 Iniciando Bot de Trading...
start "App Leonardo - Bot" cmd /k "cd /d "%~dp0" && python main.py"

:: Aguardar um pouco para o bot iniciar
timeout /t 3 /nobreak >nul

:: Iniciar Dashboard
echo 📊 Iniciando Dashboard Web...
echo.
echo    Acesse: http://localhost:8050
echo    Pressione Ctrl+C para parar o Dashboard
echo.

start http://localhost:8050
python frontend/dashboard_saldo.py

pause
