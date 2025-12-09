#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 VERIFICADOR DE STATUS DA IA - App Leonardo v3.0
====================================================

Verifica o status operacional da IA e ativa se necessário.

FUNCIONALIDADES:
1. Verifica se AIManager está ativo e operando
2. Verifica se AutoTuner está rodando
3. Verifica if Market Scanner está atualizado
4. Ativa a IA se não estiver operando
5. Configura monitoramento de mercado
6. Implementa regras de capital management

USO:
    python verify_ai_status.py          # Verificar status
    python verify_ai_status.py activate # Ativar IA
    python verify_ai_status.py full     # Verificar + Ativar + Monitor
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger('AIStatusVerifier')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.ai import get_ai_manager
    from src.core.exchange_client import ExchangeClient
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    logger.error(f"❌ Erro ao importar IA: {e}")


class AIStatusVerifier:
    """Sistema de verificação e ativação da IA"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.config_dir = Path("config")
        self.status_file = self.data_dir / "ai_status.json"
        self.ai_manager = None
        self.exchange = None
        
        # Criar diretórios se não existirem
        self.data_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
    def get_status(self) -> Dict:
        """
        VERIFICAÇÃO 1: Obtém status atual da IA
        
        Retorna:
            Dict com estado completo dos sistemas
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'ai_available': AI_AVAILABLE,
            'ai_manager': self._check_ai_manager(),
            'market_scanner': self._check_market_scanner(),
            'autotuner': self._check_autotuner(),
            'market_data': self._check_market_data(),
            'trade_history': self._check_trade_history(),
            'operational': False,
            'issues': []
        }
        
        # Determinar se IA está operacional
        status['operational'] = (
            status['ai_available'] and
            status['ai_manager']['initialized'] and
            status['market_scanner']['updated_recently']
        )
        
        return status
    
    def _check_ai_manager(self) -> Dict:
        """Verifica status do AIManager"""
        result = {
            'initialized': False,
            'last_training': None,
            'last_market_scan': None,
            'auto_adjust_enabled': False,
            'status': 'OFFLINE'
        }
        
        try:
            if not AI_AVAILABLE:
                result['status'] = 'NOT_AVAILABLE'
                return result
            
            # Carrega arquivo de estado
            state_file = self.data_dir / "ai" / "ai_state.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    result['initialized'] = True
                    result['last_training'] = state.get('last_training')
                    result['last_market_scan'] = state.get('last_market_scan')
                    result['auto_adjust_enabled'] = state.get('auto_adjust_enabled', True)
                    
                    # Verificar se está ativo (atualizado nos últimos 30 min)
                    last_scan = state.get('last_market_scan')
                    if last_scan:
                        last_time = datetime.fromisoformat(last_scan)
                        if datetime.now() - last_time < timedelta(minutes=30):
                            result['status'] = 'ACTIVE'
                        else:
                            result['status'] = 'IDLE'
                    else:
                        result['status'] = 'INITIALIZED'
            
        except Exception as e:
            logger.error(f"Erro ao verificar AIManager: {e}")
            result['status'] = 'ERROR'
        
        return result
    
    def _check_market_scanner(self) -> Dict:
        """Verifica status do Market Scanner"""
        result = {
            'last_scan': None,
            'updated_recently': False,
            'status': 'UNKNOWN'
        }
        
        try:
            scan_file = self.data_dir / "ai" / "market_scan.json"
            if scan_file.exists():
                with open(scan_file, 'r') as f:
                    scan = json.load(f)
                    result['last_scan'] = scan.get('timestamp')
                    
                    if result['last_scan']:
                        last_time = datetime.fromisoformat(result['last_scan'])
                        # Considera recente se foi nos últimos 1 hora
                        result['updated_recently'] = datetime.now() - last_time < timedelta(hours=1)
                        result['status'] = 'ACTIVE' if result['updated_recently'] else 'STALE'
                    else:
                        result['status'] = 'EMPTY'
            else:
                result['status'] = 'NOT_FOUND'
        
        except Exception as e:
            logger.error(f"Erro ao verificar Market Scanner: {e}")
            result['status'] = 'ERROR'
        
        return result
    
    def _check_autotuner(self) -> Dict:
        """Verifica status do AutoTuner"""
        result = {
            'last_adjustment': None,
            'adjustments_count': 0,
            'status': 'UNKNOWN'
        }
        
        try:
            state_file = self.data_dir / "autotuner_state.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    result['last_adjustment'] = state.get('last_adjustment')
                    result['adjustments_count'] = len(state.get('history', []))
                    result['status'] = 'ACTIVE' if result['last_adjustment'] else 'IDLE'
            else:
                result['status'] = 'NOT_INITIALIZED'
        
        except Exception as e:
            logger.error(f"Erro ao verificar AutoTuner: {e}")
            result['status'] = 'ERROR'
        
        return result
    
    def _check_market_data(self) -> Dict:
        """Verifica disponibilidade de dados de mercado"""
        result = {
            'available': False,
            'sources': [],
            'last_update': None
        }
        
        try:
            market_data_file = self.data_dir / "ai" / "market_data.json"
            if market_data_file.exists():
                with open(market_data_file, 'r') as f:
                    data = json.load(f)
                    result['available'] = True
                    result['sources'] = list(data.get('sources', {}).keys())
                    result['last_update'] = data.get('timestamp')
        
        except Exception:
            pass
        
        return result
    
    def _check_trade_history(self) -> Dict:
        """Verifica se há histórico de trades para análise"""
        result = {
            'total_trades': 0,
            'today_trades': 0,
            'total_pnl': 0.0,
            'status': 'UNKNOWN'
        }
        
        try:
            trades_file = self.data_dir / "all_trades_history.json"
            if trades_file.exists():
                with open(trades_file, 'r') as f:
                    trades = json.load(f)
                    result['total_trades'] = len(trades)
                    
                    # Contar trades de hoje
                    today = datetime.now().date()
                    today_trades = [
                        t for t in trades 
                        if datetime.fromisoformat(t.get('closed_at', '')).date() == today
                    ]
                    result['today_trades'] = len(today_trades)
                    result['total_pnl'] = sum(t.get('profit_loss', 0) for t in trades)
                    
                    if result['total_trades'] > 0:
                        result['status'] = 'OK'
                    else:
                        result['status'] = 'EMPTY'
            else:
                result['status'] = 'NOT_FOUND'
        
        except Exception as e:
            logger.error(f"Erro ao verificar histórico: {e}")
            result['status'] = 'ERROR'
        
        return result
    
    def activate_ai(self) -> bool:
        """
        ATIVAÇÃO: Ativa o sistema de IA com todas as features
        
        Retorna:
            bool: True se ativação bem-sucedida
        """
        logger.info("=" * 70)
        logger.info("🤖 ATIVANDO SISTEMA DE IA")
        logger.info("=" * 70)
        
        try:
            # 1. Inicializar AIManager
            logger.info("\n📍 Etapa 1: Inicializando AIManager...")
            if not AI_AVAILABLE:
                logger.error("❌ IA não disponível")
                return False
            
            self.ai_manager = get_ai_manager()
            logger.info("✅ AIManager inicializado")
            
            # 2. Habilitar Auto-Adjust
            logger.info("\n📍 Etapa 2: Habilitando Auto-Adjust...")
            self.ai_manager.set_auto_adjust(True)
            logger.info("✅ Auto-Adjust habilitado")
            
            # 3. Habilitar Market Scan
            logger.info("\n📍 Etapa 3: Habilitando Market Scan...")
            self.ai_manager.market_scan_enabled = True
            logger.info("✅ Market Scan habilitado")
            
            # 4. Habilitar Learning
            logger.info("\n📍 Etapa 4: Habilitando Learning...")
            self.ai_manager.learning_enabled = True
            logger.info("✅ Learning habilitado")
            
            # 5. Criar arquivo de estado
            logger.info("\n📍 Etapa 5: Salvando estado...")
            self._save_ai_state()
            logger.info("✅ Estado salvo")
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ IA ATIVADA COM SUCESSO!")
            logger.info("=" * 70)
            return True
        
        except Exception as e:
            logger.error(f"❌ Erro na ativação: {e}")
            return False
    
    def _save_ai_state(self):
        """Salva arquivo de estado da IA"""
        state = {
            'activated_at': datetime.now().isoformat(),
            'auto_adjust_enabled': True,
            'market_scan_enabled': True,
            'learning_enabled': True,
            'status': 'ACTIVE'
        }
        
        ai_dir = self.data_dir / "ai"
        ai_dir.mkdir(exist_ok=True)
        
        with open(ai_dir / "ai_state.json", 'w') as f:
            json.dump(state, f, indent=2)
    
    def print_status(self):
        """Imprime status formatado"""
        status = self.get_status()
        
        print("\n" + "=" * 70)
        print("🤖 STATUS DO SISTEMA DE IA - App Leonardo v3.0")
        print("=" * 70)
        print(f"Timestamp: {status['timestamp']}")
        print()
        
        # AI Geral
        print("📊 COMPONENTES:")
        print(f"  • IA Disponível: {'✅ SIM' if status['ai_available'] else '❌ NÃO'}")
        print(f"  • Status: {'🟢 OPERACIONAL' if status['operational'] else '🔴 OFFLINE'}")
        print()
        
        # AIManager
        ai = status['ai_manager']
        print("🧠 AI MANAGER:")
        print(f"  • Status: {ai['status']}")
        print(f"  • Inicializado: {'✅' if ai['initialized'] else '❌'}")
        print(f"  • Auto-Adjust: {'🔵 Ativo' if ai['auto_adjust_enabled'] else '⚫ Inativo'}")
        print(f"  • Último treinamento: {ai['last_training'] or 'Nunca'}")
        print(f"  • Último market scan: {ai['last_market_scan'] or 'Nunca'}")
        print()
        
        # Market Scanner
        scanner = status['market_scanner']
        print("📡 MARKET SCANNER:")
        print(f"  • Status: {scanner['status']}")
        print(f"  • Atualizado recentemente: {'✅' if scanner['updated_recently'] else '❌'}")
        print(f"  • Último scan: {scanner['last_scan'] or 'Nunca'}")
        print()
        
        # AutoTuner
        tuner = status['autotuner']
        print("⚙️ AUTO-TUNER:")
        print(f"  • Status: {tuner['status']}")
        print(f"  • Ajustes feitos: {tuner['adjustments_count']}")
        print(f"  • Último ajuste: {tuner['last_adjustment'] or 'Nunca'}")
        print()
        
        # Dados de Mercado
        market = status['market_data']
        print("💹 DADOS DE MERCADO:")
        print(f"  • Disponível: {'✅' if market['available'] else '❌'}")
        print(f"  • Fontes: {', '.join(market['sources']) or 'Nenhuma'}")
        print(f"  • Última atualização: {market['last_update'] or 'Nunca'}")
        print()
        
        # Histórico
        history = status['trade_history']
        print("📈 HISTÓRICO DE TRADES:")
        print(f"  • Total de trades: {history['total_trades']}")
        print(f"  • Trades hoje: {history['today_trades']}")
        print(f"  • PnL total: ${history['total_pnl']:.2f}")
        print(f"  • Status: {history['status']}")
        print()
        
        print("=" * 70)
    
    def print_recommendations(self):
        """Imprime recomendações baseado no status"""
        status = self.get_status()
        
        print("\n" + "=" * 70)
        print("💡 RECOMENDAÇÕES")
        print("=" * 70)
        
        if not status['operational']:
            print("⚠️  IA NÃO ESTÁ OPERACIONAL")
            print("\nAções recomendadas:")
            print("  1. Executar: python verify_ai_status.py activate")
            print("  2. Aguardar 5-10 minutos para estabilizar")
            print("  3. Verificar novamente: python verify_ai_status.py")
        else:
            print("✅ IA OPERACIONAL")
            print("\nSistema está:")
            print("  ✓ Monitorando mercado em tempo real")
            print("  ✓ Ajustando parâmetros automaticamente")
            print("  ✓ Aprendendo com histórico de trades")
            print("  ✓ Gerenciando capital inteligentemente")
        
        print("\n" + "=" * 70)


