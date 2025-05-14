"""
Audit logger module for SecondBrain application.
Tracks system events, user actions, and security-related activities.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """Represents an audit event in the system."""

    event_id: str
    timestamp: datetime
    event_type: str
    user_id: str
    action: str
    resource: str
    status: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogger:
    """Manages audit logging and event tracking."""

    def __init__(self, log_dir: str = "logs/audit"):
        """Initialize the audit logger.

        Args:
            log_dir: Directory to store audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._initialize_event_types()

    def _setup_logging(self):
        """Set up logging for the audit logger."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _initialize_event_types(self):
        """Initialize system event types."""
        self.event_types = {
            "auth": "Authentication events",
            "access": "Resource access events",
            "modify": "Data modification events",
            "system": "System events",
            "security": "Security events",
        }

    def _generate_event_id(self, event: AuditEvent) -> str:
        """Generate a unique event ID.

        Args:
            event: Audit event to generate ID for

        Returns:
            Unique event ID
        """
        data = f"{event.timestamp.isoformat()}{event.user_id}{event.action}{event.resource}"
        return hashlib.sha256(data.encode()).hexdigest()

    def log_event(
        self,
        event_type: str,
        user_id: str,
        action: str,
        resource: str,
        status: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[str]:
        """Log an audit event.

        Args:
            event_type: Type of event
            user_id: ID of the user performing the action
            action: Action performed
            resource: Resource affected
            status: Status of the action
            details: Additional event details
            ip_address: Optional IP address
            user_agent: Optional user agent string

        Returns:
            Event ID if successful, None otherwise
        """
        try:
            if event_type not in self.event_types:
                logger.error(f"Invalid event type: {event_type}")
                return None

            # Create event
            event = AuditEvent(
                event_id="",  # Will be set after generation
                timestamp=datetime.now(),
                event_type=event_type,
                user_id=user_id,
                action=action,
                resource=resource,
                status=status,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            # Generate event ID
            event.event_id = self._generate_event_id(event)

            # Save event to log file
            log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.json"

            # Load existing events
            events = []
            if log_file.exists():
                with open(log_file, "r") as f:
                    events = json.load(f)

            # Add new event
            events.append(asdict(event))

            # Save updated events
            with open(log_file, "w") as f:
                json.dump(events, f, indent=2, default=str)

            logger.info(f"Logged audit event: {event.event_id}")
            return event.event_id

        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            return None

    def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get audit events matching specified criteria.

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            event_type: Optional event type filter
            user_id: Optional user ID filter

        Returns:
            List of matching audit events
        """
        try:
            events = []

            # Get all log files in date range
            if start_time:
                start_date = start_time.date()
            else:
                start_date = datetime.now().date() - timedelta(days=30)

            if end_time:
                end_date = end_time.date()
            else:
                end_date = datetime.now().date()

            current_date = start_date
            while current_date <= end_date:
                log_file = (
                    self.log_dir / f"audit_{current_date.strftime('%Y%m%d')}.json"
                )
                if log_file.exists():
                    with open(log_file, "r") as f:
                        events.extend(json.load(f))
                current_date += timedelta(days=1)

            # Apply filters
            filtered_events = []
            for event in events:
                event_time = datetime.fromisoformat(event["timestamp"])

                if start_time and event_time < start_time:
                    continue
                if end_time and event_time > end_time:
                    continue
                if event_type and event["event_type"] != event_type:
                    continue
                if user_id and event["user_id"] != user_id:
                    continue

                filtered_events.append(event)

            return filtered_events

        except Exception as e:
            logger.error(f"Failed to get audit events: {str(e)}")
            return []

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific audit event by ID.

        Args:
            event_id: Event ID to retrieve

        Returns:
            Audit event if found, None otherwise
        """
        try:
            # Search through all log files
            for log_file in self.log_dir.glob("audit_*.json"):
                with open(log_file, "r") as f:
                    events = json.load(f)
                    for event in events:
                        if event["event_id"] == event_id:
                            return event

            return None

        except Exception as e:
            logger.error(f"Failed to get audit event {event_id}: {str(e)}")
            return None

    def cleanup_old_logs(self, days: int = 90):
        """Clean up old audit logs.

        Args:
            days: Number of days to keep logs
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            for log_file in self.log_dir.glob("audit_*.json"):
                try:
                    # Extract date from filename
                    date_str = log_file.stem.split("_")[1]
                    file_date = datetime.strptime(date_str, "%Y%m%d").date()

                    if file_date < cutoff_date.date():
                        log_file.unlink()
                        logger.info(f"Deleted old log file: {log_file}")

                except Exception as e:
                    logger.error(f"Failed to process log file {log_file}: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {str(e)}")


# Example usage
if __name__ == "__main__":
    audit = AuditLogger()

    # Log an event
    event_id = audit.log_event(
        event_type="auth",
        user_id="testuser",
        action="login",
        resource="system",
        status="success",
        details={"method": "password"},
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0",
    )

    # Get recent events
    events = audit.get_events(
        start_time=datetime.now() - timedelta(hours=1), event_type="auth"
    )
    print("Recent auth events:", events)
