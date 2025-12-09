#!/usr/bin/env python3
"""
Script para atualizar configurações de produção no EC2
- Atualizar amounts dos 4 bots para valores estratégicos
- Alterar unico_bot de $500 para $50
- Ativar todas as estratégias
"""

import yaml
import sys

def update_bots_config(filepath):
    """Atualiza configuração dos 4 bots"""
    with open(filepath, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Valores estratégicos determinados ontem
    amounts = {
        'bot_estavel': 39.15,
        'bot_medio': 39.15,
        'bot_volatil': 39.15,
        'bot_meme': 30.0
    }
    
    # Ativar todos os bots e atualizar amounts
    for bot_name, amount in amounts.items():
        if bot_name in config:
            config[bot_name]['enabled'] = True
            config[bot_name]['trading']['amount_per_trade'] = amount
            print(f"✅ {bot_name}: amount = ${amount:.2f}, enabled = True")
    
    # Salvar
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"\n✅ bots_config.yaml atualizado!")

def update_unico_bot_config(filepath):
    """Atualiza configuração do unico_bot"""
    with open(filepath, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Alterar amount_per_trade de 500 para 50
    if 'unico_bot' in config:
        old_amount = config['unico_bot']['trading'].get('amount_per_trade', 500)
        config['unico_bot']['trading']['amount_per_trade'] = 50
        config['unico_bot']['enabled'] = False  # Desativar por padrão (usar os 4 bots)
        
        print(f"✅ unico_bot: amount {old_amount} → $50.00")
        print(f"✅ unico_bot: enabled = False (usar os 4 bots ao invés)")
    
    # Salvar
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"\n✅ unico_bot_config.yaml atualizado!")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 ATUALIZANDO CONFIGURAÇÕES DE PRODUÇÃO")
    print("=" * 60)
    
    # Atualizar bots_config.yaml
    print("\n📝 Atualizando bots_config.yaml...")
    try:
        update_bots_config('config/bots_config.yaml')
    except Exception as e:
        print(f"❌ Erro ao atualizar bots_config.yaml: {e}")
        sys.exit(1)
    
    # Atualizar unico_bot_config.yaml
    print("\n📝 Atualizando unico_bot_config.yaml...")
    try:
        update_unico_bot_config('config/unico_bot_config.yaml')
    except Exception as e:
        print(f"❌ Erro ao atualizar unico_bot_config.yaml: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ CONFIGURAÇÕES ATUALIZADAS COM SUCESSO!")
    print("=" * 60)
    print("""
Próximas ações:
1. Reiniciar o bot: pkill main_multibot.py && nohup ./venv/bin/python main_multibot.py
2. Verificar os 4 bots estão ativos nos logs
3. Monitorar as posições no dashboard

Valores configurados:
- Bot Estável: $39.15/trade, 4 posições
- Bot Médio: $39.15/trade, 4 posições  
- Bot Volátil: $39.15/trade, 3 posições
- Bot Meme: $30.00/trade, 2 posições
- UnicoBot: $50.00/trade (desativado)
    """)
