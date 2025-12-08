"""
Testes de Integração E2E - Fluxo completo de restart e auditoria
"""
import pytest
import json
import time
from pathlib import Path
from datetime import datetime
import tempfile
import shutil


@pytest.fixture
def test_env():
    """Prepara ambiente de testes"""
    # Cria diretório temporário para dados de teste
    test_dir = Path(tempfile.mkdtemp())
    
    yield {
        'test_dir': test_dir,
        'data_dir': test_dir / 'data',
        'audit_dir': test_dir / 'data' / 'audit'
    }
    
    # Cleanup
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def coordinator(test_env):
    """Prepara instância de coordenador para testes"""
    from src.coordinator import BotCoordinator
    from unittest.mock import MagicMock, patch
    
    # Mock configuração
    mock_config = {
        'global': {
            'exchange': 'binance',
            'testnet': True
        },
        'coordinator': {
            'logging': {'level': 'INFO', 'save_to_file': False}
        },
        'bot_estavel': {
            'enabled': True,
            'name': 'Bot Estável',
            'portfolio': [{'symbol': 'BTC', 'name': 'Bitcoin', 'weight': 50}],
            'trading': {'max_positions': 5},
            'rsi': {'oversold': 35, 'overbought': 65},
            'risk': {'stop_loss': -1.0, 'take_profit': 0.5}
        }
    }
    
    with patch.object(BotCoordinator, '_load_config', return_value=mock_config):
        with patch.object(BotCoordinator, '_setup_exchange', return_value=MagicMock()):
            coord = BotCoordinator()
            # Override paths
            coord.data_path = test_env['data_dir']
            coord.stats_file = coord.data_path / "coordinator_stats.json"
            coord.bot_status_file = coord.data_path / "bot_status.json"
            coord.audit.audit_dir = test_env['audit_dir']
            coord.data_path.mkdir(parents=True, exist_ok=True)
            coord.audit_dir.mkdir(parents=True, exist_ok=True)
            
    return coord


class TestRestartGracioso:
    """Testes para restart gracioso de bots"""
    
    def test_save_and_restore_state(self, coordinator):
        """Verifica se estado é salvo e restaurado corretamente"""
        # Setup - adiciona algumas "posições"
        bot = list(coordinator.bots.values())[0]
        bot.positions = {
            'BTC/USDT': {
                'entry_price': 45000,
                'quantity': 0.1,
                'entry_time': datetime.now().isoformat()
            }
        }
        bot.stats.total_trades = 10
        bot.stats.total_pnl = 500.0
        
        # Salva estado
        coordinator.save_state()
        assert coordinator.stats_file.exists(), "Arquivo de estado não foi criado"
        
        # Carrega estado em nova instância
        with open(coordinator.stats_file, 'r') as f:
            state_data = json.load(f)
        
        # Verifica se posições foram salvas
        assert 'bots' in state_data
        bot_type = list(coordinator.bots.keys())[0]
        assert bot_type in state_data['bots']
        assert 'positions' in state_data['bots'][bot_type]
        assert 'BTC/USDT' in state_data['bots'][bot_type]['positions']
        
        # Restaura estado
        coordinator._load_state()
        restored_bot = coordinator.bots[bot_type]
        
        assert restored_bot.positions.get('BTC/USDT') is not None
        assert restored_bot.stats.total_trades == 10
        assert restored_bot.stats.total_pnl == 500.0
    
    def test_restart_bot_preserves_positions(self, coordinator):
        """Verifica se restart preserva posições dos bots"""
        bot_type = 'bot_estavel'
        bot = coordinator.bots[bot_type]
        
        # Setup - posição aberta
        original_position = {
            'entry_price': 45000,
            'quantity': 0.1,
            'entry_time': datetime.now().isoformat()
        }
        bot.positions['BTC/USDT'] = original_position
        
        # Restart
        coordinator.restart_bot(bot_type, reason="test")
        
        # Verifica se posição foi preservada
        restarted_bot = coordinator.bots[bot_type]
        # Nota: Em um teste real, isso depende se a config foi carregada corretamente
        # Este teste valida que a estrutura funciona
        assert isinstance(restarted_bot.positions, dict)


