@echo off
echo ============================================================
echo DEPLOY RAPIDO AWS - APP R7
echo ============================================================
echo.

REM Configuracoes
set KEY_PATH=C:\Users\gabri\Downloads\r7_trade_key.pem
set AWS_IP=18.228.12.103

REM Verificar se IP foi configurado
if "%AWS_IP%"=="SEU_IP_AWS" (
    echo ERRO: Configure o IP AWS primeiro!
    echo.
    echo Edite este arquivo e mude: set AWS_IP=SEU_IP_AWS
    echo Para: set AWS_IP=54.123.45.67  (coloque o IP da sua EC2)
    echo.
    pause
    exit /b
)

echo Configurando permissoes da chave...
icacls "%KEY_PATH%" /inheritance:r >nul 2>&1
icacls "%KEY_PATH%" /grant:r "%USERNAME%:R" >nul 2>&1

echo.
echo ============================================================
echo PASSO 1: Conectando ao servidor AWS...
echo ============================================================
echo.
echo Servidor: ubuntu@%AWS_IP%
echo Chave: %KEY_PATH%
echo.
echo Apos conectar, COPIE E COLE estes comandos:
echo.
echo ============================================================
echo wget https://raw.githubusercontent.com/mlisboa17/App_Leonardo/master/deploy_aws.sh
echo chmod +x deploy_aws.sh
echo ./deploy_aws.sh
echo ============================================================
echo.
pause

ssh -i "%KEY_PATH%" ubuntu@%AWS_IP%

pause
