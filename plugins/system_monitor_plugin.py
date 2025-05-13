"""
System Monitor Plugin - Provides system resource monitoring capabilities through voice commands
"""

import logging
import psutil
import platform
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """Data structure for system metrics."""
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
            'system': self._handle_system_command,
            'cpu': self._handle_cpu_command,
            'memory': self._handle_memory_command,
            'disk': self._handle_disk_command,
            'network': self._handle_network_command,
            'uptime': self._handle_uptime_command,
            'metrics': self._handle_metrics_command,
            'processes': self._handle_processes_command,
            'temperature': self._handle_temperature_command,
            'battery': self._handle_battery_command,
            'gpu': self._handle_gpu_command
        }
    
    def get_info(self) -> Dict:
        """Get plugin information."""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'commands': list(self.commands.keys())
        }
    
    def get_commands(self) -> str:
        """Get available commands."""
        return "\n".join([
            "system - Show overall system information",
            "cpu - Show CPU usage",
            "memory - Show memory usage",
            "disk - Show disk usage",
            "network - Show network I/O",
            "uptime - Show system uptime",
            "metrics - Show all system metrics",
            "processes - Show running processes",
            "temperature - Show system temperature",
            "battery - Show battery status",
            "gpu - Show GPU usage"
        ])
    
    def _get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk metrics
            disk_usage = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = usage.percent
                except Exception as e:
                    logger.warning(f"Could not get disk usage for {partition.mountpoint}: {str(e)}")
                    continue
            
            # Network metrics
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            # Temperature (if available)
            try:
                temperature = psutil.sensors_temperatures()
                if temperature:
                    temperature = temperature.get('coretemp', [{}])[0].current
                else:
                    temperature = None
            except Exception as e:
                logger.warning(f"Could not get temperature: {str(e)}")
                temperature = None
            
            # Battery (if available)
            try:
                battery = psutil.sensors_battery()
                if battery:
                    battery = {
                        'percent': battery.percent,
                        'power_plugged': battery.power_plugged,
                        'time_left': battery.secsleft if battery.secsleft != -2 else None
                    }
                else:
                    battery = None
            except Exception as e:
                logger.warning(f"Could not get battery info: {str(e)}")
                battery = None
            
            # GPU usage (if available)
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                gpu_usage = gpus[0].load * 100 if gpus else None
            except Exception as e:
                logger.warning(f"Could not get GPU usage: {str(e)}")
                gpu_usage = None
            
            # Boot time and uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = (datetime.now() - boot_time).total_seconds()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage=disk_usage,
                network_io=network_io,
                boot_time=boot_time,
                uptime=uptime,
                process_count=process_count,
                temperature=temperature,
                battery=battery,
                gpu_usage=gpu_usage
            )
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            raise
    
    def _handle_system_command(self, args: List[str]) -> str:
        """Handle system command."""
        try:
            metrics = self._get_system_metrics()
            system_info = platform.uname()
            
            response = [
                f"System: {system_info.system} {system_info.release}",
                f"Machine: {system_info.machine}",
                f"Processor: {system_info.processor}",
                f"CPU Usage: {metrics.cpu_percent}%",
                f"Memory Usage: {metrics.memory_percent}%",
                f"Process Count: {metrics.process_count}",
                f"Uptime: {metrics.uptime / 3600:.1f} hours"
            ]
            
            if metrics.temperature:
                response.append(f"Temperature: {metrics.temperature}°C")
            
            if metrics.battery:
                response.append(f"Battery: {metrics.battery['percent']}%")
                if metrics.battery['time_left']:
                    response.append(f"Time Left: {metrics.battery['time_left'] / 3600:.1f} hours")
            
            if metrics.gpu_usage:
                response.append(f"GPU Usage: {metrics.gpu_usage}%")
            
            return "\n".join(response)
        except Exception as e:
            logger.error(f"Error handling system command: {str(e)}")
            return "Error getting system information"
    
    def _handle_cpu_command(self, args: List[str]) -> str:
        """Handle CPU command."""
        try:
            metrics = self._get_system_metrics()
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            response = [
                f"CPU Usage: {metrics.cpu_percent}%",
                f"CPU Cores: {cpu_count}",
                f"CPU Frequency: {cpu_freq.current:.1f} MHz"
            ]
            
            return "\n".join(response)
        except Exception as e:
            logger.error(f"Error handling CPU command: {str(e)}")
            return "Error getting CPU information"
    
    def _handle_memory_command(self, args: List[str]) -> str:
        """Handle memory command."""
        try:
            metrics = self._get_system_metrics()
            memory = psutil.virtual_memory()
            
            response = [
                f"Memory Usage: {metrics.memory_percent}%",
                f"Total Memory: {memory.total / (1024**3):.1f} GB",
                f"Available Memory: {memory.available / (1024**3):.1f} GB",
                f"Used Memory: {memory.used / (1024**3):.1f} GB"
            ]
            
            return "\n".join(response)
        except Exception as e:
            logger.error(f"Error handling memory command: {str(e)}")
            return "Error getting memory information"
    
    def _handle_disk_command(self, args: List[str]) -> str:
        """Handle disk command."""
        try:
            metrics = self._get_system_metrics()
            
            response = ["Disk Usage:"]
            for mount, usage in metrics.disk_usage.items():
                response.append(f"{mount}: {usage}%")
            
            return "\n".join(response)
        except Exception as e:
            logger.error(f"Error handling disk command: {str(e)}")
            return "Error getting disk information"
    
    def _handle_network_command(self, args: List[str]) -> str:
        """Handle network command."""
        try:
            metrics = self._get_system_metrics()
            
            response = [
                "Network I/O:",
                f"Bytes Sent: {metrics.network_io['bytes_sent'] / (1024**2):.1f} MB",
                f"Bytes Received: {metrics.network_io['bytes_recv'] / (1024**2):.1f} MB",
                f"Packets Sent: {metrics.network_io['packets_sent']}",
                f"Packets Received: {metrics.network_io['packets_recv']}"
            ]
            
            return "\n".join(response)
        except Exception as e:
            logger.error(f"Error handling network command: {str(e)}")
            return "Error getting network information"
    
    def _handle_uptime_command(self, args: List[str]) -> str:
        """Handle uptime command."""
        try:
            metrics = self._get_system_metrics()
            
            days = int(metrics.uptime / 86400)
            hours = int((metrics.uptime % 86400) / 3600)
            minutes = int((metrics.uptime % 3600) / 60)
            
            response = [
                f"System Uptime:",
                f"Days: {days}",
                f"Hours: {hours}",
                f"Minutes: {minutes}",
                f"Boot Time: {metrics.boot_time.strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            return "\n".join(response)
        except Exception as e:
            logger.error(f"Error handling uptime command: {str(e)}")
            return "Error getting uptime information"
    
    def _handle_metrics_command(self, args: List[str]) -> str:
        """Handle metrics command."""
        try:
            metrics = self._get_system_metrics()
            
            response = [
                "System Metrics:",
                f"CPU Usage: {metrics.cpu_percent}%",
                f"Memory Usage: {metrics.memory_percent}%",
                f"Process Count: {metrics.process_count}",
                f"Network I/O: {metrics.network_io['bytes_sent'] / (1024**2):.1f} MB sent, {metrics.network_io['bytes_recv'] / (1024**2):.1f} MB received"
            ]
            
            if metrics.temperature:
                response.append(f"Temperature: {metrics.temperature}°C")
            
            if metrics.battery:
                response.append(f"Battery: {metrics.battery['percent']}%")
            
            if metrics.gpu_usage:
                response.append(f"GPU Usage: {metrics.gpu_usage}%")
            
            return "\n".join(response)
        except Exception as e:
            logger.error(f"Error handling metrics command: {str(e)}")
            return "Error getting system metrics"
    
    def _handle_processes_command(self, args: List[str]) -> str:
        """Handle processes command."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            response = ["Top 5 processes by CPU usage:"]
            for proc in processes[:5]:
                response.append(
                    f"{proc['name']} (PID: {proc['pid']}) - "
                    f"CPU: {proc['cpu_percent']}%, "
                    f"Memory: {proc['memory_percent']:.1f}%"
                )
            
            return "\n".join(response)
        except Exception as e:
            logger.error(f"Error handling processes command: {str(e)}")
            return "Error getting process information"
    
    def _handle_temperature_command(self, args: List[str]) -> str:
        """Handle temperature command."""
        try:
            metrics = self._get_system_metrics()
            
            if metrics.temperature:
                return f"System Temperature: {metrics.temperature}°C"
            else:
                return "Temperature information not available"
        except Exception as e:
            logger.error(f"Error handling temperature command: {str(e)}")
            return "Error getting temperature information"
    
    def _handle_battery_command(self, args: List[str]) -> str:
        """Handle battery command."""
        try:
            metrics = self._get_system_metrics()
            
            if metrics.battery:
                response = [
                    f"Battery Level: {metrics.battery['percent']}%",
                    f"Power Plugged: {'Yes' if metrics.battery['power_plugged'] else 'No'}"
                ]
                
                if metrics.battery['time_left']:
                    response.append(f"Time Left: {metrics.battery['time_left'] / 3600:.1f} hours")
                
                return "\n".join(response)
            else:
                return "Battery information not available"
        except Exception as e:
            logger.error(f"Error handling battery command: {str(e)}")
            return "Error getting battery information"
    
    def _handle_gpu_command(self, args: List[str]) -> str:
        """Handle GPU command."""
        try:
            metrics = self._get_system_metrics()
            
            if metrics.gpu_usage:
                return f"GPU Usage: {metrics.gpu_usage}%"
            else:
                return "GPU information not available"
        except Exception as e:
            logger.error(f"Error handling GPU command: {str(e)}")
            return "Error getting GPU information" 