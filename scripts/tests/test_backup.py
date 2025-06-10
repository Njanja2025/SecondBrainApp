import os
import pytest
from unittest.mock import patch, MagicMock
from backup import MemoryEngineBackup

@pytest.fixture
def backup():
    return MemoryEngineBackup('test_config.json')

@pytest.fixture
def mock_config():
    return {
        'db_path': '/test/db.sqlite',
        'backup_path': 'test_backups',
        'schedule': {
            'full_backup': {
                'interval_days': 7,
                'retention_days': 30
            },
            'incremental_backup': {
                'interval_hours': 24,
                'retention_days': 7
            }
        },
        'compression': {
            'enabled': True,
            'format': 'zip'
        },
        'encryption': {
            'enabled': False
        },
        'verification': {
            'enabled': True,
            'checksum': True
        }
    }

def test_load_config(backup, mock_config):
    with patch('json.load', return_value=mock_config):
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                config = backup.load_config('test_config.json')
                assert config == mock_config

def test_create_backup_dir(backup):
    with patch('os.makedirs') as mock_makedirs:
        backup.create_backup_dir()
        assert mock_makedirs.call_count == 3

def test_get_last_backup_time(backup):
    with patch('os.path.exists', return_value=True):
        with patch('os.listdir', return_value=['backup_20230101.db']):
            with patch('os.path.getctime', return_value=1672531200):
                result = backup.get_last_backup_time('full')
                assert result == 1672531200

def test_should_backup(backup):
    with patch.object(backup, 'get_last_backup_time', return_value=None):
        result = backup.should_backup('full')
        assert result is True

def test_create_full_backup(backup):
    with patch('shutil.copy2') as mock_copy:
        with patch('os.path.join', return_value='test_backup.db'):
            with patch('shutil.make_archive') as mock_archive:
                with patch.object(backup, 'verify_backup', return_value=True):
                    result = backup.create_full_backup()
                    assert result == 'test_backup.db.zip'
                    mock_copy.assert_called_once()
                    mock_archive.assert_called_once()

def test_create_incremental_backup(backup):
    with patch.object(backup, 'get_last_backup_time', return_value=1672531200):
        with patch('sqlite3.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_connect.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [(1, '2023-01-01', 'data')]
            
            with patch('shutil.make_archive') as mock_archive:
                with patch.object(backup, 'verify_backup', return_value=True):
                    result = backup.create_incremental_backup()
                    assert result.endswith('.zip')
                    mock_archive.assert_called_once()

def test_encrypt_backup(backup):
    with patch('cryptography.fernet.Fernet') as mock_fernet:
        with patch('builtins.open', MagicMock()):
            with patch.object(backup, 'config', {'encryption': {'key_file': 'test.key'}}):
                backup.encrypt_backup('test_backup.db')
                mock_fernet.assert_called_once()

def test_verify_backup(backup):
    with patch('os.path.exists', return_value=True):
        with patch('hashlib.sha256') as mock_hash:
            with patch('builtins.open', MagicMock()):
                with patch('sqlite3.connect') as mock_connect:
                    result = backup.verify_backup('test_backup.db')
                    assert result is True
                    mock_hash.assert_called_once()

def test_cleanup_old_backups(backup):
    with patch('os.path.exists', return_value=True):
        with patch('os.listdir', return_value=['old_backup.db']):
            with patch('os.path.getctime', return_value=0):
                with patch('os.remove') as mock_remove:
                    backup.cleanup_old_backups()
                    mock_remove.assert_called()

def test_send_notification(backup):
    with patch.object(backup, 'send_email_notification') as mock_email:
        with patch.object(backup, 'send_webhook_notification') as mock_webhook:
            backup.send_notification('test message', 'success')
            mock_email.assert_called_once()
            mock_webhook.assert_called_once()

def test_send_email_notification(backup):
    with patch('smtplib.SMTP') as mock_smtp:
        with patch.object(backup, 'config', {
            'notifications': {
                'email': {
                    'smtp_server': 'test.com',
                    'smtp_port': 587,
                    'sender': 'test@test.com',
                    'recipients': ['test@test.com']
                }
            }
        }):
            backup.send_email_notification('test message', 'success')
            mock_smtp.assert_called_once()

def test_send_webhook_notification(backup):
    with patch('requests.post') as mock_post:
        with patch.object(backup, 'config', {
            'notifications': {
                'webhook': {
                    'url': 'http://test.com',
                    'headers': {}
                }
            }
        }):
            backup.send_webhook_notification('test message', 'success')
            mock_post.assert_called_once()

def test_backup_worker(backup):
    with patch.object(backup, 'create_full_backup', return_value='test_backup.db'):
        with patch.object(backup, 'send_notification') as mock_send:
            backup.backup_queue.put('full')
            backup.backup_worker()
            mock_send.assert_called_once()

def test_start(backup):
    with patch.object(backup, 'create_backup_dir') as mock_create:
        with patch.object(backup, 'worker_thread', MagicMock()):
            with patch.object(backup, 'should_backup', return_value=True):
                with patch.object(backup, 'backup_queue') as mock_queue:
                    with patch.object(backup, 'cleanup_old_backups') as mock_cleanup:
                        with patch('time.sleep', side_effect=KeyboardInterrupt):
                            backup.start()
                            mock_create.assert_called_once()
                            mock_queue.put.assert_called()
                            mock_cleanup.assert_called_once()

def test_stop(backup):
    with patch.object(backup, 'backup_queue') as mock_queue:
        with patch.object(backup, 'worker_thread', MagicMock()):
            backup.stop()
            mock_queue.join.assert_called_once() 