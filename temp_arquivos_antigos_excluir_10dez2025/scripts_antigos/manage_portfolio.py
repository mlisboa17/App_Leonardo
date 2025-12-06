"""
============================================================
GERENCIADOR DE PORTFOLIO - App Leonardo v3.0
============================================================

Permite adicionar ou remover cryptos do portfolio de cada bot.
Uso via linha de comando ou importação.

Uso:
    python manage_portfolio.py add bot_estavel AAVEUSDT Aave 15
    python manage_portfolio.py remove bot_meme PEPEUSDT
    python manage_portfolio.py list
    python manage_portfolio.py available

============================================================
"""

import os
import sys
import yaml
import argparse
from pathlib import Path


CONFIG_PATH = Path("config/bots_config.yaml")


def load_config():
    """Carrega configuração"""
    if not CONFIG_PATH.exists():
        print(f"❌ Arquivo {CONFIG_PATH} não encontrado!")
        return None
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_config(config):
    """Salva configuração"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print("✅ Configuração salva!")


def list_portfolios():
    """Lista todos os portfolios"""
    config = load_config()
    if not config:
        return
    
    bot_types = ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']
    
    print("\n" + "="*60)
    print("📦 PORTFOLIOS DOS BOTS")
    print("="*60)
    
    for bot_type in bot_types:
        if bot_type in config:
            bot = config[bot_type]
            name = bot.get('name', bot_type)
            portfolio = bot.get('portfolio', [])
            
            print(f"\n{name}:")
            print("-"*40)
            
            total_weight = 0
            for crypto in portfolio:
                symbol = crypto.get('symbol', '')
                crypto_name = crypto.get('name', '')
                weight = crypto.get('weight', 0)
                total_weight += weight
                print(f"  • {symbol:12} {crypto_name:15} {weight}%")
            
            print(f"  {'─'*35}")
            print(f"  Total: {total_weight}%")
    
    print("\n" + "="*60)


def list_available():
    """Lista cryptos disponíveis para adicionar"""
    config = load_config()
    if not config:
        return
    
    available = config.get('available_cryptos', {})
    
    print("\n" + "="*60)
    print("📋 CRYPTOS DISPONÍVEIS PARA ADICIONAR")
    print("="*60)
    
    categories = {
        'stable': '🔵 Estáveis (para bot_estavel)',
        'medium': '🟢 Médias (para bot_medio)',
        'volatile': '🟡 Voláteis (para bot_volatil)',
        'meme': '🔴 Meme (para bot_meme)'
    }
    
    for category, title in categories.items():
        if category in available:
            print(f"\n{title}:")
            print("-"*40)
            for crypto in available[category]:
                symbol = crypto.get('symbol', '')
                name = crypto.get('name', '')
                volatility = crypto.get('volatility', '')
                print(f"  • {symbol:12} {name:20} ({volatility})")
    
    print("\n" + "="*60)


def add_crypto(bot_type: str, symbol: str, name: str, weight: int = 10):
    """Adiciona crypto ao portfolio de um bot"""
    config = load_config()
    if not config:
        return False
    
    if bot_type not in config:
        print(f"❌ Bot '{bot_type}' não encontrado!")
        print("   Bots disponíveis: bot_estavel, bot_medio, bot_volatil, bot_meme")
        return False
    
    portfolio = config[bot_type].get('portfolio', [])
    
    # Verifica se já existe
    existing = [c for c in portfolio if c['symbol'] == symbol]
    if existing:
        print(f"⚠️ {symbol} já existe no portfolio!")
        return False
    
    # Adiciona
    portfolio.append({
        'symbol': symbol,
        'name': name,
        'weight': weight
    })
    
    config[bot_type]['portfolio'] = portfolio
    save_config(config)
    
    print(f"✅ {symbol} ({name}) adicionado ao {config[bot_type].get('name', bot_type)} com peso {weight}%")
    return True


def remove_crypto(bot_type: str, symbol: str):
    """Remove crypto do portfolio de um bot"""
    config = load_config()
    if not config:
        return False
    
    if bot_type not in config:
        print(f"❌ Bot '{bot_type}' não encontrado!")
        return False
    
    portfolio = config[bot_type].get('portfolio', [])
    
    # Verifica se existe
    existing = [c for c in portfolio if c['symbol'] == symbol]
    if not existing:
        print(f"⚠️ {symbol} não existe no portfolio!")
        return False
    
    # Remove
    portfolio = [c for c in portfolio if c['symbol'] != symbol]
    config[bot_type]['portfolio'] = portfolio
    save_config(config)
    
    print(f"🗑️ {symbol} removido do {config[bot_type].get('name', bot_type)}")
    return True


def update_weight(bot_type: str, symbol: str, weight: int):
    """Atualiza peso de uma crypto"""
    config = load_config()
    if not config:
        return False
    
    if bot_type not in config:
        print(f"❌ Bot '{bot_type}' não encontrado!")
        return False
    
    portfolio = config[bot_type].get('portfolio', [])
    
    found = False
    for crypto in portfolio:
        if crypto['symbol'] == symbol:
            crypto['weight'] = weight
            found = True
            break
    
    if not found:
        print(f"⚠️ {symbol} não existe no portfolio!")
        return False
    
    config[bot_type]['portfolio'] = portfolio
    save_config(config)
    
    print(f"✅ Peso de {symbol} atualizado para {weight}%")
    return True


def interactive_menu():
    """Menu interativo"""
    while True:
        print("\n" + "="*50)
        print("🔧 GERENCIADOR DE PORTFOLIO")
        print("="*50)
        print("\n1. Listar portfolios atuais")
        print("2. Listar cryptos disponíveis")
        print("3. Adicionar crypto")
        print("4. Remover crypto")
        print("5. Atualizar peso")
        print("0. Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == '1':
            list_portfolios()
        
        elif choice == '2':
            list_available()
        
        elif choice == '3':
            print("\nBots: bot_estavel, bot_medio, bot_volatil, bot_meme")
            bot = input("Bot: ").strip()
            symbol = input("Symbol (ex: BTCUSDT): ").strip().upper()
            name = input("Nome (ex: Bitcoin): ").strip()
            weight = input("Peso % (default 10): ").strip()
            weight = int(weight) if weight else 10
            add_crypto(bot, symbol, name, weight)
        
        elif choice == '4':
            print("\nBots: bot_estavel, bot_medio, bot_volatil, bot_meme")
            bot = input("Bot: ").strip()
            symbol = input("Symbol (ex: BTCUSDT): ").strip().upper()
            remove_crypto(bot, symbol)
        
        elif choice == '5':
            print("\nBots: bot_estavel, bot_medio, bot_volatil, bot_meme")
            bot = input("Bot: ").strip()
            symbol = input("Symbol (ex: BTCUSDT): ").strip().upper()
            weight = int(input("Novo peso %: ").strip())
            update_weight(bot, symbol, weight)
        
        elif choice == '0':
            print("Até logo!")
            break
        
        else:
            print("Opção inválida!")


def main():
    parser = argparse.ArgumentParser(description='Gerenciador de Portfolio Multi-Bot')
    parser.add_argument('action', nargs='?', choices=['list', 'available', 'add', 'remove', 'weight'],
                       help='Ação a executar')
    parser.add_argument('bot', nargs='?', help='Tipo do bot')
    parser.add_argument('symbol', nargs='?', help='Symbol da crypto')
    parser.add_argument('name', nargs='?', help='Nome da crypto')
    parser.add_argument('weight', nargs='?', type=int, default=10, help='Peso percentual')
    
    args = parser.parse_args()
    
    if not args.action:
        # Menu interativo
        interactive_menu()
    
    elif args.action == 'list':
        list_portfolios()
    
    elif args.action == 'available':
        list_available()
    
    elif args.action == 'add':
        if not args.bot or not args.symbol or not args.name:
            print("Uso: python manage_portfolio.py add <bot> <symbol> <name> [weight]")
            print("Ex:  python manage_portfolio.py add bot_estavel AAVEUSDT Aave 15")
            return
        add_crypto(args.bot, args.symbol, args.name, args.weight)
    
    elif args.action == 'remove':
        if not args.bot or not args.symbol:
            print("Uso: python manage_portfolio.py remove <bot> <symbol>")
            print("Ex:  python manage_portfolio.py remove bot_meme PEPEUSDT")
            return
        remove_crypto(args.bot, args.symbol)
    
    elif args.action == 'weight':
        if not args.bot or not args.symbol or not args.weight:
            print("Uso: python manage_portfolio.py weight <bot> <symbol> <weight>")
            print("Ex:  python manage_portfolio.py weight bot_estavel BTCUSDT 40")
            return
        update_weight(args.bot, args.symbol, args.weight)


if __name__ == "__main__":
    main()
