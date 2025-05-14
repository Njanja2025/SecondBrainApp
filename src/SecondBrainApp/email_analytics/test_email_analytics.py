"""
Test cases for the email analytics module.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from email_metrics import (
    EmailMetricsManager,
    MetricType,
    MetricCategory,
    EmailMetricConfig,
    MonitorConfig,
)
from inbox_monitor import InboxMonitor, FilterConfig, AlertConfig, MonitorConfig


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary directory for configurations."""
    config_dir = tmp_path / "config" / "email"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def sample_metric_config():
    """Create a sample metric configuration."""
    return EmailMetricConfig(
        name="inbox_volume",
        type=MetricType.VOLUME,
        category=MetricCategory.INBOX,
        description="Number of emails in inbox",
        unit="count",
        threshold=1000,
    )


@pytest.fixture
def sample_monitor_config():
    """Create a sample monitor configuration."""
    return MonitorConfig(
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


@pytest.fixture
def sample_filter_config():
    """Create a sample filter configuration."""
    return FilterConfig(
        name="newsletter_filter",
        field="subject",
        pattern="newsletter|update|digest",
        action="move",
        target="Newsletters",
    )


@pytest.fixture
def sample_alert_config():
    """Create a sample alert configuration."""
    return AlertConfig(
        name="high_volume_alert", condition="threshold", threshold=100, action="notify"
    )


class TestEmailMetricsManager:
    """Test cases for EmailMetricsManager."""

    def test_init(self, temp_config_dir):
        """Test initialization."""
        manager = EmailMetricsManager(str(temp_config_dir))
        assert manager.config_dir == temp_config_dir
        assert isinstance(manager.configs, dict)
        assert len(manager.configs) == 0

    def test_create_config(self, temp_config_dir, sample_monitor_config):
        """Test configuration creation."""
        manager = EmailMetricsManager(str(temp_config_dir))
        assert manager.create_config(sample_monitor_config)
        assert sample_monitor_config.name in manager.configs

    def test_update_config(self, temp_config_dir, sample_monitor_config):
        """Test configuration update."""
        manager = EmailMetricsManager(str(temp_config_dir))
        manager.create_config(sample_monitor_config)

        updated_config = MonitorConfig(
            name=sample_monitor_config.name,
            metrics=sample_monitor_config.metrics,
            sampling_interval=600,
            analysis_window=172800,
        )
        assert manager.update_config(sample_monitor_config.name, updated_config)
        assert manager.configs[sample_monitor_config.name].sampling_interval == 600

    def test_delete_config(self, temp_config_dir, sample_monitor_config):
        """Test configuration deletion."""
        manager = EmailMetricsManager(str(temp_config_dir))
        manager.create_config(sample_monitor_config)
        assert manager.delete_config(sample_monitor_config.name)
        assert sample_monitor_config.name not in manager.configs

    def test_get_config(self, temp_config_dir, sample_monitor_config):
        """Test configuration retrieval."""
        manager = EmailMetricsManager(str(temp_config_dir))
        manager.create_config(sample_monitor_config)
        config = manager.get_config(sample_monitor_config.name)
        assert config.name == sample_monitor_config.name

    def test_list_configs(self, temp_config_dir, sample_monitor_config):
        """Test configuration listing."""
        manager = EmailMetricsManager(str(temp_config_dir))
        manager.create_config(sample_monitor_config)
        configs = manager.list_configs()
        assert sample_monitor_config.name in configs

    @patch("imaplib.IMAP4_SSL")
    def test_collect_metrics(self, mock_imap, temp_config_dir, sample_monitor_config):
        """Test metric collection."""
        # Mock IMAP responses
        mock_imap.return_value.search.return_value = (None, [b"1 2 3"])
        mock_imap.return_value.fetch.return_value = (None, [(None, b"")])

        manager = EmailMetricsManager(str(temp_config_dir))
        manager.create_config(sample_monitor_config)

        metrics = manager.collect_metrics(
            sample_monitor_config.name, "imap.gmail.com", "test@gmail.com", "password"
        )
        assert isinstance(metrics, dict)

    def test_analyze_metrics(self, temp_config_dir, sample_monitor_config):
        """Test metric analysis."""
        manager = EmailMetricsManager(str(temp_config_dir))
        manager.create_config(sample_monitor_config)

        # Create sample metrics data
        metrics_data = [
            {"inbox_volume": 100, "response_time": 1800},
            {"inbox_volume": 120, "response_time": 2000},
            {"inbox_volume": 90, "response_time": 1600},
        ]

        result = manager.analyze_metrics(metrics_data, sample_monitor_config)
        assert isinstance(result, dict)
        assert "statistics" in result
        assert "anomalies" in result
        assert "recommendations" in result


class TestInboxMonitor:
    """Test cases for InboxMonitor."""

    def test_init(self, temp_config_dir):
        """Test initialization."""
        monitor = InboxMonitor(str(temp_config_dir))
        assert monitor.config_dir == temp_config_dir
        assert isinstance(monitor.configs, dict)
        assert len(monitor.configs) == 0

    def test_create_config(
        self, temp_config_dir, sample_filter_config, sample_alert_config
    ):
        """Test configuration creation."""
        monitor = InboxMonitor(str(temp_config_dir))
        config = MonitorConfig(
            name="gmail_monitor",
            filters=[sample_filter_config],
            alerts=[sample_alert_config],
            check_interval=300,
            retention_days=30,
        )
        assert monitor.create_config(config)
        assert config.name in monitor.configs

    def test_update_config(
        self, temp_config_dir, sample_filter_config, sample_alert_config
    ):
        """Test configuration update."""
        monitor = InboxMonitor(str(temp_config_dir))
        config = MonitorConfig(
            name="gmail_monitor",
            filters=[sample_filter_config],
            alerts=[sample_alert_config],
            check_interval=300,
            retention_days=30,
        )
        monitor.create_config(config)

        updated_config = MonitorConfig(
            name=config.name,
            filters=config.filters,
            alerts=config.alerts,
            check_interval=600,
            retention_days=60,
        )
        assert monitor.update_config(config.name, updated_config)
        assert monitor.configs[config.name].check_interval == 600

    def test_delete_config(
        self, temp_config_dir, sample_filter_config, sample_alert_config
    ):
        """Test configuration deletion."""
        monitor = InboxMonitor(str(temp_config_dir))
        config = MonitorConfig(
            name="gmail_monitor",
            filters=[sample_filter_config],
            alerts=[sample_alert_config],
            check_interval=300,
            retention_days=30,
        )
        monitor.create_config(config)
        assert monitor.delete_config(config.name)
        assert config.name not in monitor.configs

    def test_get_config(
        self, temp_config_dir, sample_filter_config, sample_alert_config
    ):
        """Test configuration retrieval."""
        monitor = InboxMonitor(str(temp_config_dir))
        config = MonitorConfig(
            name="gmail_monitor",
            filters=[sample_filter_config],
            alerts=[sample_alert_config],
            check_interval=300,
            retention_days=30,
        )
        monitor.create_config(config)
        retrieved_config = monitor.get_config(config.name)
        assert retrieved_config.name == config.name

    def test_list_configs(
        self, temp_config_dir, sample_filter_config, sample_alert_config
    ):
        """Test configuration listing."""
        monitor = InboxMonitor(str(temp_config_dir))
        config = MonitorConfig(
            name="gmail_monitor",
            filters=[sample_filter_config],
            alerts=[sample_alert_config],
            check_interval=300,
            retention_days=30,
        )
        monitor.create_config(config)
        configs = monitor.list_configs()
        assert config.name in configs

    @patch("imaplib.IMAP4_SSL")
    def test_apply_filters(
        self, mock_imap, temp_config_dir, sample_filter_config, sample_alert_config
    ):
        """Test filter application."""
        # Mock IMAP responses
        mock_imap.return_value.search.return_value = (None, [b"1 2 3"])
        mock_imap.return_value.fetch.return_value = (None, [(None, b"")])

        monitor = InboxMonitor(str(temp_config_dir))
        config = MonitorConfig(
            name="gmail_monitor",
            filters=[sample_filter_config],
            alerts=[sample_alert_config],
            check_interval=300,
            retention_days=30,
        )
        monitor.create_config(config)

        monitor.apply_filters(mock_imap.return_value, config)
        mock_imap.return_value.select.assert_called()
        mock_imap.return_value.search.assert_called()

    @patch("imaplib.IMAP4_SSL")
    def test_check_alerts(
        self, mock_imap, temp_config_dir, sample_filter_config, sample_alert_config
    ):
        """Test alert checking."""
        # Mock IMAP responses
        mock_imap.return_value.search.return_value = (None, [b"1 2 3"])
        mock_imap.return_value.fetch.return_value = (None, [(None, b"")])

        monitor = InboxMonitor(str(temp_config_dir))
        config = MonitorConfig(
            name="gmail_monitor",
            filters=[sample_filter_config],
            alerts=[sample_alert_config],
            check_interval=300,
            retention_days=30,
        )
        monitor.create_config(config)

        monitor.check_alerts(mock_imap.return_value, config)
        assert not monitor.alert_queue.empty()

    @patch("imaplib.IMAP4_SSL")
    def test_start_stop_monitoring(
        self, mock_imap, temp_config_dir, sample_filter_config, sample_alert_config
    ):
        """Test monitoring start and stop."""
        # Mock IMAP responses
        mock_imap.return_value.search.return_value = (None, [b"1 2 3"])
        mock_imap.return_value.fetch.return_value = (None, [(None, b"")])

        monitor = InboxMonitor(str(temp_config_dir))
        config = MonitorConfig(
            name="gmail_monitor",
            filters=[sample_filter_config],
            alerts=[sample_alert_config],
            check_interval=300,
            retention_days=30,
        )
        monitor.create_config(config)

        monitor.start_monitoring(
            config.name, "imap.gmail.com", "test@gmail.com", "password"
        )
        assert monitor.is_running

        monitor.stop_monitoring()
        assert not monitor.is_running
