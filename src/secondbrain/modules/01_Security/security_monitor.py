"""
Security monitor module for SecondBrain application.
Detects and alerts on security events and suspicious activities.
"""

import os
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .audit_logger import AuditLogger

logger = logging.getLogger(__name__)


@dataclass
class SecurityAlert:
    """Represents a security alert in the system."""

    alert_id: str
    timestamp: datetime
    alert_type: str
    severity: str
    description: str
    source: str
    details: Dict[str, Any]
    status: str = "new"
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


@dataclass
class SecurityMetrics:
    """Represents security metrics for monitoring."""

    failed_attempts: Dict[str, int]  # user_id -> count
    last_attempt: Dict[str, datetime]  # user_id -> timestamp
    suspicious_ips: Set[str]
    unusual_access: Dict[str, int]  # user_id -> count
    concurrent_sessions: Dict[str, int]  # user_id -> count


class SecurityMonitor:
    """Monitors system security and generates alerts."""

    def __init__(self, audit_logger: AuditLogger, config_dir: str = "config/security"):
        """Initialize the security monitor.

        Args:
            audit_logger: Audit logger instance
            config_dir: Directory to store security configuration
        """
        self.audit_logger = audit_logger
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_config()
        self._initialize_metrics()
        self._start_monitoring()

    def _setup_logging(self):
        """Set up logging for the security monitor."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_config(self):
        """Load security monitoring configuration."""
        config_file = self.config_dir / "monitor_config.json"

        if config_file.exists():
            with open(config_file, "r") as f:
                self.config = json.load(f)
        else:
            # Default configuration
            self.config = {
                "failed_attempts_threshold": 5,
                "failed_attempts_window": 300,  # 5 minutes
                "unusual_time_threshold": 3,
                "concurrent_sessions_threshold": 3,
                "alert_retention_days": 90,
                "known_good_ips": [],
            }

            # Save default configuration
            with open(config_file, "w") as f:
                json.dump(self.config, f, indent=2)

    def _initialize_metrics(self):
        """Initialize security metrics."""
        self.metrics = SecurityMetrics(
            failed_attempts={},
            last_attempt={},
            suspicious_ips=set(),
            unusual_access={},
            concurrent_sessions={},
        )
        self.alerts: List[SecurityAlert] = []

    def _start_monitoring(self):
        """Start the security monitoring thread."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                self._check_security_metrics()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")

    def _check_security_metrics(self):
        """Check security metrics and generate alerts."""
        try:
            # Check failed login attempts
            for user_id, count in self.metrics.failed_attempts.items():
                if count >= self.config["failed_attempts_threshold"]:
                    self._create_alert(
                        alert_type="failed_attempts",
                        severity="high",
                        description=f"Multiple failed login attempts for user {user_id}",
                        source="auth",
                        details={"user_id": user_id, "attempts": count},
                    )

            # Check unusual access patterns
            for user_id, count in self.metrics.unusual_access.items():
                if count >= self.config["unusual_time_threshold"]:
                    self._create_alert(
                        alert_type="unusual_access",
                        severity="medium",
                        description=f"Unusual access pattern detected for user {user_id}",
                        source="access",
                        details={"user_id": user_id, "count": count},
                    )

            # Check concurrent sessions
            for user_id, count in self.metrics.concurrent_sessions.items():
                if count > self.config["concurrent_sessions_threshold"]:
                    self._create_alert(
                        alert_type="concurrent_sessions",
                        severity="medium",
                        description=f"Multiple concurrent sessions for user {user_id}",
                        source="session",
                        details={"user_id": user_id, "sessions": count},
                    )

        except Exception as e:
            logger.error(f"Error checking security metrics: {str(e)}")

    def _create_alert(
        self,
        alert_type: str,
        severity: str,
        description: str,
        source: str,
        details: Dict[str, Any],
    ) -> Optional[str]:
        """Create a new security alert.

        Args:
            alert_type: Type of alert
            severity: Alert severity
            description: Alert description
            source: Alert source
            details: Additional alert details

        Returns:
            Alert ID if successful, None otherwise
        """
        try:
            alert = SecurityAlert(
                alert_id=f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.alerts)}",
                timestamp=datetime.now(),
                alert_type=alert_type,
                severity=severity,
                description=description,
                source=source,
                details=details,
            )

            self.alerts.append(alert)
            logger.info(f"Created security alert: {alert.alert_id}")

            # Log alert to audit log
            self.audit_logger.log_event(
                event_type="security",
                user_id="system",
                action="alert",
                resource="security",
                status="new",
                details=asdict(alert),
            )

            return alert.alert_id

        except Exception as e:
            logger.error(f"Failed to create security alert: {str(e)}")
            return None

    def record_login_attempt(
        self, user_id: str, success: bool, ip_address: Optional[str] = None
    ):
        """Record a login attempt.

        Args:
            user_id: User ID
            success: Whether the attempt was successful
            ip_address: Optional IP address
        """
        try:
            now = datetime.now()

            # Update last attempt timestamp
            self.metrics.last_attempt[user_id] = now

            if not success:
                # Increment failed attempts counter
                self.metrics.failed_attempts[user_id] = (
                    self.metrics.failed_attempts.get(user_id, 0) + 1
                )

                # Check if IP is suspicious
                if ip_address and ip_address not in self.config["known_good_ips"]:
                    self.metrics.suspicious_ips.add(ip_address)
            else:
                # Reset failed attempts on successful login
                self.metrics.failed_attempts[user_id] = 0

        except Exception as e:
            logger.error(f"Failed to record login attempt: {str(e)}")

    def record_access(self, user_id: str, is_unusual: bool = False):
        """Record a resource access.

        Args:
            user_id: User ID
            is_unusual: Whether the access is unusual
        """
        try:
            if is_unusual:
                self.metrics.unusual_access[user_id] = (
                    self.metrics.unusual_access.get(user_id, 0) + 1
                )
            else:
                self.metrics.unusual_access[user_id] = 0

        except Exception as e:
            logger.error(f"Failed to record access: {str(e)}")

    def record_session(self, user_id: str, action: str):
        """Record a session event.

        Args:
            user_id: User ID
            action: Session action (start/end)
        """
        try:
            if action == "start":
                self.metrics.concurrent_sessions[user_id] = (
                    self.metrics.concurrent_sessions.get(user_id, 0) + 1
                )
            elif action == "end":
                self.metrics.concurrent_sessions[user_id] = max(
                    0, self.metrics.concurrent_sessions.get(user_id, 0) - 1
                )

        except Exception as e:
            logger.error(f"Failed to record session: {str(e)}")

    def get_alerts(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        alert_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get security alerts matching specified criteria.

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            alert_type: Optional alert type filter
            severity: Optional severity filter
            status: Optional status filter

        Returns:
            List of matching security alerts
        """
        try:
            filtered_alerts = []

            for alert in self.alerts:
                if start_time and alert.timestamp < start_time:
                    continue
                if end_time and alert.timestamp > end_time:
                    continue
                if alert_type and alert.alert_type != alert_type:
                    continue
                if severity and alert.severity != severity:
                    continue
                if status and alert.status != status:
                    continue

                filtered_alerts.append(asdict(alert))

            return filtered_alerts

        except Exception as e:
            logger.error(f"Failed to get security alerts: {str(e)}")
            return []

    def resolve_alert(self, alert_id: str, resolution_notes: str) -> bool:
        """Resolve a security alert.

        Args:
            alert_id: Alert ID to resolve
            resolution_notes: Notes about the resolution

        Returns:
            bool: True if alert was resolved successfully
        """
        try:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.status = "resolved"
                    alert.resolved_at = datetime.now()
                    alert.resolution_notes = resolution_notes

                    # Log resolution to audit log
                    self.audit_logger.log_event(
                        event_type="security",
                        user_id="system",
                        action="resolve_alert",
                        resource="security",
                        status="resolved",
                        details={
                            "alert_id": alert_id,
                            "resolution_notes": resolution_notes,
                        },
                    )

                    logger.info(f"Resolved security alert: {alert_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to resolve security alert {alert_id}: {str(e)}")
            return False

    def add_known_good_ip(self, ip_address: str):
        """Add an IP address to the known good list.

        Args:
            ip_address: IP address to add
        """
        try:
            if ip_address not in self.config["known_good_ips"]:
                self.config["known_good_ips"].append(ip_address)

                # Save updated configuration
                with open(self.config_dir / "monitor_config.json", "w") as f:
                    json.dump(self.config, f, indent=2)

                logger.info(f"Added known good IP: {ip_address}")

        except Exception as e:
            logger.error(f"Failed to add known good IP {ip_address}: {str(e)}")

    def cleanup_old_alerts(self):
        """Clean up old security alerts."""
        try:
            cutoff_date = datetime.now() - timedelta(
                days=self.config["alert_retention_days"]
            )

            self.alerts = [
                alert
                for alert in self.alerts
                if alert.timestamp > cutoff_date or alert.status == "new"
            ]

            logger.info("Cleaned up old security alerts")

        except Exception as e:
            logger.error(f"Failed to cleanup old alerts: {str(e)}")


# Example usage
if __name__ == "__main__":
    audit = AuditLogger()
    monitor = SecurityMonitor(audit)

    # Record some events
    monitor.record_login_attempt("testuser", False, "192.168.1.1")
    monitor.record_login_attempt("testuser", False, "192.168.1.1")
    monitor.record_login_attempt("testuser", True, "192.168.1.1")

    # Get alerts
    alerts = monitor.get_alerts(
        start_time=datetime.now() - timedelta(hours=1), severity="high"
    )
    print("Recent high severity alerts:", alerts)