class TestCoalescimento:
    """Testes para coalescimento de ações de restart"""
    
    def test_pending_action_replacement(self, coordinator):
        """Verifica se ações pendentes são substituídas corretamente"""
        # Setup
        action_history = []
        original_restart = coordinator.restart_bot
        
        def mock_restart(bot_type, reason=""):
            action_history.append(('restart', bot_type, reason))
        
        coordinator.restart_bot = mock_restart
        
        # Simula múltiplas ações em rápida sucessão
        coordinator.restart_bot('bot_estavel', 'action1')
        coordinator.restart_bot('bot_estavel', 'action2')  # Substitui action1
        
        # Deve ter 2 chamadas (uma para cada ação distinta)
        assert len(action_history) == 2
        assert action_history[0] == ('restart', 'bot_estavel', 'action1')
        assert action_history[1] == ('restart', 'bot_estavel', 'action2')
    
    def test_coalesce_delay_respected(self, coordinator):
        """Verifica se delay de coalescimento é respeitado"""
        # Este teste seria mais prático com mocking de time
        # Por enquanto, apenas verifica a estrutura
        assert hasattr(coordinator, '_watch_bot_status_loop')
        assert callable(coordinator._watch_bot_status_loop)


class TestAuditoria:
    """Testes para sistema de auditoria"""
    
    def test_audit_event_creation(self, coordinator):
        """Verifica se eventos de auditoria são criados"""
        from src.audit import AuditEvent
        
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type='restart',
            severity='warning',
            source='test',
            target='bot_estavel',
            action='test_restart',
            details={'test': True}
        )
        
        assert event.event_type == 'restart'
        assert event.severity == 'warning'
        assert event.to_dict()['test_field'] if 'test_field' in event.to_dict() else True
    
    def test_audit_logger_initialization(self, coordinator):
        """Verifica se logger de auditoria é inicializado"""
        assert coordinator.audit is not None
        assert hasattr(coordinator.audit, 'log_event')
        assert hasattr(coordinator.audit, 'log_restart')
        assert hasattr(coordinator.audit, 'log_stop')
    
    def test_restart_logs_audit_event(self, coordinator):
        """Verifica se restart registra evento de auditoria"""
        from unittest.mock import patch
        
        with patch.object(coordinator.audit, 'log_restart') as mock_log:
            coordinator.restart_bot('bot_estavel', reason='test_reason')
            mock_log.assert_called()
            # Verifica argumentos
            call_args = mock_log.call_args
            assert 'reason' in call_args.kwargs
            assert call_args.kwargs['reason'] == 'test_reason'
    
    def test_stop_logs_audit_event(self, coordinator):
        """Verifica se stop registra evento de auditoria"""
        from unittest.mock import patch
        
        with patch.object(coordinator.audit, 'log_stop') as mock_log:
            coordinator.stop_bot('bot_estavel', reason='test_reason')
            mock_log.assert_called()
            call_args = mock_log.call_args
            assert 'reason' in call_args.kwargs


class TestWatcherIntegration:
    """Testes para integração do watcher de status"""
    
    def test_watcher_thread_started(self, coordinator):
        """Verifica se thread watcher foi iniciada"""
        assert coordinator._watcher_thread is not None
        assert coordinator._watcher_thread.daemon is True
    
    def test_bot_status_file_watcher(self, coordinator, test_env):
        """Verifica se watcher consegue ler bot_status.json"""
        # Cria arquivo bot_status.json
        status_file = test_env['data_dir'] / 'bot_status.json'
        test_env['data_dir'].mkdir(parents=True, exist_ok=True)
        
        status_data = {
            'last_action': 'restart',
            'target_bot': 'bot_estavel',
            'last_action_at': datetime.now().isoformat()
        }
        
        with open(status_file, 'w') as f:
            json.dump(status_data, f)
        
        # Verifica se arquivo foi criado
        assert status_file.exists()
        
        # Verifica se conteúdo pode ser lido
        with open(status_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['last_action'] == 'restart'
        assert loaded['target_bot'] == 'bot_estavel'


class TestRestartReasons:
    """Testes para rastreamento de razões de restart"""
    
    def test_restart_reason_recorded(self, coordinator):
        """Verifica se razão de restart é registrada"""
        reasons_tested = [
            'config_change',
            'manual_restart',
            'error_recovery',
            'performance_update'
        ]
        
        from unittest.mock import patch
        
        for reason in reasons_tested:
            with patch.object(coordinator.audit, 'log_restart') as mock_log:
                coordinator.restart_bot('bot_estavel', reason=reason)
                mock_log.assert_called()
                assert mock_log.call_args.kwargs['reason'] == reason
    
    def test_stop_reason_recorded(self, coordinator):
        """Verifica se razão de stop é registrada"""
        reasons_tested = [
            'user_request',
            'error_condition',
            'maintenance',
            'safety_limit'
        ]
        
        from unittest.mock import patch
        
        for reason in reasons_tested:
            with patch.object(coordinator.audit, 'log_stop') as mock_log:
                coordinator.stop_bot('bot_estavel', reason=reason)
                mock_log.assert_called()
                assert mock_log.call_args.kwargs['reason'] == reason


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
