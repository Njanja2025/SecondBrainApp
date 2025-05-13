"""
Unit tests for the system monitor plugin.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from plugins.system_monitor_plugin import SystemMonitorPlugin, SystemMetrics

@pytest.fixture
def plugin():
    """Create a plugin instance for testing."""
    return SystemMonitorPlugin()

@pytest.fixture
def mock_metrics():
    """Create mock system metrics for testing."""
    return SystemMetrics(
        cpu_percent=50.0,
        memory_percent=75.0,
        disk_usage={'/': 60.0, '/home': 80.0},
        network_io={
            'bytes_sent': 1024 * 1024,  # 1 MB
            'bytes_recv': 2 * 1024 * 1024,  # 2 MB
            'packets_sent': 1000,
            'packets_recv': 2000
        },
        boot_time=datetime.now() - timedelta(days=1),
        uptime=86400.0,  # 1 day in seconds
        process_count=100,
        temperature=45.0,
        battery={
            'percent': 75.0,
            'power_plugged': True,
            'time_left': 7200.0  # 2 hours
        },
        gpu_usage=30.0
    )

class TestSystemMonitorPlugin:
    """Test cases for the system monitor plugin."""
    
    def test_initialization(self, plugin):
        """Test plugin initialization."""
        assert plugin.name == "System Monitor"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Monitor system resources through voice commands"
        assert isinstance(plugin.commands, dict)
        assert len(plugin.commands) == 11
    
    def test_get_info(self, plugin):
        """Test get_info method."""
        info = plugin.get_info()
        assert info['name'] == plugin.name
        assert info['version'] == plugin.version
        assert info['description'] == plugin.description
        assert isinstance(info['commands'], list)
        assert len(info['commands']) == 11
    
    def test_get_commands(self, plugin):
        """Test get_commands method."""
        commands = plugin.get_commands()
        assert isinstance(commands, str)
        assert "system" in commands
        assert "cpu" in commands
        assert "memory" in commands
        assert "disk" in commands
        assert "network" in commands
        assert "uptime" in commands
        assert "metrics" in commands
        assert "processes" in commands
        assert "temperature" in commands
        assert "battery" in commands
        assert "gpu" in commands
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_partitions')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    @patch('psutil.boot_time')
    @patch('psutil.pids')
    @patch('psutil.sensors_temperatures')
    @patch('psutil.sensors_battery')
    @patch('GPUtil.getGPUs')
    def test_get_system_metrics(self, mock_gpu, mock_battery, mock_temp, mock_pids,
                              mock_boot_time, mock_net_io, mock_disk_usage,
                              mock_partitions, mock_memory, mock_cpu, plugin, mock_metrics):
        """Test get_system_metrics method."""
        # Setup mocks
        mock_cpu.return_value = mock_metrics.cpu_percent
        mock_memory.return_value = MagicMock(percent=mock_metrics.memory_percent)
        mock_partitions.return_value = [
            MagicMock(mountpoint='/'),
            MagicMock(mountpoint='/home')
        ]
        mock_disk_usage.side_effect = [
            MagicMock(percent=mock_metrics.disk_usage['/']),
            MagicMock(percent=mock_metrics.disk_usage['/home'])
        ]
        mock_net_io.return_value = MagicMock(
            bytes_sent=mock_metrics.network_io['bytes_sent'],
            bytes_recv=mock_metrics.network_io['bytes_recv'],
            packets_sent=mock_metrics.network_io['packets_sent'],
            packets_recv=mock_metrics.network_io['packets_recv']
        )
        mock_boot_time.return_value = mock_metrics.boot_time.timestamp()
        mock_pids.return_value = list(range(mock_metrics.process_count))
        mock_temp.return_value = {'coretemp': [MagicMock(current=mock_metrics.temperature)]}
        mock_battery.return_value = MagicMock(
            percent=mock_metrics.battery['percent'],
            power_plugged=mock_metrics.battery['power_plugged'],
            secsleft=mock_metrics.battery['time_left']
        )
        mock_gpu.return_value = [MagicMock(load=mock_metrics.gpu_usage / 100)]
        
        # Get metrics
        metrics = plugin._get_system_metrics()
        
        # Verify metrics
        assert metrics.cpu_percent == mock_metrics.cpu_percent
        assert metrics.memory_percent == mock_metrics.memory_percent
        assert metrics.disk_usage == mock_metrics.disk_usage
        assert metrics.network_io == mock_metrics.network_io
        assert abs(metrics.uptime - mock_metrics.uptime) < 1  # Allow 1 second difference
        assert metrics.process_count == mock_metrics.process_count
        assert metrics.temperature == mock_metrics.temperature
        assert metrics.battery == mock_metrics.battery
        assert metrics.gpu_usage == mock_metrics.gpu_usage
    
    @patch('platform.uname')
    def test_system_command(self, mock_uname, plugin, mock_metrics):
        """Test system command handler."""
        # Setup mocks
        mock_uname.return_value = MagicMock(
            system="Linux",
            release="5.4.0",
            machine="x86_64",
            processor="Intel(R) Core(TM) i7-9750H"
        )
        
        with patch.object(plugin, '_get_system_metrics', return_value=mock_metrics):
            response = plugin._handle_system_command([])
            
            assert "Linux 5.4.0" in response
            assert "x86_64" in response
            assert "Intel" in response
            assert "50.0%" in response  # CPU usage
            assert "75.0%" in response  # Memory usage
            assert "100" in response  # Process count
            assert "24.0 hours" in response  # Uptime
            assert "45.0°C" in response  # Temperature
            assert "75.0%" in response  # Battery
            assert "30.0%" in response  # GPU usage
    
    def test_processes_command(self, plugin):
        """Test processes command handler."""
        mock_processes = [
            {'pid': 1, 'name': 'process1', 'cpu_percent': 10.0, 'memory_percent': 5.0},
            {'pid': 2, 'name': 'process2', 'cpu_percent': 8.0, 'memory_percent': 3.0},
            {'pid': 3, 'name': 'process3', 'cpu_percent': 6.0, 'memory_percent': 2.0},
            {'pid': 4, 'name': 'process4', 'cpu_percent': 4.0, 'memory_percent': 1.0},
            {'pid': 5, 'name': 'process5', 'cpu_percent': 2.0, 'memory_percent': 0.5}
        ]
        
        with patch('psutil.process_iter', return_value=[
            MagicMock(info=proc) for proc in mock_processes
        ]):
            response = plugin._handle_processes_command([])
            
            assert "Top 5 processes by CPU usage:" in response
            assert "process1" in response
            assert "process2" in response
            assert "process3" in response
            assert "process4" in response
            assert "process5" in response
    
    def test_temperature_command(self, plugin, mock_metrics):
        """Test temperature command handler."""
        with patch.object(plugin, '_get_system_metrics', return_value=mock_metrics):
            response = plugin._handle_temperature_command([])
            assert "45.0°C" in response
    
    def test_battery_command(self, plugin, mock_metrics):
        """Test battery command handler."""
        with patch.object(plugin, '_get_system_metrics', return_value=mock_metrics):
            response = plugin._handle_battery_command([])
            assert "75.0%" in response
            assert "Yes" in response  # Power plugged
            assert "2.0 hours" in response  # Time left
    
    def test_gpu_command(self, plugin, mock_metrics):
        """Test GPU command handler."""
        with patch.object(plugin, '_get_system_metrics', return_value=mock_metrics):
            response = plugin._handle_gpu_command([])
            assert "30.0%" in response
    
    @patch('psutil.cpu_count')
    @patch('psutil.cpu_freq')
    def test_cpu_command(self, mock_freq, mock_count, plugin, mock_metrics):
        """Test CPU command handler."""
        # Setup mocks
        mock_count.return_value = 8
        mock_freq.return_value = MagicMock(current=3000.0)
        
        with patch.object(plugin, '_get_system_metrics', return_value=mock_metrics):
            response = plugin._handle_cpu_command([])
            
            assert "50.0%" in response  # CPU usage
            assert "8" in response  # CPU cores
            assert "3000.0 MHz" in response  # CPU frequency
    
    @patch('psutil.virtual_memory')
    def test_memory_command(self, mock_memory, plugin, mock_metrics):
        """Test memory command handler."""
        # Setup mocks
        mock_memory.return_value = MagicMock(
            total=16 * 1024**3,  # 16 GB
            available=4 * 1024**3,  # 4 GB
            used=12 * 1024**3  # 12 GB
        )
        
        with patch.object(plugin, '_get_system_metrics', return_value=mock_metrics):
            response = plugin._handle_memory_command([])
            
            assert "75.0%" in response  # Memory usage
            assert "16.0 GB" in response  # Total memory
            assert "4.0 GB" in response  # Available memory
            assert "12.0 GB" in response  # Used memory
    
    def test_disk_command(self, plugin, mock_metrics):
        """Test disk command handler."""
        with patch.object(plugin, '_get_system_metrics', return_value=mock_metrics):
            response = plugin._handle_disk_command([])
            
            assert "/: 60.0%" in response
            assert "/home: 80.0%" in response
    
    def test_network_command(self, plugin, mock_metrics):
        """Test network command handler."""
        with patch.object(plugin, '_get_system_metrics', return_value=mock_metrics):
            response = plugin._handle_network_command([])
            
            assert "1.0 MB" in response  # Bytes sent
            assert "2.0 MB" in response  # Bytes received
            assert "1000" in response  # Packets sent
            assert "2000" in response  # Packets received
    
    def test_uptime_command(self, plugin, mock_metrics):
        """Test uptime command handler."""
        with patch.object(plugin, '_get_system_metrics', return_value=mock_metrics):
            response = plugin._handle_uptime_command([])
            
            assert "System Uptime:" in response
            assert "Days: 1" in response
            assert "Hours: 0" in response
            assert "Minutes: 0" in response
            assert "Boot Time:" in response
    
    def test_metrics_command(self, plugin, mock_metrics):
        """Test metrics command handler."""
        with patch.object(plugin, '_get_system_metrics', return_value=mock_metrics):
            response = plugin._handle_metrics_command([])
            
            assert "System Metrics:" in response
            assert "50.0%" in response  # CPU usage
            assert "75.0%" in response  # Memory usage
            assert "100" in response  # Process count
            assert "1.0 MB sent" in response  # Network sent
            assert "2.0 MB received" in response  # Network received
            assert "45.0°C" in response  # Temperature
            assert "75.0%" in response  # Battery
            assert "30.0%" in response  # GPU usage 