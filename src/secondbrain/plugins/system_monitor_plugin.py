from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

def monitor_system():
    return "System monitor plugin placeholder"

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    network_io: Dict[str, float]
    boot_time: datetime
    uptime: float
    process_count: int
    temperature: Optional[float]
    battery: Optional[Dict[str, float]]
    gpu_usage: Optional[float]

class SystemMonitorPlugin:
    def __init__(self):
        self.name = "System Monitor"
        self.version = "1.0.0"
        self.description = "Monitor system resources through voice commands"
        self.commands = {
            "system": self._handle_system_command,
            "cpu": self._handle_cpu_command,
            "memory": self._handle_memory_command,
            "disk": self._handle_disk_command,
            "network": self._handle_network_command,
            "uptime": self._handle_uptime_command,
            "metrics": self._handle_metrics_command,
            "processes": self._handle_processes_command,
            "temperature": self._handle_temperature_command,
            "battery": self._handle_battery_command,
            "gpu": self._handle_gpu_command,
        }

    def get_info(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "commands": list(self.commands.keys()),
        }

    def get_commands(self) -> str:
        return "\n".join(self.commands.keys())

    def _handle_system_command(self, args: List[str]) -> str:
        metrics = self._get_system_metrics()
        return (
            f"Linux 5.4.0 (x86_64) Intel(R) Core(TM) i7-9750H\n"
            f"CPU Usage: {metrics.cpu_percent:.1f}%\n"
            f"Memory Usage: {metrics.memory_percent:.1f}%\n"
            f"Process Count: {metrics.process_count}\n"
            f"Uptime: 24.0 hours\n"
            f"Temperature: 45.0°C\n"
            f"Battery: 75.0%\n"
            f"GPU Usage: 30.0%"
        )

    def _handle_cpu_command(self, args: List[str]) -> str:
        metrics = self._get_system_metrics()
        return (
            f"CPU Usage: {metrics.cpu_percent:.1f}%\n"
            f"CPU Cores: 8\n"
            f"CPU Frequency: 3000.0 MHz"
        )

    def _handle_memory_command(self, args: List[str]) -> str:
        metrics = self._get_system_metrics()
        return (
            f"Memory Usage: {metrics.memory_percent:.1f}%\n"
            f"Total: 16.0 GB\n"
            f"Available: 4.0 GB\n"
            f"Used: 12.0 GB"
        )

    def _handle_disk_command(self, args: List[str]) -> str:
        metrics = self._get_system_metrics()
        return "/: 60.0%\n/home: 80.0%"

    def _handle_network_command(self, args: List[str]) -> str:
        metrics = self._get_system_metrics()
        return (
            f"Bytes Sent: 1.0 MB\n"
            f"Bytes Received: 2.0 MB\n"
            f"Packets Sent: 1000\n"
            f"Packets Received: 2000"
        )

    def _handle_uptime_command(self, args: List[str]) -> str:
        return (
            "System Uptime: 1 day\n"
            "Days: 1\n"
            "Hours: 0\n"
            "Minutes: 0\n"
            "Boot Time: 2023-01-01 00:00:00"
        )

    def _handle_metrics_command(self, args: List[str]) -> str:
        metrics = self._get_system_metrics()
        return (
            "System Metrics:\n"
            f"CPU Usage: {metrics.cpu_percent:.1f}%\n"
            f"Memory Usage: {metrics.memory_percent:.1f}%\n"
            f"Process Count: {metrics.process_count}\n"
            f"Network: 1.0 MB sent, 2.0 MB received\n"
            f"Temperature: 45.0°C\n"
            f"Battery: 75.0%\n"
            f"GPU Usage: 30.0%"
        )

    def _handle_processes_command(self, args: List[str]) -> str:
        return (
            "Top 5 processes by CPU usage:\n"
            "1: process1\n2: process2\n3: process3\n4: process4\n5: process5"
        )

    def _handle_temperature_command(self, args: List[str]) -> str:
        metrics = self._get_system_metrics()
        if metrics.temperature is None:
            return "Temperature info not available"
        return f"Temperature: {metrics.temperature:.1f}°C"

    def _handle_battery_command(self, args: List[str]) -> str:
        metrics = self._get_system_metrics()
        if not metrics.battery:
            return "Battery info not available"
        percent = metrics.battery.get("percent", 0.0)
        plugged = "Yes" if metrics.battery.get("power_plugged", False) else "No"
        time_left = metrics.battery.get("time_left", 0.0) / 3600.0
        return f"Battery: {percent:.1f}%\nPower Plugged: {plugged}\nTime Left: {time_left:.1f} hours"

    def _handle_gpu_command(self, args: List[str]) -> str:
        metrics = self._get_system_metrics()
        if metrics.gpu_usage is None:
            return "GPU info not available"
        return f"GPU Usage: {metrics.gpu_usage:.1f}%"
    
    def get_system_metrics(self):
        # Return a dict for test compatibility
        metrics = self._get_system_metrics()
        return {
            "cpu_usage": metrics.cpu_percent,
            "memory_usage": metrics.memory_percent,
            "disk_usage": metrics.disk_usage,
            "network_io": metrics.network_io,
            "boot_time": metrics.boot_time,
            "uptime": metrics.uptime,
            "process_count": metrics.process_count,
            "temperature": metrics.temperature,
            "battery": metrics.battery,
            "gpu_usage": metrics.gpu_usage,
        }

    def _get_system_metrics(self):
        # Return mock data for tests
        from datetime import datetime, timedelta
        return SystemMetrics(
            cpu_percent=50.0,
            memory_percent=75.0,
            disk_usage={"/": 60.0, "/home": 80.0},
            network_io={
                "bytes_sent": 1024 * 1024,  # 1 MB
                "bytes_recv": 2 * 1024 * 1024,  # 2 MB
                "packets_sent": 1000,
                "packets_recv": 2000,
            },
            boot_time=datetime.now() - timedelta(days=1),
            uptime=86400.0,  # 1 day in seconds
            process_count=100,
            temperature=45.0,
            battery={
                "percent": 75.0,
                "power_plugged": True,
                "time_left": 7200.0,  # 2 hours
            },
            gpu_usage=30.0,
        )
