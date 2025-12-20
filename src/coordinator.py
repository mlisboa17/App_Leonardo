"""
============================================================
COORDENADOR MULTI-BOT - R7_V1 - Otimizado para IA
============================================================

Responsabilidades:
1. Gerenciar os 4 bots especializados
2. Distribuir capital entre os bots (incluindo ajustes via IA)
3. Monitorar performance geral
4. Salvar estatísticas unificadas
5. Controlar limites de segurança
6. Orquestrar comandos de execução da IA.

============================================================
"""

import os
import sys
import yaml
import json
import time
import logging
import threading
import random # Adicionado para a simulação de execução da IA
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
from threading import Event
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega variáveis de ambiente
load_dotenv('config/.env')

# Importa módulo de auditoria
from src.audit import get_audit_logger, AuditEvent

# Importa observabilidade
from src.observability import get_metrics, measure_execution_time

from src.core.exchange_client import ExchangeClient


@dataclass
class BotStats:
    """Estatísticas de um bot individual"""
    name: str
    bot_type: str
    enabled: bool = True
    
    # Capital
    allocated_capital: float = 0.0
    current_capital: float = 0.0
    
    # Trades
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    
    # PnL
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    monthly_pnl: float = 0.0
    
    # Posições
    open_positions: int = 0
    max_positions: int = 5
    
    # Timestamps
    last_trade_time: str = ""
    last_update: str = ""
    
    # Status
    status: str = "idle"  # idle, running, paused, error
    error_message: str = ""
    
    def to_dict(self):
        return asdict(self)


@dataclass
class CoordinatorStats:
    """Estatísticas globais do coordenador"""
    # Capital total
    total_capital: float = 0.0
    available_capital: float = 0.0
    invested_capital: float = 0.0
    
    # PnL Global
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    monthly_pnl: float = 0.0
    
    # Trades globais
    total_trades: int = 0
    total_wins: int = 0
    total_losses: int = 0
    global_win_rate: float = 0.0
    
    # Bots
    active_bots: int = 0
    total_open_positions: int = 0
    
    # Status
    status: str = "stopped"  # stopped, running, paused
    start_time: str = ""
    last_update: str = ""
    
    # Por bot
    bots: Dict[str, BotStats] = field(default_factory=dict)
    
    def to_dict(self):
        result = asdict(self)
        result['bots'] = {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in self.bots.items()}
        return result


class MultiBot:
    """
    Classe que representa um bot especializado.
    Cada bot opera com um conjunto específico de cryptos.
    """
    
    def __init__(self, bot_type: str, config: dict, exchange_client: ExchangeClient, logger: logging.Logger):
        self.bot_type = bot_type
        self.config = config
        self.exchange = exchange_client
        self.logger = logger
        
        # Configurações do bot
        self.name = config.get('name', f'Bot {bot_type}')
        self.enabled = config.get('enabled', True)
        self.portfolio = config.get('portfolio', [])
        self.trading_config = config.get('trading', {})
        self.rsi_config = config.get('rsi', {})
        self.risk_config = config.get('risk', {})
        
        # Estado
        self.positions: Dict[str, dict] = {}
        self.stats = BotStats(
            name=self.name,
            bot_type=bot_type,
            enabled=self.enabled,
            max_positions=self.trading_config.get('max_positions', 5)
        )
        
        # Importa estratégia
        from src.strategies.smart_strategy import SmartStrategy
        
        # PASSA AS CONFIGURAÇÕES DO BOT PARA A ESTRATÉGIA
        strategy_config = {
            'bot_type': bot_type,
            'rsi': self.rsi_config,
            'risk': self.risk_config,
        }
        self.strategy = SmartStrategy(config=strategy_config)
        
        # Configura estratégia com parâmetros do bot
        self._configure_strategy()
        
    def _configure_strategy(self):
        """Configura a estratégia com os parâmetros específicos do bot"""
        # Parâmetros de risco
        self.strategy.stop_loss_pct = self.risk_config.get('stop_loss', -1.0)
        self.strategy.max_take_pct = self.risk_config.get('take_profit', 0.5)
        # Default trailing stop wider (2.0%) to avoid early cuts unless configured
        self.strategy.trailing_stop_pct = float(self.risk_config.get('trailing_stop', 2.0))
        # Default minimum hold before selling to avoid quick sells
        self.strategy.min_hold_minutes = int(self.risk_config.get('min_hold_minutes', 15))
        self.strategy.max_hold_minutes = self.risk_config.get('max_hold_minutes', 5)
        self.strategy.min_profit_to_hold = self.risk_config.get('min_profit', 0.15)
        # Min hold minutes for optimized selling (default 3)
        self.strategy.min_hold_minutes = int(self.risk_config.get('min_hold_minutes', 3))
        
    def get_symbols(self) -> List[str]:
        """Retorna lista de símbolos que este bot opera"""
        return [crypto['symbol'] for crypto in self.portfolio]
    
    def analyze_symbol(self, symbol: str, df) -> tuple:
        """Analisa um símbolo específico"""
        # Ajusta RSI baseado na configuração do bot
        rsi_oversold = self.rsi_config.get('oversold', 35)
        rsi_overbought = self.rsi_config.get('overbought', 65)
        
        signal, reason, indicators = self.strategy.analyze(df, symbol)
        
        return signal, reason, indicators
    
    def should_sell_position(self, symbol: str, entry_price: float, current_price: float, 
                             df, position_time: datetime, position_size: float = None) -> tuple:
        """Verifica se deve vender uma posição"""
        positions_full = len(self.positions) >= self.stats.max_positions
        return self.strategy.should_sell(symbol, entry_price, current_price, df, 
                                         position_time, positions_full, position_size)
    
    def update_stats(self, pnl: float, is_win: bool):
        """Atualiza estatísticas do bot"""
        self.stats.total_trades += 1
        self.stats.total_pnl += pnl
        self.stats.daily_pnl += pnl
        
        if is_win:
            self.stats.wins += 1
        else:
            self.stats.losses += 1
        
        if self.stats.total_trades > 0:
            self.stats.win_rate = (self.stats.wins / self.stats.total_trades) * 100
        
        self.stats.last_trade_time = datetime.now().isoformat()
        self.stats.last_update = datetime.now().isoformat()


