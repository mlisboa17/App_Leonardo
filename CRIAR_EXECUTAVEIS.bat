@echo off
echo ============================================
echo    CRIANDO EXECUTAVEIS - App Leonardo
echo ============================================
echo.

REM Verifica se PyInstaller esta instalado
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INSTALANDO] PyInstaller...
    pip install pyinstaller
)

echo.
echo [1/2] Criando executavel do BOT...
echo ============================================
cd /d "%~dp0"
pyinstaller --onefile --name AppLeonardo_Bot ^
    --add-data "config/config.yaml;config" ^
    --add-data "data/crypto_profiles.json;data" ^
    --hidden-import ccxt ^
    --hidden-import pandas ^
    --hidden-import pandas_ta ^
    --hidden-import numpy ^
    --hidden-import yaml ^
    --hidden-import dotenv ^
    --hidden-import sqlite3 ^
    --console ^
    main.py

echo.
echo [2/2] Criando executavel do DASHBOARD...
echo ============================================
cd frontend
pyinstaller --onefile --name AppLeonardo_Dashboard ^
    --add-data "../config/config.yaml;config" ^
    --hidden-import dash ^
    --hidden-import dash_bootstrap_components ^
    --hidden-import plotly ^
    --hidden-import ccxt ^
    --hidden-import pandas ^
    --hidden-import numpy ^
    --hidden-import flask ^
    --hidden-import werkzeug ^
    --hidden-import dotenv ^
    --console ^
    dashboard_saldo.py

cd ..

echo.
echo ============================================
echo    EXECUTAVEIS CRIADOS COM SUCESSO!
echo ============================================
echo.
echo Arquivos criados:
echo   - dist\AppLeonardo_Bot.exe
echo   - frontend\dist\AppLeonardo_Dashboard.exe
echo.
echo IMPORTANTE: Copie tambem a pasta 'config' com seu .env
echo.
pause
