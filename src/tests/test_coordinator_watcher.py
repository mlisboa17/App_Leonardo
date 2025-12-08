import os
import json
import time
from datetime import datetime

from src.coordinator import BotCoordinator


def ensure_config_for_test():
    # Create minimal config with a bot to ensure the coordinator finds it
    cfg_dir = os.path.join(os.getcwd(), 'config')
    os.makedirs(cfg_dir, exist_ok=True)
    cfg_path = os.path.join(cfg_dir, 'bots_config.yaml')
    if not os.path.exists(cfg_path):
        with open(cfg_path, 'w', encoding='utf-8') as f:
            f.write('bot_estavel:\n  name: bot_estavel\n  enabled: true\n  trading:\n    max_positions: 2\n  portfolio: []\n')


def write_bot_status(action: str, target_bot: str | None = None):
    os.makedirs('data', exist_ok=True)
    status = {
        'running': True if action != 'stop' else False,
        'last_action': action,
        'last_action_by': 'test',
        'last_action_at': datetime.now().isoformat(),
        'target_bot': target_bot
    }
    with open('data/bot_status.json', 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)


def test_watcher_restart_and_stop(tmp_path):
    ensure_config_for_test()
    # instantiate coordinator (this will start watcher in background)
    coordinator = BotCoordinator(config_path='config/bots_config.yaml')
    try:
        # Ensure bot exists
        assert 'bot_estavel' in coordinator.bots

        # Trigger restart for bot_estavel
        write_bot_status('restart', 'bot_estavel')
        # Wait to allow the watcher to coalesce and execute
        time.sleep(3)
        # After restart, the bot should still be present and enabled according to config
        assert 'bot_estavel' in coordinator.bots
        assert coordinator.bots['bot_estavel'].enabled is True

        # Trigger stop
        write_bot_status('stop', 'bot_estavel')
        time.sleep(3)
        assert coordinator.bots['bot_estavel'].enabled is False
    finally:
        # Stop watcher thread to avoid leaking on test suite
        try:
            coordinator._watcher_stop_event.set()
        except Exception:
            pass
