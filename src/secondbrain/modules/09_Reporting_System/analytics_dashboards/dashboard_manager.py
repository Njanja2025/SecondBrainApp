"""
Dashboard manager for handling analytics dashboards.
Manages dashboard layouts, widgets, and data visualization.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DashboardConfig:
    """Configuration for analytics dashboards."""

    name: str
    layout: List[Dict[str, Any]]
    widgets: List[Dict[str, Any]]
    refresh_interval: int = 300  # seconds
    theme: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    description: str = None


class DashboardManager:
    """Manages analytics dashboards and visualizations."""

    def __init__(self, config_dir: str = "config/dashboards"):
        """Initialize the dashboard manager.

        Args:
            config_dir: Directory to store dashboard configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()

    def _setup_logging(self):
        """Set up logging for the dashboard manager."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_configs(self):
        """Load dashboard configurations."""
        try:
            config_file = self.config_dir / "dashboard_configs.json"

            if config_file.exists():
                with open(config_file, "r") as f:
                    self.configs = {
                        name: DashboardConfig(**config)
                        for name, config in json.load(f).items()
                    }
            else:
                self.configs = {}
                self._save_configs()

            logger.info("Dashboard configurations loaded")

        except Exception as e:
            logger.error(f"Failed to load dashboard configurations: {str(e)}")
            raise

    def _save_configs(self):
        """Save dashboard configurations."""
        try:
            config_file = self.config_dir / "dashboard_configs.json"

            with open(config_file, "w") as f:
                json.dump(
                    {name: vars(config) for name, config in self.configs.items()},
                    f,
                    indent=2,
                )

        except Exception as e:
            logger.error(f"Failed to save dashboard configurations: {str(e)}")

    def create_config(self, config: DashboardConfig) -> bool:
        """Create a new dashboard configuration.

        Args:
            config: Dashboard configuration

        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False

            self.configs[config.name] = config
            self._save_configs()

            logger.info(f"Created dashboard configuration {config.name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to create dashboard configuration {config.name}: {str(e)}"
            )
            return False

    def update_config(self, name: str, config: DashboardConfig) -> bool:
        """Update an existing dashboard configuration.

        Args:
            name: Configuration name
            config: New dashboard configuration

        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False

            self.configs[name] = config
            self._save_configs()

            logger.info(f"Updated dashboard configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update dashboard configuration {name}: {str(e)}")
            return False

    def delete_config(self, name: str) -> bool:
        """Delete a dashboard configuration.

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

            logger.info(f"Deleted dashboard configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete dashboard configuration {name}: {str(e)}")
            return False

    def get_config(self, name: str) -> Optional[DashboardConfig]:
        """Get dashboard configuration.

        Args:
            name: Configuration name

        Returns:
            Dashboard configuration if found
        """
        return self.configs.get(name)

    def list_configs(self) -> List[str]:
        """List all dashboard configurations.

        Returns:
            List of configuration names
        """
        return list(self.configs.keys())

    def render_dashboard(
        self, config_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Render a dashboard with data.

        Args:
            config_name: Configuration name
            data: Dashboard data

        Returns:
            Rendered dashboard if successful
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return None

            # Create dashboard layout
            dashboard = {
                "name": config.name,
                "layout": config.layout,
                "widgets": [],
                "theme": config.theme or {},
                "metadata": config.metadata or {},
            }

            # Render widgets
            for widget in config.widgets:
                rendered_widget = self._render_widget(widget, data)
                if rendered_widget:
                    dashboard["widgets"].append(rendered_widget)

            logger.info(f"Rendered dashboard {config_name}")
            return dashboard

        except Exception as e:
            logger.error(f"Failed to render dashboard {config_name}: {str(e)}")
            return None

    def _render_widget(
        self, widget: Dict[str, Any], data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Render a dashboard widget.

        Args:
            widget: Widget configuration
            data: Widget data

        Returns:
            Rendered widget if successful
        """
        try:
            widget_type = widget["type"]
            widget_data = data.get(widget["data_key"], {})

            if widget_type == "line_chart":
                return self._create_line_chart(widget, widget_data)
            elif widget_type == "bar_chart":
                return self._create_bar_chart(widget, widget_data)
            elif widget_type == "pie_chart":
                return self._create_pie_chart(widget, widget_data)
            elif widget_type == "table":
                return self._create_table(widget, widget_data)
            elif widget_type == "metric":
                return self._create_metric(widget, widget_data)
            else:
                logger.error(f"Unsupported widget type: {widget_type}")
                return None

        except Exception as e:
            logger.error(f"Failed to render widget: {str(e)}")
            return None

    def _create_line_chart(
        self, widget: Dict[str, Any], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a line chart widget.

        Args:
            widget: Widget configuration
            data: Widget data

        Returns:
            Line chart widget
        """
        try:
            df = pd.DataFrame(data)
            fig = px.line(
                df,
                x=widget["x_axis"],
                y=widget["y_axis"],
                title=widget.get("title", ""),
            )

            return {
                "type": "line_chart",
                "title": widget.get("title", ""),
                "data": fig.to_json(),
            }

        except Exception as e:
            logger.error(f"Failed to create line chart: {str(e)}")
            return None

    def _create_bar_chart(
        self, widget: Dict[str, Any], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a bar chart widget.

        Args:
            widget: Widget configuration
            data: Widget data

        Returns:
            Bar chart widget
        """
        try:
            df = pd.DataFrame(data)
            fig = px.bar(
                df,
                x=widget["x_axis"],
                y=widget["y_axis"],
                title=widget.get("title", ""),
            )

            return {
                "type": "bar_chart",
                "title": widget.get("title", ""),
                "data": fig.to_json(),
            }

        except Exception as e:
            logger.error(f"Failed to create bar chart: {str(e)}")
            return None

    def _create_pie_chart(
        self, widget: Dict[str, Any], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a pie chart widget.

        Args:
            widget: Widget configuration
            data: Widget data

        Returns:
            Pie chart widget
        """
        try:
            df = pd.DataFrame(data)
            fig = px.pie(
                df,
                values=widget["values"],
                names=widget["names"],
                title=widget.get("title", ""),
            )

            return {
                "type": "pie_chart",
                "title": widget.get("title", ""),
                "data": fig.to_json(),
            }

        except Exception as e:
            logger.error(f"Failed to create pie chart: {str(e)}")
            return None

    def _create_table(
        self, widget: Dict[str, Any], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a table widget.

        Args:
            widget: Widget configuration
            data: Widget data

        Returns:
            Table widget
        """
        try:
            df = pd.DataFrame(data)

            return {
                "type": "table",
                "title": widget.get("title", ""),
                "data": df.to_dict("records"),
                "columns": widget.get("columns", list(df.columns)),
            }

        except Exception as e:
            logger.error(f"Failed to create table: {str(e)}")
            return None

    def _create_metric(
        self, widget: Dict[str, Any], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a metric widget.

        Args:
            widget: Widget configuration
            data: Widget data

        Returns:
            Metric widget
        """
        try:
            value = data.get(widget["value_key"], 0)
            change = data.get(widget.get("change_key"), 0)

            return {
                "type": "metric",
                "title": widget.get("title", ""),
                "value": value,
                "change": change,
                "format": widget.get("format", "number"),
            }

        except Exception as e:
            logger.error(f"Failed to create metric: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    manager = DashboardManager()

    # Create dashboard configuration
    config = DashboardConfig(
        name="user_analytics",
        layout=[
            {
                "type": "grid",
                "rows": 2,
                "columns": 2,
                "widgets": [
                    {"id": "user_activity", "row": 0, "col": 0},
                    {"id": "user_distribution", "row": 0, "col": 1},
                    {"id": "user_metrics", "row": 1, "col": 0},
                    {"id": "user_table", "row": 1, "col": 1},
                ],
            }
        ],
        widgets=[
            {
                "id": "user_activity",
                "type": "line_chart",
                "title": "User Activity",
                "data_key": "activity",
                "x_axis": "date",
                "y_axis": "count",
            },
            {
                "id": "user_distribution",
                "type": "pie_chart",
                "title": "User Distribution",
                "data_key": "distribution",
                "values": "count",
                "names": "category",
            },
            {
                "id": "user_metrics",
                "type": "metric",
                "title": "Total Users",
                "data_key": "metrics",
                "value_key": "total_users",
                "change_key": "user_change",
            },
            {
                "id": "user_table",
                "type": "table",
                "title": "Recent Users",
                "data_key": "users",
                "columns": ["username", "email", "created_at"],
            },
        ],
        theme={"colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"], "font": "Arial"},
        description="User analytics dashboard",
    )
    manager.create_config(config)

    # Render dashboard
    data = {
        "activity": [
            {"date": "2024-01-01", "count": 10},
            {"date": "2024-01-02", "count": 15},
            {"date": "2024-01-03", "count": 20},
        ],
        "distribution": [
            {"category": "Active", "count": 60},
            {"category": "Inactive", "count": 40},
        ],
        "metrics": {"total_users": 100, "user_change": 5},
        "users": [
            {
                "username": "john_doe",
                "email": "john@example.com",
                "created_at": "2024-01-01",
            },
            {
                "username": "jane_doe",
                "email": "jane@example.com",
                "created_at": "2024-01-02",
            },
        ],
    }
    dashboard = manager.render_dashboard("user_analytics", data)
    print(json.dumps(dashboard, indent=2))
