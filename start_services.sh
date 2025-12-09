#!/usr/bin/env bash

# Start Services - R7 Trading Bot
# Execute este script DEPOIS de atualizar as credenciais em config/.env

set -e

echo "=========================================="
echo "Iniciando R7 Trading Bot Services"
echo "=========================================="
echo ""

# Verificar se config/.env existe e tem credenciais
if [ ! -f "config/.env" ]; then
    echo "[ERRO] config/.env nao encontrado!"
    echo "Execute primeiro:"
    echo "  cd r7-trading-bot"
    echo "  nano config/.env"
    exit 1
fi

# Verificar se tem BINANCE_API_KEY
if ! grep -q "BINANCE_API_KEY=" config/.env; then
    echo "[ERRO] BINANCE_API_KEY nao configurado em config/.env"
    echo "Execute: nano config/.env"
    exit 1
fi

echo "[1/4] Verificando permissoes..."
sudo -v > /dev/null 2>&1 || {
    echo "[ERRO] Precisa de permissoes sudo"
    exit 1
}
echo "  ✓ Permissoes OK"

echo ""
echo "[2/4] Iniciando r7-trading-bot..."
sudo systemctl start r7-trading-bot
sleep 2
STATUS=$(sudo systemctl is-active r7-trading-bot)
if [ "$STATUS" = "active" ]; then
    echo "  ✓ r7-trading-bot iniciado"
else
    echo "  ✗ r7-trading-bot FALHOU"
    sudo journalctl -u r7-trading-bot -n 20
    exit 1
fi

echo ""
echo "[3/4] Iniciando r7-trading-dashboard..."
sudo systemctl start r7-trading-dashboard
sleep 2
STATUS=$(sudo systemctl is-active r7-trading-dashboard)
if [ "$STATUS" = "active" ]; then
    echo "  ✓ r7-trading-dashboard iniciado"
else
    echo "  ✗ r7-trading-dashboard FALHOU"
    sudo journalctl -u r7-trading-dashboard -n 20
    exit 1
fi

echo ""
echo "[4/4] Status dos servicos..."
sudo systemctl status r7-trading-bot --no-pager
echo ""
sudo systemctl status r7-trading-dashboard --no-pager

echo ""
echo "=========================================="
echo "✓ Todos os servicos iniciados!"
echo "=========================================="
echo ""
echo "Proximas acoes:"
echo "  1. Testar API: curl http://localhost:8080/api/health"
echo "  2. Acessar Dashboard: http://localhost:8501"
echo "  3. Ver logs: journalctl -u r7-trading-bot -f"
echo ""
echo "Se houver erros:"
echo "  - Verificar credenciais em config/.env"
echo "  - Ver logs detalhados: journalctl -u r7-trading-bot -n 50"
echo ""
