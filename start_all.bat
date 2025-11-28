@echo off
echo ============================================================
echo    App Leonardo - Trading Bot + Dashboard
echo ============================================================
echo.

echo [1/3] Iniciando Django Dashboard...
start "Django Dashboard - NAO FECHE" cmd /c "call venv\Scripts\activate && python manage.py runserver 8000"
timeout /t 5 /nobreak >nul

echo [2/3] Iniciando Bot de Trading...
start "Trading Bot - NAO FECHE" cmd /c "call venv\Scripts\activate && python main.py"
timeout /t 3 /nobreak >nul

echo [3/3] Abrindo Dashboard no navegador (modo anônimo)...
start chrome --incognito http://127.0.0.1:8000/

echo.
echo ============================================================
echo   Sistema Iniciado!
echo ============================================================
echo   Dashboard: http://127.0.0.1:8000/
echo   Bot e Django em janelas separadas (usando venv)
echo.
echo ============================================================
exit
