import pytest
from unittest import mock
import builtins
import src.ai_agent.baddy_agent as baddy

def test_handle_status_logs(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    baddy.handle_status()
    assert any("System is stable" in l for l in logs)

def test_handle_stealth_scan_logs(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    baddy.handle_stealth_scan()
    assert any("Scanning system files" in l for l in logs)

def test_handle_build_drone_logs(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    baddy.handle_build_drone()
    assert any("Generating drone blueprint" in l for l in logs)

def test_handle_defend_logs(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    monkeypatch.setattr(baddy, "phantom_protocol", lambda lockdown=False: logs.append("phantom called"))
    baddy.handle_defend()
    assert any("Activating defense" in l for l in logs)
    assert any("phantom called" in l for l in logs)

def test_handle_phantom_lockdown_logs(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    monkeypatch.setattr(baddy, "phantom_protocol", lambda lockdown=False: logs.append(f"phantom called lockdown={lockdown}"))
    baddy.handle_phantom_lockdown()
    assert any("Lockdown initiated" in l for l in logs)
    assert any("lockdown=True" in l for l in logs)

def test_handle_system_health_logs(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    baddy.handle_system_health()
    assert any("System health is optimal" in l for l in logs)

def test_handle_version_logs(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    baddy.handle_version()
    assert any("Agent version" in l for l in logs)

def test_handle_help_logs(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    baddy.handle_help()
    assert any("Available commands" in l for l in logs)

def test_handle_unrecognized_logs(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    baddy.handle_unrecognized("foobar")
    assert any("Unrecognized command" in l for l in logs)

def test_claud_commands(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    baddy.handle_claud_analyze()
    baddy.handle_claud_summarize()
    baddy.handle_claud_sync()
    baddy.handle_claud_secure()
    baddy.handle_claud_upgrade()
    baddy.handle_claud_help()
    assert any("Analyzing system" in l for l in logs)
    assert any("Summarizing logs" in l for l in logs)
    assert any("Syncing with cloud" in l for l in logs)
    assert any("advanced security checks" in l for l in logs)
    assert any("self-updating" in l for l in logs)
    assert any("Available CLAUD commands" in l for l in logs)

def test_handle_task_dispatch(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    baddy.handle_task("status")
    baddy.handle_task("claud analyze")
    baddy.handle_task("notarealcommand")
    assert any("System is stable" in l for l in logs)
    assert any("Analyzing system" in l for l in logs)
    assert any("Unrecognized command" in l for l in logs)

def test_log_creates_log_file(tmp_path, monkeypatch):
    log_file = tmp_path / "baddy_agent.log"
    monkeypatch.setattr(baddy, "LOG_FILE", str(log_file))
    baddy.log("test message")
    with open(log_file) as f:
        content = f.read()
    assert "test message" in content

def test_claud_analyze_with_psutil(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    class FakePsutil:
        @staticmethod
        def cpu_percent(interval=None): return 42.0
        @staticmethod
        def virtual_memory():
            class M: percent = 24.0
            return M()
    monkeypatch.setattr(baddy, "psutil", FakePsutil)
    monkeypatch.setattr(baddy, "LOG_FILE", __file__)  # Use this file as dummy log
    baddy.handle_claud_analyze()
    assert any("CPU: 42.0%" in l for l in logs)
    assert any("MEM: 24.0%" in l for l in logs)

def test_claud_analyze_without_psutil(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    monkeypatch.setattr(baddy, "psutil", None)
    monkeypatch.setattr(baddy, "LOG_FILE", __file__)
    baddy.handle_claud_analyze()
    assert any("psutil not installed" in l for l in logs)

def test_claud_sync_with_requests(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    class FakeResp:
        status_code = 200
    class FakeRequests:
        @staticmethod
        def post(url, json): return FakeResp()
    monkeypatch.setattr(baddy, "requests", FakeRequests)
    monkeypatch.setattr(baddy, "CLAUD_SYNC_FILE", "test_sync.txt")
    baddy.handle_claud_sync()
    assert any("Cloud sync response: 200" in l for l in logs)
    assert any("Synced with cloud" in l for l in logs)

def test_claud_sync_without_requests(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    monkeypatch.setattr(baddy, "requests", None)
    monkeypatch.setattr(baddy, "CLAUD_SYNC_FILE", "test_sync.txt")
    baddy.handle_claud_sync()
    assert any("requests not installed" in l for l in logs)
    assert any("Synced with cloud" in l for l in logs)

def test_claud_upgrade_with_requests(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    class FakeResp:
        ok = True
        text = "9.9.9"
    class FakeRequests:
        @staticmethod
        def get(url): return FakeResp()
    monkeypatch.setattr(baddy, "requests", FakeRequests)
    monkeypatch.setattr(baddy, "VERSION", "1.0.0")
    monkeypatch.setattr(baddy, "REMOTE_VERSION", "1.2.0")
    monkeypatch.setattr(baddy, "CLAUD_UPGRADE_ENDPOINT", "fakeurl")
    baddy.handle_claud_upgrade()
    assert any("Upgrade available" in l for l in logs)

def test_claud_upgrade_without_requests(monkeypatch):
    logs = []
    monkeypatch.setattr(baddy, "log", logs.append)
    monkeypatch.setattr(baddy, "requests", None)
    monkeypatch.setattr(baddy, "VERSION", "1.0.0")
    monkeypatch.setattr(baddy, "REMOTE_VERSION", "9.9.9")
    baddy.handle_claud_upgrade()
    assert any("Upgrade available" in l for l in logs) 