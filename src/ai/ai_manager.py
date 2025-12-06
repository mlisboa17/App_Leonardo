# -*- coding: utf-8 -*-
"""
App Leonardo v3.0 - AI Manager
==============================

Gerenciador central que integra todos os módulos de IA:
- AdaptiveEngine (ML de trades)
- MarketScanner (Notícias e sentimento)
- AutoConfig (Ajuste automático)

Este módulo coordena a IA e expõe uma interface simples
para o bot principal usar.
"""

import os
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from .adaptive_engine import AdaptiveEngine
from .market_scanner import MarketScanner
from .auto_config import AutoConfig
from .ai_persistence import AIPersistence, get_ai_persistence

logger = logging.getLogger('AIManager')


class AIManager:
    """
    Gerenciador central da Inteligência Artificial.
    
    Coordena:
    - Aprendizado com histórico de trades
    - Scan de mercado e notícias
    - Ajuste automático de configurações
    - Recomendações em tempo real
    """
    
    def __init__(self, config_path: str = "config/bots_config.yaml", 
                 data_dir: str = "data"):
        self.data_dir = data_dir
        self.ai_data_dir = os.path.join(data_dir, "ai")
        os.makedirs(self.ai_data_dir, exist_ok=True)
        
        # Sistema de persistência
        self.persistence = get_ai_persistence()
        
        # Módulos de AI
        self.adaptive_engine = AdaptiveEngine(data_dir)
        self.market_scanner = MarketScanner(data_dir)
        self.auto_config = AutoConfig(config_path, data_dir)
        
        # Estado
        self.last_training = None
        self.last_market_scan = None
        self.last_auto_adjust = None
        self.last_backup = None
        
        # Intervalos (em minutos)
        self.training_interval = 60      # Treinar modelo a cada hora
        self.market_scan_interval = 15   # Scan de mercado a cada 15 min
        self.auto_adjust_interval = 30   # Ajuste automático a cada 30 min
        self.backup_interval = 360       # Backup a cada 6 horas
        
        # Flags
        self.auto_adjust_enabled = True
        self.market_scan_enabled = True
        self.learning_enabled = True
        
        # Cache de recomendações
        self.current_recommendations = {
            'market': {},
            'trading': {},
            'adjustments': [],
            'last_update': None
        }
        
        # Thread de background
        self._bg_thread = None
        self._running = False
        
        # Carregar estado
        self._load_state()
        
        logger.info("🤖 AI Manager inicializado")
    
    def _load_state(self):
        """Carrega estado salvo"""
        state_file = os.path.join(self.ai_data_dir, "ai_state.json")
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.last_training = state.get('last_training')
                    self.last_market_scan = state.get('last_market_scan')
                    self.last_auto_adjust = state.get('last_auto_adjust')
                    self.last_backup = state.get('last_backup')
                    self.auto_adjust_enabled = state.get('auto_adjust_enabled', True)
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar estado: {e}")
    
    def _save_state(self):
        """Salva estado atual"""
        state_file = os.path.join(self.ai_data_dir, "ai_state.json")
        try:
            with open(state_file, 'w') as f:
                json.dump({
                    'last_training': self.last_training,
                    'last_market_scan': self.last_market_scan,
                    'last_auto_adjust': self.last_auto_adjust,
                    'last_backup': self.last_backup,
                    'auto_adjust_enabled': self.auto_adjust_enabled
                }, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Erro ao salvar estado: {e}")
    
    def start_background_tasks(self):
        """Inicia tarefas de background da AI"""
        if self._running:
            return
        
        self._running = True
        self._bg_thread = threading.Thread(target=self._background_loop, daemon=True)
        self._bg_thread.start()
        logger.info("🔄 Background tasks da AI iniciadas")
    
    def stop_background_tasks(self):
        """Para tarefas de background"""
        self._running = False
        if self._bg_thread:
            self._bg_thread.join(timeout=5)
        logger.info("⏹️ Background tasks da AI paradas")
    
    def _background_loop(self):
        """Loop de background para tarefas periódicas"""
        import time
        
        while self._running:
            try:
                now = datetime.now()
                
                # Scan de mercado
                if self.market_scan_enabled:
                    if self._should_run('market_scan', self.market_scan_interval):
                        self._run_market_scan()
                
                # Ajuste automático
                if self.auto_adjust_enabled:
                    if self._should_run('auto_adjust', self.auto_adjust_interval):
                        self._run_auto_adjust()
                
                # Treino de modelo (menos frequente)
                if self.learning_enabled:
                    if self._should_run('training', self.training_interval):
                        self._run_training()
                
                # Backup automático (a cada 6 horas)
                if self._should_run('backup', self.backup_interval):
                    self._run_backup()
                
                # Esperar 60 segundos antes de próximo check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Erro no background loop: {e}")
                time.sleep(30)
    
    def _should_run(self, task: str, interval_minutes: int) -> bool:
        """Verifica se uma tarefa deve rodar"""
        last_run = None
        if task == 'market_scan':
            last_run = self.last_market_scan
        elif task == 'auto_adjust':
            last_run = self.last_auto_adjust
        elif task == 'training':
            last_run = self.last_training
        elif task == 'backup':
            last_run = self.last_backup
        
        if last_run is None:
            return True
        
        try:
            if isinstance(last_run, str):
                last_run = datetime.fromisoformat(last_run)
            
            elapsed = (datetime.now() - last_run).total_seconds() / 60
            return elapsed >= interval_minutes
        except:
            return True
    
    def _run_market_scan(self):
        """Executa scan de mercado"""
        try:
            logger.info("📡 Executando scan de mercado...")
            summary = self.market_scanner.get_market_summary()
            
            self.current_recommendations['market'] = {
                'fear_greed': summary.get('fear_greed', {}),
                'sentiment': summary.get('overall_sentiment', 'NEUTRAL'),
                'recommendations': summary.get('recommendations', []),
                'should_trade': self.market_scanner.should_trade_now()
            }
            
            self.last_market_scan = datetime.now().isoformat()
            self._save_state()
            
            logger.info(f"✅ Market scan: {summary.get('overall_sentiment', 'NEUTRAL')}")
        except Exception as e:
            logger.error(f"❌ Erro no market scan: {e}")
    
    def _run_auto_adjust(self):
        """Executa ajuste automático baseado no mercado"""
        try:
            market_data = self.current_recommendations.get('market', {})
            
            if not market_data:
                return
            
            # Determinar regime de mercado
            sentiment = market_data.get('sentiment', 'NEUTRAL')
            fear_greed = market_data.get('fear_greed', {}).get('value', 50)
            
            regime_map = {
                'BULLISH': 'bullish',
                'BEARISH': 'bearish',
                'NEUTRAL': 'sideways'
            }
            regime = regime_map.get(sentiment, 'sideways')
            
            # Verificar se é volátil (F&G extremo)
            if fear_greed <= 25 or fear_greed >= 75:
                regime = 'volatile'
            
            # Aplicar ajustes
            changes = self.auto_config.apply_market_adjustment(regime, fear_greed)
            
            self.current_recommendations['adjustments'] = changes
            self.last_auto_adjust = datetime.now().isoformat()
            self._save_state()
            
            logger.info(f"🔧 Auto-adjust aplicado: {changes.get('mode', 'normal')}")
        except Exception as e:
            logger.error(f"❌ Erro no auto-adjust: {e}")
    
    def _run_training(self):
        """Executa treinamento do modelo"""
        try:
            # Carregar histórico de trades
            trades = self._load_all_trades()
            
            if len(trades) < 20:
                logger.info("⚠️ Poucos trades para treinar")
                return
            
            # Treinar modelo global
            result = self.adaptive_engine.train_from_history(trades, 'global')
            
            # Treinar por bot
            trades_by_bot = {}
            for trade in trades:
                bot = trade.get('bot_type', trade.get('bot', 'unknown'))
                if bot not in trades_by_bot:
                    trades_by_bot[bot] = []
                trades_by_bot[bot].append(trade)
            
            for bot_name, bot_trades in trades_by_bot.items():
                if len(bot_trades) >= 10:
                    self.adaptive_engine.train_from_history(bot_trades, bot_name)
            
            self.last_training = datetime.now().isoformat()
            self._save_state()
            
            logger.info(f"🧠 Modelo treinado: {result.get('accuracy', 0)}% accuracy")
        except Exception as e:
            logger.error(f"❌ Erro no treinamento: {e}")
    
    def _run_backup(self):
        """Executa backup automático"""
        try:
            logger.info("💾 Executando backup automático...")
            backup_path = self.persistence.create_backup(reason="scheduled")
            
            self.last_backup = datetime.now().isoformat()
            self._save_state()
            
            if backup_path:
                logger.info(f"✅ Backup automático criado: {backup_path}")
            else:
                logger.warning("⚠️ Falha no backup automático")
        except Exception as e:
            logger.error(f"❌ Erro no backup: {e}")
    
    def _load_all_trades(self) -> List[Dict]:
        """Carrega todos os trades do histórico"""
        trades = []
        
        history_files = [
            "data/multibot_history.json",
            "data/history/bot_estavel_trades.json",
            "data/history/bot_medio_trades.json",
            "data/history/bot_volatil_trades.json",
            "data/history/bot_meme_trades.json",
        ]
        
        for file_path in history_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        file_trades = json.load(f)
                        if isinstance(file_trades, list):
                            trades.extend(file_trades)
                except:
                    pass
        
        return trades
    
    # ========== INTERFACE PÚBLICA ==========
    
    def should_buy(self, symbol: str, bot_name: str, trade_params: Dict) -> Dict:
        """
        Verifica se deve executar uma compra.
        Combina análise técnica com AI.
        
        Args:
            symbol: Símbolo (ex: BTCUSDT)
            bot_name: Nome do bot
            trade_params: Parâmetros do trade (RSI, MACD, etc)
            
        Returns:
            Dict com decisão e razões
        """
        result = {
            'should_buy': True,
            'confidence': 'medium',
            'reasons': [],
            'warnings': []
        }
        
        # 1. Verificar condições de mercado
        market = self.current_recommendations.get('market', {})
        should_trade = market.get('should_trade', {})
        
        if should_trade.get('recommendation') == 'WAIT':
            result['should_buy'] = False
            result['reasons'].append("⚠️ Mercado desfavorável - aguardar")
            return result
        
        if should_trade.get('recommendation') == 'CAUTION':
            result['warnings'].append("🟡 Operar com cautela")
        
        # 2. Verificar predição do modelo
        prediction = self.adaptive_engine.predict_trade_success(trade_params, bot_name)
        
        if prediction.get('probability', 50) < 40:
            result['should_buy'] = False
            result['reasons'].append(f"🤖 AI prevê baixa chance de sucesso ({prediction.get('probability')}%)")
            return result
        
        if prediction.get('probability', 50) >= 60:
            result['reasons'].append(f"✅ AI aprova ({prediction.get('probability')}% chance)")
            result['confidence'] = 'high'
        
        # 3. Adicionar insights
        for insight in prediction.get('insights', []):
            if '⚠️' in insight or '🚨' in insight:
                result['warnings'].append(insight)
            else:
                result['reasons'].append(insight)
        
        # 4. Verificar sentimento específico da crypto
        crypto_sentiment = self.market_scanner.get_crypto_sentiment(symbol)
        if crypto_sentiment.get('sentiment') == 'BEARISH':
            result['warnings'].append(f"📰 Sentimento negativo para {symbol}")
        elif crypto_sentiment.get('sentiment') == 'BULLISH':
            result['reasons'].append(f"📰 Sentimento positivo para {symbol}")
        
        return result
    
    def on_trade_completed(self, trade: Dict):
        """
        Chamado quando um trade é completado.
        Atualiza o modelo de aprendizado.
        
        Args:
            trade: Dict com informações do trade completado
        """
        try:
            # Salvar no histórico de AI
            ai_history_file = os.path.join(self.ai_data_dir, "completed_trades.json")
            
            trades = []
            if os.path.exists(ai_history_file):
                with open(ai_history_file, 'r') as f:
                    trades = json.load(f)
            
            trades.append({
                **trade,
                'ai_recorded_at': datetime.now().isoformat()
            })
            
            # Manter últimos 1000
            trades = trades[-1000:]
            
            with open(ai_history_file, 'w') as f:
                json.dump(trades, f, indent=2)
            
            logger.info(f"📝 Trade registrado para aprendizado")
        except Exception as e:
            logger.error(f"❌ Erro ao registrar trade: {e}")
    
    def get_dashboard_data(self) -> Dict:
        """
        Retorna dados para exibição no dashboard.
        
        Returns:
            Dict com todos os dados de AI para o dashboard
        """
        return {
            'market': {
                'fear_greed': self.current_recommendations.get('market', {}).get('fear_greed', {}),
                'sentiment': self.current_recommendations.get('market', {}).get('sentiment', 'NEUTRAL'),
                'should_trade': self.current_recommendations.get('market', {}).get('should_trade', {}),
                'recommendations': self.current_recommendations.get('market', {}).get('recommendations', [])
            },
            'learning': self.adaptive_engine.get_learning_summary(),
            'config': {
                'mode': self.auto_config.get_current_mode(),
                'recent_changes': self.auto_config.get_changes_summary(hours=24)
            },
            'insights': self.adaptive_engine.insights,
            'status': {
                'last_training': self.last_training,
                'last_market_scan': self.last_market_scan,
                'last_auto_adjust': self.last_auto_adjust,
                'auto_adjust_enabled': self.auto_adjust_enabled,
                'learning_enabled': self.learning_enabled
            }
        }
    
    def get_bot_insights(self, bot_name: str) -> Dict:
        """
        Retorna insights específicos para um bot.
        
        Args:
            bot_name: Nome do bot
            
        Returns:
            Dict com insights
        """
        bot_config = self.auto_config.get_bot_config(bot_name)
        recommendations = self.adaptive_engine.get_bot_recommendations(bot_name, bot_config)
        
        return {
            'current_config': bot_config,
            'recommendations': recommendations,
            'best_rsi_range': self.adaptive_engine.insights.get('best_rsi_range', {}).get(bot_name),
            'best_hours': self.adaptive_engine.insights.get('best_hours', {}).get(bot_name),
            'crypto_performance': self.adaptive_engine.insights.get('crypto_performance', {}).get(bot_name, {})
        }
    
    def set_auto_adjust(self, enabled: bool):
        """Habilita/desabilita ajuste automático"""
        self.auto_adjust_enabled = enabled
        self._save_state()
        logger.info(f"🔧 Auto-adjust: {'habilitado' if enabled else 'desabilitado'}")
    
    def set_risk_profile(self, profile: str, bots: List[str] = None) -> Dict:
        """
        Define perfil de risco manualmente.
        
        Args:
            profile: 'ultra_conservative', 'conservative', 'normal', 'aggressive', 'ultra_aggressive'
            bots: Lista de bots (None = todos)
            
        Returns:
            Dict com mudanças aplicadas
        """
        return self.auto_config.set_risk_profile(profile, bots)
    
    def force_market_scan(self) -> Dict:
        """Força um scan de mercado imediato"""
        self._run_market_scan()
        return self.current_recommendations.get('market', {})
    
    def force_training(self) -> Dict:
        """Força treinamento imediato do modelo"""
        self._run_training()
        return self.adaptive_engine.get_learning_summary()
    
    def reset_to_defaults(self, bot_name: str = None) -> bool:
        """Reseta configurações para valores originais"""
        return self.auto_config.reset_to_original(bot_name)
    
    def create_backup(self, reason: str = "manual") -> str:
        """
        Cria backup manual do aprendizado.
        
        Returns:
            Caminho do backup criado
        """
        return self.persistence.create_backup(reason)
    
    def list_backups(self) -> list:
        """Lista todos os backups disponíveis"""
        return self.persistence.list_backups()
    
    def restore_backup(self, backup_name: str) -> bool:
        """Restaura um backup específico"""
        success = self.persistence.restore_backup(backup_name)
        if success:
            # Recarregar módulos
            self.adaptive_engine = AdaptiveEngine(self.data_dir)
            self._load_state()
        return success
    
    def export_learning(self, export_path: str = None) -> str:
        """
        Exporta todo o aprendizado para um arquivo.
        Útil para transferir para outra máquina.
        
        Returns:
            Caminho do arquivo exportado
        """
        return self.persistence.export_learning(export_path)
    
    def import_learning(self, import_path: str) -> bool:
        """
        Importa aprendizado de um arquivo exportado.
        
        Returns:
            True se sucesso
        """
        success = self.persistence.import_learning(import_path)
        if success:
            # Recarregar módulos
            self.adaptive_engine = AdaptiveEngine(self.data_dir)
        return success
    
    def get_learning_stats(self) -> Dict:
        """Retorna estatísticas do aprendizado"""
        return self.persistence.get_learning_stats()
    
    def verify_integrity(self) -> Dict:
        """Verifica integridade dos dados da IA"""
        return self.persistence.verify_integrity()


# Singleton
_ai_manager: Optional[AIManager] = None

def get_ai_manager() -> AIManager:
    """Retorna instância singleton do AIManager"""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = AIManager()
    return _ai_manager


# Teste standalone
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = get_ai_manager()
    
    print("\n🤖 AI Manager Status:")
    status = manager.get_dashboard_data()
    print(f"  Last training: {status['status']['last_training']}")
    print(f"  Auto-adjust: {status['status']['auto_adjust_enabled']}")
    
    print("\n📡 Forçando scan de mercado...")
    market = manager.force_market_scan()
    print(f"  Sentiment: {market.get('sentiment', 'N/A')}")
    print(f"  Fear & Greed: {market.get('fear_greed', {}).get('value', 'N/A')}")
    
    print("\n🔮 Testando decisão de compra...")
    decision = manager.should_buy('BTCUSDT', 'bot_estavel', {
        'symbol': 'BTCUSDT',
        'buy_reason': 'RSI 28 | MACD↑',
        'entry_price': 96000
    })
    print(f"  Should buy: {decision['should_buy']}")
    print(f"  Confidence: {decision['confidence']}")
    for reason in decision['reasons']:
        print(f"    {reason}")
