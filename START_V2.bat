@echo off
cls
echo ========================================
echo   🚀 APP LEONARDO v2.0
echo   Arquitetura Profissional
echo ========================================
echo.
echo 📊 NOVA ESTRUTURA:
echo    Backend: FastAPI (Assíncrono)
echo    Frontend: Plotly Dash
echo    Database: PostgreSQL + Redis
echo    Estratégia: Agressiva
echo.
echo ⚠️  REQUISITOS:
echo    - PostgreSQL rodando (porta 5432)
echo    - Redis rodando (porta 6379)
echo.
pause

echo.
echo 🔄 Verificando dependências...
pip install -q -r requirements_new.txt

echo.
echo 🚀 Iniciando Backend (FastAPI)...
start "FastAPI Backend" cmd /k "python backend/main.py"

timeout /t 3 /nobreak > nul

echo.
echo 🎨 Iniciando Frontend (Plotly Dash v2.0)...
start "Plotly Dash v2.0" cmd /k "python frontend/dashboard_v2.py"

echo.
echo ========================================
echo   ✅ SISTEMA INICIADO!
echo ========================================
echo.
echo 📊 Dashboard: http://localhost:8050
echo 🔌 API: http://localhost:8001
echo 📚 Docs: http://localhost:8001/docs
echo.
echo Pressione Ctrl+C nos terminais para parar
echo ========================================
pause
