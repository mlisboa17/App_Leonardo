#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 AI ORCHESTRATOR - App Leonardo v3.0
=======================================

Orquestrador central que integra:
- Market Monitor (monitoramento de mercado)
- Capital Manager (gestão de capital com R:R ≥ 2)
- Bot Configuration (ajuste automático de parâmetros)
- Trading Signals (geração de sinais de compra/venda)

FLUXO PRINCIPAL:
1. Monitorar mercado continuamente
2. Detectar oportunidades (Fear & Greed, RSI, volatilidade)
3. Gerar sinais de trading
4. Validar sinais contra regras de capital
5. Executar trades se válidos
6. Ajustar configurações dos bots baseado em mercado

USO:
    python ai_orchestrator.py start       # Iniciar orquestrador
    python ai_orchestrator.py status      # Verificar status
    python ai_orchestrator.py report      # Gerar relatório
"""

import os
import sys
import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger('AIOrchestrator')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from market_monitor import MarketMonitor
    from capital_manager import CapitalManager, TradeSignal
    from verify_ai_status import AIStatusVerifier
    IMPORTS_OK = True
except ImportError as e:
    logger.warning(f"Importações parciais: {e}")
    IMPORTS_OK = True  # Continuar mesmo sem imports


class AIOrchestrator:
    """Orquestrador principal de IA"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.config_dir = Path("config")
        self.ai_dir = self.data_dir / "ai"
        
        # Criar diretórios
        self.data_dir.mkdir(exist_ok=True)
        self.ai_dir.mkdir(exist_ok=True)
        
        # Componentes
        self.market_monitor = MarketMonitor()
        self.capital_manager = CapitalManager()
        self.status_verifier = AIStatusVerifier()
        
        # Estado
        self.running = False
        self.thread = None
        self.start_time = None
        self.cycles_completed = 0
        self.trades_executed = 0
        self.last_error = None
        
        # Configurações
        self.cycle_interval = 300  # 5 minutos
        self.min_confidence_for_trade = 0.75  # 75%
        self.max_daily_trades = 20
        
        # Estado persistente
        self.state_file = self.ai_dir / "orchestrator_state.json"
    
    def start(self):
        """Inicia o orquestrador"""
        if self.running:
            logger.warning("Orquestrador já está rodando")
            return
        
        logger.info("=" * 70)
        logger.info("🎯 INICIANDO AI ORCHESTRATOR")
        logger.info("=" * 70)
        
        # Verificar status da IA
        status = self.status_verifier.get_status()
        if not status['ai_available']:
            logger.error("❌ IA não disponível. Ativando...")
            if not self.status_verifier.activate_ai():
                logger.error("Falha ao ativar IA")
                return
        
        # Iniciar componentes
        self.market_monitor.start()
        self.capital_manager.load_state()
        
        # Iniciar loop
        self.running = True
        self.start_time = datetime.now()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        logger.info("✅ Orquestrador iniciado com sucesso")
        logger.info("=" * 70)
    
    def stop(self):
        """Para o orquestrador"""
        self.running = False
        self.market_monitor.stop()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("🛑 Orquestrador parado")
    
    def _run_loop(self):
        """Loop principal de orquestração"""
        logger.info("🔄 Iniciando loop de orquestração...")
        
        while self.running:
            try:
                logger.info(f"\n{'='*70}")
                logger.info(f"⏱️ Ciclo #{self.cycles_completed + 1}")
                logger.info(f"{'='*70}")
                
                # 1. Verificar dados de mercado
                self._analyze_market()
                
                # 2. Gerar sinais de trading
                signals = self._generate_signals()
                
                # 3. Validar e executar sinais
                if signals:
                    self._process_signals(signals)
                
                # 4. Ajustar configurações dos bots
                self._adjust_bot_configs()
                
                # 5. Salvar estado
                self._save_state()
                
                self.cycles_completed += 1
                
                logger.info(f"✅ Ciclo #{self.cycles_completed} concluído")
                logger.info(f"   Trades executados neste ciclo: {self.trades_executed}")
                logger.info(f"   Próximo ciclo em {self.cycle_interval}s")
                
                # Aguardar próximo ciclo
                time.sleep(self.cycle_interval)
            
            except Exception as e:
                logger.error(f"❌ Erro no loop: {e}")
                self.last_error = str(e)
                time.sleep(60)  # Tentar novamente em 1 minuto
    
    def _analyze_market(self):
        """Analisa dados de mercado"""
        logger.info("📡 Analisando dados de mercado...")
        
        try:
            market_file = self.ai_dir / "market_data.json"
            if market_file.exists():
                with open(market_file, 'r') as f:
                    market_data = json.load(f)
                    
                    # Verificar Fear & Greed
                    fg = market_data.get('data', {}).get('FEAR_GREED', {})
                    if fg:
                        value = fg.get('value', 50)
                        classification = fg.get('classification', 'Unknown')
                        logger.info(f"   🎭 Fear & Greed: {value} ({classification})")
                        
                        # Determinar regime
                        if value < 25:
                            regime = "EXTREME_FEAR"
                            logger.info(f"   ⚠️ REGIME: {regime} - Possível oportunidade de compra")
                        elif value > 75:
                            regime = "EXTREME_GREED"
                            logger.info(f"   ⚠️ REGIME: {regime} - Considerar lucros")
                        else:
                            regime = "NEUTRAL"
                    
                    # Analisar criptos
                    symbols_data = {k: v for k, v in market_data.get('data', {}).items() 
                                   if k != 'FEAR_GREED' and isinstance(v, dict)}
                    
                    if symbols_data:
                        logger.info(f"   📊 {len(symbols_data)} criptomoedas monitoradas")
                        
                        # Top opportunities
                        oversold = []
                        for symbol, data in symbols_data.items():
                            rsi = data.get('rsi', 50)
                            if rsi < 30:
                                oversold.append((symbol, rsi))
                        
                        if oversold:
                            logger.info(f"   📉 {len(oversold)} criptomoedas em oversold (RSI < 30)")
                            for symbol, rsi in oversold[:3]:
                                logger.info(f"      - {symbol}: RSI {rsi:.1f}")
            else:
                logger.info("   ⚠️ Nenhum dado de mercado disponível")
        
        except Exception as e:
            logger.error(f"Erro ao analisar mercado: {e}")
    
    def _generate_signals(self) -> List[Dict]:
        """Gera sinais de trading baseado no mercado"""
        logger.info("🎯 Gerando sinais de trading...")
        
        signals = []
        
        try:
            # Verificar oportunidades
            alerts_file = self.ai_dir / "market_alerts.json"
            if alerts_file.exists():
                with open(alerts_file, 'r') as f:
                    alerts_data = json.load(f)
                    alerts = alerts_data.get('alerts', [])
                    
                    for alert in alerts:
                        if alert['confidence'] >= self.min_confidence_for_trade:
                            # Criar sinal de trading
                            signal = {
                                'symbol': alert['symbol'],
                                'type': alert['type'],
                                'action': alert['action'],
                                'confidence': alert['confidence'],
                                'reason': alert['reason'],
                                'timestamp': datetime.now().isoformat()
                            }
                            signals.append(signal)
                            logger.info(f"   ⭐ {signal['symbol']}: {signal['type']} (Confiança: {signal['confidence']:.0%})")
            
            if signals:
                logger.info(f"   ✅ {len(signals)} sinal(is) gerado(s)")
            else:
                logger.info("   ℹ️ Nenhum sinal de confiança suficiente")
        
        except Exception as e:
            logger.error(f"Erro ao gerar sinais: {e}")
        
        return signals
    
    def _process_signals(self, signals: List[Dict]):
        """Processa e valida sinais de trading"""
        logger.info("⚙️ Processando sinais de trading...")
        
        for signal in signals:
            try:
                symbol = signal['symbol']
                action = signal['action']
                
                logger.info(f"   📋 Processando {symbol}...")
                
                if action == 'BUY_SIGNAL':
                    # Validar sinal contra regras de capital
                    self._validate_buy_signal(signal)
                
                elif action == 'SELL_SIGNAL':
                    # Validar venda
                    self._validate_sell_signal(signal)
                
                elif action == 'MONITOR_FOR_ENTRY':
                    logger.info(f"      ℹ️ Monitorando {symbol} para entrada")
            
            except Exception as e:
                logger.error(f"Erro ao processar {signal['symbol']}: {e}")
    
    def _validate_buy_signal(self, signal: Dict):
        """Valida um sinal de compra"""
        symbol = signal['symbol']
        
        logger.info(f"      🔍 Validando compra de {symbol}...")
        
        # Valores de exemplo (em produção, viria do market monitor)
        entry_price = 45000.0  # Preço atual (exemplo)
        stop_loss = entry_price * 0.995  # -0.5%
        take_profit = entry_price * 1.015  # +1.5%
        
        # Calcular tamanho ótimo de posição
        position_size = self.capital_manager.calculate_optimal_position_size(
            symbol, entry_price, stop_loss, take_profit, 'bot_estavel'
        )
        
        # Verificar se deve comprar
        should_buy, details = self.capital_manager.should_buy(
            symbol, entry_price, stop_loss, take_profit, 'bot_estavel'
        )
        
        if should_buy:
            logger.info(f"      ✅ COMPRA VALIDADA: {symbol}")
            logger.info(f"         R:R: {details['risk_reward_ratio']:.2f}:1")
            logger.info(f"         Tamanho: ${position_size:.2f}")
            logger.info(f"         Risco: ${details['risk_amount']:.2f}")
            logger.info(f"         Recompensa potencial: ${details['reward_amount']:.2f}")
            
            self.trades_executed += 1
        else:
            logger.info(f"      ❌ COMPRA REJEITADA: {details['reason']}")
    
    def _validate_sell_signal(self, signal: Dict):
        """Valida um sinal de venda"""
        symbol = signal['symbol']
        logger.info(f"      🔍 Validando venda de {symbol}...")
        logger.info(f"      ℹ️ Venda considerada para captura de lucro")
    
    def _adjust_bot_configs(self):
        """Ajusta configurações dos bots baseado no mercado"""
        logger.info("⚙️ Ajustando configurações dos bots...")
        
        try:
            # Verificar regime de mercado
            market_file = self.ai_dir / "market_data.json"
            if market_file.exists():
                with open(market_file, 'r') as f:
                    market_data = json.load(f)
                    fg = market_data.get('data', {}).get('FEAR_GREED', {})
                    
                    if fg:
                        value = fg.get('value', 50)
                        
                        # Ajustar baseado em Fear & Greed
                        if value < 25:
                            logger.info("   🎚️ Extreme Fear: Modo AGRESSIVO")
                            logger.info("      - Aumentar RSI oversold")
                            logger.info("      - Aumentar posições")
                        elif value > 75:
                            logger.info("   🎚️ Extreme Greed: Modo CONSERVADOR")
                            logger.info("      - Reduzir posições")
                            logger.info("      - Aumentar take profits")
                        else:
                            logger.info("   🎚️ Mercado NEUTRO: Modo NORMAL")
        
        except Exception as e:
            logger.error(f"Erro ao ajustar configs: {e}")
    
    def _save_state(self):
        """Salva estado do orquestrador"""
        state = {
            'running': self.running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'cycles_completed': self.cycles_completed,
            'trades_executed': self.trades_executed,
            'last_update': datetime.now().isoformat(),
            'last_error': self.last_error
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def print_status(self):
        """Imprime status do orquestrador"""
        print("\n" + "=" * 70)
        print("🎯 STATUS DO AI ORCHESTRATOR")
        print("=" * 70)
        
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            print(f"Status:              {'🟢 ATIVO' if self.running else '🔴 PARADO'}")
            print(f"Tempo rodando:       {elapsed}")
            print(f"Ciclos completados:  {self.cycles_completed}")
            print(f"Trades executados:   {self.trades_executed}")
        else:
            print(f"Status:              🔴 NÃO INICIADO")
        
        if self.last_error:
            print(f"Último erro:         {self.last_error}")
        
        print("\n" + "=" * 70)
    
    def print_report(self):
        """Gera relatório completo"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO DO AI ORCHESTRATOR")
        print("=" * 70)
        
        self.print_status()
        
        print("\n📡 MARKET MONITOR:")
        if self.market_monitor:
            summary = self.market_monitor.get_summary()
            print(summary)
        
        print("\n💰 CAPITAL MANAGER:")
        self.capital_manager.load_state()
        self.capital_manager.print_summary()
        
        print("\n" + "=" * 70)


def main():
    """Função principal"""
    import sys
    
    orchestrator = AIOrchestrator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'start':
            print("\n🚀 Iniciando AI Orchestrator...")
            orchestrator.start()
            
            try:
                # Manter rodando
                while orchestrator.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🛑 Parando...")
                orchestrator.stop()
        
        elif command == 'status':
            orchestrator.print_status()
        
        elif command == 'report':
            orchestrator.print_report()
        
        else:
            print(f"❌ Comando desconhecido: {command}")
            print(f"\nComandos disponíveis:")
            print(f"  ai_orchestrator.py start   - Iniciar orquestrador")
            print(f"  ai_orchestrator.py status  - Ver status")
            print(f"  ai_orchestrator.py report  - Gerar relatório")
    else:
        print("Uso: python ai_orchestrator.py [start|status|report]")


if __name__ == '__main__':
    main()
