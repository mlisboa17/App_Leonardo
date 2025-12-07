"""
============================================================
MAIN MULTI-BOT - App Leonardo v3.0 (com AI Adaptativa)
============================================================

Executa o sistema de 4 bots especializados em paralelo.
Cada bot opera independentemente com suas cryptos específicas.

🤖 NOVO: Sistema de IA que aprende e adapta os bots!
- Aprende com erros e acertos
- Busca notícias e sentimento de mercado
- Ajusta parâmetros automaticamente

Uso:
    python main_multibot.py

============================================================
"""

import os
import sys
import time
import yaml
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.coordinator import BotCoordinator, get_coordinator
from src.core.exchange_client import ExchangeClient
from src.strategies.smart_strategy import SmartStrategy
from src.indicators.technical_indicators import TechnicalIndicators

# ===== IMPORTAÇÃO DO UNICO BOT =====
try:
    from src.strategies.unico_bot import UnicoBot, should_use_unico_bot
    UNICO_BOT_AVAILABLE = True
except ImportError as e:
    UNICO_BOT_AVAILABLE = False
    print(f"⚠️ UnicoBot não disponível: {e}")

# ===== IMPORTAÇÃO DA IA =====
try:
    from src.ai import get_ai_manager, AIManager
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    print(f"⚠️ AI não disponível: {e}")

# ===== IMPORTAÇÃO DO AUTO-TUNER =====
try:
    from src.ai import get_autotuner, AutoTuner
    AUTOTUNER_AVAILABLE = True
except ImportError as e:
    AUTOTUNER_AVAILABLE = False
    print(f"⚠️ AutoTuner não disponível: {e}")


