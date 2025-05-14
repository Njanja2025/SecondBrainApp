"""
Audit logging and security monitoring system for SecondBrain application.
Provides comprehensive logging, monitoring, and alerting capabilities.
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from threading import Lock
import time
from ..security.access_control import User, AccessControl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/audit.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """Audit event data structure."""

    timestamp: datetime
    user_id: str
    username: str
    action: str
    target: str
    status: str
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class SecurityAlert:
    """Security alert data structure."""

    def __init__(
        self, alert_type: str, severity: str, message: str, details: Dict[str, Any]
    ):
        self.timestamp = datetime.utcnow()
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.details = details


class AuditSystem:
    """Manages audit logging and security monitoring."""

    def __init__(self, db_path: str = "data/audit.db"):
        """
        Initialize audit system.

        Args:
            db_path: Path to SQLite database for audit logs
        """
        self.db_path = db_path
        self.lock = Lock()
        self._init_database()

        # Security monitoring thresholds
        self.thresholds = {
            "failed_logins_per_hour": 5,
            "api_requests_per_minute": 100,
            "suspicious_ip_requests": 50,
            "concurrent_sessions_per_user": 3,
        }

        # Initialize monitoring
        self._start_monitoring()

    def _init_database(self):
        """Initialize audit database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()

            # Create audit events table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    user_id TEXT,
                    username TEXT,
                    action TEXT,
                    target TEXT,
                    status TEXT,
                    ip_address TEXT,
                    session_id TEXT,
                    details TEXT,
                    notes TEXT
                )
            """
            )

            # Create security alerts table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS security_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    details TEXT
                )
            """
            )

            # Create indexes for common queries
            c.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)"
            )
            c.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_events(user_id)"
            )
            c.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events(action)"
            )

            conn.commit()

    def log_event(self, event: AuditEvent):
        """
        Log an audit event.

        Args:
            event: AuditEvent object containing event details
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO audit_events 
                    (timestamp, user_id, username, action, target, status, 
                     ip_address, session_id, details, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event.timestamp,
                        event.user_id,
                        event.username,
                        event.action,
                        event.target,
                        event.status,
                        event.ip_address,
                        event.session_id,
                        json.dumps(event.details) if event.details else None,
                        event.notes,
                    ),
                )
                conn.commit()

    def create_audit_event(
        self,
        user: User,
        action: str,
        target: str,
        status: str = "success",
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> AuditEvent:
        """
        Create and log an audit event.

        Args:
            user: User performing the action
            action: Action performed
            target: Target of the action
            status: Status of the action
            ip_address: IP address of the user
            session_id: Session ID
            details: Additional details
            notes: Additional notes

        Returns:
            AuditEvent: Created audit event
        """
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            user_id=user.id,
            username=user.username,
            action=action,
            target=target,
            status=status,
            ip_address=ip_address,
            session_id=session_id,
            details=details,
            notes=notes,
        )
        self.log_event(event)
        return event

    def create_security_alert(self, alert: SecurityAlert):
        """
        Create a security alert.

        Args:
            alert: SecurityAlert object
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO security_alerts 
                    (timestamp, alert_type, severity, message, details)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        alert.timestamp,
                        alert.alert_type,
                        alert.severity,
                        alert.message,
                        json.dumps(alert.details),
                    ),
                )
                conn.commit()

                # Log alert
                logger.warning(f"Security Alert: {alert.message}")

    def _start_monitoring(self):
        """Start security monitoring in background thread."""

        def monitor_security():
            while True:
                try:
                    self._check_security_metrics()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Error in security monitoring: {e}")
                    time.sleep(60)

        import threading

        thread = threading.Thread(target=monitor_security, daemon=True)
        thread.start()

    def _check_security_metrics(self):
        """Check security metrics and generate alerts if needed."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()

            # Check failed login attempts
            c.execute(
                """
                SELECT COUNT(*) FROM audit_events
                WHERE action = 'login' AND status = 'failed'
                AND timestamp >= datetime('now', '-1 hour')
            """
            )
            failed_logins = c.fetchone()[0]

            if failed_logins >= self.thresholds["failed_logins_per_hour"]:
                self.create_security_alert(
                    SecurityAlert(
                        alert_type="failed_logins",
                        severity="high",
                        message=f"High number of failed login attempts: {failed_logins} in the last hour",
                        details={"failed_attempts": failed_logins},
                    )
                )

            # Check API request rate
            c.execute(
                """
                SELECT COUNT(*) FROM audit_events
                WHERE action = 'api_request'
                AND timestamp >= datetime('now', '-1 minute')
            """
            )
            api_requests = c.fetchone()[0]

            if api_requests >= self.thresholds["api_requests_per_minute"]:
                self.create_security_alert(
                    SecurityAlert(
                        alert_type="high_api_rate",
                        severity="medium",
                        message=f"High API request rate: {api_requests} requests/minute",
                        details={"request_count": api_requests},
                    )
                )

    def get_user_activity(self, user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get user activity for the specified time period.

        Args:
            user_id: User ID to check
            hours: Number of hours to look back

        Returns:
            List of audit events
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT * FROM audit_events
                WHERE user_id = ? AND timestamp >= datetime('now', ?)
                ORDER BY timestamp DESC
            """,
                (user_id, f"-{hours} hours"),
            )

            columns = [description[0] for description in c.description]
            return [dict(zip(columns, row)) for row in c.fetchall()]

    def get_security_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get security alerts for the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            List of security alerts
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT * FROM security_alerts
                WHERE timestamp >= datetime('now', ?)
                ORDER BY timestamp DESC
            """,
                (f"-{hours} hours",),
            )

            columns = [description[0] for description in c.description]
            return [dict(zip(columns, row)) for row in c.fetchall()]


# Example usage
if __name__ == "__main__":
    # Initialize audit system
    audit_system = AuditSystem()

    # Create test user
    user = User(id="1", username="test_user", role="user")

    # Log some events
    audit_system.create_audit_event(
        user=user,
        action="login",
        target="system",
        status="success",
        ip_address="192.168.1.1",
        notes="Successful login",
    )

    audit_system.create_audit_event(
        user=user,
        action="encrypt",
        target="journal_entry_2024_03_15",
        status="success",
        details={"entry_id": "123", "encryption_type": "AES-256"},
        notes="Encrypted journal entry",
    )

    # Simulate failed login attempts
    for _ in range(6):
        audit_system.create_audit_event(
            user=user,
            action="login",
            target="system",
            status="failed",
            ip_address="192.168.1.1",
            notes="Failed login attempt",
        )

    # Get user activity
    activity = audit_system.get_user_activity(user.id)
    print(f"User activity: {json.dumps(activity, indent=2)}")

    # Get security alerts
    alerts = audit_system.get_security_alerts()
    print(f"Security alerts: {json.dumps(alerts, indent=2)}")
