@echo off
echo ============================================================
echo    App Leonardo - Bot + Dashboard (Mesmo Terminal)
echo ============================================================
echo.

echo Iniciando Django em segundo plano...
start /B python manage.py runserver >nul 2>&1

echo Aguardando Django iniciar...
timeout /t 5 /nobreak >nul

echo Abrindo navegador...
start http://127.0.0.1:8000/test/

echo.
echo Dashboard: http://127.0.0.1:8000/test/
echo.
echo ============================================================
echo Iniciando Bot (logs aparecerao abaixo)...
echo ============================================================
echo.

python main.py

echo.
echo Bot encerrado.
pause
