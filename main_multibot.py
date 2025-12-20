# -*- coding: utf-8 -*-
"""
============================================================
MAIN MULTI-BOT - App Leonardo v3.0 (com AI Adaptativa)
============================================================

Executa o sistema de 4 bots especializados em paralelo.
Cada bot opera independentemente com suas cryptos específicas.

NOVO: Sistema de IA que aprende e adapta os bots!
- Aprende com erros e acertos
- Busca notícias e sentimento de mercado
- Ajusta parâmetros automaticamente

Uso:
    python main_multibot.py

============================================================
"""

# Carrega variáveis de ambiente ANTES de qualquer import
try:
    from dotenv import load_dotenv
    load_dotenv('config/.env')
    print("Variáveis de ambiente carregadas do .env")
except ImportError:
    print("Aviso: python-dotenv não instalado. Usando variáveis do sistema.")

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
from src.metrics.metrics_manager import MetricsManager
from src.ai.ai_poller import AIPoller

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

# ===== IMPORTAÇÃO DO CAPITAL MANAGER =====
try:
    from capital_manager import CapitalManager
    CAPITAL_MANAGER_AVAILABLE = True
except ImportError as e:
    CAPITAL_MANAGER_AVAILABLE = False
    print(f"⚠️ CapitalManager não disponível: {e}")
    print(f"⚠️ AI não disponível: {e}")

# ===== IMPORTAÇÃO DO SAFETY MANAGER =====
try:
    from src.safety.safety_manager import SafetyManager
    SAFETY_MANAGER_AVAILABLE = True
except ImportError as e:
    SAFETY_MANAGER_AVAILABLE = False
    print(f"⚠️ SafetyManager não disponível: {e}")

# ===== IMPORTAÇÃO DO AUTO-TUNER =====
try:
    from src.ai import get_autotuner, AutoTuner
    AUTOTUNER_AVAILABLE = True
except ImportError as e:
    AUTOTUNER_AVAILABLE = False
    print(f"⚠️ AutoTuner não disponível: {e}")

# ===== SEM IA - APENAS ESTRATÉGIAS TÉCNICAS =====
# AI Monitor removido - sistema funciona apenas com análise técnica
AI_MONITOR_AVAILABLE = False


