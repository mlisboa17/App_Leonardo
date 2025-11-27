"""
Configurador Interativo do Bot Leonardo
Interface de terminal para configurar o bot de trading
"""
import os
import yaml
from typing import Dict, Any

class BotConfigurator:
    """Configurador interativo para o bot"""
    
    def __init__(self):
        self.config = {}
        self.clear_screen()
        
    def clear_screen(self):
        """Limpa a tela do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """Imprime cabeçalho formatado"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70 + "\n")
    
    def print_section(self, section: str):
        """Imprime título de seção"""
        print(f"\n{'─'*70}")
        print(f"📋 {section}")
        print(f"{'─'*70}\n")
    
    def get_input(self, prompt: str, default: Any, data_type: type = str, 
                  options: list = None, description: str = None) -> Any:
        """
        Solicita entrada do usuário com valor padrão
        """
        if description:
            print(f"ℹ️  {description}")
        
        if options:
            print(f"   Opções: {', '.join(map(str, options))}")
        
        if data_type == bool:
            default_str = "sim" if default else "não"
            user_input = input(f"➤ {prompt} [{default_str}]: ").strip().lower()
            
            if user_input == '':
                return default
            return user_input in ['sim', 's', 'yes', 'y', 'true', '1']
        
        else:
            default_str = str(default)
            user_input = input(f"➤ {prompt} [{default_str}]: ").strip()
            
            if user_input == '':
                return default
            
            try:
                if data_type == int:
                    return int(user_input)
                elif data_type == float:
                    return float(user_input)
                else:
                    return user_input
            except ValueError:
                print(f"⚠️  Valor inválido! Usando padrão: {default}")
                return default
    
    def configure_exchange(self) -> Dict:
        """Configura parâmetros da exchange"""
        self.print_section("CONFIGURAÇÃO DA EXCHANGE")
        
        exchange_config = {}
        
        # Nome da exchange
        print("🔹 Exchange suportadas: binance, bybit, okx, kraken, etc.")
        exchange_config['name'] = self.get_input(
            "Nome da exchange",
            default="binance",
            description="Exchange para conectar (via CCXT)"
        )
        
        # Modo testnet
        exchange_config['testnet'] = self.get_input(
            "Usar modo TESTNET? (RECOMENDADO para começar)",
            default=True,
            data_type=bool,
            description="⚠️  SEMPRE use testnet para testes! Só desative após validar tudo."
        )
        
        if not exchange_config['testnet']:
            confirm = self.get_input(
                "🚨 ATENÇÃO: Vai usar DINHEIRO REAL! Confirma? (sim/não)",
                default=False,
                data_type=bool
            )
            if not confirm:
                exchange_config['testnet'] = True
                print("✅ Voltando para modo TESTNET (seguro)")
        
        return exchange_config
    
    def configure_trading(self) -> Dict:
        """Configura parâmetros de trading"""
        self.print_section("CONFIGURAÇÃO DE TRADING")
        
        trading_config = {}
        
        # Par de trading
        print("🔹 Exemplos: BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT")
        trading_config['symbol'] = self.get_input(
            "Par de trading",
            default="BTC/USDT",
            description="Par para operar (formato: BASE/QUOTE)"
        )
        
        # Timeframe
        print("🔹 Opções comuns: 1m, 5m, 15m, 1h, 4h, 1d")
        trading_config['timeframe'] = self.get_input(
            "Timeframe (intervalo dos candles)",
            default="1h",
            description="Quanto menor, mais operações (e mais arriscado)"
        )
        
        # Valor por trade
        trading_config['amount_per_trade'] = self.get_input(
            "Valor por trade (em USDT)",
            default=100,
            data_type=float,
            description="💡 Comece com valores pequenos (10-100 USDT no testnet)"
        )
        
        # Máximo de posições
        trading_config['max_positions'] = self.get_input(
            "Máximo de posições simultâneas",
            default=3,
            data_type=int,
            description="Quantas operações abertas ao mesmo tempo (1-5 recomendado)"
        )
        
        return trading_config
    
    def configure_safety(self) -> Dict:
        """Configura sistema de segurança"""
        self.print_section("⚠️  SISTEMA DE SEGURANÇA (ANTI-ALUCINAÇÃO)")
        
        safety_config = {}
        
        # Perda máxima diária
        safety_config['max_daily_loss'] = self.get_input(
            "Perda máxima DIÁRIA (USDT) - KILL SWITCH",
            default=500,
            data_type=float,
            description="🛑 Bot para AUTOMATICAMENTE ao atingir esta perda no dia"
        )
        
        # Drawdown máximo
        safety_config['max_drawdown'] = self.get_input(
            "Drawdown máximo (%) - KILL SWITCH",
            default=20,
            data_type=float,
            description="🛑 % de queda do pico de saldo para parar tudo (10-30% recomendado)"
        )
        
        # Limite de desvio de preço
        safety_config['price_deviation_limit'] = self.get_input(
            "Limite de variação de preço suspeita (%)",
            default=5,
            data_type=float,
            description="⚠️  Rejeita preços que variarem mais que isso em 1 tick (anti-spike)"
        )
        
        return safety_config
    
    def configure_indicators(self) -> Dict:
        """Configura indicadores técnicos"""
        self.print_section("📊 INDICADORES TÉCNICOS")
        
        indicators_config = {}
        
        # RSI
        print("\n🔹 RSI (Relative Strength Index)")
        indicators_config['rsi'] = {
            'period': self.get_input(
                "  Período do RSI",
                default=14,
                data_type=int,
                description="  Padrão: 14 (mais sensível: 7-10, mais suave: 20-30)"
            ),
            'oversold': self.get_input(
                "  Nível de sobrevenda (compra)",
                default=30,
                data_type=int,
                description="  Compra quando RSI < este valor (20-30 padrão)"
            ),
            'overbought': self.get_input(
                "  Nível de sobrecompra (venda)",
                default=70,
                data_type=int,
                description="  Vende quando RSI > este valor (70-80 padrão)"
            )
        }
        
        # MACD
        print("\n🔹 MACD (Moving Average Convergence Divergence)")
        indicators_config['macd'] = {
            'fast': self.get_input(
                "  Período rápido",
                default=12,
                data_type=int,
                description="  EMA rápida (padrão: 12)"
            ),
            'slow': self.get_input(
                "  Período lento",
                default=26,
                data_type=int,
                description="  EMA lenta (padrão: 26)"
            ),
            'signal': self.get_input(
                "  Período do sinal",
                default=9,
                data_type=int,
                description="  Linha de sinal (padrão: 9)"
            )
        }
        
        # SMAs
        print("\n🔹 Médias Móveis Simples (SMA)")
        print("  💡 Deixe em branco para usar padrão [20, 50, 200]")
        sma_input = input("  ➤ Períodos das SMAs (separados por vírgula) [20,50,200]: ").strip()
        
        if sma_input:
            try:
                indicators_config['sma'] = {
                    'periods': [int(x.strip()) for x in sma_input.split(',')]
                }
            except:
                print("  ⚠️  Formato inválido! Usando padrão [20, 50, 200]")
                indicators_config['sma'] = {'periods': [20, 50, 200]}
        else:
            indicators_config['sma'] = {'periods': [20, 50, 200]}
        
        return indicators_config
    
    def configure_logging(self) -> Dict:
        """Configura sistema de logs"""
        self.print_section("📝 SISTEMA DE LOGS")
        
        logging_config = {}
        
        # Nível de log
        print("🔹 Níveis: DEBUG (muito detalhado), INFO (normal), WARNING, ERROR")
        logging_config['level'] = self.get_input(
            "Nível de logging",
            default="INFO",
            options=["DEBUG", "INFO", "WARNING", "ERROR"],
            description="INFO é recomendado (DEBUG para troubleshooting)"
        )
        
        # Arquivo de log
        logging_config['file'] = self.get_input(
            "Arquivo de log",
            default="logs/trading_bot.log",
            description="Caminho onde os logs serão salvos"
        )
        
        return logging_config
    
    def configure_data(self) -> Dict:
        """Configura gerenciamento de dados"""
        self.print_section("💾 GERENCIAMENTO DE DADOS")
        
        data_config = {}
        
        data_config['cache_enabled'] = self.get_input(
            "Habilitar cache de dados?",
            default=True,
            data_type=bool,
            description="Cache acelera o bot e reduz chamadas à API"
        )
        
        data_config['cache_dir'] = self.get_input(
            "Diretório de cache",
            default="data/cache"
        )
        
        data_config['csv_reports'] = self.get_input(
            "Diretório de relatórios CSV",
            default="data/reports"
        )
        
        return data_config
    
    def configure_execution(self) -> Dict:
        """Configura parâmetros de execução"""
        self.print_section("⚙️  EXECUÇÃO DO BOT")
        
        exec_config = {}
        
        exec_config['interval_seconds'] = self.get_input(
            "Intervalo entre análises (segundos)",
            default=60,
            data_type=int,
            description="Tempo entre cada ciclo de análise (60s = 1min, 300s = 5min)"
        )
        
        exec_config['dry_run'] = self.get_input(
            "Modo DRY RUN (apenas simula, não executa ordens)?",
            default=False,
            data_type=bool,
            description="✅ ATIVE para testar sem executar ordens reais (mesmo no testnet)"
        )
        
        return exec_config
    
    def show_summary(self, config: Dict):
        """Mostra resumo da configuração"""
        self.print_section("📋 RESUMO DA CONFIGURAÇÃO")
        
        print(f"""
🏦 EXCHANGE:
   Exchange: {config['exchange']['name']}
   Testnet:  {'✅ SIM (SEGURO)' if config['exchange']['testnet'] else '⚠️  NÃO (DINHEIRO REAL!)'}

💰 TRADING:
   Par:              {config['trading']['symbol']}
   Timeframe:        {config['trading']['timeframe']}
   Valor por trade:  ${config['trading']['amount_per_trade']} USDT
   Max posições:     {config['trading']['max_positions']}
   Intervalo:        {config['execution']['interval_seconds']}s
   Modo DRY RUN:     {'✅ SIM (apenas simula)' if config['execution']['dry_run'] else '❌ NÃO (executa real)'}

🛡️  SEGURANÇA:
   Perda máxima dia: ${config['safety']['max_daily_loss']} USDT
   Drawdown máximo:  {config['safety']['max_drawdown']}%
   Desvio de preço:  {config['safety']['price_deviation_limit']}%

📊 INDICADORES:
   RSI:  Período {config['indicators']['rsi']['period']} | Sobrevenda<{config['indicators']['rsi']['oversold']} | Sobrecompra>{config['indicators']['rsi']['overbought']}
   MACD: Fast={config['indicators']['macd']['fast']} | Slow={config['indicators']['macd']['slow']} | Signal={config['indicators']['macd']['signal']}
   SMA:  Períodos {config['indicators']['sma']['periods']}

📝 LOGS:
   Nível:   {config['logging']['level']}
   Arquivo: {config['logging']['file']}
""")
    
    def save_config(self, config: Dict, filename: str = "config/config.yaml"):
        """Salva configuração em arquivo YAML"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            print(f"\n✅ Configuração salva em: {filename}")
            return True
        except Exception as e:
            print(f"\n❌ Erro ao salvar configuração: {e}")
            return False
    
    def run(self):
        """Executa o configurador"""
        self.clear_screen()
        self.print_header("🤖 CONFIGURADOR DO BOT DE TRADING LEONARDO")
        
        print("""
