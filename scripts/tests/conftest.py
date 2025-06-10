import os
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'PYTHONPATH': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'TESTING': 'true'
    }):
        yield

@pytest.fixture
def mock_logging():
    """Mock logging for testing."""
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        yield mock_logger

@pytest.fixture
def mock_file_system():
    """Mock file system operations for testing."""
    with patch('os.path.exists') as mock_exists:
        with patch('os.makedirs') as mock_makedirs:
            with patch('os.remove') as mock_remove:
                with patch('shutil.copy2') as mock_copy:
                    with patch('shutil.move') as mock_move:
                        yield {
                            'exists': mock_exists,
                            'makedirs': mock_makedirs,
                            'remove': mock_remove,
                            'copy': mock_copy,
                            'move': mock_move
                        }

@pytest.fixture
def mock_subprocess():
    """Mock subprocess operations for testing."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        yield mock_run

@pytest.fixture
def mock_sqlite():
    """Mock SQLite operations for testing."""
    with patch('sqlite3.connect') as mock_connect:
        mock_cursor = mock_connect.return_value.cursor.return_value
        yield {
            'connect': mock_connect,
            'cursor': mock_cursor
        }

@pytest.fixture
def mock_requests():
    """Mock requests for testing."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        yield mock_post

@pytest.fixture
def mock_smtp():
    """Mock SMTP for testing."""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_smtp.return_value.__enter__.return_value = mock_smtp.return_value
        yield mock_smtp

@pytest.fixture
def mock_time():
    """Mock time operations for testing."""
    with patch('time.time') as mock_time:
        with patch('time.sleep') as mock_sleep:
            yield {
                'time': mock_time,
                'sleep': mock_sleep
            }

@pytest.fixture
def mock_threading():
    """Mock threading operations for testing."""
    with patch('threading.Thread') as mock_thread:
        mock_thread.return_value.start = MagicMock()
        mock_thread.return_value.join = MagicMock()
        yield mock_thread

@pytest.fixture
def mock_queue():
    """Mock queue operations for testing."""
    with patch('queue.Queue') as mock_queue:
        mock_queue.return_value.put = MagicMock()
        mock_queue.return_value.get = MagicMock()
        mock_queue.return_value.task_done = MagicMock()
        mock_queue.return_value.join = MagicMock()
        yield mock_queue

@pytest.fixture
def mock_psutil():
    """Mock psutil operations for testing."""
    with patch('psutil.Process') as mock_process:
        with patch('psutil.disk_usage') as mock_disk:
            mock_process.return_value.memory_percent.return_value = 50.0
            mock_process.return_value.cpu_percent.return_value = 30.0
            mock_disk.return_value.percent = 60.0
            yield {
                'process': mock_process,
                'disk': mock_disk
            }

@pytest.fixture
def mock_cryptography():
    """Mock cryptography operations for testing."""
    with patch('cryptography.fernet.Fernet') as mock_fernet:
        mock_fernet.return_value.encrypt.return_value = b'encrypted_data'
        yield mock_fernet

@pytest.fixture
def mock_hashlib():
    """Mock hashlib operations for testing."""
    with patch('hashlib.sha256') as mock_sha256:
        mock_sha256.return_value.hexdigest.return_value = 'test_hash'
        yield mock_sha256

@pytest.fixture
def mock_json():
    """Mock json operations for testing."""
    with patch('json.load') as mock_load:
        with patch('json.dump') as mock_dump:
            yield {
                'load': mock_load,
                'dump': mock_dump
            }

@pytest.fixture
def mock_datetime():
    """Mock datetime operations for testing."""
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.fromtimestamp.return_value = mock_datetime(2023, 1, 1, 12, 0, 0)
        yield mock_datetime 