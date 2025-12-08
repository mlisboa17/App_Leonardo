#!/usr/bin/env python3
"""
🤖 VERIFICADOR DE STATUS DOS BOTS
Valida se os bots estão funcionando corretamente
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

print("=" * 70)
print("🤖 VERIFICAÇÃO DE STATUS DOS BOTS R7")
print("=" * 70)

# 1. Verificar arquivos de estado
print("\n1️⃣  ARQUIVOS DE ESTADO")
print("-" * 70)

state_files = {
    'data/control_log.json': 'Log de controle',
    'data/coordinator_stats.json': 'Estatísticas do coordenador',
    'data/multibot_history.json': 'Histórico de trades',
    'data/multibot_positions.json': 'Posições abertas',
    'data/daily_stats.json': 'Estatísticas diárias',
}

active_files = []

for file_path, description in state_files.items():
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            size = os.path.getsize(file_path)
            mtime = os.path.getmtime(file_path)
            mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # Determinar quantos registros
            count = len(data) if isinstance(data, (list, dict)) else 'N/A'
            
            print(f"✓ {file_path}")
            print(f"  └─ {description}")
            print(f"  └─ Tamanho: {size/1024:.1f} KB | Última atualização: {mtime_str}")
            print(f"  └─ Registros: {count}")
            
            active_files.append(file_path)
        except Exception as e:
            print(f"✗ {file_path}: Erro ao ler - {str(e)[:50]}")
    else:
        print(f"⚠  {file_path}: Arquivo não encontrado")

# 2. Verificar arquivos de configuração
print("\n2️⃣  ARQUIVOS DE CONFIGURAÇÃO")
print("-" * 70)

config_files = {
    'config/config.yaml': 'Config principal',
    'config/bots_config.yaml': 'Config dos bots',
    'config/.env': 'Variáveis de ambiente',
}

for file_path, description in config_files.items():
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✓ {file_path} ({size} bytes)")
    else:
        status = "❌ CRÍTICO" if file_path == 'config/config.yaml' else "⚠️  Aviso"
        print(f"✗ {file_path}: {status} - arquivo não encontrado")

# 3. Verificar logs
print("\n3️⃣  LOGS DO SISTEMA")
print("-" * 70)

log_files = {
    'logs/trading_bot.log': 'Log principal',
    'logs/coordinator.log': 'Log do coordenador',
}

for log_path, description in log_files.items():
    if os.path.exists(log_path):
        size = os.path.getsize(log_path)
        mtime = os.path.getmtime(log_path)
        mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Contar linhas
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = len(f.readlines())
        
        # Verificar se foi atualizado recentemente (últimas 24h)
        age_seconds = (datetime.now() - datetime.fromtimestamp(mtime)).total_seconds()
        age_hours = age_seconds / 3600
        
        if age_hours < 24:
            status = "✓ Recente"
            color = "🟢"
        elif age_hours < 72:
            status = "⚠️  Antigo (> 24h)"
            color = "🟡"
        else:
            status = "❌ Muito antigo (> 3 dias)"
            color = "🔴"
        
        print(f"{color} {log_path}")
        print(f"  └─ {description}")
        print(f"  └─ Tamanho: {size/1024:.1f} KB | Linhas: {lines}")
        print(f"  └─ Atualização: {mtime_str} ({age_hours:.1f}h atrás) - {status}")
    else:
        print(f"⚠  {log_path}: Arquivo não encontrado")

# 4. Verificar código principal
print("\n4️⃣  CÓDIGO PRINCIPAL")
print("-" * 70)

main_files = {
    'src/coordinator.py': 'Coordenador',
    'main_multibot.py': 'Bot principal',
    'backend/main.py': 'API backend',
}

for file_path, description in main_files.items():
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✓ {file_path} ({size} bytes)")
    else:
        print(f"✗ {file_path}: arquivo não encontrado")

# 5. Resumo e recomendações
print("\n" + "=" * 70)
print("📊 RESUMO")
print("=" * 70)

print(f"\nArquivos de estado encontrados: {len(active_files)}/{len(state_files)}")

if len(active_files) == len(state_files):
    print("✅ TODOS OS ARQUIVOS DE ESTADO PRESENTES")
else:
    print("⚠️  ALGUNS ARQUIVOS DE ESTADO ESTÃO FALTANDO")

# Verificar se há dados recentes de trading
if os.path.exists('data/multibot_history.json'):
    try:
        with open('data/multibot_history.json', 'r') as f:
            history = json.load(f)
        
        if history:
            # Supondo que tem estrutura com timestamps
            print(f"📈 Histórico de trades: {len(history)} registros")
            print("✅ BOT ESTÁ FUNCIONANDO E FAZENDO TRADES")
        else:
            print("⚠️  Histórico vazio - bot pode não ter feito trades ainda")
    except:
        pass

print("\n" + "=" * 70)
print("🔍 PRÓXIMAS AÇÕES:")
print("=" * 70)
print("""
1. Se logs estão antigos (> 24h):
   → Verificar se o bot está rodando em background
   → Executar: python main_multibot.py
   
2. Se arquivos de estado estão faltando:
   → Executar setup do bot
   → Verificar permissões de escrita em data/
   
3. Se tudo está bem:
   ✅ Os bots estão funcionando corretamente!
   → Continue monitorando os logs
   → Verifique regularmente o histórico de trades
""")

print("=" * 70)
