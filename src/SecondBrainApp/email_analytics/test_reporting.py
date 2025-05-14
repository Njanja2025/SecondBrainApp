"""
Tests for the email analytics reporting module.
"""

import os
import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from reporting import (
    EmailReportManager,
    ReportFormat,
    ReportTemplate,
    ChartConfig,
    ChartType,
)
from visualization import EmailVisualizer
from email_metrics import EmailMetricsManager


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary configuration directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    return str(config_dir)


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    dates = pd.date_range(start="2024-01-01", end="2024-01-31", freq="D")
    return {
        "emails": [
            {
                "from": f"user{i}@example.com",
                "to": [f"user{j}@example.com" for j in range(1, 4)],
                "subject": f"Test email {i}",
                "body": f"This is test email {i}",
                "date": datetime.now() - timedelta(days=i),
                "thread_id": f"thread{i}",
            }
            for i in range(1, 11)
        ],
        "metrics": {
            "response_rate": 75.0,
            "avg_response_time": 3600,
            "avg_sentiment": 0.5,
        },
        "anomalies": [
            {
                "metric": "response_time",
                "value": 7200,
                "z_score": 3.5,
                "timestamp": datetime.now(),
            }
        ],
        "recommendations": [
            "Response Time: Consider improving response time for urgent emails."
        ],
        "volume_metrics": pd.DataFrame(
            {"dates": dates, "values": np.random.randint(10, 100, size=len(dates))}
        ),
        "response_metrics": pd.DataFrame(
            {"times": range(24), "counts": np.random.randint(1, 50, size=24)}
        ),
        "sentiment_metrics": pd.Series(
            [0.3, 0.5, 0.2], index=["Positive", "Neutral", "Negative"]
        ),
        "category_metrics": pd.Series(
            [40, 30, 20, 10], index=["Work", "Personal", "Newsletter", "Other"]
        ),
        "network_metrics": {
            "x": np.random.rand(10),
            "y": np.random.rand(10),
            "labels": [f"User {i}" for i in range(10)],
        },
    }


@pytest.fixture
def sample_template():
    """Create sample report template."""
    return ReportTemplate(
        name="test_report",
        format=ReportFormat.HTML,
        template_path="templates/email_report.html",
        sections=["overview", "metrics", "anomalies", "recommendations"],
        charts=[
            ChartConfig(
                name="volume_metrics",
                type=ChartType.LINE,
                title="Email Volume Over Time",
            ),
            ChartConfig(
                name="response_metrics",
                type=ChartType.BAR,
                title="Response Rate Distribution",
            ),
        ],
    )


class TestEmailReportManager:
    """Test cases for EmailReportManager class."""

    def test_init(self, temp_config_dir):
        """Test initialization."""
        manager = EmailReportManager(temp_config_dir)
        assert manager.config_dir == Path(temp_config_dir)
        assert isinstance(manager.metrics_manager, EmailMetricsManager)
        assert isinstance(manager.visualizer, EmailVisualizer)

    def test_generate_report(self, temp_config_dir, sample_data, sample_template):
        """Test report generation."""
        manager = EmailReportManager(temp_config_dir)
        output_path = str(Path(temp_config_dir) / "reports" / "test_report.html")

        report_path = manager.generate_report(sample_data, sample_template, output_path)

        assert report_path is not None
        assert Path(report_path).exists()
        assert Path(report_path).suffix == ".html"

    def test_generate_summary(self, temp_config_dir, sample_data):
        """Test summary generation."""
        manager = EmailReportManager(temp_config_dir)
        summary = manager.generate_summary(sample_data)

        assert "overview" in summary
        assert "metrics" in summary
        assert "anomalies" in summary
        assert "recommendations" in summary

        assert summary["overview"]["total_emails"] == 10
        assert summary["metrics"]["response_rate"] == 75.0
        assert summary["anomalies"]["count"] == 1

    def test_generate_dashboard(self, temp_config_dir, sample_data, sample_template):
        """Test dashboard generation."""
        manager = EmailReportManager(temp_config_dir)
        output_path = str(Path(temp_config_dir) / "reports" / "test_dashboard.html")

        dashboard_path = manager.generate_dashboard(
            sample_data, sample_template, output_path
        )

        assert dashboard_path is not None
        assert Path(dashboard_path).exists()
        assert Path(dashboard_path).suffix == ".html"

    def test_invalid_template(self, temp_config_dir, sample_data):
        """Test report generation with invalid template."""
        manager = EmailReportManager(temp_config_dir)
        invalid_template = ReportTemplate(
            name="invalid",
            format="invalid",
            template_path="nonexistent.html",
            sections=[],
            charts=[],
        )

        with pytest.raises(Exception):
            manager.generate_report(
                sample_data, invalid_template, "reports/invalid.html"
            )

    def test_missing_data(self, temp_config_dir, sample_template):
        """Test report generation with missing data."""
        manager = EmailReportManager(temp_config_dir)
        empty_data = {}

        with pytest.raises(Exception):
            manager.generate_report(empty_data, sample_template, "reports/empty.html")

    def test_different_formats(self, temp_config_dir, sample_data, sample_template):
        """Test report generation in different formats."""
        manager = EmailReportManager(temp_config_dir)
        formats = [
            (ReportFormat.HTML, ".html"),
            (ReportFormat.PDF, ".pdf"),
            (ReportFormat.MARKDOWN, ".md"),
            (ReportFormat.CSV, ".csv"),
            (ReportFormat.YAML, ".yaml"),
        ]

        for format_type, extension in formats:
            template = ReportTemplate(
                name=f"test_{format_type}",
                format=format_type,
                template_path=f"templates/email_report.{format_type}",
                sections=sample_template.sections,
                charts=sample_template.charts,
            )

            output_path = str(Path(temp_config_dir) / "reports" / f"test{extension}")
            report_path = manager.generate_report(sample_data, template, output_path)

            assert report_path is not None
            assert Path(report_path).exists()
            assert Path(report_path).suffix == extension


if __name__ == "__main__":
    pytest.main([__file__])
