"""
Advanced metrics collection and monitoring system.
"""

import os
import time
import psutil
import platform
import logging
from typing import Dict, Any
from datetime import datetime
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from datadog import initialize, statsd

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self, enable_prometheus: bool = True, enable_datadog: bool = True):
        """Initialize metrics collector."""
        self.start_time = time.time()

        # Prometheus metrics
        if enable_prometheus:
            # Start Prometheus server
            start_http_server(8000)

            # System metrics
            self.cpu_usage = Gauge("system_cpu_usage", "CPU usage percentage")
            self.memory_usage = Gauge("system_memory_usage", "Memory usage percentage")
            self.disk_usage = Gauge("system_disk_usage", "Disk usage percentage")

            # Application metrics
            self.api_requests = Counter("app_api_requests_total", "Total API requests")
            self.blockchain_transactions = Counter(
                "blockchain_transactions_total", "Total blockchain transactions"
            )
            self.voice_commands = Counter(
                "voice_commands_total", "Total voice commands processed"
            )

            # Performance metrics
            self.request_duration = Histogram(
                "request_duration_seconds",
                "Request duration in seconds",
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            )

            # Security metrics
            self.security_incidents = Counter(
                "security_incidents_total", "Total security incidents"
            )
            self.failed_auth_attempts = Counter(
                "failed_auth_attempts_total", "Failed authentication attempts"
            )

        # Datadog metrics
        if enable_datadog:
            initialize(
                api_key=os.getenv("DATADOG_API_KEY"),
                app_key=os.getenv("DATADOG_APP_KEY"),
            )

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu": {
                    "percent": psutil.cpu_percent(interval=1),
                    "count": psutil.cpu_count(),
                    "frequency": (
                        psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                    ),
                },
                "memory": psutil.virtual_memory()._asdict(),
                "disk": psutil.disk_usage("/")._asdict(),
                "network": {
                    "connections": len(psutil.net_connections()),
                    "io_counters": (
                        psutil.net_io_counters()._asdict()
                        if psutil.net_io_counters()
                        else None
                    ),
                },
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            },
            "process": {
                "cpu_percent": psutil.Process().cpu_percent(),
                "memory_percent": psutil.Process().memory_percent(),
                "threads": psutil.Process().num_threads(),
                "open_files": len(psutil.Process().open_files()),
                "connections": len(psutil.Process().connections()),
            },
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
        }

        # Update Prometheus metrics
        self.cpu_usage.set(metrics["system"]["cpu"]["percent"])
        self.memory_usage.set(metrics["system"]["memory"]["percent"])
        self.disk_usage.set(metrics["system"]["disk"]["percent"])

        # Send to Datadog
        statsd.gauge("system.cpu.usage", metrics["system"]["cpu"]["percent"])
        statsd.gauge("system.memory.usage", metrics["system"]["memory"]["percent"])
        statsd.gauge("system.disk.usage", metrics["system"]["disk"]["percent"])

        return metrics

    def track_api_request(self, endpoint: str, duration: float, status_code: int):
        """Track API request metrics."""
        self.api_requests.inc()
        self.request_duration.observe(duration)

        # Datadog metrics
        statsd.increment("api.requests")
        statsd.histogram("api.request_duration", duration)
        statsd.increment(f"api.status_code.{status_code}")

    def track_blockchain_transaction(self, tx_type: str, gas_used: int, status: str):
        """Track blockchain transaction metrics."""
        self.blockchain_transactions.inc()

        # Datadog metrics
        statsd.increment("blockchain.transactions")
        statsd.gauge("blockchain.gas_used", gas_used)
        statsd.increment(f"blockchain.transaction_status.{status}")

    def track_voice_command(
        self, command_type: str, processing_time: float, success: bool
    ):
        """Track voice command metrics."""
        self.voice_commands.inc()

        # Datadog metrics
        statsd.increment("voice.commands")
        statsd.histogram("voice.processing_time", processing_time)
        statsd.increment("voice.success" if success else "voice.failure")

    def track_security_incident(self, incident_type: str, severity: str):
        """Track security incident metrics."""
        self.security_incidents.inc()
        self.failed_auth_attempts.inc() if incident_type == "auth_failure" else None

        # Datadog metrics
        statsd.increment("security.incidents")
        statsd.increment(f"security.incident_type.{incident_type}")
        statsd.increment(f"security.severity.{severity}")

    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.start_time

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        return {
            "uptime_seconds": self.get_uptime(),
            "cpu_percent": psutil.Process().cpu_percent(),
            "memory_percent": psutil.Process().memory_percent(),
            "open_files": len(psutil.Process().open_files()),
            "threads": psutil.Process().num_threads(),
            "connections": len(psutil.Process().connections()),
        }

    def get_resource_usage(self) -> Dict[str, Any]:
        """Get detailed resource usage metrics."""
        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            },
            "memory": psutil.virtual_memory()._asdict(),
            "swap": psutil.swap_memory()._asdict(),
            "disk": {
                "usage": psutil.disk_usage("/")._asdict(),
                "io_counters": (
                    psutil.disk_io_counters()._asdict()
                    if psutil.disk_io_counters()
                    else None
                ),
            },
            "network": {
                "io_counters": (
                    psutil.net_io_counters()._asdict()
                    if psutil.net_io_counters()
                    else None
                ),
                "connections": len(psutil.net_connections()),
            },
        }
