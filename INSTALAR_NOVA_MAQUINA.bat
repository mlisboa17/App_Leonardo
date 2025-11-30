@echo off
chcp 65001 >nul
title App Leonardo - Instalação

echo ╔═══════════════════════════════════════════════════════════╗
echo ║          APP LEONARDO - INSTALAÇÃO                        ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  Instalador de dependências para nova máquina             ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo Por favor, instale o Python 3.9+ primeiro:
    echo    1. Acesse: https://www.python.org/downloads/
    echo    2. Baixe e instale o Python
    echo    3. IMPORTANTE: Marque "Add Python to PATH"
    echo    4. Execute este script novamente
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado!
python --version
echo.

:: Ir para a pasta do projeto
cd /d "%~dp0"

echo ╔═══════════════════════════════════════════════════════════╗
echo ║  Instalando dependências...                               ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ❌ Erro ao instalar dependências!
    echo Verifique sua conexão com a internet e tente novamente.
    pause
    exit /b 1
)

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  ✅ INSTALAÇÃO CONCLUÍDA!                                 ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║                                                           ║
echo ║  Para iniciar o sistema:                                  ║
echo ║    - Duplo clique em: INICIAR_TUDO.bat                    ║
echo ║                                                           ║
echo ║  Ou separadamente:                                        ║
echo ║    - Bot: INICIAR_BOT.bat                                 ║
echo ║    - Dashboard: INICIAR_DASHBOARD.bat                     ║
echo ║                                                           ║
echo ║  Dashboard: http://localhost:8050                         ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

pause