class MultiBotEngine:
    """
    Engine principal que executa todos os bots em paralelo.
    Agora com IA adaptativa e AUTO-TUNER integrados!
    
    MODOS DE OPERAÇÃO:
    1. UNICO BOT: Um único bot gerencia TODAS as cryptos e TODO o saldo
    2. MULTI BOT: 4 bots especializados (estável, médio, volátil, meme)
    """
    
    def __init__(self):
        # ===== VERIFICA MODO DE OPERAÇÃO =====
        self.unico_bot_mode = False
        self.unico_bot = None
        
        if UNICO_BOT_AVAILABLE and should_use_unico_bot():
            self.unico_bot_mode = True
            self.unico_bot = UnicoBot()
            if self.unico_bot.enabled:
                print("=" * 60)
                print("🤖 MODO UNICO BOT ATIVADO")
                print("=" * 60)
                print(f"   → {self.unico_bot.name} gerenciando TODAS as cryptos")
                print(f"   → Símbolos: {len(self.unico_bot.portfolio)}")
                print(f"   → Max posições: {self.unico_bot.trading_config.get('max_positions', 15)}")
                print("=" * 60)
            else:
                self.unico_bot_mode = False
                print("⚠️ UnicoBot está desabilitado no config")
        
        # Coordenador (usado para exchange e configs gerais)
        self.coordinator = get_coordinator()
        
        # Exchange compartilhada
        self.exchange = self.coordinator.exchange
        
        # Indicadores
        self.indicators = TechnicalIndicators()
        
        # ===== INICIALIZAÇÃO DA IA =====
        self.ai_manager = None
        self.ai_enabled = True
        if AI_AVAILABLE:
            try:
                self.ai_manager = get_ai_manager()
                self.ai_manager.start_background_tasks()
                print("🤖 Sistema de IA inicializado!")
            except Exception as e:
                print(f"⚠️ Erro ao inicializar IA: {e}")
                self.ai_enabled = False
        else:
            self.ai_enabled = False
            print("⚠️ IA não disponível - operando sem AI")
        
        # ===== INICIALIZAÇÃO DO AUTO-TUNER =====
        self.autotuner = None
        self.autotuner_enabled = True
        if AUTOTUNER_AVAILABLE:
            try:
                self.autotuner = get_autotuner(self.exchange, "config/bots_config.yaml")
                self.autotuner.start()
                print("🎛️ Sistema de Auto-Tuner inicializado!")
                print("   → Configs serão ajustadas automaticamente baseado no mercado")
            except Exception as e:
                print(f"⚠️ Erro ao inicializar AutoTuner: {e}")
                self.autotuner_enabled = False
        else:
            self.autotuner_enabled = False
            print("⚠️ AutoTuner não disponível - configs estáticas")
        
        # Controle
        self.running = False
        self.iteration = 0
        
        # Posições abertas (global)
        self.positions: dict = {}  # {symbol: {bot_type, entry_price, amount, time, ...}}
        
        # ===== POUPANÇA =====
        self.poupanca = {
            'balance': 0,           # Saldo atual na poupança
            'initial': 0,           # Valor inicial alocado
            'used': 0,              # Quanto já foi usado
            'recovered': 0,         # Quanto já recuperou
        }
        
        # Setup logging
        self.logger = logging.getLogger('MultiBotEngine')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
        
        # Carrega posições existentes
        self._load_positions()
        
        # Arquivo de histórico global
        self.history_file = Path("data/multibot_history.json")
        
        # ===== HISTÓRICO POR BOT =====
        self.bot_history_files = {
            'bot_estavel': Path("data/history/bot_estavel_trades.json"),
            'bot_medio': Path("data/history/bot_medio_trades.json"),
            'bot_volatil': Path("data/history/bot_volatil_trades.json"),
            'bot_meme': Path("data/history/bot_meme_trades.json"),
            'poupanca': Path("data/history/poupanca_trades.json"),
        }
        
        # Cria diretório de histórico se não existir
        Path("data/history").mkdir(parents=True, exist_ok=True)
        
        # Estatísticas por bot
        self.bot_stats = {
            'bot_estavel': self._load_bot_stats('bot_estavel'),
            'bot_medio': self._load_bot_stats('bot_medio'),
            'bot_volatil': self._load_bot_stats('bot_volatil'),
            'bot_meme': self._load_bot_stats('bot_meme'),
            'poupanca': self._load_bot_stats('poupanca'),
        }
        
        # ===== MONITORAMENTO DE CRYPTOS EXTERNAS =====
        # Cryptos que não estão na carteira mas são monitoradas
        self.watchlist = self._load_watchlist()
        self.watchlist_alerts = []  # Alertas de oportunidades
        self.last_watchlist_scan = datetime.now() - timedelta(minutes=5)
    
    def _load_bot_stats(self, bot_type: str) -> dict:
        """Carrega estatísticas do bot do histórico"""
        stats_file = Path(f"data/history/{bot_type}_stats.json")
        default_stats = {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'total_invested': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'win_rate': 0.0,
            'last_trade': None,
            'daily_pnl': 0.0,
            'daily_trades': 0,
            'daily_date': datetime.now().strftime('%Y-%m-%d'),
        }
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    loaded = json.load(f)
                    # Reset daily se mudou o dia
                    if loaded.get('daily_date') != datetime.now().strftime('%Y-%m-%d'):
                        loaded['daily_pnl'] = 0.0
                        loaded['daily_trades'] = 0
                        loaded['daily_date'] = datetime.now().strftime('%Y-%m-%d')
                    return {**default_stats, **loaded}
            except:
                pass
        return default_stats
    
    def _save_bot_stats(self, bot_type: str):
        """Salva estatísticas do bot"""
        stats_file = Path(f"data/history/{bot_type}_stats.json")
        with open(stats_file, 'w') as f:
            json.dump(self.bot_stats[bot_type], f, indent=2)
    
    def _load_watchlist(self) -> list:
        """
        Carrega lista de cryptos para monitorar (fora da carteira).
        Cryptos com potencial baseado em liquidez e volatilidade.
        """
        # Cryptos populares para monitorar
        return [
            # Layer 1 / Layer 2
            {'symbol': 'MATICUSDT', 'name': 'Polygon', 'category': 'medium'},
            {'symbol': 'ARBUSDT', 'name': 'Arbitrum', 'category': 'medium'},
            {'symbol': 'OPUSDT', 'name': 'Optimism', 'category': 'medium'},
            {'symbol': 'APTUSDT', 'name': 'Aptos', 'category': 'medium'},
            {'symbol': 'SUIUSDT', 'name': 'Sui', 'category': 'medium'},
            {'symbol': 'SEIUSDT', 'name': 'Sei', 'category': 'volatile'},
            {'symbol': 'INJUSDT', 'name': 'Injective', 'category': 'volatile'},
            # DeFi
            {'symbol': 'CRVUSDT', 'name': 'Curve', 'category': 'medium'},
            {'symbol': 'COMPUSDT', 'name': 'Compound', 'category': 'stable'},
            {'symbol': 'SNXUSDT', 'name': 'Synthetix', 'category': 'volatile'},
            {'symbol': 'LDOUSDT', 'name': 'Lido', 'category': 'medium'},
            {'symbol': '1INCHUSDT', 'name': '1inch', 'category': 'medium'},
            # AI / Storage
            {'symbol': 'FETUSDT', 'name': 'Fetch.ai', 'category': 'volatile'},
            {'symbol': 'RENDERUSDT', 'name': 'Render', 'category': 'volatile'},
            {'symbol': 'FILUSDT', 'name': 'Filecoin', 'category': 'medium'},
            {'symbol': 'ARUSDT', 'name': 'Arweave', 'category': 'volatile'},
            # Gaming / NFT
            {'symbol': 'IMXUSDT', 'name': 'Immutable X', 'category': 'volatile'},
            {'symbol': 'ENJUSDT', 'name': 'Enjin', 'category': 'volatile'},
            {'symbol': 'CHZUSDT', 'name': 'Chiliz', 'category': 'volatile'},
            # Outros
            {'symbol': 'VETUSDT', 'name': 'VeChain', 'category': 'medium'},
            {'symbol': 'ICPUSDT', 'name': 'Internet Computer', 'category': 'volatile'},
            {'symbol': 'HBARUSDT', 'name': 'Hedera', 'category': 'medium'},
            {'symbol': 'ALGOUSDT', 'name': 'Algorand', 'category': 'medium'},
            {'symbol': 'EGLDUSDT', 'name': 'MultiversX', 'category': 'medium'},
            {'symbol': 'RUNEUSDT', 'name': 'THORChain', 'category': 'volatile'},
            {'symbol': 'KASUSDT', 'name': 'Kaspa', 'category': 'volatile'},
            # Memes
            {'symbol': 'WIFUSDT', 'name': 'Dogwifhat', 'category': 'meme'},
            {'symbol': '1000SATSUSDT', 'name': '1000SATS', 'category': 'meme'},
            {'symbol': 'MEMEUSDT', 'name': 'Memecoin', 'category': 'meme'},
        ]
    
    def scan_watchlist(self) -> list:
        """
        Escaneia cryptos da watchlist procurando oportunidades.
        Retorna lista de alertas com oportunidades encontradas.
        """
        alerts = []
        
        # Só escaneia a cada 5 minutos
        if (datetime.now() - self.last_watchlist_scan).total_seconds() < 300:
            return self.watchlist_alerts
        
        self.last_watchlist_scan = datetime.now()
        
        # Obtém símbolos já na carteira
        portfolio_symbols = set()
        for bot in self.coordinator.bots.values():
            for crypto in bot.portfolio:
                portfolio_symbols.add(crypto['symbol'])
        
        for crypto in self.watchlist:
            symbol = crypto['symbol']
            
            # Pula se já está na carteira
            if symbol in portfolio_symbols:
                continue
            
            try:
                # Obtém dados OHLCV
                df = self.exchange.fetch_ohlcv_dataframe(symbol, '1m', limit=100)
                if df is None or len(df) < 50:
                    continue
                
                # Calcula RSI
                from src.strategies.smart_strategy import SmartStrategy
                strategy = SmartStrategy()
                df = strategy.calculate_indicators(df)
                
                current_rsi = df.iloc[-1].get('rsi', 50)
                current_price = df.iloc[-1]['close']
                
                # Define thresholds por categoria
                rsi_thresholds = {
                    'stable': 35,
                    'medium': 32,
                    'volatile': 28,
                    'meme': 25
                }
                
                threshold = rsi_thresholds.get(crypto['category'], 30)
                
                # Alerta se RSI muito baixo
                if current_rsi < threshold:
                    alert = {
                        'symbol': symbol,
                        'name': crypto['name'],
                        'category': crypto['category'],
                        'rsi': round(current_rsi, 1),
                        'price': current_price,
                        'threshold': threshold,
                        'timestamp': datetime.now().isoformat(),
                        'suggested_bot': self._suggest_bot_for_crypto(crypto['category'])
                    }
                    alerts.append(alert)
                    
            except Exception as e:
                pass  # Ignora erros silenciosamente
        
        # Ordena por RSI (menor = melhor oportunidade)
        alerts.sort(key=lambda x: x['rsi'])
        
        # Mantém últimos 10 alertas
        self.watchlist_alerts = alerts[:10]
        
        return self.watchlist_alerts
    
    def _suggest_bot_for_crypto(self, category: str) -> str:
        """Sugere qual bot deve operar uma crypto baseado na categoria"""
        mapping = {
            'stable': 'bot_estavel',
            'medium': 'bot_medio',
            'volatile': 'bot_volatil',
            'meme': 'bot_meme'
        }
        return mapping.get(category, 'bot_medio')
    
    def get_watchlist_opportunities(self) -> list:
        """Retorna oportunidades da watchlist para o dashboard"""
        return self.scan_watchlist()
        
    def _load_positions(self):
        """Carrega posições abertas do arquivo"""
        positions_file = Path("data/multibot_positions.json")
        if positions_file.exists():
            try:
                with open(positions_file, 'r') as f:
                    self.positions = json.load(f)
                    
                    # Converte timestamps
                    for symbol, pos in self.positions.items():
                        if 'time' in pos and isinstance(pos['time'], str):
                            pos['time'] = datetime.fromisoformat(pos['time'])
                    
                self.logger.info(f"📂 {len(self.positions)} posições restauradas")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao carregar posições: {e}")
    
    def _save_positions(self):
        """Salva posições abertas no arquivo"""
        Path("data").mkdir(parents=True, exist_ok=True)
        
        # Prepara para JSON (converte datetime)
        positions_to_save = {}
        for symbol, pos in self.positions.items():
            positions_to_save[symbol] = pos.copy()
            if 'time' in positions_to_save[symbol]:
                positions_to_save[symbol]['time'] = pos['time'].isoformat()
        
        with open("data/multibot_positions.json", 'w') as f:
            json.dump(positions_to_save, f, indent=2)
    
    def _save_trade_history(self, trade: dict):
        """Salva histórico de trades (global)"""
        history = []
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        history.append(trade)
        
        # Mantém últimos 1000 trades
        if len(history) > 1000:
            history = history[-1000:]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _save_bot_trade(self, bot_type: str, trade: dict):
        """
        Salva trade no histórico específico do bot
        
        Args:
            bot_type: 'bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme', 'poupanca'
            trade: dict com informações do trade
        """
        # Arquivo de histórico do bot
        history_file = self.bot_history_files.get(bot_type, self.history_file)
        
        # Carrega histórico existente
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        # Adiciona trade com timestamp
        trade_record = {
            **trade,
            'timestamp': datetime.now().isoformat(),
            'bot_type': bot_type,
        }
        history.append(trade_record)
        
        # Mantém últimos 500 trades por bot
        if len(history) > 500:
            history = history[-500:]
        
        # Salva
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        # Atualiza estatísticas do bot
        self._update_bot_stats(bot_type, trade)
        
        # Também salva no histórico global
        self._save_trade_history(trade_record)
    
    def _update_bot_stats(self, bot_type: str, trade: dict):
        """Atualiza estatísticas do bot após um trade"""
        stats = self.bot_stats[bot_type]
        pnl = trade.get('pnl', 0)
        invested = trade.get('invested', 0)
        
        # Contadores
        stats['total_trades'] += 1
        stats['total_pnl'] += pnl
        stats['total_invested'] += invested
        stats['daily_trades'] += 1
        stats['daily_pnl'] += pnl
        
        # Win/Loss
        if pnl > 0:
            stats['wins'] += 1
            if pnl > stats['best_trade']:
                stats['best_trade'] = pnl
            # Média de wins
            win_count = stats['wins']
            stats['avg_win'] = ((stats['avg_win'] * (win_count - 1)) + pnl) / win_count
        else:
            stats['losses'] += 1
            if pnl < stats['worst_trade']:
                stats['worst_trade'] = pnl
            # Média de losses
            loss_count = stats['losses']
            if loss_count > 0:
                stats['avg_loss'] = ((stats['avg_loss'] * (loss_count - 1)) + pnl) / loss_count
        
        # Win rate
        if stats['total_trades'] > 0:
            stats['win_rate'] = (stats['wins'] / stats['total_trades']) * 100
        
        # Último trade
        stats['last_trade'] = datetime.now().isoformat()
        
        # Salva
        self._save_bot_stats(bot_type)
    
    def get_bot_summary(self, bot_type: str) -> dict:
        """Retorna resumo completo das estatísticas do bot"""
        stats = self.bot_stats.get(bot_type, {})
        
        return {
            'bot_type': bot_type,
            'total_trades': stats.get('total_trades', 0),
            'wins': stats.get('wins', 0),
            'losses': stats.get('losses', 0),
            'win_rate': round(stats.get('win_rate', 0), 1),
            'total_pnl': round(stats.get('total_pnl', 0), 2),
            'daily_pnl': round(stats.get('daily_pnl', 0), 2),
            'daily_trades': stats.get('daily_trades', 0),
            'best_trade': round(stats.get('best_trade', 0), 2),
            'worst_trade': round(stats.get('worst_trade', 0), 2),
            'avg_win': round(stats.get('avg_win', 0), 2),
            'avg_loss': round(stats.get('avg_loss', 0), 2),
        }
    
    def get_all_bots_summary(self) -> dict:
        """Retorna resumo de todos os bots"""
        return {
            bot_type: self.get_bot_summary(bot_type)
            for bot_type in ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme', 'poupanca']
        }

    # ===== FUNÇÕES DE INICIALIZAÇÃO =====
    
    def liquidate_all_positions(self) -> dict:
        """
        🔴 VENDE TODAS AS POSIÇÕES ABERTAS
        Chamado no início para começar limpo.
        
        Returns:
            dict com resumo da liquidação
        """
        print("\n" + "="*70)
        print("🔴 LIQUIDANDO TODAS AS POSIÇÕES...")
        print("="*70)
        
        results = {
            'sold': 0,
            'failed': 0,
            'total_pnl': 0,
            'positions': []
        }
        
        # Primeiro, obtém todas as posições na exchange
        try:
            balance = self.exchange.fetch_balance()
            if not balance:
                print("⚠️ Não foi possível obter saldo da exchange")
                return results
            
            # Lista de cryptos para vender (exclui USDT)
            cryptos_to_sell = []
            for asset, data in balance.items():
                if asset == 'USDT':
                    continue
                free = data.get('free', 0)
                if free > 0:
                    cryptos_to_sell.append({
                        'asset': asset,
                        'symbol': f"{asset}USDT",
                        'amount': free
                    })
            
            if not cryptos_to_sell:
                print("✅ Nenhuma posição para liquidar")
                return results
            
            print(f"📊 Encontradas {len(cryptos_to_sell)} posições para liquidar:")
            
            for crypto in cryptos_to_sell:
                symbol = crypto['symbol']
                amount = crypto['amount']
                
                try:
                    # Obtém preço atual
                    ticker = self.exchange.fetch_ticker(symbol)
                    if not ticker:
                        continue
                    
                    current_price = ticker.get('last', ticker.get('close', 0))
                    
                    # Executa venda
                    order = self.exchange.create_market_order(
                        symbol=symbol,
                        side='sell',
                        amount=amount
                    )
                    
                    if order:
                        results['sold'] += 1
                        value_usd = amount * current_price
                        
                        # Se tinha registro local da posição, calcula PnL
                        if symbol in self.positions:
                            pos = self.positions[symbol]
                            pnl_pct = ((current_price - pos['entry_price']) / pos['entry_price']) * 100
                            pnl_usd = pos['amount_usd'] * (pnl_pct / 100)
                            results['total_pnl'] += pnl_usd
                            
                            print(f"   💰 {symbol}: {amount:.6f} @ ${current_price:.4f} = ${value_usd:.2f} | PnL: {pnl_usd:+.2f}")
                            
                            # Remove do registro local
                            del self.positions[symbol]
                        else:
                            print(f"   💰 {symbol}: {amount:.6f} @ ${current_price:.4f} = ${value_usd:.2f}")
                        
                        results['positions'].append({
                            'symbol': symbol,
                            'amount': amount,
                            'price': current_price,
                            'value': value_usd
                        })
                    else:
                        results['failed'] += 1
                        print(f"   ❌ {symbol}: Falha na venda")
                        
                except Exception as e:
                    results['failed'] += 1
                    print(f"   ❌ {symbol}: Erro - {e}")
            
            # Salva estado limpo
            self._save_positions()
            
        except Exception as e:
            self.logger.error(f"Erro na liquidação: {e}")
        
        print(f"\n✅ Liquidação completa: {results['sold']} vendidas, {results['failed']} falharam")
        if results['total_pnl'] != 0:
            print(f"   PnL total da liquidação: ${results['total_pnl']:+.2f}")
        
        return results
    
    def initialize_poupanca(self, total_balance: float) -> float:
        """
        💰 INICIALIZA A POUPANÇA
        Separa parte do capital para super oportunidades.
        
        Args:
            total_balance: Saldo total em USDT
            
        Returns:
            Valor alocado para poupança
        """
        config = self.coordinator.config.get('global', {}).get('poupanca', {})
        
        if not config.get('enabled', False):
            print("ℹ️ Poupança desabilitada nas configurações")
            return 0
        
        percentual = config.get('percentual', 15) / 100
        min_balance = config.get('min_balance', 500)
        
        # Calcula valor da poupança
        poupanca_value = total_balance * percentual
        poupanca_value = max(poupanca_value, min_balance)
        
        # Não pode ser mais que 30% do total
        poupanca_value = min(poupanca_value, total_balance * 0.3)
        
        self.poupanca = {
            'balance': poupanca_value,
            'initial': poupanca_value,
            'used': 0,
            'recovered': 0,
        }
        
        print(f"\n💰 POUPANÇA INICIALIZADA:")
        print(f"   Valor: ${poupanca_value:.2f} ({percentual*100:.0f}% do capital)")
        print(f"   Para: Super oportunidades (RSI < {config.get('super_opportunity_threshold', 20)})")
        
        # Salva estado da poupança
        self._save_poupanca()
        
        return poupanca_value
    
    def _save_poupanca(self):
        """Salva estado da poupança"""
        Path("data").mkdir(parents=True, exist_ok=True)
        with open("data/poupanca.json", 'w') as f:
            json.dump(self.poupanca, f, indent=2)
    
    def _save_dashboard_data(self):
        """
        Salva dados para o dashboard:
        - Saldo USDT
        - Saldo em Cripto
        - Saldo Total
        - Progresso Meta Diária
        """
        try:
            balance = self.exchange.fetch_balance()
            if not balance:
                return
            
            # Saldo USDT
            usdt_balance = balance.get('USDT', {}).get('free', 0) + balance.get('USDT', {}).get('used', 0)
            
            # Saldo em cryptos
            crypto_balance = 0
            crypto_positions = {}
            
            for asset, data in balance.items():
                if asset in ['USDT', 'info', 'free', 'used', 'total', 'debt', 'timestamp', 'datetime']:
                    continue
                
                total_amount = data.get('free', 0) + data.get('used', 0)
                if total_amount > 0:
                    try:
                        # Obtém preço atual
                        ticker = self.exchange.fetch_ticker(f"{asset}USDT")
                        if ticker:
                            price = ticker.get('last', ticker.get('close', 0))
                            value_usd = total_amount * price
                            if value_usd > 0.01:  # Ignora poeira
                                crypto_balance += value_usd
                                crypto_positions[asset] = {
                                    'amount': total_amount,
                                    'price': price,
                                    'value_usd': value_usd
                                }
                    except:
                        pass
            
            # Total
            total_balance = usdt_balance + crypto_balance
            
            # Meta diária (configurável, padrão 1% do capital)
            config = self.coordinator.config.get('global', {}).get('daily_target', {})
            daily_target_pct = config.get('percentage', 1.0)  # 1% por padrão
            daily_target_usd = total_balance * (daily_target_pct / 100)
            
            # PnL do dia
            history = []
            if self.history_file.exists():
                try:
                    with open(self.history_file, 'r') as f:
                        history = json.load(f)
                except:
                    pass
            
            today = datetime.now().date().isoformat()
            daily_pnl = sum(
                t.get('pnl_usd', 0) 
                for t in history 
                if t.get('exit_time', t.get('timestamp', '')).startswith(today)
            )
            
            # Progresso da meta
            if daily_target_usd > 0:
                daily_progress = (daily_pnl / daily_target_usd) * 100
            else:
                daily_progress = 0
            
            # Salva dados
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'usdt_balance': usdt_balance,
                'crypto_balance': crypto_balance,
                'total_balance': total_balance,
                'crypto_positions': crypto_positions,
                'poupanca': self.poupanca.get('balance', 0),
                'daily_target_pct': daily_target_pct,
                'daily_target_usd': daily_target_usd,
                'daily_pnl': daily_pnl,
                'daily_progress': daily_progress,
            }
            
            with open("data/dashboard_balances.json", 'w') as f:
                json.dump(dashboard_data, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao salvar dados do dashboard: {e}")
    
    def _load_poupanca(self):
        """Carrega estado da poupança"""
        poupanca_file = Path("data/poupanca.json")
        if poupanca_file.exists():
            try:
                with open(poupanca_file, 'r') as f:
                    self.poupanca = json.load(f)
                self.logger.info(f"💰 Poupança carregada: ${self.poupanca['balance']:.2f}")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao carregar poupança: {e}")
    
    def check_super_opportunity(self, symbol: str, rsi: float) -> bool:
        """
        🔥 VERIFICA SE É SUPER OPORTUNIDADE
        
        Super oportunidade = RSI muito baixo em crypto importante
        Usa dinheiro da poupança para comprar mais.
        """
        config = self.coordinator.config.get('global', {}).get('poupanca', {})
        
        if not config.get('enabled', False):
            return False
        
        # Verifica se crypto está na lista permitida
        allowed_cryptos = config.get('cryptos_allowed', ['BTCUSDT', 'ETHUSDT'])
        if symbol not in allowed_cryptos:
            return False
        
        # Verifica RSI threshold
        threshold = config.get('super_opportunity_threshold', 20)
        if rsi > threshold:
            return False
        
        # Verifica se tem poupança disponível
        min_balance = config.get('min_balance', 500)
        if self.poupanca['balance'] < min_balance:
            return False
        
        return True
    
    def use_poupanca(self, symbol: str, amount: float) -> float:
        """
        💸 USA DINHEIRO DA POUPANÇA
        
        Returns:
            Valor usado (pode ser menor que solicitado)
        """
        config = self.coordinator.config.get('global', {}).get('poupanca', {})
        max_use_pct = config.get('max_use_per_trade', 30) / 100
        min_balance = config.get('min_balance', 500)
        
        # Máximo que pode usar
        available = self.poupanca['balance'] - min_balance
        max_use = self.poupanca['balance'] * max_use_pct
        
        # Usa o menor entre: solicitado, máximo permitido, disponível
        use_amount = min(amount, max_use, available)
        
        if use_amount <= 0:
            return 0
        
        self.poupanca['balance'] -= use_amount
        self.poupanca['used'] += use_amount
        self._save_poupanca()
        
        self.logger.info(f"💸 POUPANÇA: Usou ${use_amount:.2f} para {symbol}")
        self.logger.info(f"   Saldo poupança: ${self.poupanca['balance']:.2f}")
        
        return use_amount
    
    def recover_to_poupanca(self, profit: float) -> float:
        """
        💰 RECUPERA LUCRO PARA POUPANÇA
        
        Parte do lucro volta para a poupança.
        """
        if profit <= 0:
            return 0
        
        config = self.coordinator.config.get('global', {}).get('poupanca', {})
        recovery_rate = config.get('recovery_rate', 10) / 100
        
        # Só recupera se poupança estiver abaixo do inicial
        if self.poupanca['balance'] >= self.poupanca['initial']:
            return 0
        
        # Recupera parte do lucro
        recover_amount = profit * recovery_rate
        
        # Não passa do inicial
        max_recover = self.poupanca['initial'] - self.poupanca['balance']
        recover_amount = min(recover_amount, max_recover)
        
        if recover_amount > 0:
            self.poupanca['balance'] += recover_amount
            self.poupanca['recovered'] += recover_amount
            self._save_poupanca()
            
            self.logger.info(f"💰 POUPANÇA: Recuperou ${recover_amount:.2f}")
        
        return recover_amount
    
    def get_balance(self) -> float:
        """Retorna saldo USDT"""
        try:
            balance = self.exchange.fetch_balance()
            if balance:
                return balance.get('USDT', {}).get('free', 0)
            return 0
        except Exception as e:
            self.logger.error(f"Erro ao obter saldo: {e}")
            return 0
    
    def _sync_positions_with_exchange(self):
        """
        Sincroniza posições locais com o saldo real na exchange.
        Detecta cryptos que temos mas não estão registradas.
        """
        print("   🔄 Sincronizando posições com a exchange...")
        
        try:
            balance = self.exchange.fetch_balance()
            if not balance:
                print("   ⚠️ Não foi possível obter saldo")
                return
            
            synced = 0
            for asset, data in balance.items():
                if asset in ['USDT', 'info', 'free', 'used', 'total', 'debt', 'timestamp', 'datetime']:
                    continue
                
                total_amount = data.get('free', 0) + data.get('used', 0)
                if total_amount > 0.0001:
                    symbol = f"{asset}USDT"
                    
                    # Se não está nas nossas posições registradas, adiciona
                    if symbol not in self.positions:
                        try:
                            ticker = self.exchange.fetch_ticker(symbol)
                            if ticker:
                                current_price = ticker.get('last', ticker.get('close', 0))
                                value_usd = total_amount * current_price
                                
                                if value_usd > 1:  # Só registra se valor > $1
                                    self.positions[symbol] = {
                                        'bot_type': 'unico_bot' if self.unico_bot_mode else 'unknown',
                                        'entry_price': current_price,  # Usa preço atual como referência
                                        'amount': total_amount,
                                        'amount_usd': value_usd,
                                        'time': datetime.now(),
                                        'synced': True  # Marca que foi sincronizado
                                    }
                                    synced += 1
                                    print(f"      ✅ {symbol}: {total_amount:.6f} (${value_usd:.2f})")
                        except:
                            pass
            
            if synced > 0:
                print(f"   📊 {synced} posições sincronizadas")
                self._save_positions()
            else:
                print(f"   ✅ Posições já estavam sincronizadas ({len(self.positions)} registradas)")
                
        except Exception as e:
            self.logger.error(f"Erro ao sincronizar: {e}")
    
    def _run_unico_bot_cycle(self):
        """
        Executa um ciclo completo do UnicoBot.
        Processa TODAS as cryptos do portfolio.
        """
        if not self.unico_bot or not self.unico_bot.enabled:
            return
        
        import pandas as pd
        
        # Configurações do UnicoBot
        trading_config = self.unico_bot.trading_config
        max_positions = trading_config.get('max_positions', 15)
        amount_per_trade = trading_config.get('amount_per_trade', 50)
        
        # Conta posições abertas
        open_positions = len(self.positions)
        
        # ===== 1. VERIFICA POSIÇÕES EXISTENTES (VENDER?) =====
        positions_to_close = []
        
        for symbol, pos in list(self.positions.items()):
            try:
                # Obtém preço atual
                ticker = self.exchange.fetch_ticker(symbol)
                if not ticker:
                    continue
                
                current_price = ticker.get('last', ticker.get('close', 0))
                entry_price = pos.get('entry_price', current_price)
                entry_time = pos.get('time', datetime.now())
                
                if isinstance(entry_time, str):
                    entry_time = datetime.fromisoformat(entry_time)
                
                # Calcula PnL
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                pnl_usd = pos.get('amount_usd', 0) * (pnl_pct / 100)
                
                # Obtém dados para análise
                ohlcv = self.exchange.fetch_ohlcv(symbol, '1m', limit=100)
                df = None
                if ohlcv and len(ohlcv) > 0:
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # Verifica se deve vender
                should_close, reason = self.unico_bot.should_close(
                    symbol=symbol,
                    entry_price=entry_price,
                    current_price=current_price,
                    entry_time=entry_time,
                    df=df
                )
                
                if should_close:
                    positions_to_close.append({
                        'symbol': symbol,
                        'reason': reason,
                        'pnl_pct': pnl_pct,
                        'pnl_usd': pnl_usd,
                        'current_price': current_price
                    })
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao verificar {symbol}: {e}")
        
        # Executa vendas
        for close_info in positions_to_close:
            symbol = close_info['symbol']
            try:
                pos = self.positions[symbol]
                amount = pos.get('amount', 0)
                
                # Executa venda
                order = self.exchange.create_market_order(
                    symbol=symbol,
                    side='sell',
                    amount=amount
                )
                
                if order:
                    pnl_emoji = "✅" if close_info['pnl_usd'] >= 0 else "❌"
                    print(f"{pnl_emoji} VENDA {symbol}: {close_info['reason']} | PnL: ${close_info['pnl_usd']:+.2f}")
                    
                    # Registra trade
                    trade = {
                        'symbol': symbol,
                        'side': 'sell',
                        'amount': amount,
                        'price': close_info['current_price'],
                        'pnl_pct': close_info['pnl_pct'],
                        'pnl_usd': close_info['pnl_usd'],
                        'reason': close_info['reason'],
                        'bot_type': 'unico_bot'
                    }
                    self._save_bot_trade('unico_bot', trade)
                    
                    # Remove da lista de posições
                    del self.positions[symbol]
                    open_positions -= 1
                    
            except Exception as e:
                print(f"❌ Erro ao vender {symbol}: {e}")
        
        # ===== 2. PROCURA NOVAS OPORTUNIDADES (COMPRAR?) =====
        if open_positions < max_positions:
            # Verifica saldo disponível
            usdt_balance = self.get_balance()
            
            if usdt_balance >= amount_per_trade:
                for crypto in self.unico_bot.portfolio:
                    if open_positions >= max_positions:
                        break
                    
                    symbol = crypto['symbol']
                    
                    # Pula se já tem posição
                    if symbol in self.positions:
                        continue
                    
                    try:
                        # Obtém dados
                        ohlcv = self.exchange.fetch_ohlcv(symbol, '1m', limit=100)
                        if not ohlcv or len(ohlcv) < 50:
                            continue
                        
                        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        
                        # Analisa
                        signal, reason, indicators = self.unico_bot.analyze_symbol(symbol, df)
                        
                        if signal == 'BUY':
                            # Calcula quantidade
                            current_price = df.iloc[-1]['close']
                            trade_amount = min(amount_per_trade, usdt_balance)
                            crypto_amount = trade_amount / current_price
                            
                            # Executa compra
                            order = self.exchange.create_market_order(
                                symbol=symbol,
                                side='buy',
                                amount=crypto_amount
                            )
                            
                            if order:
                                print(f"🟢 COMPRA {symbol}: {reason} | ${trade_amount:.2f}")
                                
                                # Registra posição
                                self.positions[symbol] = {
                                    'bot_type': 'unico_bot',
                                    'entry_price': current_price,
                                    'amount': crypto_amount,
                                    'amount_usd': trade_amount,
                                    'time': datetime.now(),
                                    'reason': reason
                                }
                                
                                # Atualiza tempo do último trade
                                self.unico_bot.update_trade_time(symbol)
                                
                                open_positions += 1
                                usdt_balance -= trade_amount
                                
                    except Exception as e:
                        self.logger.warning(f"⚠️ Erro ao analisar {symbol}: {e}")
        
        # Salva posições
        self._save_positions()
    
    # ===== MÉTODOS DO AUTO-TUNER =====
    
    def get_autotuner_status(self) -> dict:
        """Retorna status do auto-tuner"""
        if not self.autotuner_enabled or not self.autotuner:
            return {
                'enabled': False,
                'message': 'AutoTuner não disponível'
            }
        return self.autotuner.get_status()
    
    def get_market_report(self) -> str:
        """Retorna relatório de mercado formatado"""
        if not self.autotuner_enabled or not self.autotuner:
            return "AutoTuner não disponível"
        return self.autotuner.get_market_report()
    
    def force_tune(self) -> dict:
        """Força ajuste imediato das configs"""
        if not self.autotuner_enabled or not self.autotuner:
            return {'error': 'AutoTuner não disponível'}
        return self.autotuner.force_tune()
    
    def get_dynamic_config(self, bot_type: str) -> dict:
        """Retorna config dinâmica atual para um bot"""
        if not self.autotuner_enabled or not self.autotuner:
            return {}
        return self.autotuner.get_current_adjustments(bot_type)
    
    def get_ai_data(self) -> dict:
        """
        Retorna dados da IA para o dashboard.
        
        Returns:
            Dict com informações de mercado, aprendizado e configurações
        """
        if not self.ai_enabled or not self.ai_manager:
            return {
                'enabled': False,
                'message': 'AI não disponível'
            }
        
        try:
            return {
                'enabled': True,
                **self.ai_manager.get_dashboard_data()
            }
        except Exception as e:
            return {
                'enabled': False,
                'error': str(e)
            }
    
    def get_ai_bot_insights(self, bot_name: str) -> dict:
        """
        Retorna insights da AI para um bot específico.
        
        Args:
            bot_name: Nome do bot
            
        Returns:
            Dict com insights
        """
        if not self.ai_enabled or not self.ai_manager:
            return {}
        
        try:
            return self.ai_manager.get_bot_insights(bot_name)
        except:
            return {}
    
    def set_ai_auto_adjust(self, enabled: bool):
        """Habilita/desabilita ajuste automático da AI"""
        if self.ai_manager:
            self.ai_manager.set_auto_adjust(enabled)
    
    def set_ai_risk_profile(self, profile: str, bots: list = None) -> dict:
        """Define perfil de risco via AI"""
        if self.ai_manager:
            return self.ai_manager.set_risk_profile(profile, bots)
        return {}
    
    def force_ai_market_scan(self) -> dict:
        """Força scan de mercado da AI"""
        if self.ai_manager:
            return self.ai_manager.force_market_scan()
        return {}
    
    def run_bot_cycle(self, bot_type: str):
        """
        Executa um ciclo de análise para um bot específico.
        """
        bot = self.coordinator.bots.get(bot_type)
        if not bot or not bot.enabled:
            return
        
        bot.stats.status = "running"
        
        for crypto in bot.portfolio:
            symbol = crypto['symbol']
            
            try:
                # Obtém candles
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=bot.trading_config.get('timeframe', '1m'),
                    limit=200
                )
                
                if ohlcv is None or len(ohlcv) == 0:
                    continue
                
                # Converte para DataFrame
                import pandas as pd
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Adiciona indicadores usando o método da estratégia
                df = bot.strategy.calculate_indicators(df)
                
                current_price = df.iloc[-1]['close']
                current_rsi = df.iloc[-1].get('rsi', 50)
                
                # Verifica se tem posição aberta
                if symbol in self.positions:
                    pos = self.positions[symbol]
                    
                    # Calcula o tamanho da posição em USDT
                    position_size = pos.get('amount', 0) * pos.get('entry_price', 0)
                    
                    # Verifica se deve vender
                    should_sell, reason = bot.should_sell_position(
                        symbol=symbol,
                        entry_price=pos['entry_price'],
                        current_price=current_price,
                        df=df,
                        position_time=pos['time'],
                        position_size=position_size
                    )
                    
                    if should_sell:
                        self._close_position(symbol, current_price, reason, bot_type)
                else:
                    # ===== VERIFICA SUPER OPORTUNIDADE =====
                    if self.check_super_opportunity(symbol, current_rsi):
                        self._open_super_opportunity(symbol, current_price, current_rsi, bot_type, bot)
                    
                    # ===== VERIFICA SINAL NORMAL =====
                    elif len(self.positions) < self._get_max_total_positions():
                        if bot.stats.open_positions < bot.stats.max_positions:
                            
                            signal, reason, indicators = bot.analyze_symbol(symbol, df)
                            
                            if signal == 'BUY':
                                self._open_position(symbol, current_price, reason, bot_type, bot)
                
            except Exception as e:
                self.logger.error(f"[{bot.name}] Erro em {symbol}: {e}")
        
        bot.stats.status = "idle"
        bot.stats.last_update = datetime.now().isoformat()
    
    def _get_max_total_positions(self) -> int:
        """Retorna número máximo de posições total (todos os bots)"""
        total = 0
        for bot in self.coordinator.bots.values():
            if bot.enabled:
                total += bot.stats.max_positions
        return total
    
    def _open_super_opportunity(self, symbol: str, price: float, rsi: float, bot_type: str, bot):
        """
        🔥 ABRE POSIÇÃO COM DINHEIRO DA POUPANÇA
        
        Usa dinheiro extra da poupança para super oportunidades.
        """
        config = self.coordinator.config.get('global', {}).get('poupanca', {})
        
        # Valor base do trade normal
        base_amount = bot.trading_config.get('amount_per_trade', 500)
        
        # Usa poupança para adicionar mais
        extra_amount = self.use_poupanca(symbol, base_amount)
        total_amount = base_amount + extra_amount
        
        # Verifica saldo (não inclui a poupança que foi reservada)
        balance = self.get_balance()
        if balance < base_amount:
            self.logger.warning(f"Saldo insuficiente: ${balance:.2f} < ${base_amount}")
            return
        
        try:
            # Calcula quantidade de crypto
            amount_crypto = total_amount / price
            
            # Executa ordem
            order = self.exchange.create_market_order(
                symbol=symbol,
                side='buy',
                amount=amount_crypto
            )
            
            if order:
                # Registra posição
                self.positions[symbol] = {
                    'bot_type': bot_type,
                    'entry_price': price,
                    'amount': order.get('filled', amount_crypto),
                    'amount_usd': total_amount,
                    'from_poupanca': extra_amount,  # Marca quanto veio da poupança
                    'time': datetime.now(),
                    'reason': f"🔥 SUPER OPORTUNIDADE RSI={rsi:.1f}",
                    'order_id': order.get('id'),
                    'is_super_opportunity': True
                }
                
                bot.stats.open_positions += 1
                self._save_positions()
                
                self.logger.info(f"🔥🔥🔥 SUPER OPORTUNIDADE DETECTADA!")
                self.logger.info(f"[{bot.name}] COMPRA {symbol} @ ${price:.2f}")
                self.logger.info(f"   RSI: {rsi:.1f} (muito baixo!)")
                self.logger.info(f"   Valor: ${total_amount:.2f} (${base_amount:.2f} + ${extra_amount:.2f} poupança)")
                
        except Exception as e:
            self.logger.error(f"Erro ao abrir super oportunidade {symbol}: {e}")
    
    def _open_position(self, symbol: str, price: float, reason: str, bot_type: str, bot):
        """Abre uma posição"""
        amount_usd = bot.trading_config.get('amount_per_trade', 500)
        
        # ===== VERIFICAÇÃO DA IA =====
        if self.ai_enabled and self.ai_manager:
            try:
                trade_params = {
                    'symbol': symbol,
                    'buy_reason': reason,
                    'entry_price': price,
                    'amount': amount_usd
                }
                ai_decision = self.ai_manager.should_buy(symbol, bot_type, trade_params)
                
                if not ai_decision.get('should_buy', True):
                    reasons = ai_decision.get('reasons', [])
                    self.logger.info(f"🤖 [AI] Bloqueou compra de {symbol}: {', '.join(reasons)}")
                    return
                
                # Log de warnings da AI
                for warning in ai_decision.get('warnings', []):
                    self.logger.info(f"🤖 [AI] {warning}")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Erro na AI: {e} - prosseguindo com compra")
        
        # Verifica saldo
        balance = self.get_balance()
        if balance < amount_usd:
            self.logger.warning(f"Saldo insuficiente: ${balance:.2f} < ${amount_usd}")
            return
        
        try:
            # Calcula quantidade de crypto
            amount_crypto = amount_usd / price
            
            # Executa ordem
            order = self.exchange.create_market_order(
                symbol=symbol,
                side='buy',
                amount=amount_crypto
            )
            
            if order:
                # Registra posição
                self.positions[symbol] = {
                    'bot_type': bot_type,
                    'entry_price': price,
                    'amount': order.get('filled', amount_crypto),
                    'amount_usd': amount_usd,
                    'time': datetime.now(),
                    'reason': reason,
                    'order_id': order.get('id')
                }
                
                bot.stats.open_positions += 1
                self._save_positions()
                
                self.logger.info(f"[{bot.name}] COMPRA {symbol} @ {price:.4f}")
                self.logger.info(f"   Razao: {reason}")
                
        except Exception as e:
            self.logger.error(f"Erro ao abrir posicao {symbol}: {e}")
    
    def _close_position(self, symbol: str, price: float, reason: str, bot_type: str):
        """Fecha uma posição"""
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        bot = self.coordinator.bots.get(pos['bot_type'])
        
        if not bot:
            return
        
        try:
            # Executa ordem de venda
            order = self.exchange.create_market_order(
                symbol=symbol,
                side='sell',
                amount=pos['amount']
            )
            
            if order:
                # Calcula PnL
                entry_price = pos['entry_price']
                pnl_pct = ((price - entry_price) / entry_price) * 100
                pnl_usd = pos['amount_usd'] * (pnl_pct / 100)
                is_win = pnl_usd > 0
                
                # Atualiza estatísticas do bot
                bot.update_stats(pnl_usd, is_win)
                
                # ===== RECUPERA PARA POUPANÇA =====
                if is_win:
                    recovered = self.recover_to_poupanca(pnl_usd)
                    if recovered > 0:
                        self.logger.info(f"   💰 Recuperado ${recovered:.2f} para poupança")
                
                # Remove posição
                del self.positions[symbol]
                bot.stats.open_positions -= 1
                self._save_positions()
                
                # Salva histórico
                trade = {
                    'symbol': symbol,
                    'bot_type': pos['bot_type'],
                    'bot_name': bot.name,
                    'entry_price': entry_price,
                    'exit_price': price,
                    'pnl_pct': pnl_pct,
                    'pnl_usd': pnl_usd,
                    'invested': pos['amount_usd'],
                    'reason': reason,
                    'entry_time': pos['time'].isoformat(),
                    'exit_time': datetime.now().isoformat(),
                    'duration_min': (datetime.now() - pos['time']).total_seconds() / 60,
                    'was_super_opportunity': pos.get('is_super_opportunity', False),
                    'from_poupanca': pos.get('from_poupanca', 0)
                }
                
                # Salva no histórico do bot específico
                self._save_bot_trade(pos['bot_type'], trade)
                
                # Log
                status = "WIN" if is_win else "LOSS"
                super_tag = "[SUPER] " if pos.get('is_super_opportunity') else ""
                self.logger.info(f"[{status}] [{bot.name}] {super_tag}VENDA {symbol} @ {price:.4f}")
                self.logger.info(f"   Entrada: {entry_price:.4f} -> Saida: {price:.4f}")
                self.logger.info(f"   PnL: {pnl_usd:+.2f} USDT ({pnl_pct:+.2f}%)")
                self.logger.info(f"   Razao: {reason}")
                
                # ===== NOTIFICA AI PARA APRENDIZADO =====
                if self.ai_enabled and self.ai_manager:
                    try:
                        self.ai_manager.on_trade_completed(trade)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Erro ao notificar AI: {e}")
                
        except Exception as e:
            self.logger.error(f"Erro ao fechar posicao {symbol}: {e}")
    
    def print_summary(self):
        """Imprime resumo do estado atual"""
        
        print("\n" + "="*70)
        print(f"📊 RESUMO - Iteração #{self.iteration} - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)
        
        if self.unico_bot_mode:
            # ===== MODO UNICO BOT =====
            print(f"\n🤖 UNICO BOT:")
            print(f"   Posições abertas: {len(self.positions)}/{self.unico_bot.trading_config.get('max_positions', 15)}")
            
            # Calcula PnL total das posições
            total_pnl = 0
            for symbol, pos in self.positions.items():
                try:
                    ticker = self.exchange.fetch_ticker(symbol)
                    if ticker:
                        current_price = ticker.get('last', ticker.get('close', 0))
                        entry_price = pos.get('entry_price', current_price)
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100
                        pnl_usd = pos.get('amount_usd', 0) * (pnl_pct / 100)
                        total_pnl += pnl_usd
                except:
                    pass
            
            print(f"   PnL Aberto: ${total_pnl:+.2f}")
            
            # Lista posições
            if self.positions:
                print(f"\n   📈 Posições:")
                for symbol, pos in list(self.positions.items())[:10]:  # Mostra até 10
                    try:
                        ticker = self.exchange.fetch_ticker(symbol)
                        if ticker:
                            current_price = ticker.get('last', ticker.get('close', 0))
                            entry_price = pos.get('entry_price', current_price)
                            pnl_pct = ((current_price - entry_price) / entry_price) * 100
                            emoji = "🟢" if pnl_pct >= 0 else "🔴"
                            print(f"      {emoji} {symbol}: {pnl_pct:+.2f}%")
                    except:
                        print(f"      ⚪ {symbol}: --")
        else:
            # ===== MODO MULTI-BOT =====
            stats = self.coordinator.get_stats_for_dashboard()
            
            # Global
            g = stats['global']
            print(f"\n🎖️  GLOBAL:")
            print(f"   PnL Total: ${g['total_pnl']:.2f} | PnL Dia: ${g['daily_pnl']:.2f}")
            print(f"   Trades: {g['total_trades']} | Win Rate: {g['win_rate']:.1f}%")
            print(f"   Posições: {g['open_positions']} abertas | Bots: {g['active_bots']} ativos")
            
            # Por bot
            print(f"\n{'─'*70}")
            for bot_type, bot_stats in stats['bots'].items():
                emoji = bot_stats['name'].split()[0] if bot_stats['name'] else "🤖"
                status_emoji = "🟢" if bot_stats['status'] == 'idle' else "🔄"
                
                print(f"\n{emoji} {bot_stats['name']}:")
                print(f"   PnL: ${bot_stats['total_pnl']:.2f} | Dia: ${bot_stats['daily_pnl']:.2f}")
                print(f"   Trades: {bot_stats['trades']} (✅{bot_stats['wins']} | ❌{bot_stats['losses']}) | WR: {bot_stats['win_rate']:.1f}%")
                print(f"   Posições: {bot_stats['open_positions']}/{bot_stats['max_positions']} | Status: {status_emoji}")
        
        print("\n" + "="*70)
    
    def run(self, interval: int = 3):
        """
        Loop principal - executa bots em sequência.
        
        MODOS:
        - UNICO BOT: Processa todas as cryptos com um único bot
        - MULTI BOT: Processa cryptos divididas entre 4 bots
        """
        self.running = True
        self.coordinator.stats.status = "running"
        self.coordinator.stats.start_time = datetime.now().isoformat()
        
        print("\n" + "="*70)
        if self.unico_bot_mode:
            print("🤖 INICIANDO UNICO BOT - App Leonardo v3.0")
            print("="*70)
            print(f"   Modo: UNICO BOT (todas as cryptos)")
            print(f"   Cryptos: {len(self.unico_bot.portfolio)}")
        else:
            print("🚀 INICIANDO SISTEMA MULTI-BOT - App Leonardo v3.0")
            print("="*70)
            print(f"   Bots ativos: {len(self.coordinator.bots)}")
            print(f"   Cryptos monitoradas: {len(self.coordinator.get_all_symbols())}")
        print(f"   Intervalo: {interval}s")
        print("="*70)
        
        # ===== FASE 1: NÃO LIQUIDA - GERENCIA POSIÇÕES EXISTENTES =====
        startup_config = self.coordinator.config.get('global', {}).get('startup', {})
        
        # REMOVIDO: Liquidação automática
        # Agora o bot gerencia as posições existentes
        print("\n📊 FASE 1: VERIFICANDO POSIÇÕES EXISTENTES")
        self._sync_positions_with_exchange()
        
        # ===== FASE 2: POUPANÇA DESABILITADA POR ENQUANTO =====
        print("\n💰 FASE 2: POUPANÇA (DESABILITADA)")
        
        # Obtém saldo atual
        total_balance = self.get_balance()
        print(f"   Saldo USDT disponível: ${total_balance:.2f}")
        print(f"   Poupança: DESABILITADA")
        
        capital_para_bots = total_balance
        print(f"\n📊 CAPITAL TOTAL DISPONÍVEL: ${capital_para_bots:.2f}")
        
        # ===== FASE 3: LOOP PRINCIPAL =====
        print("\n" + "="*70)
        print("🟢 FASE 3: INICIANDO OPERAÇÕES")
        print("="*70)
        
        try:
            while self.running:
                self.iteration += 1
                
                # ===== EXECUTA NO MODO APROPRIADO =====
                if self.unico_bot_mode:
                    # Modo UnicoBot - processa todas as cryptos
                    self._run_unico_bot_cycle()
                else:
                    # Modo MultiBots - processa cada bot separadamente
                    for bot_type in self.coordinator.bots.keys():
                        if not self.running:
                            break
                        self.run_bot_cycle(bot_type)
                    
                    # Atualiza posições abertas nos stats
                    for bot in self.coordinator.bots.values():
                        bot.stats.open_positions = sum(
                            1 for pos in self.positions.values() 
                            if pos['bot_type'] == bot.bot_type
                        )
                
                # Salva estado
                self.coordinator.save_state()
                
                # Salva dados para o dashboard (saldos, meta diária)
                self._save_dashboard_data()
                self._save_dashboard_data()
                
                # Imprime resumo
                self.print_summary()
                
                # Aguarda
                print(f"\n⏳ Aguardando {interval} segundos...\n")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Parando bots...")
        finally:
            self.running = False
            self.coordinator.stats.status = "stopped"
            self.coordinator.save_state()
            print("✅ Sistema Multi-Bot finalizado")
    
    def stop(self):
        """Para a execução"""
        self.running = False


def main():
    """Ponto de entrada principal"""
    engine = MultiBotEngine()
    engine.run(interval=3)


if __name__ == "__main__":
    main()
