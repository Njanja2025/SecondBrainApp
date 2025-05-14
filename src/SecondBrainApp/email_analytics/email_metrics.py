"""
Email Metrics Manager for SecondBrain application.
Manages email metrics collection, analysis, and reporting.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import stats
import imaplib
import email
from email.header import decode_header
import re
import threading
import queue

logger = logging.getLogger(__name__)


class MetricType:
    """Types of email metrics."""

    VOLUME = "volume"
    RESPONSE_TIME = "response_time"
    CATEGORY = "category"
    SENTIMENT = "sentiment"
    ATTACHMENT = "attachment"
    THREAD = "thread"
    CUSTOM = "custom"


class MetricCategory:
    """Categories of email metrics."""

    INBOX = "inbox"
    SENT = "sent"
    DRAFT = "draft"
    ARCHIVE = "archive"
    SPAM = "spam"
    CUSTOM = "custom"


@dataclass
class EmailMetricConfig:
    """Configuration for email metrics."""

    name: str
    type: str  # volume, response_time, category, sentiment, attachment, thread, custom
    category: str  # inbox, sent, draft, archive, spam, custom
    description: str
    unit: str  # count, ms, %, etc.
    threshold: float = None
    weight: float = 1.0
    metadata: Dict[str, Any] = None


@dataclass
class MonitorConfig:
    """Configuration for email monitoring."""

    name: str
    metrics: List[EmailMetricConfig]
    sampling_interval: int = 300  # seconds
    analysis_window: int = 86400  # seconds (24 hours)
    alert_threshold: float = 0.8  # 80%
    metadata: Dict[str, Any] = None


class EmailMetricsManager:
    """Manages email metrics collection and analysis."""

    def __init__(self, config_dir: str = "config/email"):
        """Initialize the email metrics manager.

        Args:
            config_dir: Directory to store email configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self.metrics_queue = queue.Queue()
        self.monitor_thread = None
        self.is_running = False

    def _setup_logging(self):
        """Set up logging for the email metrics manager."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_configs(self):
        """Load email configurations."""
        try:
            config_file = self.config_dir / "email_configs.json"

            if config_file.exists():
                with open(config_file, "r") as f:
                    config_data = json.load(f)
                    self.configs = {
                        name: MonitorConfig(
                            name=name,
                            metrics=[EmailMetricConfig(**m) for m in config["metrics"]],
                            **{
                                k: v
                                for k, v in config.items()
                                if k not in ["name", "metrics"]
                            },
                        )
                        for name, config in config_data.items()
                    }
            else:
                self.configs = {}
                self._save_configs()

            logger.info("Email configurations loaded")

        except Exception as e:
            logger.error(f"Failed to load email configurations: {str(e)}")
            raise

    def _save_configs(self):
        """Save email configurations."""
        try:
            config_file = self.config_dir / "email_configs.json"

            with open(config_file, "w") as f:
                json.dump(
                    {
                        name: {
                            "name": config.name,
                            "metrics": [vars(m) for m in config.metrics],
                            "sampling_interval": config.sampling_interval,
                            "analysis_window": config.analysis_window,
                            "alert_threshold": config.alert_threshold,
                            "metadata": config.metadata,
                        }
                        for name, config in self.configs.items()
                    },
                    f,
                    indent=2,
                )

        except Exception as e:
            logger.error(f"Failed to save email configurations: {str(e)}")

    def create_config(self, config: MonitorConfig) -> bool:
        """Create a new email configuration.

        Args:
            config: Email configuration

        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False

            self.configs[config.name] = config
            self._save_configs()

            logger.info(f"Created email configuration {config.name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to create email configuration {config.name}: {str(e)}"
            )
            return False

    def update_config(self, name: str, config: MonitorConfig) -> bool:
        """Update an existing email configuration.

        Args:
            name: Configuration name
            config: New email configuration

        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False

            self.configs[name] = config
            self._save_configs()

            logger.info(f"Updated email configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update email configuration {name}: {str(e)}")
            return False

    def delete_config(self, name: str) -> bool:
        """Delete an email configuration.

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

            logger.info(f"Deleted email configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete email configuration {name}: {str(e)}")
            return False

    def get_config(self, name: str) -> Optional[MonitorConfig]:
        """Get email configuration.

        Args:
            name: Configuration name

        Returns:
            Email configuration if found
        """
        return self.configs.get(name)

    def list_configs(self) -> List[str]:
        """List all email configurations.

        Returns:
            List of configuration names
        """
        return list(self.configs.keys())

    def collect_metrics(
        self, config_name: str, imap_server: str, email_address: str, password: str
    ) -> Dict[str, float]:
        """Collect email metrics.

        Args:
            config_name: Configuration name
            imap_server: IMAP server address
            email_address: Email address
            password: Email password

        Returns:
            Dictionary of metric values
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return {}

            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_address, password)

            metrics = {}

            for metric in config.metrics:
                if metric.type == MetricType.VOLUME:
                    if metric.category == MetricCategory.INBOX:
                        mail.select("INBOX")
                        _, messages = mail.search(None, "ALL")
                        metrics[metric.name] = len(messages[0].split())
                    elif metric.category == MetricCategory.SENT:
                        mail.select('"[Gmail]/Sent Mail"')
                        _, messages = mail.search(None, "ALL")
                        metrics[metric.name] = len(messages[0].split())

                elif metric.type == MetricType.RESPONSE_TIME:
                    # Calculate average response time
                    mail.select("INBOX")
                    _, messages = mail.search(None, "ALL")
                    response_times = []

                    for msg_id in messages[0].split()[-10:]:  # Last 10 messages
                        _, msg_data = mail.fetch(msg_id, "(RFC822)")
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)

                        # Get received time
                        received_time = email.utils.parsedate_to_datetime(
                            email_message["Date"]
                        )

                        # Get reply time if exists
                        if email_message["In-Reply-To"]:
                            reply_id = email_message["In-Reply-To"]
                            _, reply_data = mail.search(
                                None, f'HEADER "Message-ID" "{reply_id}"'
                            )
                            if reply_data[0]:
                                reply_time = email.utils.parsedate_to_datetime(
                                    email.message_from_bytes(
                                        mail.fetch(
                                            reply_data[0].split()[0], "(RFC822)"
                                        )[1][0][1]
                                    )["Date"]
                                )
                                response_times.append(
                                    (reply_time - received_time).total_seconds()
                                )

                    metrics[metric.name] = (
                        np.mean(response_times) if response_times else 0
                    )

                elif metric.type == MetricType.CATEGORY:
                    # Categorize emails
                    mail.select("INBOX")
                    _, messages = mail.search(None, "ALL")
                    categories = {}

                    for msg_id in messages[0].split()[-50:]:  # Last 50 messages
                        _, msg_data = mail.fetch(msg_id, "(RFC822)")
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)

                        # Simple categorization based on subject and sender
                        subject = decode_header(email_message["Subject"])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()

                        if re.search(r"newsletter|update|digest", subject.lower()):
                            categories["newsletter"] = (
                                categories.get("newsletter", 0) + 1
                            )
                        elif re.search(r"alert|warning|error", subject.lower()):
                            categories["alert"] = categories.get("alert", 0) + 1
                        else:
                            categories["other"] = categories.get("other", 0) + 1

                    metrics[metric.name] = max(categories.items(), key=lambda x: x[1])[
                        0
                    ]

                elif metric.type == MetricType.ATTACHMENT:
                    # Count attachments
                    mail.select("INBOX")
                    _, messages = mail.search(None, "ALL")
                    attachment_count = 0

                    for msg_id in messages[0].split()[-20:]:  # Last 20 messages
                        _, msg_data = mail.fetch(msg_id, "(RFC822)")
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)

                        if email_message.get_content_maintype() == "multipart":
                            for part in email_message.walk():
                                if part.get_content_maintype() == "multipart":
                                    continue
                                if part.get("Content-Disposition") is None:
                                    continue
                                attachment_count += 1

                    metrics[metric.name] = attachment_count

            mail.logout()
            return metrics

        except Exception as e:
            logger.error(f"Failed to collect metrics for {config_name}: {str(e)}")
            return {}

    def analyze_metrics(
        self, metrics_data: List[Dict[str, float]], config: MonitorConfig
    ) -> Dict[str, Any]:
        """Analyze email metrics.

        Args:
            metrics_data: List of metric values over time
            config: Email configuration

        Returns:
            Analysis result
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(metrics_data)

            # Calculate statistics
            statistics = {}
            for metric in config.metrics:
                if metric.name in df.columns:
                    statistics[f"{metric.name}_mean"] = df[metric.name].mean()
                    statistics[f"{metric.name}_std"] = df[metric.name].std()
                    statistics[f"{metric.name}_max"] = df[metric.name].max()
                    statistics[f"{metric.name}_min"] = df[metric.name].min()

            # Detect anomalies
            anomalies = []
            for metric in config.metrics:
                if metric.name in df.columns:
                    # Use z-score for anomaly detection
                    z_scores = np.abs(stats.zscore(df[metric.name]))
                    anomaly_indices = np.where(z_scores > 3)[0]

                    for idx in anomaly_indices:
                        anomalies.append(
                            {
                                "metric": metric.name,
                                "timestamp": df.index[idx],
                                "value": df[metric.name].iloc[idx],
                                "z_score": z_scores[idx],
                            }
                        )

            # Generate recommendations
            recommendations = []
            for metric in config.metrics:
                if metric.name in df.columns:
                    if df[metric.name].mean() > config.alert_threshold * 100:
                        recommendations.append(
                            f"High {metric.name} detected. Consider optimization."
                        )

            return {
                "timestamp": datetime.now(),
                "metrics": df.iloc[-1].to_dict(),
                "statistics": statistics,
                "anomalies": anomalies,
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Failed to analyze metrics: {str(e)}")
            return None

    def start_monitoring(
        self, config_name: str, imap_server: str, email_address: str, password: str
    ):
        """Start email monitoring.

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
        """Stop email monitoring."""
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
        """Monitoring loop for collecting and analyzing metrics.

        Args:
            config_name: Configuration name
            imap_server: IMAP server address
            email_address: Email address
            password: Email password
        """
        try:
            config = self.get_config(config_name)
            metrics_data = []

            while self.is_running:
                # Collect metrics
                metrics = self.collect_metrics(
                    config_name, imap_server, email_address, password
                )
                metrics_data.append(metrics)

                # Keep only recent data
                if (
                    len(metrics_data)
                    > config.analysis_window / config.sampling_interval
                ):
                    metrics_data.pop(0)

                # Analyze if enough data
                if len(metrics_data) >= 10:  # Minimum samples for analysis
                    result = self.analyze_metrics(metrics_data, config)
                    if result:
                        self.metrics_queue.put(result)

                time.sleep(config.sampling_interval)

        except Exception as e:
            logger.error(f"Monitoring loop failed: {str(e)}")
            self.is_running = False


# Example usage
if __name__ == "__main__":
    manager = EmailMetricsManager()

    # Create email configuration
    config = MonitorConfig(
        name="gmail_metrics",
        metrics=[
            EmailMetricConfig(
                name="inbox_volume",
                type=MetricType.VOLUME,
                category=MetricCategory.INBOX,
                description="Number of emails in inbox",
                unit="count",
                threshold=1000,
            ),
            EmailMetricConfig(
                name="response_time",
                type=MetricType.RESPONSE_TIME,
                category=MetricCategory.INBOX,
                description="Average response time",
                unit="ms",
                threshold=3600,
            ),
        ],
        sampling_interval=300,
        analysis_window=86400,
    )
    manager.create_config(config)

    # Start monitoring
    manager.start_monitoring(
        "gmail_metrics", "imap.gmail.com", "your.email@gmail.com", "your_password"
    )

    # Wait for some results
    time.sleep(300)

    # Stop monitoring
    manager.stop_monitoring()
