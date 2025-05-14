import psutil
import platform
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System metrics data class."""

    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    network_io: Dict[str, int]
    timestamp: datetime


@dataclass
class ProcessMetrics:
    """Process metrics data class."""

    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    status: str
    created: datetime


class SystemMonitor:
    """Monitor system resources and application health."""

    def __init__(self, metrics_history_size: int = 100):
        self.metrics_history: List[SystemMetrics] = []
        self.metrics_history_size = metrics_history_size
        self.start_time = datetime.now()
        self.last_alert_time: Optional[datetime] = None
        self.alert_cooldown = timedelta(minutes=5)

    def get_system_info(self) -> dict:
        """Get basic system information."""
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "total_memory": psutil.virtual_memory().total,
            "uptime": str(datetime.now() - self.start_time),
        }

    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            metrics = SystemMetrics(
                cpu_percent=psutil.cpu_percent(interval=1),
                memory_percent=psutil.virtual_memory().percent,
                disk_usage={
                    disk.mountpoint: psutil.disk_usage(disk.mountpoint).percent
                    for disk in psutil.disk_partitions(all=False)
                },
                network_io={
                    "bytes_sent": psutil.net_io_counters().bytes_sent,
                    "bytes_recv": psutil.net_io_counters().bytes_recv,
                },
                timestamp=datetime.now(),
            )

            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.metrics_history_size:
                self.metrics_history.pop(0)

            return metrics
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            raise

    def get_process_metrics(self) -> List[ProcessMetrics]:
        """Get metrics for all running processes."""
        process_list = []
        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent", "status", "create_time"]
        ):
            try:
                process_list.append(
                    ProcessMetrics(
                        pid=proc.info["pid"],
                        name=proc.info["name"],
                        cpu_percent=proc.info["cpu_percent"] or 0.0,
                        memory_percent=proc.info["memory_percent"] or 0.0,
                        status=proc.info["status"],
                        created=datetime.fromtimestamp(proc.info["create_time"]),
                    )
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return process_list

    def check_health(self) -> Dict[str, bool]:
        """Check system health based on metrics."""
        metrics = self.collect_metrics()

        health_status = {
            "cpu_healthy": metrics.cpu_percent < 80,
            "memory_healthy": metrics.memory_percent < 80,
            "disk_healthy": all(usage < 90 for usage in metrics.disk_usage.values()),
            "overall_healthy": True,
        }

        health_status["overall_healthy"] = all(
            status for key, status in health_status.items() if key != "overall_healthy"
        )

        return health_status

    async def monitor_loop(self, callback=None):
        """Continuous monitoring loop."""
        while True:
            try:
                metrics = self.collect_metrics()
                health = self.check_health()

                if not health["overall_healthy"]:
                    await self._handle_health_alert(health, metrics)

                if callback:
                    await callback(metrics, health)

                await asyncio.sleep(60)  # Collect metrics every minute

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _handle_health_alert(
        self, health: Dict[str, bool], metrics: SystemMetrics
    ):
        """Handle health alerts with cooldown."""
        now = datetime.now()
        if (
            not self.last_alert_time
            or now - self.last_alert_time >= self.alert_cooldown
        ):
            self.last_alert_time = now
            alert_message = self._generate_alert_message(health, metrics)
            logger.warning(alert_message)
            # Here you could add notification logic (email, Slack, etc.)

    def _generate_alert_message(
        self, health: Dict[str, bool], metrics: SystemMetrics
    ) -> str:
        """Generate alert message from health check results."""
        issues = []
        if not health["cpu_healthy"]:
            issues.append(f"High CPU usage: {metrics.cpu_percent}%")
        if not health["memory_healthy"]:
            issues.append(f"High memory usage: {metrics.memory_percent}%")
        if not health["disk_healthy"]:
            for mount, usage in metrics.disk_usage.items():
                if usage >= 90:
                    issues.append(f"High disk usage on {mount}: {usage}%")

        return "System Health Alert:\n" + "\n".join(issues)