class BotCoordinator:
    """
    Coordenador principal que gerencia todos os bots.
    """
    
    def __init__(self, config_path: str = "config/bots_config.yaml", data_dir: str = None):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Setup logging
        self._setup_logging()
        
        # Exchange client (compartilhado)
        self.exchange = self._setup_exchange()

        # Inicializa SafetyManager automaticamente se configurado
        try:
            safety_cfg = self.config.get('safety', {})
            if safety_cfg.get('require_safety_manager', True):
                self.logger.info("[safety] require_safety_manager ativo — inicializando SafetyManager")
                from src.safety.safety_manager import SafetyManager
                sm = SafetyManager({
                    'max_daily_loss': safety_cfg.get('max_daily_loss', 2.0),
                    'max_drawdown': safety_cfg.get('max_drawdown', 5),
                    'max_positions': safety_cfg.get('max_positions', 10),
                })
                # Tenta definir saldo inicial para o kill switch
                try:
                    bal = self.exchange.fetch_balance()
                    free = bal.get('USDT', {}).get('free', 0)
                    sm.kill_switch.set_initial_balance(free)
                    self.logger.info(f"[safety] SafetyManager inicializada, balance inicial={free}")
                except Exception as e:
                    self.logger.warning(f"[safety] SafetyManager inicializada, mas falha ao setar balance: {e}")
                self.safety_manager = sm
        except Exception as e:
            self.logger.exception(f"[safety] falha ao inicializar SafetyManager: {e}")
        
        # Bots
        self.bots: Dict[str, MultiBot] = {}
        
        # Estatísticas globais
        self.stats = CoordinatorStats()
        
        # Controle
        self.running = False
        self.threads: List[threading.Thread] = []
        
        # Paths
        self.data_path = Path(data_dir) if data_dir else Path("data")
        self.stats_file = self.data_path / "coordinator_stats.json"
        # Bot status file watcher
        self.bot_status_file = self.data_path / "bot_status.json"
        self._watcher_stop_event = Event()
        self._last_seen_action = None
        self._watcher_thread = threading.Thread(target=self._watch_bot_status_loop, daemon=True)
        
        # Auditoria
        self.audit = get_audit_logger()
        self.audit.logger.info("=== Coordenador inicializado ===")
        
        # Observabilidade
        self.metrics = get_metrics()
        
        # Inicializa bots
        self._init_bots()
        
        # Carrega estado anterior
        self._load_state()

        # Garantir total capital inicial (fallback para $1,933.11 se fetch falha)
        try:
            bal = self.exchange.fetch_balance()
            free = bal.get('USDT', {}).get('free', 0) if bal else 0
            total = float(free)
            if total <= 0:
                total = 1933.11
                self.logger.warning(f"Balance não informado pela exchange. Definindo fallback total_capital=${total}")
            self.stats.total_capital = total
            self.stats.available_capital = total
        except Exception as e:
            self.stats.total_capital = 1933.11
            self.stats.available_capital = 1933.11
            self.logger.warning(f"Falha ao obter balance da exchange, usando fallback ${self.stats.total_capital}: {e}")

        # Inicia watcher de bot_status.json para reinicios/stop automáticos
        try:
            self._watcher_thread.start()
            self.logger.info("[WATCHER] Bot status watcher iniciado")
        except Exception:
            self.logger.exception("[WATCHER] Falha ao inicializar watcher")

        # Inicia verificação periódica de Fear & Greed (market panic) e slippage
        self.scalping_paused = False
        self._panic_stop_event = Event()
        self._panic_thread = threading.Thread(target=self._panic_monitor_loop, daemon=True)
        try:
            self._panic_thread.start()
            self.logger.info("[PANIC_MONITOR] Monitor de Fear&Greed iniciado")
        except Exception:
            self.logger.exception("[PANIC_MONITOR] Falha ao iniciar monitor de Fear&Greed")

        # Scheduler diário para fechamento às 23:59 (Horário local - Brasília assumido)
        self._daily_close_thread = threading.Thread(target=self._daily_close_loop, daemon=True)
        try:
            self._daily_close_thread.start()
            self.logger.info("[DAILY_CLOSE] Scheduler diário de fechamento iniciado")
        except Exception:
            self.logger.exception("[DAILY_CLOSE] Falha ao iniciar scheduler diário")
        
    def _load_config(self) -> dict:
        """Carrega configuração do arquivo YAML"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self):
        """Configura logging"""
        log_config = self.config.get('coordinator', {}).get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        self.logger = logging.getLogger('Coordinator')
        self.logger.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        # Ajusta nível do handler de console conforme configuração (ou DEBUG_NETWORK)
        if os.getenv('DEBUG_NETWORK') in ('1', 'true', 'True'):
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(log_level)
        self.logger.addHandler(console_handler)
        
        # File handler
        if log_config.get('save_to_file', True):
            log_path = Path(log_config.get('file_path', 'logs/coordinator.log'))
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            # Sempre salvar DEBUG em arquivo se DEBUG_NETWORK estiver ativo
            if os.getenv('DEBUG_NETWORK') in ('1', 'true', 'True'):
                file_handler.setLevel(logging.DEBUG)
                # Forçar também bibliotecas de rede para DEBUG para diagnosticar handshake
                logging.getLogger('ccxt').setLevel(logging.DEBUG)
                logging.getLogger('urllib3').setLevel(logging.DEBUG)
                logging.getLogger('requests').setLevel(logging.DEBUG)
                logging.getLogger('websockets').setLevel(logging.DEBUG)
                self.logger.info('[DEBUG_NETWORK] ativo — bibliotecas de rede em DEBUG')
            else:
                file_handler.setLevel(log_level)
            self.logger.addHandler(file_handler)
    
    def _setup_exchange(self) -> ExchangeClient:
        """Configura cliente da exchange"""
        global_config = self.config.get('global', {})
        
        # Carrega credenciais
        api_key = os.getenv('BINANCE_API_KEY', '')
        api_secret = os.getenv('BINANCE_API_SECRET', '')
        
        if not api_key or not api_secret:
            self.logger.error("CREDENCIAIS BINANCE_API_KEY/SECRET nao encontradas no .env!")
            raise ValueError("Credenciais Binance não configuradas")
        
        # Verifica se é testnet
        testnet = global_config.get('testnet', False)
        env_type = "TESTNET" if testnet else "PRODUCAO"
        
        self.logger.warning(f"[{env_type}] MODO {env_type} - {'TESTE SEGURO' if testnet else 'DINHEIRO REAL'}!")
        
        # Carrega configuração dry_run
        dry_run = global_config.get('execution', {}).get('dry_run', False)
        
        return ExchangeClient(
            exchange_name=global_config.get('exchange', 'binance'),
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
            dry_run=dry_run
        )
    
    def _init_bots(self):
        """Inicializa os 4 bots especializados"""
        bot_types = ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']
        
        for bot_type in bot_types:
            if bot_type in self.config:
                bot_config = self.config[bot_type]
                if bot_config.get('enabled', True):
                    self.bots[bot_type] = MultiBot(
                        bot_type=bot_type,
                        config=bot_config,
                        exchange_client=self.exchange,
                        logger=self.logger
                    )
                    self.logger.info(f"[OK] {bot_config.get('name', bot_type)} inicializado")
                else:
                    self.logger.info(f"[PAUSED] {bot_config.get('name', bot_type)} desabilitado")
    
    def _load_state(self):
        """Carrega estado anterior do arquivo"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Restaura estatísticas globais
                self.stats.total_pnl = data.get('total_pnl', 0.0)
                self.stats.monthly_pnl = data.get('monthly_pnl', 0.0)
                self.stats.total_trades = data.get('total_trades', 0)
                self.stats.total_wins = data.get('total_wins', 0)
                self.stats.total_losses = data.get('total_losses', 0)
                # Restaura estatísticas e posições por bot
                bots_data = data.get('bots', {})
                for bot_type, bot_stats in bots_data.items():
                    if bot_type in self.bots:
                        self.bots[bot_type].stats.total_pnl = bot_stats.get('total_pnl', 0.0)
                        self.bots[bot_type].stats.total_trades = bot_stats.get('total_trades', 0)
                        self.bots[bot_type].stats.wins = bot_stats.get('wins', 0)
                        self.bots[bot_type].stats.losses = bot_stats.get('losses', 0)
                        # Restaurar posições abertas
                        if 'positions' in bot_stats:
                            self.bots[bot_type].positions = bot_stats['positions']
                self.logger.info("[STATE] Estado anterior restaurado (incluindo posições)")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao carregar estado: {e}")
    
    def save_state(self):
        """Salva estado atual no arquivo"""
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Atualiza estatísticas globais
        self._update_global_stats()
        
        data = self.stats.to_dict()
        # Adiciona posições dos bots
        data['total_capital'] = self.stats.total_capital
        # Salva
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    # ----- PANIC & SLIPPAGE MONITOR -----
    def _panic_monitor_loop(self):
        """Loop rodando em background para checar Fear & Greed Index e slippage"""
        import requests
        while not self._panic_stop_event.is_set():
            try:
                fng = self._fetch_fear_greed_index()
                if fng is not None:
                    self.logger.debug(f"[FNG] Fear&Greed index: {fng}")
                    if fng < 20:
                        # Suspende bots voláteis/memes
                        for bt in ['bot_volatil', 'bot_meme']:
                            bot = self.bots.get(bt)
                            if bot and bot.enabled:
                                bot.enabled = False
                                self.logger.warning(f"[PANIC] Fear&Greed {fng} < 20 — desabilitando {bt}")
                    else:
                        # Reativa bots se anteriormente desativados por pânico
                        for bt in ['bot_volatil', 'bot_meme']:
                            bot = self.bots.get(bt)
                            if bot and not bot.enabled:
                                bot.enabled = True
                                self.logger.info(f"[PANIC] Fear&Greed {fng} >= 20 — reativando {bt}")
                # Espera 5 minutos
                self._panic_stop_event.wait(timeout=300)
            except Exception as e:
                self.logger.error(f"[PANIC_MONITOR] Erro no loop: {e}")
                self._panic_stop_event.wait(timeout=300)

    def _daily_close_loop(self):
        """Loop que aguarda o horário de fechamento do dia (23:59) e executa procedimentos"""
        import time
        import pytz
        from datetime import datetime, timedelta

        tz = pytz.timezone('America/Sao_Paulo')
        while True:
            now = datetime.now(tz)
            # calcula próximo 23:59 do mesmo dia
            target = now.replace(hour=23, minute=59, second=0, microsecond=0)
            if now >= target:
                # já passou -> pega amanhã
                target = target + timedelta(days=1)
            wait_seconds = (target - now).total_seconds()
            self.logger.info(f"[DAILY_CLOSE] Aguardando fechamento diário em {wait_seconds/60:.1f} minutos")
            time.sleep(wait_seconds + 2)  # espera até o alvo + 2s
            try:
                self.logger.info("[DAILY_CLOSE] Executando procedimentos de final de dia")
                # 1) End of day in capital manager
                if self.capital_manager:
                    self.capital_manager.end_of_day_procedure()
                # 2) Gerar dashboard e enviar para Telegram
                self._send_daily_dashboard()
                # 3) Salvar estado
                self.save_state()
            except Exception as e:
                self.logger.exception(f"[DAILY_CLOSE] Erro durante procedimentos de fechamento: {e}")

    def _send_daily_dashboard(self):
        """Compila dados e envia para Telegram (3 abas)"""
        try:
            from src.communication.telegram_client import send_dashboard

            # Aba 1 - Resumo
            summary = {
                'balance': self.stats.total_capital,
                'daily_pnl': self.stats.daily_pnl,
                'loss_to_recover': getattr(self.capital_manager, 'loss_to_recover_usd', 0.0),
                'progress_to_goal': f"{(self.stats.total_capital/2125.0*100):.1f}%"
            }

            # Aba 2 - Performance por bot
            performance = {}
            for bt, bot in self.bots.items():
                performance[bt] = {
                    'trades': bot.stats.total_trades,
                    'pnl': bot.stats.total_pnl,
                    'win_rate': bot.stats.win_rate
                }

            # Aba 3 - Risco
            risk = {
                'stops_triggered': 0,  # Placeholder - incrementar quando stops ocorrerem numa implementação futura
                'ema_savings': 0.0
            }

            send_dashboard(summary, performance, risk)
            self.logger.info("[DAILY_CLOSE] Dashboard enviado por Telegram")
        except Exception as e:
            self.logger.error(f"[DAILY_CLOSE] Falha ao enviar dashboard: {e}")
    def _fetch_fear_greed_index(self) -> Optional[int]:
        """Busca Fear&Greed Index via API pública (alternative.me)"""
        try:
            import requests
            r = requests.get('https://api.alternative.me/fng/')
            if r.status_code == 200:
                data = r.json()
                if 'data' in data and len(data['data']) > 0:
                    value = int(data['data'][0].get('value', 0))
                    return value
        except Exception as e:
            self.logger.debug(f"Falha ao buscar FNG: {e}")
        return None

    def check_slippage_and_pause_scalping(self, signal_price: float, executed_price: float, symbol: str = None):
        """Analisa slippage e pausa scalping se ultrapassar 0.1%"""
        try:
            if signal_price <= 0:
                return False
            slippage_pct = abs(executed_price - signal_price) / signal_price * 100.0
            if slippage_pct > 0.1:
                self.pause_scalping(f"Slippage alto {slippage_pct:.2f}% em {symbol} (signal {signal_price} / exec {executed_price})")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro ao checar slippage: {e}")
            return False

    def pause_scalping(self, reason: str = ''):
        """Pause scalping operations and log reason"""
        if not self.scalping_paused:
            self.scalping_paused = True
            # Optionally disable specific bots that perform scalping if identifiable
            for bt, bot in self.bots.items():
                # heurística: if bot name or config mentions 'scalp' or 'scalping'
                name = bot.config.get('name', '').lower() if bot and bot.config else ''
                if 'scalp' in name or 'scalping' in name:
                    bot.enabled = False
            self.logger.warning(f"[SLIPPAGE] Scalping pausado — {reason}")

    def resume_scalping(self):
        """Resume scalping operations"""
        if self.scalping_paused:
            self.scalping_paused = False
            for bt, bot in self.bots.items():
                name = bot.config.get('name', '').lower() if bot and bot.config else ''
                if 'scalp' in name or 'scalping' in name:
                    bot.enabled = True
            self.logger.info("[SLIPPAGE] Scalping reativado manualmente")
    # ----- FIM PANIC & SLIPPAGE -----

        for bot_type, bot in self.bots.items():
            if 'bots' not in data:
                data['bots'] = {}
            if bot_type not in data['bots']:
                data['bots'][bot_type] = {}
            data['bots'][bot_type]['positions'] = bot.positions
        with open(self.stats_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def reload_config(self):
        """Recarrega YAML de configuração em memória e atualiza bots."""
        try:
            self.config = self._load_config()
            self._init_bots()
            self.logger.info("🔁 Configuração recarregada e bots reconfigurados")
            return True
        except Exception as e:
            self.logger.exception(f"Erro ao recarregar config: {e}")
            return False

    def reconfigure_bot(self, bot_type: str):
        """Recria a instância do bot a partir do YAML e mantém enabled state."""
        if bot_type not in self.config:
            self.logger.error(f"Bot config não encontrada: {bot_type}")
            return False
        try:
            bot_cfg = self.config.get(bot_type, {})
            enabled = bot_cfg.get('enabled', True)
            # Recreate instance
            self.bots[bot_type] = MultiBot(bot_type=bot_type, config=bot_cfg, exchange_client=self.exchange, logger=self.logger)
            self.bots[bot_type].enabled = enabled
            self.logger.info(f"🔧 Bot {bot_type} reconfigurado com sucesso")
            return True
        except Exception as e:
            self.logger.exception(f"Erro ao reconfigurar bot {bot_type}: {e}")
            return False

    def restart_bot(self, bot_type: str, reason: str = "config_change"):
        """Reinicia um bot: reconfigura e marca como enabled conforme configuração."""
        start_time = time.time()
        self.logger.info(f"[RESTART] Solicitado reinício do bot {bot_type} (razão: {reason})")
        self.audit.log_restart(bot_type=bot_type, reason=reason, source='coordinator')
        
        try:
            # Safety: disable, reconfigure, enable
            if bot_type in self.bots:
                try:
                    self.bots[bot_type].enabled = False
                except Exception:
                    pass
            
            # reload configuration from disk to pick up latest changes
            self.config = self._load_config()
            ok = self.reconfigure_bot(bot_type)
            
            elapsed_ms = (time.time() - start_time) * 1000
            self.metrics.record_restart(bot_type, ok, elapsed_ms)
            
            if ok:
                self.logger.info(f"[RESTART] Bot {bot_type} reiniciado com nova configuração ({elapsed_ms:.0f}ms)")
                self.audit.log_event(AuditEvent(
                    timestamp=datetime.now().isoformat(),
                    event_type='restart',
                    severity='info',
                    source='coordinator',
                    target=bot_type,
                    action='restart_completed',
                    details={'reason': reason, 'status': 'success', 'duration_ms': elapsed_ms}
                ))
            else:
                self.audit.log_error(
                    error_type='restart_failed',
                    bot_type=bot_type,
                    message=f"Falha ao reiniciar bot {bot_type}",
                    source='coordinator'
                )
            return ok
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self.metrics.record_restart(bot_type, False, elapsed_ms)
            self.audit.log_error(
                error_type='restart_exception',
                bot_type=bot_type,
                message=f"Exceção ao reiniciar: {str(e)}",
                traceback=str(e),
                source='coordinator'
            )
            raise

    def restart_all(self, reason: str = "config_change"):
        """Reinicia todos os bots (reconfigura todas as instâncias)"""
        start_time = time.time()
        self.logger.info(f"[RESTART ALL] Reiniciando todos os bots (razão: {reason})")
        self.audit.log_restart(bot_type=None, reason=reason, source='coordinator')
        
        self.config = self._load_config()
        success_count = 0
        failed_count = 0
        
        # Garante que os 4 bots padrão são incluídos
        bot_types_to_restart = list(self.config.keys())
        default_bots = ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']
        for bot_type in default_bots:
            if bot_type not in bot_types_to_restart:
                bot_types_to_restart.append(bot_type)
        
        for bot_type in bot_types_to_restart:
            if bot_type in self.config: # Garante que só reinicia o que está na config
                try:
                    if self.reconfigure_bot(bot_type):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    self.audit.log_error(
                        error_type='restart_failed',
                        bot_type=bot_type,
                        message=f"Falha ao reiniciar bot {bot_type}",
                        traceback=str(e),
                        source='coordinator'
                    )
        
        elapsed_ms = (time.time() - start_time) * 1000
        success = failed_count == 0
        
        self.logger.info(f"[RESTART ALL] {success_count} bots reiniciados com sucesso ({elapsed_ms:.0f}ms)")
        self.audit.log_event(AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type='restart',
            severity='info',
            source='coordinator',
            target='all_bots',
            action='restart_all_completed',
            details={
                'reason': reason,
                'success_count': success_count,
                'failed_count': failed_count,
                'duration_ms': elapsed_ms
            }
        ))

    def stop_bot(self, bot_type: str, reason: str = "user_request"):
        """Para um bot definindo 'enabled' para False e atualizando estado."""
        if bot_type not in self.bots:
            self.logger.error(f"Bot não encontrado para stop: {bot_type}")
            self.metrics.record_error('bot_not_found', 'coordinator')
            self.audit.log_error(
                error_type='bot_not_found',
                bot_type=bot_type,
                message=f"Bot {bot_type} não encontrado para stop",
                source='coordinator'
            )
            return False
        
        self.bots[bot_type].enabled = False
        self.metrics.record_stop(bot_type, True)
        self.logger.info(f"[STOP] Bot {bot_type} parado (razão: {reason})")
        self.audit.log_stop(bot_type=bot_type, reason=reason, source='coordinator')
        return True

    def _watch_bot_status_loop(self):
        """Loop que observa `data/bot_status.json` e aplica ações (restart/stop) com coalescimento robusto."""
        # ... (Mantido o código complexo de watcher inalterado, pois é funcional)
        import time
        last_applied = { 'action': None, 'target': None, 'at': None }
        coalesce_delay = 2.0  # segundos - configurável via config
        pending = None
        coalesce_attempts = 0
        max_coalesce_attempts = 5
        
        while not self._watcher_stop_event.is_set():
            try:
                if not self.bot_status_file.exists():
                    time.sleep(1)
                    continue
                    
                with open(self.bot_status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                action = data.get('last_action')
                target = data.get('target_bot')
                at = data.get('last_action_at')
                
                # Detecção de nova ação
                is_new_action = action and (
                    last_applied['action'] != action or 
                    last_applied['target'] != target or 
                    last_applied['at'] != at
                )
                
                if is_new_action:
                    if pending:
                        # Cancelar ação anterior e substituir pela nova
                        self.logger.info(
                            f"[WATCHER] Ação substituída: {pending['action']} target={pending['target']} "
                            f"→ {action} target={target}"
                        )
                    else:
                        self.logger.info(f"[WATCHER] Ação detectada: {action} target={target} at={at}")
                    
                    # Reinicia coalescimento
                    pending = { 
                        'action': action, 
                        'target': target, 
                        'at': at, 
                        'ts': time.time()
                    }
                    coalesce_attempts = 0
                
                # Executar ação pendente após delay de coalescimento
                if pending:
                    elapsed = time.time() - pending['ts']
                    
                    # Verificar se mais ações chegaram (coalescing)
                    if elapsed < coalesce_delay and is_new_action:
                        coalesce_attempts += 1
                        if coalesce_attempts <= max_coalesce_attempts:
                            self.logger.debug(
                                f"[WATCHER] Coalescimento: esperando {coalesce_delay:.1f}s "
                                f"(tentativa {coalesce_attempts}/{max_coalesce_attempts})"
                            )
                    
                    # Executar se delay passou
                    elif elapsed >= coalesce_delay:
                        act = pending['action']
                        tgt = pending['target']
                        
                        self.logger.info(
                            f"[WATCHER] Executando ação: {act} target={tgt} "
                            f"(após coalescimento de {elapsed:.1f}s)"
                        )
                        
                        try:
                            if act == 'restart':
                                if tgt:
                                    self.restart_bot(tgt)
                                else:
                                    self.restart_all()
                            elif act == 'stop':
                                if tgt:
                                    self.stop_bot(tgt)
                                else:
                                    for b in list(self.bots.keys()):
                                        self.stop_bot(b)
                            
                            # Marca como aplicada
                            last_applied = {'action': act, 'target': tgt, 'at': at}
                            pending = None
                            self.logger.info(f"[WATCHER] Ação {act} executada com sucesso")
                        except Exception as e:
                            self.logger.error(f"[WATCHER] Erro ao executar {act}: {e}")
                            pending = None
            except json.JSONDecodeError as e:
                self.logger.warning(f"[WATCHER] Erro ao decodificar bot_status.json: {e}")
            except Exception as e:
                self.logger.exception(f"[WATCHER] Erro durante observação: {e}")
            
            time.sleep(1)
    
    # ======================================================================
    # NOVO: MÓDULO DE ORQUESTRAÇÃO DE AÇÕES DA IA (Passo 4)
    # ======================================================================
    
    def orchestrate_ai_action(self, action_type: str, details: dict):
        """
        [ENDPOINT DA API] Recebe a ação da IA e a delega para a execução correta.
        """
        self.logger.info(f"[AI ORCHESTRATOR] Ação recebida: {action_type}, Detalhes: {details}")
        
        try:
            if action_type == "EXECUTE_TRADE":
                return self._handle_execute_trade(details)
            
            elif action_type == "ADJUST_ALLOCATION":
                return self._handle_adjust_allocation(details)
                
            else:
                msg = f"Tipo de ação desconhecido: {action_type}"
                self.logger.error(f"[AI ORCHESTRATOR] {msg}")
                self.audit.log_error('unknown_ai_action', None, msg, 'ai_orchestrator')
                return {"status": "error", "message": msg}
        except Exception as e:
            self.logger.exception(f"[AI ORCHESTRATOR] Exceção na orquestração: {e}")
            self.audit.log_error('orchestration_exception', None, str(e), 'ai_orchestrator', traceback=str(e))
            return {"status": "error", "message": f"Erro interno na orquestração: {str(e)}"}

    def _handle_execute_trade(self, details: dict):
        """Lida com a execução de uma ordem de trade sugerida pela IA (REAL)."""
        
        symbol = details.get('symbol')
        side = details.get('side')
        amount = details.get('amount')
        bot_type = details.get('bot_type', 'ai_system') # Usado para auditoria
        
        if not all([symbol, side, amount]):
            msg = f"Dados de trade insuficientes: {details}"
            self.logger.error(f"[AI TRADE FAIL] {msg}")
            self.audit.log_error('trade_data_missing', bot_type, msg, 'ai_orchestrator')
            return {"status": "error", "message": msg}

        self.logger.info(f"[AI TRADE REAL] Tentando {side} {amount} USDT em {symbol} (Bot: {bot_type})")
        
        try:
            # 1. Obter preço atual para estimativa
            price = self.exchange.get_ticker_price(symbol)
            if not price:
                raise Exception(f"Não foi possível obter preço para {symbol}.")

            # 2. Calcular a quantidade (quantity) com base no 'amount' em USDT
            quantity = amount / price 
            
            # 3. Executar a ordem REAL na Exchange
            order_result = self.exchange.create_order(
                symbol=symbol,
                side=side.upper(), # 'BUY' ou 'SELL'
                amount=quantity,   # Quantidade na moeda base
                type='MARKET'      # Ordem a mercado para simplicidade
            )
            
            trade_id = order_result.get('id', 'N/A')
            
            self.logger.info(f"[AI TRADE OK] Ordem {trade_id} executada para {symbol}. Status: {order_result.get('status')}")
            
            # 4. Auditoria e Retorno
            self.audit.log_event(AuditEvent(
                timestamp=datetime.now().isoformat(),
                event_type='ai_trade_exec_real',
                severity='critical', # Mudando para critical/warning por ser real
                source='ai_orchestrator',
                target=bot_type,
                action='trade_executed',
                details={
                    'symbol': symbol, 
                    'side': side, 
                    'amount_usd': amount, 
                    'quantity': quantity,
                    'trade_id': trade_id
                }
            ))
            return {"status": "success", "message": "Ordem de trade REAL executada com sucesso.", "trade_id": trade_id}
                
        except Exception as e:
            msg = f"Falha REAL ao executar trade para {symbol}: {str(e)}"
            self.logger.error(f"[AI TRADE FAIL] {msg}")
            self.audit.log_error('ai_trade_failed', bot_type, msg, 'ai_orchestrator', traceback=str(e))
            return {"status": "error", "message": f"Falha na execução do trade REAL: {str(e)}"}

    def _handle_adjust_allocation(self, details: dict):
        """Lida com o ajuste de alocação de capital entre bots."""
        bot_from = details.get('bot_from')
        bot_to = details.get('bot_to')
        amount_pct = details.get('amount_pct') # Ex: 0.10 para 10%
        
        if not all([bot_from, bot_to, amount_pct is not None]):
            msg = f"Dados de alocação incompletos: {details}"
            self.logger.error(f"[AI ALLOC FAIL] {msg}")
            self.audit.log_error('allocation_data_missing', None, msg, 'ai_orchestrator')
            return {"status": "error", "message": msg}

        # Verificação robusta de existência
        if bot_from not in self.config or bot_to not in self.config:
            msg = f"Bot(s) não encontrado(s) na config (YAML): {bot_from}, {bot_to}"
            self.logger.error(f"[AI ALLOC FAIL] {msg}")
            self.audit.log_error('bot_not_found', None, msg, 'ai_orchestrator')
            return {"status": "error", "message": msg}
        
        try:
            # 1. Recarregar config para garantir que o cálculo é feito com dados do disco
            self.reload_config()
            
            # 2. Obter capital (garantindo que existe no YAML)
            current_capital_from = self.config.get(bot_from, {}).get('risk', {}).get('allocated_capital_usd', 0.0)
            amount_to_move = current_capital_from * amount_pct
            
            if amount_to_move < 0.01:
                msg = f"Valor a mover ({amount_to_move:.2f} USD) é muito baixo para {amount_pct*100:.1f}% de {current_capital_from:.2f}."
                self.logger.warning(f"[AI ALLOC ABORT] {msg}")
                return {"status": "warning", "message": "Valor a mover é insignificante. Ação abortada."}

            # 3. Atualizar o capital alocado no dicionário de configuração (in-memory)
            if 'risk' not in self.config[bot_from]: self.config[bot_from]['risk'] = {}
            if 'risk' not in self.config[bot_to]: self.config[bot_to]['risk'] = {}
            
            self.config[bot_from]['risk']['allocated_capital_usd'] = max(0.0, current_capital_from - amount_to_move) # Safety check
            
            current_capital_to = self.config.get(bot_to, {}).get('risk', {}).get('allocated_capital_usd', 0.0)
            self.config[bot_to]['risk']['allocated_capital_usd'] = current_capital_to + amount_to_move

            # 4. SALVAR A CONFIGURAÇÃO ATUALIZADA NO DISCO
            config_file = Path(self.config_path)
            with open(config_file, 'w', encoding='utf-8') as f:
                # Otimização: Garantir que o YAML salva de forma legível
                yaml.dump(self.config, f, indent=2, sort_keys=False) 

            # 5. REINICIAR OS BOTS AFETADOS PARA APLICAR A NOVA CONFIGURAÇÃO
            self.restart_bot(bot_from, reason="ai_allocation_change")
            self.restart_bot(bot_to, reason="ai_allocation_change")

            self.logger.warning(
                f"[AI ALLOC OK] Realocação de ${amount_to_move:.2f} ({amount_pct*100:.1f}%) concluída."
            )
            self.audit.log_event(AuditEvent(
                timestamp=datetime.now().isoformat(),
                event_type='ai_allocation_change',
                severity='warning',
                source='ai_orchestrator',
                target='allocation_system',
                action='capital_adjusted',
                details={'from': bot_from, 'to': bot_to, 'amount_usd': amount_to_move}
            ))
            
            return {"status": "success", "message": "Alocação ajustada no disco e bots reiniciados."}

        except Exception as e:
            msg = f"Erro ao ajustar alocação: {str(e)}"
            self.logger.exception(f"[AI ALLOC FAIL] {msg}")
            self.audit.log_error('ai_allocation_exception', None, msg, 'ai_orchestrator', traceback=str(e))
            return {"status": "error", "message": f"Erro interno ao ajustar alocação: {str(e)}"}

    # ======================================================================
    # MÉTODOS DE ESTATÍSTICAS E UTILIDADE (Existente)
    # ======================================================================

    def _update_global_stats(self):
        """Atualiza estatísticas globais baseado nos bots"""
        self.stats.total_pnl = 0
        self.stats.daily_pnl = 0
        self.stats.total_trades = 0
        self.stats.total_wins = 0
        self.stats.total_losses = 0
        self.stats.total_open_positions = 0
        self.stats.active_bots = 0
        
        for bot_type, bot in self.bots.items():
            # Atualiza stats globais
            self.stats.total_pnl += bot.stats.total_pnl
            self.stats.daily_pnl += bot.stats.daily_pnl
            self.stats.total_trades += bot.stats.total_trades
            self.stats.total_wins += bot.stats.wins
            self.stats.total_losses += bot.stats.losses
            self.stats.total_open_positions += bot.stats.open_positions
            
            if bot.enabled:
                self.stats.active_bots += 1
            
            # Adiciona stats do bot (por referência)
            self.stats.bots[bot_type] = bot.stats
        
        if self.stats.total_trades > 0:
            self.stats.global_win_rate = (self.stats.total_wins / self.stats.total_trades) * 100
        
        self.stats.last_update = datetime.now().isoformat()
    
    def get_all_symbols(self) -> List[str]:
        """Retorna todos os símbolos de todos os bots"""
        symbols = []
        for bot in self.bots.values():
            symbols.extend(bot.get_symbols())
        return list(set(symbols))  # Remove duplicatas
    
    def get_bot_for_symbol(self, symbol: str) -> Optional[MultiBot]:
        """Retorna o bot responsável por um símbolo"""
        for bot in self.bots.values():
            if symbol in bot.get_symbols():
                return bot
        return None
    
    def get_stats_for_dashboard(self) -> dict:
        """Retorna estatísticas formatadas para o dashboard"""
        self._update_global_stats()
        
        return {
            'global': {
                'total_pnl': self.stats.total_pnl,
                'daily_pnl': self.stats.daily_pnl,
                'monthly_pnl': self.stats.monthly_pnl,
                'total_trades': self.stats.total_trades,
                'win_rate': self.stats.global_win_rate,
                'active_bots': self.stats.active_bots,
                'open_positions': self.stats.total_open_positions,
                'status': self.stats.status,
                'last_update': self.stats.last_update
            },
            'bots': {
                bot_type: {
                    'name': bot.stats.name,
                    'enabled': bot.stats.enabled,
                    'total_pnl': bot.stats.total_pnl,
                    'daily_pnl': bot.stats.daily_pnl,
                    'trades': bot.stats.total_trades,
                    'wins': bot.stats.wins,
                    'losses': bot.stats.losses,
                    'win_rate': bot.stats.win_rate,
                    'open_positions': bot.stats.open_positions,
                    'max_positions': bot.stats.max_positions,
                    'status': bot.stats.status,
                    'portfolio': [c['symbol'] for c in bot.portfolio]
                }
                for bot_type, bot in self.bots.items()
            }
        }
    
    def reset_daily_stats(self):
        """Reseta estatísticas diárias de todos os bots"""
        for bot in self.bots.values():
            bot.stats.daily_pnl = 0.0
        self.stats.daily_pnl = 0.0
        self.logger.info("📊 Estatísticas diárias resetadas")
    
    def add_crypto_to_bot(self, bot_type: str, symbol: str, name: str, weight: int = 10):
        """Adiciona uma crypto ao portfolio de um bot"""
        if bot_type not in self.bots:
            self.logger.error(f"Bot {bot_type} não encontrado")
            return False
        
        bot = self.bots[bot_type]
        
        # Verifica se já existe
        existing = [c for c in bot.portfolio if c['symbol'] == symbol]
        if existing:
            self.logger.warning(f"{symbol} já existe no {bot.name}")
            return False
        
        # Adiciona
        bot.portfolio.append({
            'symbol': symbol,
            'name': name,
            'weight': weight
        })
        
        self.logger.info(f"[OK] {symbol} adicionado ao {bot.name}")
        return True
    
    def remove_crypto_from_bot(self, bot_type: str, symbol: str):
        """Remove uma crypto do portfolio de um bot"""
        if bot_type not in self.bots:
            self.logger.error(f"Bot {bot_type} não encontrado")
            return False
        
        bot = self.bots[bot_type]
        bot.portfolio = [c for c in bot.portfolio if c['symbol'] != symbol]
        
        self.logger.info(f"🗑️ {symbol} removido do {bot.name}")
        return True


# Singleton para acesso global
_coordinator_instance: Optional[BotCoordinator] = None

def get_coordinator() -> BotCoordinator:
    """Retorna instância global do coordenador"""
    global _coordinator_instance
    if _coordinator_instance is None:
        data_dir = os.getenv('DATA_DIR', 'data')
        _coordinator_instance = BotCoordinator(data_dir=data_dir)
    return _coordinator_instance


if __name__ == "__main__":
    # Teste básico
    coordinator = BotCoordinator()
    
    print("\n" + "="*60)
    print("🎖️  COORDENADOR MULTI-BOT - R7 TRADING BOT API")
    print("="*60)
    
    print(f"\n📊 Bots ativos: {len(coordinator.bots)}")
    
    for bot_type, bot in coordinator.bots.items():
        print(f"\n{bot.name}")
        print(f"   Cryptos: {', '.join(bot.get_symbols())}")
        print(f"   Stop: {bot.risk_config.get('stop_loss')}% | Take: {bot.risk_config.get('take_profit')}%")
    
    print("\n" + "="*60)
    print("✅ Coordenador inicializado com sucesso!")
    print("="*60)