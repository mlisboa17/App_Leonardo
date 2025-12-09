@echo off
echo ============================================================
echo INICIAR SISTEMA COMPLETO - APP R7
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo.
echo [2/3] Iniciando auto-update de saldos (background)...
start "Auto-Update Saldos" cmd /k ".venv\Scripts\python.exe auto_update_balances.py"

timeout /t 2 /nobreak >nul

echo.
echo [3/3] Iniciando Dashboard Streamlit na porta 8503...
echo.
echo Dashboard estara disponivel em: http://localhost:8503
echo.

.venv\Scripts\python.exe -m streamlit run frontend/dashboard_multibot_v2.py --server.port 8503

pause
