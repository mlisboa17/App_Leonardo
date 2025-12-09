#!/usr/bin/env python3
"""
Script para ativar unico_bot com escolha de modo:
- SOLO: Bot Único assume tudo, pausa os 4 bots
- HYBRID: Bot Único + 4 bots trabalhando juntos
- FOMINHA: Bot Único + 4 bots | Bot leva 70% dos lucros (AGRESSIVO)
- EQUIPE: Todos trabalham juntos | Lucro dividido igualmente
"""

import yaml
import sys

def ativar_unico_bot_solo():
    """Ativa unico_bot em MODO SOLO (pausa os 4 bots)"""
    
    print("=" * 70)
    print("🎯 ATIVANDO UNICO_BOT - MODO SOLO")
    print("=" * 70)
    
    # Ativar unico_bot_config
    print("\n📝 Configurando unico_bot...")
    with open('config/unico_bot_config.yaml', 'r', encoding='utf-8') as f:
        unico = yaml.safe_load(f)
    
    unico['enabled'] = True
    unico['operation_mode'] = 'SOLO'
    
    with open('config/unico_bot_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(unico, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ unico_bot: ATIVADO (Modo SOLO)")
    
    # Desativar os 4 bots
    print("\n📝 Pausando os 4 bots especializados...")
    with open('config/bots_config.yaml', 'r', encoding='utf-8') as f:
        bots = yaml.safe_load(f)
    
    for bot_type in ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']:
        if bot_type in bots:
            bots[bot_type]['enabled'] = False
    
    with open('config/bots_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(bots, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ 4 bots especializados: PAUSADOS")
    
    print("\n" + "=" * 70)
    print("STATUS FINAL:")
    print("  • Bot Único: OPERANDO")
    print("  • Bot Estável: PAUSADO")
    print("  • Bot Médio: PAUSADO")
    print("  • Bot Volátil: PAUSADO")
    print("  • Bot Meme: PAUSADO")
    print("=" * 70 + "\n")


def ativar_unico_bot_hybrid():
    """Ativa unico_bot em MODO HÍBRIDO (trabalha junto com os 4 bots)"""
    
    print("=" * 70)
    print("🔄 ATIVANDO UNICO_BOT - MODO HÍBRIDO")
    print("=" * 70)
    
    # Ativar unico_bot_config
    print("\n📝 Configurando unico_bot...")
    with open('config/unico_bot_config.yaml', 'r', encoding='utf-8') as f:
        unico = yaml.safe_load(f)
    
    unico['enabled'] = True
    unico['operation_mode'] = 'HYBRID'
    
    with open('config/unico_bot_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(unico, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ unico_bot: ATIVADO (Modo HÍBRIDO)")
    
    print("\n" + "=" * 70)
    print("STATUS:")
    print("  • Bot Único: OPERANDO (carteira própria)")
    print("  • 4 Bots: Podem ser ativados com activate_bots.py")
    print("=" * 70 + "\n")


def ativar_unico_bot_fominha():
    """Ativa unico_bot em MODO FOMINHA (agressivo - bot leva 70%)"""
    
    print("=" * 70)
    print("🤑 ATIVANDO UNICO_BOT - MODO FOMINHA")
    print("=" * 70)
    
    print("\n📝 Configurando unico_bot...")
    with open('config/unico_bot_config.yaml', 'r', encoding='utf-8') as f:
        unico = yaml.safe_load(f)
    
    unico['enabled'] = True
    unico['operation_mode'] = 'FOMINHA'
    
    with open('config/unico_bot_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(unico, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ unico_bot: ATIVADO (Modo FOMINHA)")
    print("\n⚡ MODO AGRESSIVO:")
    print("  • Bot Único + 4 bots ATIVOS")
    print("  • Bot Único leva 70% dos lucros de TODOS")
    print("  • IA monitora Fear & Greed a cada 30s")
    print("  • IA lê notícias em tempo real")
    print("  • Até 50 trades/dia")
    print("  • Stop loss: -0.5% (apertado)")
    print("  • Take profit: 0.8% (rápido)")
    print("\n" + "=" * 70 + "\n")


def ativar_unico_bot_equipe():
    """Ativa unico_bot em MODO EQUIPE (colaborativo - lucro dividido)"""
    
    print("=" * 70)
    print("🤝 ATIVANDO UNICO_BOT - MODO EQUIPE")
    print("=" * 70)
    
    print("\n📝 Configurando unico_bot...")
    with open('config/unico_bot_config.yaml', 'r', encoding='utf-8') as f:
        unico = yaml.safe_load(f)
    
    unico['enabled'] = True
    unico['operation_mode'] = 'EQUIPE'
    
    with open('config/unico_bot_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(unico, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ unico_bot: ATIVADO (Modo EQUIPE)")
    print("\n🤝 MODO COLABORATIVO:")
    print("  • 5 bots trabalhando juntos")
    print("  • Lucro dividido igualmente (20% cada)")
    print("  • IA coordena estratégias")
    print("  • IA redistribui capital automaticamente")
    print("  • Bot Único: 40% do capital")
    print("  • 4 bots: 15% cada")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    print("\n🎮 CONTROLE DO BOT ÚNICO\n")
    print("Escolha uma opção:")
    print("  1 - Ativar Bot Único (MODO SOLO)")
    print("  2 - Ativar Bot Único (MODO HÍBRIDO)")
    print("  3 - Ativar Bot Único (MODO FOMINHA) 🤑")
    print("  4 - Ativar Bot Único (MODO EQUIPE) 🤝")
    print("  0 - Sair")
    
    try:
        escolha = input("\nDigite o número: ").strip()
        
        if escolha == '1':
            ativar_unico_bot_solo()
        elif escolha == '2':
            ativar_unico_bot_hybrid()
        elif escolha == '3':
            ativar_unico_bot_fominha()
        elif escolha == '4':
            ativar_unico_bot_equipe()
        elif escolha == '0':
            print("Saindo...")
            sys.exit(0)
        else:
            print("❌ Opção inválida!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
