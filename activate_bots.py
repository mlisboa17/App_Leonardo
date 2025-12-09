#!/usr/bin/env python3
import yaml
import sys

# Desativar unico_bot
print("Desativando unico_bot...")
with open('config/unico_bot_config.yaml', 'r', encoding='utf-8') as f:
    unico = yaml.safe_load(f)
unico['enabled'] = False
with open('config/unico_bot_config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(unico, f, allow_unicode=True)

# Ativar os 4 bots
print("Ativando os 4 bots principais...")
with open('config/bots_config.yaml', 'r', encoding='utf-8') as f:
    bots = yaml.safe_load(f)

bots['bot_estavel']['enabled'] = True
bots['bot_medio']['enabled'] = True
bots['bot_volatil']['enabled'] = True
bots['bot_meme']['enabled'] = True
bots['coordinator']['enabled'] = True
bots['global']['enabled'] = True

with open('config/bots_config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(bots, f, allow_unicode=True)

print("\n✅ STATUS:")
print(f"  bot_estavel: {bots['bot_estavel']['enabled']}")
print(f"  bot_medio: {bots['bot_medio']['enabled']}")
print(f"  bot_volatil: {bots['bot_volatil']['enabled']}")
print(f"  bot_meme: {bots['bot_meme']['enabled']}")
print(f"  coordinator: {bots['coordinator']['enabled']}")
print(f"  global: {bots['global']['enabled']}")
print(f"  unico_bot: {unico['enabled']}\n")

# Mostrar amounts
print("💵 AMOUNTS POR TRADE:")
print(f"  bot_estavel: ${bots['bot_estavel']['trading']['amount_per_trade']}")
print(f"  bot_medio: ${bots['bot_medio']['trading']['amount_per_trade']}")
print(f"  bot_volatil: ${bots['bot_volatil']['trading']['amount_per_trade']}")
print(f"  bot_meme: ${bots['bot_meme']['trading']['amount_per_trade']}")

print("\n🤖 POSIÇÕES MÁXIMAS:")
print(f"  bot_estavel: {bots['bot_estavel']['trading']['max_positions']}")
print(f"  bot_medio: {bots['bot_medio']['trading']['max_positions']}")
print(f"  bot_volatil: {bots['bot_volatil']['trading']['max_positions']}")
print(f"  bot_meme: {bots['bot_meme']['trading']['max_positions']}")

print("\n✨ Configuração salva com sucesso!")
