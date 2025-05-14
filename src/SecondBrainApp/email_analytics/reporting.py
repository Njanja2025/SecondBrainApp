"""
Email Analytics Reporting for SecondBrain application.
Provides report generation and formatting capabilities.
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
from jinja2 import Template
import pdfkit
import markdown
import csv
import yaml
from email_metrics import EmailMetricsManager
from visualization import EmailVisualizer, ChartConfig, ChartType

logger = logging.getLogger(__name__)


class ReportFormat:
    """Formats for report generation."""

    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    CSV = "csv"
    YAML = "yaml"
    CUSTOM = "custom"


@dataclass
class ReportTemplate:
    """Template for report generation."""

    name: str
    format: str
    template_path: str
    sections: List[str]
    charts: List[ChartConfig]
    metadata: Dict[str, Any] = None


class EmailReportManager:
    """Manages email analytics report generation."""

    def __init__(self, config_dir: str = "config/email"):
        """Initialize the email report manager.

        Args:
            config_dir: Directory to store configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self.metrics_manager = EmailMetricsManager(config_dir)
        self.visualizer = EmailVisualizer(config_dir)

    def _setup_logging(self):
        """Set up logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_configs(self):
        """Load configurations."""
        try:
            config_file = self.config_dir / "reporting.json"
            if config_file.exists():
                with open(config_file, "r") as f:
                    self.configs = json.load(f)
            else:
                self.configs = {}
                self._save_configs()
        except Exception as e:
            logger.error(f"Failed to load configurations: {str(e)}")
            raise

    def _save_configs(self):
        """Save configurations."""
        try:
            config_file = self.config_dir / "reporting.json"
            with open(config_file, "w") as f:
                json.dump(self.configs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save configurations: {str(e)}")

    def generate_report(
        self, data: Dict[str, Any], template: ReportTemplate, output_path: str
    ) -> str:
        """Generate report from data using template.

        Args:
            data: Report data
            template: Report template
            output_path: Output file path

        Returns:
            Path to generated report
        """
        try:
            # Load template
            with open(template.template_path, "r") as f:
                template_content = f.read()

            # Generate charts
            charts = {}
            for chart_config in template.charts:
                if chart_config.type == ChartType.LINE:
                    fig = self.visualizer.create_time_series(
                        data.get(chart_config.name, pd.DataFrame()), chart_config
                    )
                elif chart_config.type == ChartType.BAR:
                    fig = self.visualizer.create_bar_chart(
                        data.get(chart_config.name, pd.DataFrame()), chart_config
                    )
                elif chart_config.type == ChartType.PIE:
                    fig = self.visualizer.create_pie_chart(
                        data.get(chart_config.name, pd.Series()), chart_config
                    )
                elif chart_config.type == ChartType.HEATMAP:
                    fig = self.visualizer.create_heatmap(
                        data.get(chart_config.name, pd.DataFrame()), chart_config
                    )
                elif chart_config.type == ChartType.NETWORK:
                    fig = self.visualizer.create_network_graph(
                        data.get(chart_config.name, nx.Graph()), chart_config
                    )
                elif chart_config.type == ChartType.WORDCLOUD:
                    fig = self.visualizer.create_wordcloud(
                        data.get(chart_config.name, ""), chart_config
                    )

                if fig:
                    chart_path = self.visualizer.save_chart(
                        fig, f"{template.name}_{chart_config.name}", format="png"
                    )
                    charts[chart_config.name] = chart_path

            # Render template
            template = Template(template_content)
            rendered = template.render(
                data=data, charts=charts, timestamp=datetime.now()
            )

            # Save report
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if template.format == ReportFormat.HTML:
                with open(output_path, "w") as f:
                    f.write(rendered)

            elif template.format == ReportFormat.PDF:
                pdfkit.from_string(rendered, str(output_path))

            elif template.format == ReportFormat.MARKDOWN:
                with open(output_path, "w") as f:
                    f.write(rendered)

            elif template.format == ReportFormat.CSV:
                df = pd.DataFrame(data)
                df.to_csv(output_path, index=False)

            elif template.format == ReportFormat.YAML:
                with open(output_path, "w") as f:
                    yaml.dump(data, f)

            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            return None

    def generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of report data.

        Args:
            data: Report data

        Returns:
            Summary data
        """
        try:
            summary = {}

            # Overview
            summary["overview"] = {
                "total_emails": len(data.get("emails", [])),
                "total_threads": len(
                    set(e.get("thread_id") for e in data.get("emails", []))
                ),
                "date_range": {
                    "start": min(e.get("date") for e in data.get("emails", [])),
                    "end": max(e.get("date") for e in data.get("emails", [])),
                },
            }

            # Metrics summary
            metrics = data.get("metrics", {})
            summary["metrics"] = {
                "response_rate": metrics.get("response_rate", 0),
                "avg_response_time": metrics.get("avg_response_time", 0),
                "sentiment_score": metrics.get("avg_sentiment", 0),
            }

            # Anomalies summary
            anomalies = data.get("anomalies", [])
            summary["anomalies"] = {
                "count": len(anomalies),
                "types": list(set(a.get("metric") for a in anomalies)),
            }

            # Recommendations summary
            recommendations = data.get("recommendations", [])
            summary["recommendations"] = {
                "count": len(recommendations),
                "categories": list(set(r.split(":")[0] for r in recommendations)),
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            return {}

    def generate_dashboard(
        self, data: Dict[str, Any], template: ReportTemplate, output_path: str
    ) -> str:
        """Generate interactive dashboard.

        Args:
            data: Dashboard data
            template: Dashboard template
            output_path: Output file path

        Returns:
            Path to generated dashboard
        """
        try:
            # Create dashboard layout
            fig = make_subplots(
                rows=2,
                cols=2,
                subplot_titles=(
                    "Email Volume Over Time",
                    "Response Rate Distribution",
                    "Sentiment Analysis",
                    "Network Graph",
                ),
            )

            # Add time series
            dates = pd.date_range(
                start=data["overview"]["date_range"]["start"],
                end=data["overview"]["date_range"]["end"],
            )
            volume_data = pd.DataFrame(
                {
                    "Emails": data.get("volume_metrics", []),
                    "Responses": data.get("response_metrics", []),
                },
                index=dates,
            )

            fig.add_trace(
                go.Scatter(x=volume_data.index, y=volume_data["Emails"], name="Emails"),
                row=1,
                col=1,
            )

            # Add response rate
            response_data = pd.Series(data.get("response_rates", []))
            fig.add_trace(
                go.Bar(
                    x=response_data.index, y=response_data.values, name="Response Rate"
                ),
                row=1,
                col=2,
            )

            # Add sentiment
            sentiment_data = pd.Series(data.get("sentiment_scores", []))
            fig.add_trace(
                go.Pie(
                    labels=sentiment_data.index,
                    values=sentiment_data.values,
                    name="Sentiment",
                ),
                row=2,
                col=1,
            )

            # Add network graph
            G = nx.Graph(data.get("network_data", {}))
            pos = nx.spring_layout(G)

            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            fig.add_trace(
                go.Scatter(
                    x=edge_x,
                    y=edge_y,
                    line=dict(width=0.5, color="#888"),
                    hoverinfo="none",
                    mode="lines",
                    name="Network",
                ),
                row=2,
                col=2,
            )

            # Update layout
            fig.update_layout(
                title_text="Email Analytics Dashboard", height=800, showlegend=True
            )

            # Save dashboard
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(output_path))

            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to generate dashboard: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    manager = EmailReportManager()

    # Sample data
    data = {
        "emails": [
            {
                "from": "user1@example.com",
                "to": ["user2@example.com"],
                "subject": "Test email",
                "body": "This is a test email.",
                "date": datetime.now(),
                "thread_id": "thread1",
            }
        ],
        "metrics": {
            "response_rate": 75.0,
            "avg_response_time": 3600,
            "avg_sentiment": 0.5,
        },
        "anomalies": [{"metric": "response_time", "value": 7200, "z_score": 3.5}],
        "recommendations": [
            "Response Time: Consider improving response time for urgent emails."
        ],
    }

    # Create report template
    template = ReportTemplate(
        name="email_analytics",
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

    # Generate report
    report_path = manager.generate_report(
        data, template, "reports/email_analytics.html"
    )

    # Generate dashboard
    dashboard_path = manager.generate_dashboard(
        data, template, "reports/email_dashboard.html"
    )