class MultiBotEngine:
    """
    Engine principal que executa todos os bots em paralelo.
    Agora com IA adaptativa e AUTO-TUNER integrados!

    MODOS DE OPERAÇÃO:
    1. UNICO BOT: Um único bot gerencia TODAS as cryptos e TODO o saldo
    2. MULTI BOT: 4 bots especializados (estável, médio, volátil, meme)
    """

    def liquidate_profitable_positions(self, min_profit_pct: float = 0.1) -> dict:
        """
        💸 VENDE APENAS POSIÇÕES COM LUCRO
        min_profit_pct: lucro mínimo em % para considerar venda (default: 0.1%)
        """
        print("\n" + "="*70)
        print(f"💸 LIQUIDANDO POSIÇÕES COM LUCRO (>{min_profit_pct:.2f}%):")
        print("="*70)

        results = {
            'sold': 0,
            'failed': 0,
            'total_pnl': 0,
            'positions': []
        }

        for symbol, pos in list(self.positions.items()):
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                if not ticker:
                    continue
                current_price = ticker.get('last', ticker.get('close', 0))
                entry_price = pos.get('entry_price')
                if not entry_price:
                    continue
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                if pnl_pct >= min_profit_pct:
                    amount = pos.get('amount')
                    if not amount:
                        continue
                    order = self.exchange.create_market_order(
                        symbol=symbol,
                        side='sell',
                        amount=amount
                    )
                    if order:
                        results['sold'] += 1
                        pnl_usd = pos.get('amount_usd', 0) * (pnl_pct / 100)
                        results['total_pnl'] += pnl_usd
                        print(f"   ✅ {symbol}: {amount:.6f} @ ${current_price:.4f} | PnL: {pnl_pct:+.2f}% (${pnl_usd:+.2f})")
                        del self.positions[symbol]
                        results['positions'].append({
                            'symbol': symbol,
                            'amount': amount,
                            'price': current_price,
                            'pnl_pct': pnl_pct,
                            'pnl_usd': pnl_usd
                        })
                    else:
                        results['failed'] += 1
                        print(f"   ❌ {symbol}: Falha na venda")
            except Exception as e:
                results['failed'] += 1
                print(f"   ❌ {symbol}: Erro - {e}")

        self._save_positions()
        print(f"\nResumo: {results['sold']} vendidas com lucro, {results['failed']} falharam.")
        return results

    def redeem_earn_flexible(self, min_amount=10):
        """Resgata automaticamente saldo de TODOS os ativos do Earn Flexível para Spot se disponível e acima do mínimo."""
        try:
            flexible_positions = self.exchange.exchange.sapi_get_simple_earn_flexible_position()
            if flexible_positions and 'rows' in flexible_positions:
                for pos in flexible_positions['rows']:
                    asset = pos.get('asset')
                    amount = float(pos.get('totalAmount', 0))
                    can_redeem = pos.get('canRedeem', False)
                    if can_redeem and amount >= min_amount:
                        params = {
                            'productId': asset,
                            'amount': str(amount),
                            'type': 'FAST'
                        }
                        result = self.exchange.exchange.sapi_post_simple_earn_flexible_redeem(params)
                        print(f"\n[Earn] Resgate automático solicitado: {amount} {asset} para Spot! Resultado: {result}")
                    else:
                        print(f"[Earn] Nada a resgatar ou valor insuficiente para {asset} (disponível: {amount})")
        except Exception as e:
            print(f"[Earn] Erro ao tentar resgatar do Earn Flexível: {e}")

    def __init__(self):
        # ===== DEFINE DIRETÓRIO DE DADOS =====
        # Permite subconta usar seu próprio diretório
        self.data_dir = Path(os.getenv('DATA_DIR', 'data'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # ===== VERIFICA MODO DE OPERAÇÃO =====
        self.unico_bot_mode = False
        self.unico_bot = None
        
        if UNICO_BOT_AVAILABLE and should_use_unico_bot():
            self.unico_bot_mode = True
            self.unico_bot = UnicoBot()
            if self.unico_bot.enabled:
                print("=" * 60, flush=True)
                print("MODO UNICO BOT ATIVADO", flush=True)
                print("=" * 60, flush=True)
                print(f"   -> {self.unico_bot.name} gerenciando TODAS as cryptos", flush=True)
                print(f"   -> Simbolos: {len(self.unico_bot.portfolio)}", flush=True)
                print(f"   -> Max posicoes: {self.unico_bot.trading_config.get('max_positions', 15)}", flush=True)
                print("=" * 60)
            else:
                self.unico_bot_mode = False
                print("⚠️ UnicoBot está desabilitado no config")
        
        # Coordenador (usado para exchange e configs gerais)
        self.coordinator = get_coordinator()
        
        # Exchange compartilhada
        self.exchange = self.coordinator.exchange
        
        # ===== INICIALIZAÇÃO DA IA =====
        self.ai_manager = None
        self.ai_enabled = True
        if AI_AVAILABLE:
            try:
                self.ai_manager = get_ai_manager()
                self.ai_manager.start_background_tasks()
                print("Sistema de IA inicializado!")
            except Exception as e:
                print(f"⚠️ Erro ao inicializar IA: {e}")
                self.ai_enabled = False
        else:
            self.ai_enabled = False
            print("⚠️ IA não disponível - operando sem AI")
        
        # ===== INICIALIZAÇÃO DO CAPITAL MANAGER =====
        self.capital_manager = None
        if CAPITAL_MANAGER_AVAILABLE:
            try:
                self.capital_manager = CapitalManager()
                print("💰 Capital Manager inicializado com otimização temporal!")
                print("   → Posições ajustadas automaticamente por horário ótimo")
            except Exception as e:
                print(f"⚠️ Erro ao inicializar CapitalManager: {e}")
                self.capital_manager = None
        else:
            print("⚠️ Capital Manager não disponível - usando tamanhos fixos")
        
        # ===== INICIALIZAÇÃO DO SAFETY MANAGER =====
        self.safety_manager = None
        if SAFETY_MANAGER_AVAILABLE:
            try:
                # Carrega configurações de segurança
                safety_config = self.coordinator.config.get('global', {}).get('safety', {})
                
                self.safety_manager = SafetyManager(safety_config)
                print("🛡️ Safety Manager inicializado!")
                print(f"   → Limite diário: {self.safety_manager.kill_switch.max_daily_loss}%")
                print(f"   → Max drawdown: {self.safety_manager.kill_switch.max_drawdown_pct}%")
            except Exception as e:
                print(f"⚠️ Erro ao inicializar SafetyManager: {e}")
                self.safety_manager = None
        else:
            print("⚠️ Safety Manager não disponível - sem proteção automática")

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
            print("⚠️ AutoTuner não disponível")
        
        # ===== LISTA CONFIGURAÇÕES INICIAIS =====
        print("\n===== CONFIGURAÇÕES INICIAIS DO BOT =====")
        print(f"Exchange: {self.exchange.exchange.name}")
        print(f"API Key: {os.getenv('BINANCE_API_KEY', '***')[:6]}... (oculta)")
        print(f"Modo UnicoBot: {self.unico_bot_mode}")
        print(f"Data Dir: {self.data_dir}")
        print(f"IA Ativada: {self.ai_enabled}")
        print(f"AutoTuner: {self.autotuner_enabled}")
        print(f"Config Global: {self.coordinator.config.get('global', {})}")
        # Lista de moedas disponíveis (símbolos)
        try:
            symbols = [s['symbol'] for s in self.exchange.exchange.public_get_exchangeinfo()['symbols']]
            print(f"Moedas disponíveis ({len(symbols)}): {', '.join(symbols[:20])}{' ...' if len(symbols) > 20 else ''}")
            
            # ===== VALIDAÇÃO DOS SÍMBOLOS CONFIGURADOS =====
            print("\n🔍 VALIDANDO SÍMBOLOS CONFIGURADOS...")
            invalid_symbols = []
            all_config_symbols = set()
            
            # Coleta todos os símbolos dos portfolios dos bots
            for bot_type, bot in self.coordinator.bots.items():
                for crypto in bot.portfolio:
                    symbol = crypto.get('symbol', '')
                    if symbol:
                        all_config_symbols.add(symbol)
            
            # Verifica se cada símbolo é uma combinação válida MOEDA + USDT
            for symbol in all_config_symbols:
                if symbol not in symbols:
                    invalid_symbols.append(symbol)
                    print(f"❌ Símbolo inválido: {symbol} - não existe na exchange")
                elif not symbol.endswith('USDT'):
                    print(f"⚠️ Símbolo não termina com USDT: {symbol}")
                else:
                    # Verifica se a base (sem USDT) é uma moeda conhecida
                    base_currency = symbol[:-4]  # Remove 'USDT'
                    if not any(s.startswith(base_currency) for s in symbols):
                        print(f"⚠️ Moeda base suspeita: {base_currency} em {symbol}")
                    else:
                        print(f"✅ Símbolo válido: {symbol}")
            
            # ===== LIMPA POSIÇÕES INVÁLIDAS =====
            print("\n🧹 LIMPANDO POSIÇÕES INVÁLIDAS...")
            try:
                invalid_positions = []
                for symbol in list(self.positions.keys()):
                    if symbol not in self._valid_symbols_cache:
                        invalid_positions.append(symbol)
                        del self.positions[symbol]
                        print(f"   ❌ Removida posição inválida: {symbol}")
                
                if invalid_positions:
                    print(f"   🗑️ {len(invalid_positions)} posições inválidas removidas")
                    self._save_positions()  # Salva após limpeza
                else:
                    print("   ✅ Nenhuma posição inválida encontrada")
            except AttributeError as e:
                print(f"   ⚠️ Erro ao limpar posições (ainda não inicializadas): {e}")
            except Exception as e:
                print(f"   ⚠️ Erro inesperado na limpeza: {e}")
                
        except Exception as e:
            print(f"Erro ao obter lista de moedas: {e}")
        print("========================================\n")

        # ===== RESGATE AUTOMÁTICO DO EARN FLEXÍVEL =====
        self.redeem_earn_flexible(min_amount=10)
        
        # Indicadores
        self.indicators = TechnicalIndicators()
        
        # Cache para filtros de mercado (para otimizar performance)
        self.market_filters_cache = {}
        self.cache_timestamp = None
        self.cache_duration = 300  # 5 minutos
        
        # ===== SEM IA - APENAS MONITORAMENTO TÉCNICO =====
        # AI Monitor removido - apenas estratégias técnicas

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
            # Configura codificação UTF-8 para Windows
            import sys
            if sys.platform == 'win32':
                try:
                    import io
                    handler.stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
                except:
                    pass  # Fallback para codificação padrão
            self.logger.addHandler(handler)
        
        # Carrega posições existentes
        self._load_positions()
        
        # Arquivo de histórico global
        self.history_file = self.data_dir / "multibot_history.json"

        # Métricas (daily/monthly progress)
        try:
            init_cap = 0.0
            try:
                init_cap = float(self.coordinator.config.get('global', {}).get('initial_capital', 0.0))
            except Exception:
                init_cap = 0.0
            self.metrics = MetricsManager(self.data_dir, initial_cap=init_cap)
            # aplica target mensal se disponível
            mt = self.coordinator.config.get('global', {}).get('monthly_target')
            if mt:
                try:
                    self.metrics.set_monthly_target(float(mt))
                except Exception:
                    pass
            # reseta diário se necessário (timezone Brasil)
            try:
                self.metrics.reset_daily_if_needed()
            except Exception:
                pass
        except Exception as e:
            print(f"⚠️ Não foi possível inicializar MetricsManager: {e}")
            self.metrics = None
        # ===== INICIAR POLLER DE IA (6h) =====
        try:
            self.ai_poller = AIPoller(self.coordinator, interval_seconds=6*3600)
            # start poller only if AI subsystem present
            try:
                from src.ai import get_ai_manager
                # start poller in background
                self.ai_poller.start()
                print("🔄 AI Poller iniciado (a cada 6 horas)")
            except Exception:
                # still start poller; it will gracefully skip unavailable clients
                self.ai_poller.start()
        except Exception as e:
            print(f"⚠️ Não foi possível iniciar AI Poller: {e}")
            self.ai_poller = None
        
        # ===== HISTÓRICO POR BOT =====
        self.bot_history_files = {
            'bot_estavel': self.data_dir / "history" / "bot_estavel_trades.json",
            'bot_medio': self.data_dir / "history" / "bot_medio_trades.json",
            'bot_volatil': self.data_dir / "history" / "bot_volatil_trades.json",
            'bot_meme': self.data_dir / "history" / "bot_meme_trades.json",
            'poupanca': self.data_dir / "history" / "poupanca_trades.json",
        }
        
        # Cria diretório de histórico se não existir
        (self.data_dir / "history").mkdir(parents=True, exist_ok=True)
        
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
        stats_file = self.data_dir / "history" / f"{bot_type}_stats.json"
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
        stats_file = self.data_dir / "history" / f"{bot_type}_stats.json"
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
        positions_file = self.data_dir / "multibot_positions.json"
        if positions_file.exists():
            try:
                with open(positions_file, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    # Normaliza formatos legados (lista) para o formato atual (dict)
                    if isinstance(raw, dict):
                        loaded = raw
                    elif isinstance(raw, list):
                        # Converte lista de posições para dict keyed by symbol quando possível
                        loaded = {}
                        for i, item in enumerate(raw):
                            if not isinstance(item, dict):
                                continue
                            key = item.get('symbol') or item.get('pair') or item.get('s') or item.get('asset') or item.get('symbol_name')
                            if key:
                                loaded[key] = item
                            else:
                                # fallback com índice para evitar perda de dados
                                loaded[f'pos_{i}'] = item
                        if not loaded:
                            loaded = {}
                        if isinstance(raw, list):
                            self.logger.warning("⚠️ Arquivo de posições estava em formato antigo (lista); convertido para dict para compatibilidade")
                    else:
                        loaded = {}

                    self.positions = loaded

                    # Converte timestamps
                    for symbol, pos in self.positions.items():
                        if isinstance(pos, dict) and 'time' in pos and isinstance(pos['time'], str):
                            try:
                                pos['time'] = datetime.fromisoformat(pos['time'])
                            except Exception:
                                # ignora formatos inesperados de tempo
                                pass
                    
                self.logger.info(f"📂 {len(self.positions)} posições restauradas")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao carregar posições: {e}")
    
    def _save_positions(self):
        """Salva posições abertas no arquivo"""
        Path("data").mkdir(parents=True, exist_ok=True)
        
        # Prepara para JSON (converte datetime)
        positions_to_save = {}
        if isinstance(self.positions, dict):
            for symbol, pos in self.positions.items():
                positions_to_save[symbol] = pos.copy()
                if 'time' in positions_to_save[symbol] and hasattr(positions_to_save[symbol]['time'], 'isoformat'):
                    positions_to_save[symbol]['time'] = pos['time'].isoformat()
        elif isinstance(self.positions, list):
            # Compatibilidade: converte lista de posições para dict
            for i, item in enumerate(self.positions):
                if not isinstance(item, dict):
                    continue
                key = item.get('symbol') or item.get('pair') or item.get('s') or item.get('asset') or item.get('symbol_name') or f'pos_{i}'
                positions_to_save[key] = item.copy()
                if 'time' in positions_to_save[key] and isinstance(positions_to_save[key]['time'], str):
                    try:
                        # assume already isoformat string
                        pass
                    except Exception:
                        pass
        else:
            # Unexpected format - salva vazio para não quebrar dashboard
            positions_to_save = {}

        with open(self.data_dir / "multibot_positions.json", 'w') as f:
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
        
        # Normalize and ensure exit reason fields for compatibility
        if trade.get('reason'):
            trade['exit_reason'] = trade.get('reason')
            trade['close_reason'] = trade.get('reason')
        else:
            # Fallback mapping from status if available
            status = str(trade.get('status', '')).lower()
            if 'stop' in status or 'stopped' in status:
                trade['exit_reason'] = 'STOP_LOSS'
                trade['close_reason'] = 'STOP_LOSS'
            elif 'profit' in status or 'take' in status or 'tp' in status:
                trade['exit_reason'] = 'TAKE_PROFIT'
                trade['close_reason'] = 'TAKE_PROFIT'
            elif 'timeout' in status:
                trade['exit_reason'] = 'TIMEOUT_CLOSED'
                trade['close_reason'] = 'TIMEOUT_CLOSED'
            else:
                trade['exit_reason'] = trade.get('exit_reason', '')
                trade['close_reason'] = trade.get('close_reason', '')

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
        # Ensure exit_reason/close_reason normalized for new trades
        if trade_record.get('reason'):
            trade_record['exit_reason'] = trade_record.get('reason')
            trade_record['close_reason'] = trade_record.get('reason')
        history.append(trade_record)
        
        # Mantém últimos 500 trades por bot
        if len(history) > 500:
            history = history[-500:]
        
        # Salva
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        # Atualiza estatísticas do bot
        self._update_bot_stats(bot_type, trade)

        # Atualiza métricas globais (daily/monthly)
        try:
            if getattr(self, 'metrics', None):
                self.metrics.record_trade(trade.get('pnl', 0))
        except Exception:
            pass
        
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
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.data_dir / "poupanca.json", 'w') as f:
            json.dump(self.poupanca, f, indent=2)
    
    def _save_dashboard_data(self):
        """
        Salva dados para o dashboard:
        - Saldo USDT
        - Saldo em Cripto
        - Saldo em EARN (Simple Earn/Locked)
        - Saldo Total
        - Progresso Meta Diária
        """
        try:
            balance = self.exchange.fetch_balance()
            if not balance:
                return
            
            # Saldo USDT
            usdt_balance = balance.get('USDT', {}).get('free', 0) + balance.get('USDT', {}).get('used', 0)
            
            # Saldo em cryptos (incluindo posições abertas)
            crypto_balance = 0
            crypto_positions = {}
            
            # Identifica assets que têm posições abertas (para evitar duplicatas)
            position_assets = set()
            for symbol, pos_data in self.positions.items():
                asset = symbol.replace('USDT', '') if symbol.endswith('USDT') else symbol
                position_assets.add(asset)
            
            # Primeiro, adiciona saldos livres de criptos (exceto assets com posições abertas)
            for asset, data in balance.items():
                if asset in ['USDT', 'info', 'free', 'used', 'total', 'debt', 'timestamp', 'datetime']:
                    continue


                # Pula assets que têm posições abertas para evitar duplicatas
                if asset in position_assets:
                    continue

                total_amount = data.get('free', 0) + data.get('used', 0)
                if total_amount > 0:
                    # Corrige: se asset já termina com USDT, não adiciona novamente
                    symbol = asset if asset.endswith('USDT') else f"{asset}USDT"
                    # ✅ Valida se o símbolo existe antes de buscar ticker
                    if not self.exchange.is_valid_symbol(symbol):
                        self.logger.warning(f"⚠️ Símbolo {symbol} não existe na exchange - pulando")
                        continue
                    try:
                        # Obtém preço atual
                        ticker = self.exchange.fetch_ticker(symbol)
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
            
            # Segundo, adiciona valor das posições abertas do bot
            for symbol, pos_data in self.positions.items():
                if symbol not in crypto_positions:  # Evita duplicatas
                    try:
                        # Remove 'USDT' do final para obter o asset
                        asset = symbol.replace('USDT', '') if symbol.endswith('USDT') else symbol
                        amount = pos_data.get('amount', 0)
                        entry_price = pos_data.get('entry_price', 0)
                        
                        # Usa preço atual para calcular valor corrente
                        ticker = self.exchange.fetch_ticker(symbol)
                        if ticker:
                            current_price = ticker.get('last', ticker.get('close', entry_price))
                            value_usd = amount * current_price
                            
                            if value_usd > 0.01:
                                crypto_balance += value_usd
                                crypto_positions[asset] = {
                                    'amount': amount,
                                    'price': current_price,
                                    'value_usd': value_usd,
                                    'entry_price': entry_price,
                                    'pnl_pct': ((current_price - entry_price) / entry_price) * 100
                                }
                    except Exception as e:
                        self.logger.warning(f"⚠️ Erro ao calcular valor da posição {symbol}: {e}")
                        # Fallback: usa preço de entrada
                        try:
                            amount = pos_data.get('amount', 0)
                            entry_price = pos_data.get('entry_price', 0)
                            value_usd = amount * entry_price
                            
                            if value_usd > 0.01:
                                crypto_balance += value_usd
                                asset = symbol.replace('USDT', '') if symbol.endswith('USDT') else symbol
                                crypto_positions[asset] = {
                                    'amount': amount,
                                    'price': entry_price,
                                    'value_usd': value_usd,
                                    'entry_price': entry_price,
                                    'pnl_pct': 0
                                }
                        except:
                            pass
            
            # Saldo em EARN (Simple Earn Flexible + Locked)
            earn_balance = 0
            earn_positions = {}
            try:
                # Buscar posições em Flexible Earn
                flexible_positions = self.exchange.exchange.sapi_get_simple_earn_flexible_position()
                if flexible_positions and 'rows' in flexible_positions:
                    for pos in flexible_positions['rows']:
                        asset = pos.get('asset')
                        amount = float(pos.get('totalAmount', 0))
                        if amount > 0:
                            try:
                                if asset == 'USDT':
                                    value_usd = amount
                                else:
                                    ticker = self.exchange.fetch_ticker(f"{asset}USDT")
                                    price = ticker.get('last', ticker.get('close', 0))
                                    value_usd = amount * price
                                
                                if value_usd > 0.01:
                                    earn_balance += value_usd
                                    earn_positions[asset] = {
                                        'amount': amount,
                                        'value_usd': value_usd,
                                        'type': 'flexible',
                                        'canRedeem': pos.get('canRedeem', False)
                                    }
                            except:
                                pass
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao buscar Simple Earn: {e}")
            
            # Total (incluindo EARN)
            total_balance = usdt_balance + crypto_balance + earn_balance
            
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
                'earn_balance': earn_balance,
                'total_balance': total_balance,
                'crypto_positions': crypto_positions,
                'earn_positions': earn_positions,
                'poupanca': self.poupanca.get('balance', 0),
                'daily_target_pct': daily_target_pct,
                'daily_target_usd': daily_target_usd,
                'daily_pnl': daily_pnl,
                'daily_progress': daily_progress,
            }
            
            with open(self.data_dir / "dashboard_balances.json", 'w') as f:
                json.dump(dashboard_data, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao salvar dados do dashboard: {e}")
    
    def _load_poupanca(self):
        """Carrega estado da poupança"""
        poupanca_file = self.data_dir / "poupanca.json"
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
        """Retorna saldo USDT disponível com validação extra"""
        try:
            balance = self.exchange.fetch_balance()
            if balance:
                free_usdt = balance.get('USDT', {}).get('free', 0)
                total_usdt = balance.get('USDT', {}).get('total', 0)
                used_usdt = balance.get('USDT', {}).get('used', 0)

                # Log detalhado para debug
                print(f"[SALDO DEBUG] USDT - Free: ${free_usdt:.2f}, Used: ${used_usdt:.2f}, Total: ${total_usdt:.2f}")

                # Validação: free + used deve ser aproximadamente igual a total
                if abs((free_usdt + used_usdt) - total_usdt) > 0.01:
                    print(f"[SALDO WARNING] Inconsistência no saldo: free+used ({free_usdt + used_usdt:.2f}) != total ({total_usdt:.2f})")

                return free_usdt
            return 0
        except Exception as e:
            self.logger.error(f"Erro ao obter saldo: {e}")
            print(f"[SALDO ERROR] Falha ao consultar saldo: {e}")
            return 0
    
    def _sync_positions_with_exchange(self):
        """
        Sincroniza posições locais com o saldo real na exchange.
        Detecta cryptos que temos mas não estão registradas.
        Trata timeouts e interrupções de rede.
        """
        print("   🔄 Sincronizando posições com a exchange...")
        
        try:
            balance = self.exchange.fetch_balance()
            if not balance:
                print("   ⚠️ Não foi possível obter saldo")
                return
            
            # Carrega lista de símbolos válidos da exchange se ainda não tem
            if not hasattr(self, '_valid_symbols_cache'):
                try:
                    self._valid_symbols_cache = set(s['symbol'] for s in self.exchange.exchange.public_get_exchangeinfo()['symbols'])
                except Exception as e:
                    print(f"[ERRO] Falha ao carregar cache de símbolos: {e}")
                    self._valid_symbols_cache = set()
            
            synced = 0
            for asset, data in balance.items():
                if asset in ['USDT', 'info', 'free', 'used', 'total', 'debt', 'timestamp', 'datetime']:
                    continue
                
                total_amount = data.get('free', 0) + data.get('used', 0)
                if total_amount > 0.0001:
                    symbol = f"{asset}USDT"
                    
                    # VERIFICA se o símbolo é válido antes de tentar sincronizar
                    if symbol not in self._valid_symbols_cache:
                        print(f"      ⚠️ Pulando {symbol} - ativo {asset} não tem par USDT válido na exchange")
                        continue
                    
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
                        except Exception as e:
                            print(f"      ❌ Erro ao buscar ticker {symbol}: {e}")
            
            if synced > 0:
                print(f"   📊 {synced} posições sincronizadas")
                
        except KeyboardInterrupt:
            print("   ⚠️ Sincronização interrompida - continuando sem sincronização")
            self.logger.warning("⚠️ Sincronização de posições interrompida por timeout de rede")
        except Exception as e:
            print(f"   ⚠️ Erro na sincronização: {e}")
            self.logger.error(f"Erro na sincronização de posições: {e}")
            
        # Salva posições após sincronização
        self._save_positions()
    
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
                # Verifica se a posição ainda existe (pode ter sido removida por outro processo)
                if symbol not in self.positions:
                    print(f"⚠️ Posição {symbol} já foi fechada - pulando")
                    continue
                    
                pos = self.positions[symbol]
                amount = pos.get('amount', 0)
                
                # Verifica se ainda tem saldo da crypto
                try:
                    balance = self.exchange.fetch_balance()
                    crypto_balance = balance.get(symbol.replace('USDT', ''), {}).get('free', 0)
                    
                    if crypto_balance < amount * 0.99:  # 1% margem de erro
                        print(f"⚠️ Saldo insuficiente para vender {symbol}: {crypto_balance:.6f} < {amount:.6f}")
                        # Remove posição do registro local
                        del self.positions[symbol]
                        open_positions -= 1
                        continue
                        
                except Exception as balance_error:
                    print(f"⚠️ Erro ao verificar saldo para {symbol}: {balance_error}")
                    # Continua tentando vender mesmo com erro de verificação
                
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
                    
                else:
                    print(f"⚠️ Ordem de venda {symbol} não executada")
                    
            except Exception as e:
                error_msg = str(e).lower()
                if "insufficient balance" in error_msg:
                    print(f"⚠️ Saldo insuficiente detectado ao vender {symbol} - removendo posição do registro")
                    # Remove posição do registro local se não há saldo
                    if symbol in self.positions:
                        del self.positions[symbol]
                        open_positions -= 1
                elif "network" in error_msg or "timeout" in error_msg:
                    print(f"⚠️ Erro de rede ao vender {symbol}: {e} - tentando novamente em próximo ciclo")
                    # Não remove posição, tenta novamente depois
                else:
                    print(f"❌ Erro ao vender {symbol}: {e}")
                    # Para outros erros, remove posição para evitar loops
                    if symbol in self.positions:
                        del self.positions[symbol]
                        open_positions -= 1
        
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
                            # Calcula quantidade usando Capital Manager (se disponível)
                            current_price = df.iloc[-1]['close']
                            
                            if self.capital_manager:
                                # Usa otimização temporal do Capital Manager
                                stop_loss = current_price * 0.995  # -0.5%
                                take_profit = current_price * 1.015  # +1.5%
                                
                                position_size = self.capital_manager.calculate_optimal_position_size(
                                    symbol, current_price, stop_loss, take_profit, 'unico_bot'
                                )
                                
                                print(f"💰 Capital Manager: {symbol} | Tamanho otimizado: ${position_size:.2f}")
                                trade_amount = position_size
                            else:
                                # Fallback para valor fixo
                                trade_amount = min(amount_per_trade, usdt_balance)
                            
                            crypto_amount = trade_amount / current_price
                            
                            print(f"🔍 DEBUG: Tentando comprar {symbol} | Preço: ${current_price:.6f} | Trade Amount: ${trade_amount:.2f} | Crypto Amount: {crypto_amount:.6f} | Saldo USDT: ${usdt_balance:.2f}")
                            
                            # ===== VERIFICAÇÃO DE LIMITE DIÁRIO =====
                            if self.safety_manager:
                                # Calcula PnL diário atual
                                daily_pnl = sum(
                                    stats.get('daily_pnl', 0) 
                                    for stats in self.bot_stats.values()
                                )
                                
                                # Verifica se atingiu limite diário
                                if self.safety_manager.kill_switch.check_daily_loss(daily_pnl):
                                    print(f"🛑 BLOQUEADO: Limite diário de perda atingido (${abs(daily_pnl):.2f} >= ${self.safety_manager.kill_switch.max_daily_loss})")
                                    print("   → Bot será parado para proteção de capital")
                                    self.stop()
                                    return
                            
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
            else:
                # Modo observação - sem saldo para novas compras
                if self.iteration % 20 == 0:  # Log a cada 20 ciclos (~1 min)
                    self.logger.info(f"👁️ MODO OBSERVAÇÃO: Saldo ${usdt_balance:.2f} insuficiente para novos trades (mín: ${amount_per_trade:.2f})")
        
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
                    timeframe=bot.trading_config.get('timeframe', '5m'),
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
            
            # ===== VERIFICAÇÃO DE LIMITE DIÁRIO =====
            if self.safety_manager:
                # Calcula PnL diário atual
                daily_pnl = sum(
                    stats.get('daily_pnl', 0) 
                    for stats in self.bot_stats.values()
                )
                
                # Verifica se atingiu limite diário
                if self.safety_manager.kill_switch.check_daily_loss(daily_pnl):
                    print(f"🛑 BLOQUEADO: Limite diário de perda atingido (${abs(daily_pnl):.2f} >= ${self.safety_manager.kill_switch.max_daily_loss})")
                    print("   → Super oportunidade cancelada para proteção de capital")
                    return
            
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
        print(f"[LOG] Tentando abrir posição para o símbolo: {symbol}")
        # Log de debug: de onde vem esse símbolo?
        print(f"[DEBUG] Símbolo recebido: {symbol}, bot_type: {bot_type}, bot: {bot.name if bot else 'None'}")
        if hasattr(bot, 'portfolio'):
            portfolio_symbols = [crypto.get('symbol', '') for crypto in bot.portfolio]
            print(f"[DEBUG] Portfolio do bot {bot_type}: {portfolio_symbols}")
            if symbol not in portfolio_symbols:
                print(f"[DEBUG] ALERTA: {symbol} NÃO está no portfolio do bot {bot_type}!")
        
        # Verifica se o símbolo existe na lista oficial da exchange (cacheada)
        if not hasattr(self, '_valid_symbols_cache'):
            try:
                self._valid_symbols_cache = set(s['symbol'] for s in self.exchange.exchange.public_get_exchangeinfo()['symbols'])
            except Exception as e:
                print(f"[ERRO] Falha ao carregar cache de símbolos: {e}")
                self._valid_symbols_cache = set()
        
        if symbol not in self._valid_symbols_cache:
            print(f"[ERRO] Símbolo {symbol} não existe na lista oficial da exchange - pulando")
            self.logger.warning(f"⚠️ Símbolo {symbol} não existe na exchange - pulando")
            return
        amount_usd = bot.trading_config.get('amount_per_trade', 500)
        # Regra: primeiras N trades mínimo definido (se configurado globalmente ou por bot)
        try:
            first_min = bot.trading_config.get('first_n_trades_min_amount', None)
            first_count = bot.trading_config.get('first_n_trades_count', None)
            # fallback to ABSOLUTE_LIMITS if bot not configured
            if not first_min or not first_count:
                from src.safety.safety_manager import ABSOLUTE_LIMITS
                first_min = float(first_min or ABSOLUTE_LIMITS.get('FIRST_N_TRADES_MIN_AMOUNT', 0))
                first_count = int(first_count or ABSOLUTE_LIMITS.get('FIRST_N_TRADES_COUNT', 0))

            if first_count > 0 and first_min > 0:
                import json
                history_path = os.path.join(os.getcwd(), 'data', 'multibot_history.json')
                buys = 0
                try:
                    with open(history_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        buys = sum(1 for t in data if t.get('side') == 'buy')
                except Exception:
                    buys = 0

                if buys < first_count and amount_usd < float(first_min):
                    print(f"[PRIMEIRAS_TRADES] Ajustando amount_usd ${amount_usd:.2f} -> ${first_min:.2f} (primeiras {first_count} trades)")
                    amount_usd = float(first_min)
        except Exception:
            pass
        print(f"[CONFIG] amount_per_trade do bot {bot_type}: ${amount_usd}")
        
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
                
                # Log de warnings da AI (apenas se houver)
                warnings = ai_decision.get('warnings', [])
                if warnings:
                    for warning in warnings:
                        self.logger.info(f"🤖 [AI] {warning}")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Erro na AI: {e} - prosseguindo com compra")
        
# Verifica saldo COM ATUALIZAÇÃO EM TEMPO REAL
        balance = self.get_balance()
        if balance < amount_usd:
            self.logger.warning(f"Saldo insuficiente: ${balance:.2f} < ${amount_usd}")
            # Loga saldo USDT spot detalhado apenas se insuficiente
            try:
                spot_balance = self.exchange.fetch_balance()
                usdt_total = spot_balance.get('total', {}).get('USDT', 0)
                usdt_free = spot_balance.get('free', {}).get('USDT', 0)
                usdt_used = spot_balance.get('used', {}).get('USDT', 0)
                print(f"[SALDO USDT SPOT] total={usdt_total}, free={usdt_free}, used={usdt_used}")
                print(f"[SALDO VERIFICAÇÃO] Necessário: ${amount_usd}, Disponível: ${usdt_free}")
                if usdt_free >= amount_usd:
                    print(f"[SALDO OK] Saldo suficiente, prosseguindo...")
                    balance = usdt_free  # Atualiza balance com valor real
                else:
                    print(f"[SALDO INSUFICIENTE] Abortando trade")
                    return
            except Exception as e:
                print(f"[ERRO ao consultar saldo USDT spot]: {e}")
            return

        # Log permissões da API (removido para otimizar - descomente se precisar)
        # try:
        #     permissions = self.exchange.fetch_permissions() if hasattr(self.exchange, 'fetch_permissions') else None
        #     print(f"[PERMISSOES API] {permissions}")
        # except Exception as e:
        #     print(f"[ERRO ao consultar permissoes da API]: {e}")

        # Log valor exato da ordem e símbolo
        print(f"[ORDEM] Tentando abrir ordem: symbol={symbol}, amount_usd={amount_usd}, price={price}")

        # Log filtros de trading do par (minQty, minNotional, stepSize)
        try:
            # Usa cache se disponível e recente
            now = time.time()
            if symbol not in self.market_filters_cache or (self.cache_timestamp and now - self.cache_timestamp > self.cache_duration):
                market = self.exchange.markets.get(symbol)
                if market:
                    filters = market.get('info', {}).get('filters', [])
                    min_qty = min_notional = step_size = None
                    for f in filters:
                        if f.get('filterType') == 'LOT_SIZE':
                            min_qty = float(f.get('minQty', 0))
                            step_size = float(f.get('stepSize', 0))
                        if f.get('filterType') == 'MIN_NOTIONAL':
                            min_notional = float(f.get('minNotional', 0))
                    self.market_filters_cache[symbol] = {
                        'min_qty': min_qty,
                        'step_size': step_size,
                        'min_notional': min_notional
                    }
                    self.cache_timestamp = now
                else:
                    print(f"[FILTROS] Par {symbol} não encontrado em self.exchange.markets")
                    return  # Não prossegue se não encontrar o mercado
            
            filters = self.market_filters_cache.get(symbol, {})
            min_qty = filters.get('min_qty')
            step_size = filters.get('step_size')
            min_notional = filters.get('min_notional')
            print(f"[FILTROS] minQty={min_qty}, stepSize={step_size}, minNotional={min_notional}")
        except Exception as e:
            print(f"[ERRO ao consultar filtros do par]: {e}")
            return  # Não prossegue em caso de erro
        
        # Calcula e valida quantidade de crypto
        amount_crypto = amount_usd / price
        
        # Log detalhado dos cálculos
        print(f"[CÁLCULO] amount_usd={amount_usd}, price={price}")
        print(f"[CÁLCULO] amount_crypto calculado = {amount_crypto}")
        print(f"[CÁLCULO] Valor esperado da ordem = ${amount_crypto * price}")
        
        # Ajusta quantidade para respeitar minQty e stepSize
        if min_qty and amount_crypto < min_qty:
            print(f"[VALIDAÇÃO] amount_crypto {amount_crypto} < minQty {min_qty} - pulando")
            return
        if step_size:
            # Arredonda para múltiplo do stepSize
            amount_crypto = (amount_crypto // step_size) * step_size
            print(f"[AJUSTE] amount_crypto arredondado para stepSize: {amount_crypto}")
            if amount_crypto < min_qty:
                amount_crypto = min_qty
                print(f"[AJUSTE] Ajustado para minQty: {amount_crypto}")
        
        # Verifica minNotional
        order_value = amount_crypto * price
        if min_notional and order_value < min_notional:
            print(f"[VALIDAÇÃO] Valor da ordem ${order_value:.2f} < minNotional ${min_notional} - pulando")
            return
        
        print(f"[ORDEM FINAL] symbol={symbol}, amount_crypto={amount_crypto}, valor_total=${order_value:.2f}")
        
        # Verifica saldo novamente após ajustes
        final_cost = order_value
        if balance < final_cost:
            print(f"[SALDO INSUFICIENTE] Saldo: ${balance:.2f}, Custo da ordem: ${final_cost:.2f}")
            return
        
        try:
            # Log final antes de enviar ordem
            print(f"[ORDEM ENVIANDO] symbol={symbol}, side=buy, amount={amount_crypto}, price={price}")
            print(f"[ORDEM ENVIANDO] Valor esperado: ${order_value:.2f}")
            print(f"[SALDO DISPONÍVEL] ${balance:.2f}")
            
            # Verificação extra: saldo deve ser suficiente
            if balance < order_value * 1.01:  # 1% margem de segurança
                print(f"[BLOQUEADO] Saldo insuficiente com margem: ${balance:.2f} < ${order_value * 1.01:.2f}")
                return
            
            # ===== VERIFICAÇÃO DE LIMITE DIÁRIO =====
            if self.safety_manager:
                # Calcula PnL diário atual
                daily_pnl = sum(
                    stats.get('daily_pnl', 0) 
                    for stats in self.bot_stats.values()
                )
                
                # Verifica se atingiu limite diário
                if self.safety_manager.kill_switch.check_daily_loss(daily_pnl):
                    print(f"🛑 BLOQUEADO: Limite diário de perda atingido (${abs(daily_pnl):.2f} >= ${self.safety_manager.kill_switch.max_daily_loss})")
                    print("   → Trade cancelado para proteção de capital")
                    return
            
            # Executa ordem (prefere LIMIT/maker se configurado)
            from src.core.utils import load_config
            cfg = load_config()
            exec_cfg = cfg.get('execution', {})
            prefer_limit = bool(exec_cfg.get('prefer_limit', False))
            limit_timeout = int(exec_cfg.get('limit_order_timeout_sec', 5))

            order = None
            if prefer_limit:
                try:
                    limit_price = price * (1.0 - 0.001)  # 0.1% melhor para ser maker (compra)
                    print(f"[EXECUTANDO ORDEM LIMIT] symbol={symbol}, side=buy, amount={amount_crypto}, price={limit_price:.6f}")
                    order = self.exchange.create_limit_order(symbol=symbol, side='buy', amount=amount_crypto, price=limit_price)
                    if order and order.get('filled', 0) == 0:
                        time_waited = 0
                        while time_waited < limit_timeout:
                            time.sleep(1)
                            time_waited += 1
                            status = self.exchange.fetch_order_status(order.get('id'), symbol)
                            if status and status.get('filled', 0) > 0:
                                order = status
                                break
                        if order and order.get('filled', 0) == 0:
                            try:
                                self.exchange.cancel_order(order.get('id'), symbol)
                                print(f"[LIMIT TIMEOUT] Ordem LIMIT não preenchida em {limit_timeout}s - cancelando e fallback para MARKET")
                            except Exception as e:
                                print(f"[LIMIT CANCEL ERROR] {e}")
                            order = None
                except Exception as e:
                    print(f"[LIMIT ERROR] {e} - fallback para MARKET")

            if not order:
                print(f"[EXECUTANDO ORDEM] create_market_order: symbol={symbol}, side=buy, amount={amount_crypto}")
                order = self.exchange.create_market_order(
                    symbol=symbol,
                    side='buy',
                    amount=amount_crypto
                )
            
            # Log detalhado do que realmente aconteceu na ordem
            if order:
                print(f"[ORDEM EXECUTADA COM SUCESSO]")
                print(f"  ID: {order.get('id')}")
                print(f"  Status: {order.get('status')}")
                print(f"  Symbol: {order.get('symbol')}")
                print(f"  Side: {order.get('side')}")
                print(f"  Type: {order.get('type')}")
                print(f"  Amount solicitado: {order.get('amount')}")
                print(f"  Amount preenchido: {order.get('filled', 0)}")
                print(f"  Preço médio: {order.get('average', order.get('price', 0))}")
                print(f"  Custo total: {order.get('cost', 0)}")
                print(f"  Taxas: {order.get('fee', {})}")
                print(f"  Timestamp: {order.get('timestamp')}")
                if order.get('trades'):
                    print(f"  Trades: {len(order.get('trades'))} execuções")
                    for trade in order.get('trades', []):
                        print(f"    - Preço: {trade.get('price')}, Qty: {trade.get('amount')}, Custo: {trade.get('cost')}")
                
                # Verifica se foi totalmente preenchida
                filled = order.get('filled', 0)
                if filled == 0:
                    print(f"[AVISO] Ordem não foi preenchida! Verifique saldo ou liquidez.")
                    return
                
                # Registra posição
                invested = order.get('cost', amount_usd)
                fee_info = order.get('fee')
                try:
                    if fee_info and isinstance(fee_info, dict):
                        entry_fee = float(fee_info.get('cost', invested * 0.001))
                    else:
                        entry_fee = invested * 0.001
                except Exception:
                    entry_fee = invested * 0.001

                self.positions[symbol] = {
                    'bot_type': bot_type,
                    'entry_price': order.get('average', price),  # Usa preço médio real
                    'amount': filled,
                    'amount_usd': invested,  # Usa custo real
                    'entry_fee': entry_fee,
                    'time': datetime.now(),
                    'reason': reason,
                    'order_id': order.get('id')
                }
                
                bot.stats.open_positions += 1
                self._save_positions()
                
                self.logger.info(f"[{bot.name}] COMPRA {symbol} @ {order.get('average', price):.4f} (real)")
                self.logger.info(f"   Razao: {reason}")
                self.logger.info(f"   Quantidade: {filled}, Custo: ${order.get('cost', 0):.2f}")
            else:
                print(f"[ERRO] Ordem retornou None - possível falha na API")
                
        except Exception as e:
            error_msg = str(e)
            print(f"[ERRO DETALHADO] ao abrir posição {symbol}: {error_msg}")
            print(f"  Tipo do erro: {type(e).__name__}")
            
            # Análise específica do erro de saldo insuficiente
            if "insufficient balance" in error_msg.lower():
                print(f"[ANÁLISE ERRO] Saldo insuficiente detectado para {symbol}!")
                print(f"  Saldo disponível: ${balance:.2f}")
                print(f"  Valor da ordem: ${order_value:.2f}")
                print(f"  Diferença: ${balance - order_value:.2f}")
                print(f"  Preço usado: ${price:.4f}")
                print(f"  Amount crypto: {amount_crypto}")
                
                # Verifica se pode ser problema de subconta ou API
                try:
                    full_balance = self.exchange.fetch_balance()
                    usdt_info = full_balance.get('USDT', {})
                    print(f"  USDT total: {usdt_info.get('total', 0)}")
                    print(f"  USDT free: {usdt_info.get('free', 0)}")
                    print(f"  USDT used: {usdt_info.get('used', 0)}")
                    
                    # Verifica preço atual do símbolo
                    ticker = self.exchange.fetch_ticker(symbol)
                    current_price = ticker.get('last', 0)
                    print(f"  Preço atual de {symbol}: ${current_price:.4f}")
                    print(f"  Diferença de preço: ${abs(price - current_price):.4f}")
                    
                except Exception as balance_error:
                    print(f"  Erro ao verificar detalhes: {balance_error}")
            else:
                print(f"[OUTRO ERRO] {error_msg}")
            
            import traceback
            print(f"  Traceback completo:")
            traceback.print_exc()
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
            # Executa ordem de venda (prefere LIMIT/maker se configurado)
            from src.core.utils import load_config
            cfg = load_config()
            exec_cfg = cfg.get('execution', {})
            prefer_limit = bool(exec_cfg.get('prefer_limit', False))
            limit_timeout = int(exec_cfg.get('limit_order_timeout_sec', 5))

            order = None
            if prefer_limit:
                try:
                    limit_price = price * (1.0 + 0.001)  # 0.1% better to be maker for sells
                    print(f"[EXECUTANDO ORDEM LIMIT] symbol={symbol}, side=sell, amount={pos['amount']}, price={limit_price:.6f}")
                    order = self.exchange.create_limit_order(symbol=symbol, side='sell', amount=pos['amount'], price=limit_price)
                    if order and order.get('filled', 0) == 0:
                        time_waited = 0
                        while time_waited < limit_timeout:
                            time.sleep(1)
                            time_waited += 1
                            status = self.exchange.fetch_order_status(order.get('id'), symbol)
                            if status and status.get('filled', 0) > 0:
                                order = status
                                break
                        if order and order.get('filled', 0) == 0:
                            try:
                                self.exchange.cancel_order(order.get('id'), symbol)
                                print(f"[LIMIT TIMEOUT] Ordem LIMIT não preenchida em {limit_timeout}s - cancelando e fallback para MARKET")
                            except Exception as e:
                                print(f"[LIMIT CANCEL ERROR] {e}")
                            order = None
                except Exception as e:
                    print(f"[LIMIT ERROR] {e} - fallback para MARKET")

            if not order:
                print(f"[EXECUTANDO ORDEM] create_market_order: symbol={symbol}, side=sell, amount={pos['amount']}")
                order = self.exchange.create_market_order(
                    symbol=symbol,
                    side='sell',
                    amount=pos['amount']
                )
            
            # Log detalhado do que realmente aconteceu na ordem de venda
            if order:
                print(f"[ORDEM DE VENDA EXECUTADA COM SUCESSO]")
                print(f"  ID: {order.get('id')}")
                print(f"  Status: {order.get('status')}")
                print(f"  Symbol: {order.get('symbol')}")
                print(f"  Side: {order.get('side')}")
                print(f"  Type: {order.get('type')}")
                print(f"  Amount solicitado: {order.get('amount')}")
                print(f"  Amount preenchido: {order.get('filled', 0)}")
                print(f"  Preço médio: {order.get('average', order.get('price', 0))}")
                print(f"  Recebido: {order.get('cost', 0)}")
                print(f"  Taxas: {order.get('fee', {})}")
                print(f"  Timestamp: {order.get('timestamp')}")
                if order.get('trades'):
                    print(f"  Trades: {len(order.get('trades'))} execuções")
                    for trade in order.get('trades', []):
                        print(f"    - Preço: {trade.get('price')}, Qty: {trade.get('amount')}, Recebido: {trade.get('cost')}")
                
                # Verifica se foi totalmente preenchida
                filled = order.get('filled', 0)
                if filled == 0:
                    print(f"[AVISO] Ordem de venda não foi preenchida! Verifique liquidez.")
                    return
                
                # Usa preço médio real da venda
                exit_price = order.get('average', price)
                received_usd = order.get('cost', pos['amount_usd'])

                # Exit fee: try exchange-provided, else assume 0.1% of received
                exit_fee = 0.0
                fee_info = order.get('fee')
                try:
                    if fee_info and isinstance(fee_info, dict):
                        exit_fee = float(fee_info.get('cost', 0.0))
                    else:
                        exit_fee = received_usd * 0.001
                except Exception:
                    exit_fee = received_usd * 0.001

                # Calcula PnL líquido subtraindo taxas de entrada/saida (0.1% cada execução)
                entry_price = pos['entry_price']
                gross_pnl_usd = received_usd - pos['amount_usd']
                entry_fee = pos.get('entry_fee', pos['amount_usd'] * 0.001)
                net_pnl_usd = gross_pnl_usd - entry_fee - exit_fee
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                pnl_usd = net_pnl_usd
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
                    'exit_price': exit_price,
                    'pnl_pct': pnl_pct,
                    'pnl_usd': pnl_usd,
                    'invested': pos['amount_usd'],
                    'received': received_usd,
                    'entry_fee': pos.get('entry_fee', 0.0),
                    'exit_fee': exit_fee,
                    'net_pnl_usd': pnl_usd,
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
                self.logger.info(f"[{status}] [{bot.name}] {super_tag}VENDA {symbol} @ {exit_price:.4f} (real)")
                self.logger.info(f"   Entrada: {entry_price:.4f} -> Saida: {exit_price:.4f}")
                self.logger.info(f"   PnL: {pnl_usd:+.2f} USDT ({pnl_pct:+.2f}%) - Recebido: ${received_usd:.2f}")
                self.logger.info(f"   Razao: {reason}")
                
                # ===== NOTIFICA AI PARA APRENDIZADO =====
                if self.ai_enabled and self.ai_manager:
                    try:
                        self.ai_manager.on_trade_completed(trade)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Erro ao notificar AI: {e}")
            else:
                print(f"[ERRO] Ordem de venda retornou None - possível falha na API")
                
        except Exception as e:
            print(f"[ERRO DETALHADO] ao fechar posição {symbol}: {str(e)}")
            print(f"  Tipo do erro: {type(e).__name__}")
            import traceback
            print(f"  Traceback: {traceback.format_exc()}")
            self.logger.error(f"Erro ao fechar posicao {symbol}: {e}")
                
        except Exception as e:
            self.logger.error(f"Erro ao fechar posicao {symbol}: {e}")
    
    def print_summary(self):
        """Imprime resumo do estado atual"""
        
        print("\n" + "="*70)
        print(f"📊 RESUMO - Iteração #{self.iteration} - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)
        
        if self.unico_bot_mode:
            # ===== MODO UNICO BOT =====
            print(f"\nUNICO BOT:")
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
                emoji = bot_stats['name'].split()[0] if bot_stats['name'] else "BOT"
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
            print("INICIANDO UNICO BOT - App Leonardo v3.0")
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
        try:
            self._sync_positions_with_exchange()
        except KeyboardInterrupt:
            print("   ⚠️ Sincronização interrompida - continuando com posições locais")
            self.logger.warning("⚠️ Sincronização inicial interrompida - usando posições locais")
        except Exception as e:
            print(f"   ⚠️ Erro na sincronização inicial: {e}")
            self.logger.error(f"Erro na sincronização inicial: {e}")
            print("   🔄 Continuando com posições locais...")
        
        # ===== FASE 2: POUPANÇA DESABILITADA POR ENQUANTO =====
        print("\n💰 FASE 2: POUPANÇA (DESABILITADA)")
        
        # Obtém saldo atual
        total_balance = self.get_balance()

        # Se houver um INITIAL_BALANCE configurado no .env, use-o como override seguro
        try:
            env_initial = os.getenv('INITIAL_BALANCE')
            if env_initial:
                env_val = float(env_initial)
                if env_val > 0:
                    self.logger.info(f"🔁 Usando INITIAL_BALANCE do ambiente (override): ${env_val:.2f}")
                    total_balance = env_val
        except Exception:
            # Falha ao interpretar env INITIAL_BALANCE -> ignora
            pass

        print(f"   Saldo USDT disponível: ${total_balance:.2f}")
        print(f"   Poupança: DESABILITADA")
        # Inicializa KillSwitch com saldo inicial para checagens diárias
        if self.safety_manager and hasattr(self.safety_manager, 'kill_switch'):
            try:
                # Inicializa saldo e respeita valor configurado em config/config.yaml (ex: 5.0%)
                self.safety_manager.kill_switch.set_initial_balance(total_balance)
                print(f"🛡️ KillSwitch inicializado com saldo: ${total_balance:.2f} (max_daily_loss={self.safety_manager.kill_switch.max_daily_loss}%)")
            except Exception as e:
                print(f"⚠️ Falha ao setar kill switch initial balance: {e}")
        else:
            print("⚠️ SafetyManager ausente: RECOMENDADO habilitar SafetyManager antes de operar em real")

        # Se o TELEGRAM estiver configurado, envie um alerta de sistema online
        try:
            if os.getenv('USE_TELEGRAM', 'False').lower() in ('1', 'true', 'yes'):
                try:
                    from src.communication.telegram_client import send_message
                    msg = f"SISTEMA ONLINE - MONITORAMENTO ATIVADO\nSaldo configurado: ${total_balance:.2f}\nProtocolo: EMA200 + DailyStop 1.5% + MaxExposure 2%"
                    sent = send_message(msg)
                    if sent:
                        self.logger.info("✅ Mensagem de inicialização enviada ao Telegram")
                except Exception as tele_ex:
                    self.logger.warning(f"⚠️ Falha ao enviar mensagem Telegram: {tele_ex}")
        except Exception:
            pass
        
        capital_para_bots = total_balance
        print(f"\n📊 CAPITAL TOTAL DISPONÍVEL: ${capital_para_bots:.2f}")
        
        # Verifica se tem saldo para operar
        if capital_para_bots <= 0:
            print("\n⚠️  MODO OBSERVAÇÃO ATIVADO")
            print("   Sem saldo USDT disponível para novas operações")
            print("   Bot continuará monitorando mercado e gerenciando posições existentes")
            print("   Transfira USDT para a conta para iniciar trading")
        
        # ===== FASE 3: LOOP PRINCIPAL =====
        print("\n" + "="*70)
        print("🟢 FASE 3: INICIANDO OPERAÇÕES")
        print("="*70)
        
        try:
            # If running in REAL mode (not dry_run) ensure SafetyManager is present
            if not self.exchange.dry_run and not self.safety_manager:
                print("⛔ EXECUÇÃO REAL BLOQUEADA: SafetyManager não está ativo. Habilite SafetyManager e tente novamente.")
                self.running = False
                return

            while self.running:
                # Verifica Kill-Switch diário antes de cada iteração
                try:
                    if self.safety_manager and self.safety_manager.kill_switch.is_active:
                        print(f"⛔ KillSwitch ativo: {self.safety_manager.kill_switch.activation_reason} - Parando execução até amanhã")
                        self.running = False
                        break
                    # Avalia perda diária atual (usa coordinator.stats.daily_pnl em USD)
                    if self.safety_manager and self.safety_manager.kill_switch.check_daily_loss(self.coordinator.stats.daily_pnl):
                        print(f"⛔ KillSwitch acionado por perda diária. Motivo: {self.safety_manager.kill_switch.activation_reason}")
                        self.running = False
                        break
                except Exception as e:
                    print(f"⚠️ Erro ao avaliar KillSwitch: {e}")

                self.iteration += 1
                print(f"\n🔄 ITERAÇÃO {self.iteration} - Iniciando...")
                
                # Resgate automático periódico (a cada 10 iterações)
                if self.iteration % 10 == 0:
                    print("🔄 Verificando resgate automático do Earn Flexível...")
                    self.redeem_earn_flexible(min_amount=10)
                
                # ===== EXECUTA NO MODO APROPRIADO =====
                try:
                    if self.unico_bot_mode:
                        # Modo UnicoBot - processa todas as cryptos
                        print("Executando ciclo UnicoBot...")
                        self._run_unico_bot_cycle()
                        print("✅ Ciclo UnicoBot concluído")
                    else:
                        # Modo MultiBots - processa cada bot separadamente
                        for bot_type in self.coordinator.bots.keys():
                            if not self.running:
                                break
                            try:
                                self.run_bot_cycle(bot_type)
                            except Exception as bot_error:
                                print(f"⚠️ Erro no bot {bot_type}: {bot_error}")
                                # Continua com outros bots mesmo se um falhar
                                continue
                        
                        # Atualiza posições abertas nos stats
                        for bot in self.coordinator.bots.values():
                            bot.stats.open_positions = sum(
                                1 for pos in self.positions.values() 
                                if pos['bot_type'] == bot.bot_type
                            )
                except Exception as cycle_error:
                    print(f"⚠️ Erro no ciclo de trading: {cycle_error}")
                    # Não para o bot, apenas loga o erro e continua
                
                print(f"💾 Salvando estado...")
                # Salva estado
                try:
                    self.coordinator.save_state()
                except Exception as save_error:
                    print(f"⚠️ Erro ao salvar estado: {save_error}")
                
                # Salva dados para o dashboard (saldos, meta diária)
                try:
                    self._save_dashboard_data()
                except Exception as dashboard_error:
                    print(f"⚠️ Erro ao salvar dados do dashboard: {dashboard_error}")
                
                # Imprime resumo
                try:
                    self.print_summary()
                except Exception as summary_error:
                    print(f"⚠️ Erro ao imprimir resumo: {summary_error}")
                
                # Aguarda
                print(f"\n⏳ Aguardando {interval} segundos...\n")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Parando bots... (KeyboardInterrupt)")
            # Salva estado final antes de parar
            try:
                self.coordinator.save_state()
                self._save_positions()
            except:
                pass
        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO no loop principal: {e}")
            print("🔄 Tentando recuperação automática...")
            
            # Tenta salvar estado antes de possível crash
            try:
                self.coordinator.save_state()
                self._save_positions()
            except:
                pass
            
            # Aguarda um pouco antes de tentar continuar
            print("⏳ Aguardando 30 segundos para recuperação...")
            time.sleep(30)
            
            # Reinicia o loop se não foi parado manualmente
            if self.running:
                print("🔄 Reiniciando loop principal...")
                # Não para o bot - deixa o loop continuar
                return self.run(interval)
        finally:
            if not self.running:  # Só executa se foi parado intencionalmente
                self.running = False
                self.coordinator.stats.status = "stopped"
                try:
                    self.coordinator.save_state()
                except:
                    pass
                print("✅ Sistema Multi-Bot finalizado")
    
    def stop(self):
        """Para a execução"""
        self.running = False
        
        # Sistema parado com sucesso


def main():
    """Ponto de entrada principal"""
    engine = MultiBotEngine()
    engine.run(interval=3)


if __name__ == "__main__":
    main()
