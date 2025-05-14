"""
Inbox Monitor for SecondBrain application.
Manages email inbox monitoring, filtering, and alerting.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import imaplib
import email
from email.header import decode_header
import re
import threading
import queue
import time
from email_metrics import EmailMetricsManager, MetricType, MetricCategory

logger = logging.getLogger(__name__)


@dataclass
class FilterConfig:
    """Configuration for email filtering."""

    name: str
    field: str  # subject, sender, body, etc.
    pattern: str  # regex pattern
    action: str  # flag, move, delete, etc.
    target: str = None  # folder name for move action
    metadata: Dict[str, Any] = None


@dataclass
class AlertConfig:
    """Configuration for email alerts."""

    name: str
    condition: str  # threshold, pattern, etc.
    threshold: float = None
    pattern: str = None
    action: str = "notify"  # notify, webhook, etc.
    target: str = None  # webhook URL, etc.
    metadata: Dict[str, Any] = None


@dataclass
class MonitorConfig:
    """Configuration for inbox monitoring."""

    name: str
    filters: List[FilterConfig]
    alerts: List[AlertConfig]
    check_interval: int = 300  # seconds
    retention_days: int = 30
    metadata: Dict[str, Any] = None


class InboxMonitor:
    """Manages email inbox monitoring and filtering."""

    def __init__(self, config_dir: str = "config/email"):
        """Initialize the inbox monitor.

        Args:
            config_dir: Directory to store monitor configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self.metrics_manager = EmailMetricsManager(config_dir)
        self.alert_queue = queue.Queue()
        self.monitor_thread = None
        self.is_running = False

    def _setup_logging(self):
        """Set up logging for the inbox monitor."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_configs(self):
        """Load monitor configurations."""
        try:
            config_file = self.config_dir / "monitor_configs.json"

            if config_file.exists():
                with open(config_file, "r") as f:
                    config_data = json.load(f)
                    self.configs = {
                        name: MonitorConfig(
                            name=name,
                            filters=[FilterConfig(**f) for f in config["filters"]],
                            alerts=[AlertConfig(**a) for a in config["alerts"]],
                            **{
                                k: v
                                for k, v in config.items()
                                if k not in ["name", "filters", "alerts"]
                            },
                        )
                        for name, config in config_data.items()
                    }
            else:
                self.configs = {}
                self._save_configs()

            logger.info("Monitor configurations loaded")

        except Exception as e:
            logger.error(f"Failed to load monitor configurations: {str(e)}")
            raise

    def _save_configs(self):
        """Save monitor configurations."""
        try:
            config_file = self.config_dir / "monitor_configs.json"

            with open(config_file, "w") as f:
                json.dump(
                    {
                        name: {
                            "name": config.name,
                            "filters": [vars(f) for f in config.filters],
                            "alerts": [vars(a) for a in config.alerts],
                            "check_interval": config.check_interval,
                            "retention_days": config.retention_days,
                            "metadata": config.metadata,
                        }
                        for name, config in self.configs.items()
                    },
                    f,
                    indent=2,
                )

        except Exception as e:
            logger.error(f"Failed to save monitor configurations: {str(e)}")

    def create_config(self, config: MonitorConfig) -> bool:
        """Create a new monitor configuration.

        Args:
            config: Monitor configuration

        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False

            self.configs[config.name] = config
            self._save_configs()

            logger.info(f"Created monitor configuration {config.name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to create monitor configuration {config.name}: {str(e)}"
            )
            return False

    def update_config(self, name: str, config: MonitorConfig) -> bool:
        """Update an existing monitor configuration.

        Args:
            name: Configuration name
            config: New monitor configuration

        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False

            self.configs[name] = config
            self._save_configs()

            logger.info(f"Updated monitor configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update monitor configuration {name}: {str(e)}")
            return False

    def delete_config(self, name: str) -> bool:
        """Delete a monitor configuration.

        Args:
            name: Configuration name

        Returns:
            bool: True if configuration was deleted successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False

            del self.configs[name]
            self._save_configs()

            logger.info(f"Deleted monitor configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete monitor configuration {name}: {str(e)}")
            return False

    def get_config(self, name: str) -> Optional[MonitorConfig]:
        """Get monitor configuration.

        Args:
            name: Configuration name

        Returns:
            Monitor configuration if found
        """
        return self.configs.get(name)

    def list_configs(self) -> List[str]:
        """List all monitor configurations.

        Returns:
            List of configuration names
        """
        return list(self.configs.keys())

    def apply_filters(self, mail: imaplib.IMAP4_SSL, config: MonitorConfig):
        """Apply filters to emails.

        Args:
            mail: IMAP connection
            config: Monitor configuration
        """
        try:
            mail.select("INBOX")
            _, messages = mail.search(None, "ALL")

            for msg_id in messages[0].split():
                _, msg_data = mail.fetch(msg_id, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)

                for filter_config in config.filters:
                    if filter_config.field == "subject":
                        subject = decode_header(email_message["Subject"])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()

                        if re.search(filter_config.pattern, subject, re.IGNORECASE):
                            if filter_config.action == "flag":
                                mail.store(msg_id, "+FLAGS", "\\Flagged")
                            elif filter_config.action == "move":
                                mail.copy(msg_id, filter_config.target)
                                mail.store(msg_id, "+FLAGS", "\\Deleted")
                            elif filter_config.action == "delete":
                                mail.store(msg_id, "+FLAGS", "\\Deleted")

                    elif filter_config.field == "sender":
                        sender = decode_header(email_message["From"])[0][0]
                        if isinstance(sender, bytes):
                            sender = sender.decode()

                        if re.search(filter_config.pattern, sender, re.IGNORECASE):
                            if filter_config.action == "flag":
                                mail.store(msg_id, "+FLAGS", "\\Flagged")
                            elif filter_config.action == "move":
                                mail.copy(msg_id, filter_config.target)
                                mail.store(msg_id, "+FLAGS", "\\Deleted")
                            elif filter_config.action == "delete":
                                mail.store(msg_id, "+FLAGS", "\\Deleted")

                    elif filter_config.field == "body":
                        body = ""
                        if email_message.is_multipart():
                            for part in email_message.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = email_message.get_payload(decode=True).decode()

                        if re.search(filter_config.pattern, body, re.IGNORECASE):
                            if filter_config.action == "flag":
                                mail.store(msg_id, "+FLAGS", "\\Flagged")
                            elif filter_config.action == "move":
                                mail.copy(msg_id, filter_config.target)
                                mail.store(msg_id, "+FLAGS", "\\Deleted")
                            elif filter_config.action == "delete":
                                mail.store(msg_id, "+FLAGS", "\\Deleted")

            mail.expunge()

        except Exception as e:
            logger.error(f"Failed to apply filters: {str(e)}")

    def check_alerts(self, mail: imaplib.IMAP4_SSL, config: MonitorConfig):
        """Check for alert conditions.

        Args:
            mail: IMAP connection
            config: Monitor configuration
        """
        try:
            for alert in config.alerts:
                if alert.condition == "threshold":
                    # Get metrics from metrics manager
                    metrics = self.metrics_manager.collect_metrics(
                        config.name, mail.host, mail.user, mail.password
                    )

                    if alert.threshold and metrics.get(alert.name, 0) > alert.threshold:
                        self.alert_queue.put(
                            {
                                "timestamp": datetime.now(),
                                "alert": alert.name,
                                "value": metrics[alert.name],
                                "threshold": alert.threshold,
                                "action": alert.action,
                                "target": alert.target,
                            }
                        )

                elif alert.condition == "pattern":
                    mail.select("INBOX")
                    _, messages = mail.search(None, "ALL")

                    for msg_id in messages[0].split()[-10:]:  # Check last 10 messages
                        _, msg_data = mail.fetch(msg_id, "(RFC822)")
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)

                        if alert.field == "subject":
                            subject = decode_header(email_message["Subject"])[0][0]
                            if isinstance(subject, bytes):
                                subject = subject.decode()

                            if re.search(alert.pattern, subject, re.IGNORECASE):
                                self.alert_queue.put(
                                    {
                                        "timestamp": datetime.now(),
                                        "alert": alert.name,
                                        "message": subject,
                                        "pattern": alert.pattern,
                                        "action": alert.action,
                                        "target": alert.target,
                                    }
                                )

        except Exception as e:
            logger.error(f"Failed to check alerts: {str(e)}")

    def start_monitoring(
        self, config_name: str, imap_server: str, email_address: str, password: str
    ):
        """Start inbox monitoring.

        Args:
            config_name: Configuration name
            imap_server: IMAP server address
            email_address: Email address
            password: Email password
        """
        try:
            if self.is_running:
                logger.error("Monitoring already running")
                return

            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return

            self.is_running = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                args=(config_name, imap_server, email_address, password),
            )
            self.monitor_thread.start()

            logger.info(f"Started monitoring for {config_name}")

        except Exception as e:
            logger.error(f"Failed to start monitoring: {str(e)}")

    def stop_monitoring(self):
        """Stop inbox monitoring."""
        try:
            if not self.is_running:
                logger.error("Monitoring not running")
                return

            self.is_running = False
            if self.monitor_thread:
                self.monitor_thread.join()

            logger.info("Stopped monitoring")

        except Exception as e:
            logger.error(f"Failed to stop monitoring: {str(e)}")

    def _monitoring_loop(
        self, config_name: str, imap_server: str, email_address: str, password: str
    ):
        """Monitoring loop for checking emails and alerts.

        Args:
            config_name: Configuration name
            imap_server: IMAP server address
            email_address: Email address
            password: Email password
        """
        try:
            config = self.get_config(config_name)

            while self.is_running:
                # Connect to IMAP server
                mail = imaplib.IMAP4_SSL(imap_server)
                mail.login(email_address, password)

                # Apply filters
                self.apply_filters(mail, config)

                # Check alerts
                self.check_alerts(mail, config)

                # Clean up old emails
                if config.retention_days:
                    cutoff_date = datetime.now() - timedelta(days=config.retention_days)
                    date_str = cutoff_date.strftime("%d-%b-%Y")
                    mail.select("INBOX")
                    mail.search(None, f"(BEFORE {date_str})")
                    mail.store("1:*", "+FLAGS", "\\Deleted")
                    mail.expunge()

                mail.logout()
                time.sleep(config.check_interval)

        except Exception as e:
            logger.error(f"Monitoring loop failed: {str(e)}")
            self.is_running = False


# Example usage
if __name__ == "__main__":
    monitor = InboxMonitor()

    # Create monitor configuration
    config = MonitorConfig(
        name="gmail_monitor",
        filters=[
            FilterConfig(
                name="newsletter_filter",
                field="subject",
                pattern="newsletter|update|digest",
                action="move",
                target="Newsletters",
            ),
            FilterConfig(
                name="spam_filter",
                field="sender",
                pattern="spam@example.com",
                action="delete",
            ),
        ],
        alerts=[
            AlertConfig(
                name="high_volume_alert",
                condition="threshold",
                threshold=100,
                action="notify",
            ),
            AlertConfig(
                name="urgent_alert",
                field="subject",
                condition="pattern",
                pattern="urgent|important|asap",
                action="notify",
            ),
        ],
        check_interval=300,
        retention_days=30,
    )
    monitor.create_config(config)

    # Start monitoring
    monitor.start_monitoring(
        "gmail_monitor", "imap.gmail.com", "your.email@gmail.com", "your_password"
    )

    # Wait for some results
    time.sleep(300)

    # Stop monitoring
    monitor.stop_monitoring()
