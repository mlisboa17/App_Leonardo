import os
import json
from datetime import datetime

from fastapi.testclient import TestClient

from ..main import app
from ..dependencies import get_current_user
from ..models import UserInDB


def make_admin_user():
    return UserInDB(
        username="test_admin",
        role="admin",
        id=1,
        hashed_password="hash",
        is_active=True,
        created_at=datetime.now()
    )


def test_update_bot_config_triggers_restart(tmp_path):
    # Setup app dependency override
    user = make_admin_user()
    app.dependency_overrides[get_current_user] = lambda: user

    client = TestClient(app)

    # Ensure config exists
    config_dir = os.path.join(os.getcwd(), "config")
    os.makedirs(config_dir, exist_ok=True)
    bot_config_path = os.path.join(config_dir, "bots_config.yaml")
    # Minimal YAML config to ensure bot exists
    with open(bot_config_path, "w", encoding="utf-8") as f:
        f.write("bots:\n  test_bot:\n    name: test_bot\n    enabled: true\n    amount_per_trade: 100\n    take_profit: 1.5\n    stop_loss: 0.5\n    max_positions: 2\n    symbols: ['BTC/USDT']\n")

    # Remove bot status file if exists
    status_file = os.path.join(os.getcwd(), "data", "bot_status.json")
    try:
        os.remove(status_file)
    except Exception:
        pass

    # Call update bot config
    resp = client.put("/api/config/bots/test_bot", json={"take_profit": 2.0})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body.get("data", {}).get("restart_scheduled") in (False, None)
    # Ensure API indicates restart scheduled
    assert body.get("data", {}).get("restart_scheduled") is True

    # After background task, bot_status should show restart and target bot
    with open(status_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("last_action") == "restart"
    assert data.get("target_bot") == "test_bot"


def test_update_global_config_triggers_restart_all(tmp_path):
    user = make_admin_user()
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)

    # Remove bot status file if exists
    status_file = os.path.join(os.getcwd(), "data", "bot_status.json")
    try:
        os.remove(status_file)
    except Exception:
        pass

    resp = client.put("/api/config/global", json={"monthly_target": 5000})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body.get("data", {}).get("restart_scheduled") is True

    with open(status_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("last_action") == "restart"
    assert data.get("target_bot") is None


def test_enable_disable_bot_triggers_restart_or_stop(tmp_path):
    user = make_admin_user()
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)

    # Ensure bot exists in config
    config_dir = os.path.join(os.getcwd(), "config")
    os.makedirs(config_dir, exist_ok=True)
    bot_config_path = os.path.join(config_dir, "bots_config.yaml")
    with open(bot_config_path, "w", encoding="utf-8") as f:
        f.write("bots:\n  test_bot2:\n    name: test_bot2\n    enabled: false\n    amount_per_trade: 50\n    take_profit: 1.2\n    stop_loss: 0.5\n    max_positions: 1\n    symbols: ['BTC/USDT']\n")

    status_file = os.path.join(os.getcwd(), "data", "bot_status.json")
    try:
        os.remove(status_file)
    except Exception:
        pass

    # Enable bot - should schedule restart
    resp = client.post("/api/config/bots/test_bot2/enable")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("data", {}).get("restart_scheduled") is True
    with open(status_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("last_action") == "restart"
    assert data.get("target_bot") == "test_bot2"

    # Disable bot - should schedule stop
    resp = client.post("/api/config/bots/test_bot2/disable")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("data", {}).get("restart_scheduled") is True
    with open(status_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("last_action") == "stop"
    assert data.get("target_bot") == "test_bot2"


def test_update_non_restart_key_does_not_trigger_restart(tmp_path):
    user = make_admin_user()
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)

    # Ensure bot exists in config
    config_dir = os.path.join(os.getcwd(), "config")
    os.makedirs(config_dir, exist_ok=True)
    bot_config_path = os.path.join(config_dir, "bots_config.yaml")
    with open(bot_config_path, "w", encoding="utf-8") as f:
        f.write("bots:\n  test_bot3:\n    name: test_bot3\n    enabled: true\n    amount_per_trade: 50\n    take_profit: 1.2\n    stop_loss: 0.5\n    max_positions: 1\n    symbols: ['BTC/USDT']\n")

    status_file = os.path.join(os.getcwd(), "data", "bot_status.json")
    try:
        os.remove(status_file)
    except Exception:
        pass

    # Update non-restart key amount_per_trade
    resp = client.put("/api/config/bots/test_bot3", json={"amount_per_trade": 100})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    # Ensure no restart happened (either no file or content doesn't show restart)
    if os.path.exists(status_file):
        with open(status_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("last_action") != "restart"
        assert data.get("target_bot") != "test_bot3"
