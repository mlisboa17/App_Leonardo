#!/usr/bin/env pwsh
# Deploy R7 Trading Bot para EC2 - Windows PowerShell

param(
    [Parameter(Mandatory=$true)]
    [string]$EC2_IP,
    
    [Parameter(Mandatory=$true)]
    [string]$SSH_KEY,
    
    [Parameter(Mandatory=$false)]
    [string]$SSH_USER = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$ARCHIVE = "r7-trading-bot.tar.gz"
)

$ErrorActionPreference = "Stop"

Write-Host "`n====== R7 Trading Bot Deploy ======`n" -ForegroundColor Green

# Validação
Write-Host "[1/5] Validando configuracao..." -ForegroundColor Cyan

if (-not (Test-Path $SSH_KEY)) {
    Write-Host "ERRO: Chave SSH nao encontrada em: $SSH_KEY" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ARCHIVE)) {
    Write-Host "ERRO: Arquivo $ARCHIVE nao encontrado" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Chave SSH encontrada" -ForegroundColor Green
Write-Host "  ✓ Arquivo de deploy encontrado ($ARCHIVE)" -ForegroundColor Green

# Upload
Write-Host "`n[2/5] Uploading arquivo para EC2 ($EC2_IP)..." -ForegroundColor Cyan
Write-Host "  Arquivo: $ARCHIVE" -ForegroundColor Gray
Write-Host "  Tamanho: ~29 MB (leva ~2-3 minutos)" -ForegroundColor Gray

scp -i $SSH_KEY $ARCHIVE "${SSH_USER}@${EC2_IP}:~/" 2>&1 | Out-String

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Upload concluido com sucesso" -ForegroundColor Green
} else {
    Write-Host "  ERRO: Upload falhou" -ForegroundColor Red
    exit 1
}

# Extrair e configurar
Write-Host "`n[3/5] Extraindo arquivo na EC2..." -ForegroundColor Cyan

$setup_commands = @"
set -e
cd ~
tar -xzf $ARCHIVE
cd r7-trading-bot
chmod +x setup_quick.sh
echo 'Extracao concluida'
"@

ssh -i $SSH_KEY "${SSH_USER}@${EC2_IP}" $setup_commands | Out-String

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Extracao concluida" -ForegroundColor Green
} else {
    Write-Host "  ERRO: Extracao falhou" -ForegroundColor Red
    exit 1
}

# Setup
Write-Host "`n[4/5] Executando setup_quick.sh (leva ~5-10 min)..." -ForegroundColor Cyan

$setup_commands = @"
set -e
cd ~/r7-trading-bot
bash setup_quick.sh
echo 'Setup concluido'
"@

ssh -i $SSH_KEY "${SSH_USER}@${EC2_IP}" $setup_commands | Out-String

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Setup concluido com sucesso" -ForegroundColor Green
} else {
    Write-Host "  AVISO: Setup teve erros - verifique os logs" -ForegroundColor Yellow
}

# Próximos passos
Write-Host "`n[5/5] Proximos passos..." -ForegroundColor Cyan

Write-Host @"

SUCESSO! Seu deploy foi preparado.

ANTES DE INICIAR OS SERVICOS:

1. REVOGUE as credenciais ANTIGAS do Binance:
   - Acesse: https://www.binance.com/en/account/api-management
   - Delete as chaves antigas
   - CONFIRME a delecao

2. CRIE novas chaves Binance:
   - Configure IP Whitelist: $EC2_IP
   - Permissoes: Spot Trading apenas
   - Guarde as chaves com seguranca

3. ATUALIZE credenciais na EC2:
   ssh -i "$SSH_KEY" ${SSH_USER}@${EC2_IP}
   nano config/.env
   # Edite BINANCE_API_KEY e BINANCE_API_SECRET
   # Salve: Ctrl+O, Enter, Ctrl+X

4. INICIE os servicos:
   ssh -i "$SSH_KEY" ${SSH_USER}@${EC2_IP}
   sudo systemctl start r7-trading-bot
   sudo systemctl start r7-trading-dashboard

5. TESTE o health check:
   curl "http://${EC2_IP}:8080/api/health"

LOGS EM TEMPO REAL:
   ssh -i "$SSH_KEY" ${SSH_USER}@${EC2_IP}
   journalctl -u r7-trading-bot -f

DASHBOARD:
   http://${EC2_IP}:8501

"@ -ForegroundColor Green

Write-Host "====== Deploy Preparado ======`n" -ForegroundColor Green
