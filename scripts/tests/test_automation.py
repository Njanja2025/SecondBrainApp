import os
import pytest
from unittest.mock import patch, MagicMock
from advanced_automation import AdvancedAutomation

@pytest.fixture
def automation():
    return AdvancedAutomation('test_config.json')

@pytest.fixture
def mock_config():
    return {
        'repo_path': '/test/path',
        'backup_path': 'test_backups',
        'max_workers': 2,
        'tasks': {
            'backup': {
                'interval': 3600,
                'retention_days': 7
            },
            'cleanup': {
                'interval': 86400,
                'max_log_size_mb': 100
            },
            'sync': {
                'interval': 300,
                'remote': 'origin',
                'branch': 'main'
            }
        }
    }

def test_load_config(automation, mock_config):
    with patch('json.load', return_value=mock_config):
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                config = automation.load_config('test_config.json')
                assert config == mock_config

def test_setup_environment(automation):
    with patch('os.makedirs') as mock_makedirs:
        with patch('subprocess.run') as mock_run:
            with patch('os.path.exists', return_value=False):
                automation.setup_environment()
                mock_makedirs.assert_called()
                mock_run.assert_called()

def test_backup_database(automation):
    with patch('shutil.copy2') as mock_copy:
        with patch('os.path.join', return_value='test_backup.db'):
            result = automation.backup_database()
            assert result is True
            mock_copy.assert_called_once()

def test_cleanup_old_backups(automation):
    with patch('os.listdir', return_value=['old_backup.db']):
        with patch('os.path.getctime', return_value=0):
            with patch('os.remove') as mock_remove:
                automation.cleanup_old_backups()
                mock_remove.assert_called_once()

def test_cleanup_logs(automation):
    with patch('os.path.exists', return_value=True):
        with patch('os.path.getsize', return_value=200 * 1024 * 1024):
            with patch('shutil.move') as mock_move:
                automation.cleanup_logs()
                mock_move.assert_called_once()

def test_sync_with_remote(automation):
    with patch('subprocess.run') as mock_run:
        automation.sync_with_remote()
        assert mock_run.call_count == 3

def test_send_notification(automation):
    with patch.object(automation, 'send_email_notification') as mock_email:
        with patch.object(automation, 'send_webhook_notification') as mock_webhook:
            automation.send_notification('test message', 'success')
            mock_email.assert_called_once()
            mock_webhook.assert_called_once()

def test_worker(automation):
    with patch.object(automation, 'backup_database') as mock_backup:
        with patch.object(automation, 'cleanup_old_backups') as mock_cleanup:
            with patch.object(automation, 'sync_with_remote') as mock_sync:
                automation.task_queue.put({'type': 'backup'})
                automation.task_queue.put({'type': 'cleanup'})
                automation.task_queue.put({'type': 'sync'})
                automation.worker()
                mock_backup.assert_called_once()
                mock_cleanup.assert_called_once()
                mock_sync.assert_called_once()

def test_schedule_tasks(automation):
    with patch('time.time', return_value=0):
        with patch.object(automation, 'task_queue') as mock_queue:
            automation.schedule_tasks()
            assert mock_queue.put.call_count == 3

def test_start(automation):
    with patch.object(automation, 'setup_environment') as mock_setup:
        with patch.object(automation, 'worker_threads', []):
            with patch('threading.Thread') as mock_thread:
                with patch('time.sleep', side_effect=KeyboardInterrupt):
                    automation.start()
                    mock_setup.assert_called_once()
                    mock_thread.assert_called()

def test_stop(automation):
    with patch.object(automation, 'task_queue') as mock_queue:
        with patch.object(automation, 'worker_threads', [MagicMock()]):
            automation.stop()
            mock_queue.join.assert_called_once() 