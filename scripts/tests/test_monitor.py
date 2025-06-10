import os
import pytest
from unittest.mock import patch, MagicMock
from monitor import MemoryEngineMonitor

@pytest.fixture
def monitor():
    return MemoryEngineMonitor('test_config.json')

@pytest.fixture
def mock_config():
    return {
        'db_path': '/test/db.sqlite',
        'check_interval': 60,
        'metrics': {
            'db_size': {
                'warning_threshold_mb': 100,
                'critical_threshold_mb': 500
            },
            'memory_usage': {
                'warning_threshold_percent': 70,
                'critical_threshold_percent': 90
            }
        },
        'alerts': {
            'email': {
                'enabled': False
            },
            'webhook': {
                'enabled': False
            }
        }
    }

def test_load_config(monitor, mock_config):
    with patch('json.load', return_value=mock_config):
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                config = monitor.load_config('test_config.json')
                assert config == mock_config

def test_check_db_size(monitor):
    with patch('os.path.getsize', return_value=1024 * 1024):
        result = monitor.check_db_size()
        assert result['metric'] == 'db_size'
        assert result['value'] == 1.0
        assert result['unit'] == 'MB'

def test_check_memory_usage(monitor):
    with patch('psutil.Process') as mock_process:
        mock_process.return_value.memory_percent.return_value = 50.0
        result = monitor.check_memory_usage()
        assert result['metric'] == 'memory_usage'
        assert result['value'] == 50.0
        assert result['unit'] == 'percent'

def test_check_cpu_usage(monitor):
    with patch('psutil.Process') as mock_process:
        mock_process.return_value.cpu_percent.return_value = 30.0
        result = monitor.check_cpu_usage()
        assert result['metric'] == 'cpu_usage'
        assert result['value'] == 30.0
        assert result['unit'] == 'percent'

def test_check_disk_usage(monitor):
    with patch('psutil.disk_usage') as mock_disk:
        mock_disk.return_value.percent = 60.0
        result = monitor.check_disk_usage()
        assert result['metric'] == 'disk_usage'
        assert result['value'] == 60.0
        assert result['unit'] == 'percent'

def test_check_db_health(monitor):
    with patch('sqlite3.connect') as mock_connect:
        mock_cursor = MagicMock()
        mock_connect.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [('ok',), [(1,)], [(1,)]]
        
        result = monitor.check_db_health()
        assert result['metric'] == 'db_health'
        assert 'integrity' in result['value']
        assert 'indexes' in result['value']
        assert 'has_stats' in result['value']

def test_check_query_performance(monitor):
    with patch('sqlite3.connect') as mock_connect:
        mock_cursor = MagicMock()
        mock_connect.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [(1,)]
        
        result = monitor.check_query_performance()
        assert result['metric'] == 'query_performance'
        assert isinstance(result['value'], dict)

def test_evaluate_metrics(monitor):
    metrics = [
        {
            'metric': 'db_size',
            'value': 200.0,
            'unit': 'MB'
        },
        {
            'metric': 'memory_usage',
            'value': 80.0,
            'unit': 'percent'
        }
    ]
    
    alerts = monitor.evaluate_metrics(metrics)
    assert len(alerts) == 2
    assert alerts[0]['level'] == 'warning'
    assert alerts[1]['level'] == 'warning'

def test_send_alert(monitor):
    with patch.object(monitor, 'send_email_alert') as mock_email:
        with patch.object(monitor, 'send_webhook_alert') as mock_webhook:
            monitor.send_alert('test message', 'warning')
            mock_email.assert_called_once()
            mock_webhook.assert_called_once()

def test_cleanup_old_data(monitor):
    with patch('os.path.exists', return_value=True):
        with patch('os.listdir', return_value=['old_file.json']):
            with patch('os.path.getctime', return_value=0):
                with patch('os.remove') as mock_remove:
                    monitor.cleanup_old_data()
                    mock_remove.assert_called()

def test_collect_metrics(monitor):
    with patch.object(monitor, 'check_db_size') as mock_db:
        with patch.object(monitor, 'check_memory_usage') as mock_mem:
            with patch.object(monitor, 'check_cpu_usage') as mock_cpu:
                with patch.object(monitor, 'check_disk_usage') as mock_disk:
                    with patch.object(monitor, 'check_db_health') as mock_health:
                        with patch.object(monitor, 'check_query_performance') as mock_query:
                            mock_db.return_value = {'metric': 'db_size', 'value': 1.0}
                            mock_mem.return_value = {'metric': 'memory_usage', 'value': 50.0}
                            mock_cpu.return_value = {'metric': 'cpu_usage', 'value': 30.0}
                            mock_disk.return_value = {'metric': 'disk_usage', 'value': 60.0}
                            mock_health.return_value = {'metric': 'db_health', 'value': {}}
                            mock_query.return_value = {'metric': 'query_performance', 'value': {}}
                            
                            monitor.collect_metrics()
                            assert monitor.metrics_queue.qsize() == 1
                            assert monitor.alert_queue.qsize() == 0

def test_metrics_worker(monitor):
    with patch('json.dump') as mock_dump:
        with patch('builtins.open', MagicMock()):
            monitor.metrics_queue.put([{'metric': 'test', 'value': 1.0}])
            monitor.metrics_worker()
            mock_dump.assert_called_once()

def test_alert_worker(monitor):
    with patch.object(monitor, 'send_alert') as mock_send:
        monitor.alert_queue.put({'level': 'warning', 'message': 'test'})
        monitor.alert_worker()
        mock_send.assert_called_once()

def test_start(monitor):
    with patch.object(monitor, 'metrics_thread', MagicMock()):
        with patch.object(monitor, 'alert_thread', MagicMock()):
            with patch.object(monitor, 'collect_metrics') as mock_collect:
                with patch.object(monitor, 'cleanup_old_data') as mock_cleanup:
                    with patch('time.sleep', side_effect=KeyboardInterrupt):
                        monitor.start()
                        mock_collect.assert_called_once()
                        mock_cleanup.assert_called_once()

def test_stop(monitor):
    with patch.object(monitor, 'metrics_queue') as mock_metrics:
        with patch.object(monitor, 'alert_queue') as mock_alerts:
            with patch.object(monitor, 'metrics_thread', MagicMock()):
                with patch.object(monitor, 'alert_thread', MagicMock()):
                    monitor.stop()
                    mock_metrics.join.assert_called_once()
                    mock_alerts.join.assert_called_once() 