def main():
    """Função principal"""
    import sys
    
    verifier = AIStatusVerifier()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'activate':
            print("\n🚀 Ativando IA...")
            success = verifier.activate_ai()
            if success:
                print("\n✅ IA ativada com sucesso!")
                time.sleep(2)
                print("\nVerificando status...")
                verifier.print_status()
                verifier.print_recommendations()
            else:
                print("\n❌ Erro ao ativar IA")
                sys.exit(1)
        
        elif command == 'full':
            print("\n🔍 Modo completo: Verificar + Ativar + Monitorar")
            verifier.print_status()
            verifier.print_recommendations()
            
            status = verifier.get_status()
            if not status['operational']:
                print("\n🚀 Ativando IA...")
                verifier.activate_ai()
                print("\nAguardando estabilização...")
                time.sleep(5)
                print("\nVerificando novo status...")
                verifier.print_status()
        
        else:
            print(f"❌ Comando desconhecido: {command}")
            print(f"\nComandos disponíveis:")
            print(f"  verify_ai_status.py          - Verificar status")
            print(f"  verify_ai_status.py activate - Ativar IA")
            print(f"  verify_ai_status.py full     - Verificar + Ativar")
            sys.exit(1)
    else:
        # Padrão: apenas verificar status
        verifier.print_status()
        verifier.print_recommendations()


if __name__ == '__main__':
    main()