Bem-vindo ao configurador interativo!

Este assistente vai te guiar pela configuração do bot.
Para cada pergunta, você pode:
  • Pressionar ENTER para aceitar o valor sugerido (entre [colchetes])
  • Digitar um novo valor

⚠️  IMPORTANTE:
  • Sempre comece em modo TESTNET
  • Use valores pequenos para testes
  • Configure limites de segurança adequados
        """)
        
        input("\nPressione ENTER para começar...")
        
        # Coleta todas as configurações
        config = {
            'exchange': self.configure_exchange(),
            'trading': self.configure_trading(),
            'safety': self.configure_safety(),
            'indicators': self.configure_indicators(),
            'logging': self.configure_logging(),
            'data': self.configure_data(),
            'execution': self.configure_execution()
        }
        
        # Mostra resumo
        self.clear_screen()
        self.show_summary(config)
        
        # Confirma
        print("\n" + "="*70)
        confirm = input("\n✅ Salvar esta configuração? (sim/não) [sim]: ").strip().lower()
        
        if confirm in ['', 'sim', 's', 'yes', 'y']:
            if self.save_config(config):
                print("\n🎉 Configuração concluída com sucesso!")
                print("\n📋 Próximos passos:")
                print("   1. Execute: python test_connection.py  (testar conexão)")
                print("   2. Execute: python main.py             (iniciar bot)")
                print("\n⚠️  Lembre-se: você está em modo " + 
                      ("TESTNET ✅" if config['exchange']['testnet'] else "REAL ⚠️"))
                
                if config['execution']['dry_run']:
                    print("   🔸 Modo DRY RUN ativo - bot apenas simula operações")
                
                return True
        else:
            print("\n❌ Configuração cancelada")
            restart = input("Deseja reiniciar o configurador? (sim/não) [não]: ").strip().lower()
            if restart in ['sim', 's', 'yes', 'y']:
                return self.run()
            return False


def main():
    configurator = BotConfigurator()
    configurator.run()


if __name__ == "__main__":
    main()
