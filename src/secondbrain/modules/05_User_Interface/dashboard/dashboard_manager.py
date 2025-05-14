"""
Dashboard manager for handling main control panel views.
Manages widgets, layouts, and dashboard configurations.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DashboardConfig:
    """Configuration for dashboard layout and widgets."""

    name: str
    layout: Dict[str, Any]
    widgets: List[Dict[str, Any]]
    refresh_interval: int = 60
    theme: str = "default"
    permissions: List[str] = None


class DashboardManager:
    """Manages dashboard layouts and widgets."""

    def __init__(self, config_dir: str = "config/dashboard"):
        """Initialize the dashboard manager.

        Args:
            config_dir: Directory to store dashboard configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_dashboards()

    def _setup_logging(self):
        """Set up logging for the dashboard manager."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_dashboards(self):
        """Load dashboard configurations."""
        try:
            config_file = self.config_dir / "dashboards.json"

            if config_file.exists():
                with open(config_file, "r") as f:
                    self.dashboards = {
                        name: DashboardConfig(**config)
                        for name, config in json.load(f).items()
                    }
            else:
                self.dashboards = {}
                self._save_dashboards()

            logger.info("Dashboard configurations loaded")

        except Exception as e:
            logger.error(f"Failed to load dashboard configurations: {str(e)}")
            raise

    def _save_dashboards(self):
        """Save dashboard configurations."""
        try:
            config_file = self.config_dir / "dashboards.json"

            with open(config_file, "w") as f:
                json.dump(
                    {name: vars(config) for name, config in self.dashboards.items()},
                    f,
                    indent=2,
                )

        except Exception as e:
            logger.error(f"Failed to save dashboard configurations: {str(e)}")

    def create_dashboard(self, config: DashboardConfig) -> bool:
        """Create a new dashboard.

        Args:
            config: Dashboard configuration

        Returns:
            bool: True if dashboard was created successfully
        """
        try:
            if config.name in self.dashboards:
                logger.error(f"Dashboard {config.name} already exists")
                return False

            self.dashboards[config.name] = config
            self._save_dashboards()

            logger.info(f"Created dashboard {config.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create dashboard {config.name}: {str(e)}")
            return False

    def update_dashboard(self, name: str, config: DashboardConfig) -> bool:
        """Update an existing dashboard.

        Args:
            name: Dashboard name
            config: New dashboard configuration

        Returns:
            bool: True if dashboard was updated successfully
        """
        try:
            if name not in self.dashboards:
                logger.error(f"Dashboard {name} not found")
                return False

            self.dashboards[name] = config
            self._save_dashboards()

            logger.info(f"Updated dashboard {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update dashboard {name}: {str(e)}")
            return False

    def delete_dashboard(self, name: str) -> bool:
        """Delete a dashboard.

        Args:
            name: Dashboard name

        Returns:
            bool: True if dashboard was deleted successfully
        """
        try:
            if name not in self.dashboards:
                logger.error(f"Dashboard {name} not found")
                return False

            del self.dashboards[name]
            self._save_dashboards()

            logger.info(f"Deleted dashboard {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete dashboard {name}: {str(e)}")
            return False

    def get_dashboard(self, name: str) -> Optional[DashboardConfig]:
        """Get dashboard configuration.

        Args:
            name: Dashboard name

        Returns:
            Dashboard configuration if found
        """
        return self.dashboards.get(name)

    def list_dashboards(self) -> List[str]:
        """List all dashboards.

        Returns:
            List of dashboard names
        """
        return list(self.dashboards.keys())

    def add_widget(self, dashboard_name: str, widget: Dict[str, Any]) -> bool:
        """Add a widget to a dashboard.

        Args:
            dashboard_name: Dashboard name
            widget: Widget configuration

        Returns:
            bool: True if widget was added successfully
        """
        try:
            dashboard = self.get_dashboard(dashboard_name)
            if not dashboard:
                logger.error(f"Dashboard {dashboard_name} not found")
                return False

            dashboard.widgets.append(widget)
            self._save_dashboards()

            logger.info(f"Added widget to dashboard {dashboard_name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to add widget to dashboard {dashboard_name}: {str(e)}"
            )
            return False

    def remove_widget(self, dashboard_name: str, widget_id: str) -> bool:
        """Remove a widget from a dashboard.

        Args:
            dashboard_name: Dashboard name
            widget_id: Widget ID

        Returns:
            bool: True if widget was removed successfully
        """
        try:
            dashboard = self.get_dashboard(dashboard_name)
            if not dashboard:
                logger.error(f"Dashboard {dashboard_name} not found")
                return False

            dashboard.widgets = [
                w for w in dashboard.widgets if w.get("id") != widget_id
            ]
            self._save_dashboards()

            logger.info(f"Removed widget from dashboard {dashboard_name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to remove widget from dashboard {dashboard_name}: {str(e)}"
            )
            return False

    def update_layout(self, dashboard_name: str, layout: Dict[str, Any]) -> bool:
        """Update dashboard layout.

        Args:
            dashboard_name: Dashboard name
            layout: New layout configuration

        Returns:
            bool: True if layout was updated successfully
        """
        try:
            dashboard = self.get_dashboard(dashboard_name)
            if not dashboard:
                logger.error(f"Dashboard {dashboard_name} not found")
                return False

            dashboard.layout = layout
            self._save_dashboards()

            logger.info(f"Updated layout for dashboard {dashboard_name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to update layout for dashboard {dashboard_name}: {str(e)}"
            )
            return False


# Example usage
if __name__ == "__main__":
    manager = DashboardManager()

    # Create a dashboard
    config = DashboardConfig(
        name="main_dashboard",
        layout={"type": "grid", "columns": 3, "rows": 2},
        widgets=[
            {
                "id": "widget1",
                "type": "chart",
                "position": {"x": 0, "y": 0},
                "size": {"width": 2, "height": 1},
            }
        ],
    )
    manager.create_dashboard(config)

    # Add a widget
    widget = {
        "id": "widget2",
        "type": "table",
        "position": {"x": 2, "y": 1},
        "size": {"width": 1, "height": 1},
    }
    manager.add_widget("main_dashboard", widget)

    # Update layout
    layout = {"type": "grid", "columns": 4, "rows": 3}
    manager.update_layout("main_dashboard", layout)
