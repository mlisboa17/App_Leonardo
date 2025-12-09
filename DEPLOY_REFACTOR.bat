@echo off
echo =====================================
echo  DEPLOY DASHBOARD REFATORADO - EC2
echo =====================================
echo.

set KEY="C:\Users\gabri\Downloads\r7_trade_key.pem"
set HOST=ubuntu@18.230.59.118
set REMOTE_DIR=~/App_Leonardo

echo [1/5] Criando estrutura utils/ no servidor...
ssh -i %KEY% %HOST% "mkdir -p %REMOTE_DIR%/frontend/utils"

echo.
echo [2/5] Enviando arquivos utils/...
scp -i %KEY% frontend\utils\data_loaders.py %HOST%:%REMOTE_DIR%/frontend/utils/
scp -i %KEY% frontend\utils\calculators.py %HOST%:%REMOTE_DIR%/frontend/utils/
scp -i %KEY% frontend\utils\session_manager.py %HOST%:%REMOTE_DIR%/frontend/utils/

echo.
echo [3/5] Enviando novas páginas...
scp -i %KEY% frontend\pages\05_ai_intelligence.py %HOST%:%REMOTE_DIR%/frontend/pages/
scp -i %KEY% frontend\pages\06_bot_control.py %HOST%:%REMOTE_DIR%/frontend/pages/
scp -i %KEY% frontend\pages\07_advanced_analytics.py %HOST%:%REMOTE_DIR%/frontend/pages/
scp -i %KEY% frontend\pages\08_position_manager.py %HOST%:%REMOTE_DIR%/frontend/pages/

echo.
echo [4/5] Enviando dashboard_multibot_v2.py...
scp -i %KEY% frontend\dashboard_multibot_v2.py %HOST%:%REMOTE_DIR%/frontend/

echo.
echo [5/5] Instalando numpy (se necessário)...
ssh -i %KEY% %HOST% "cd %REMOTE_DIR% && source .venv/bin/activate && pip install numpy 2>&1 | grep -v 'already satisfied' || true"

echo.
echo ========================================
echo  DEPLOY COMPLETO!
echo ========================================
echo.
echo PROXIMOS PASSOS:
echo.
echo 1. Testar novo dashboard:
echo    ssh -i %KEY% %HOST%
echo    cd ~/App_Leonardo
echo    streamlit run frontend/dashboard_multibot_v2.py --server.port=8502
echo.
echo 2. Acessar: http://18.230.59.118:8502
echo.
echo 3. Se funcionar, substituir antigo:
echo    mv frontend/dashboard_multibot.py frontend/dashboard_multibot_OLD.py
echo    mv frontend/dashboard_multibot_v2.py frontend/dashboard_multibot.py
echo.
echo 4. Reiniciar dashboard principal (porta 8501)
echo.
pause
