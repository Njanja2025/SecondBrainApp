"""
Navigation manager for handling UI navigation and routing.
Manages page transitions, tab switching, and navigation state.
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
class NavConfig:
    """Configuration for navigation and routing."""

    name: str
    routes: Dict[str, str]
    transitions: Dict[str, Any]
    tabs: List[Dict[str, Any]]
    default_route: str
    default_tab: str
    history_size: int = 50


class NavigationManager:
    """Manages UI navigation and routing."""

    def __init__(self, config_dir: str = "config/navigation"):
        """Initialize the navigation manager.

        Args:
            config_dir: Directory to store navigation configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self._init_history()

    def _setup_logging(self):
        """Set up logging for the navigation manager."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_configs(self):
        """Load navigation configurations."""
        try:
            config_file = self.config_dir / "nav_configs.json"

            if config_file.exists():
                with open(config_file, "r") as f:
                    self.configs = {
                        name: NavConfig(**config)
                        for name, config in json.load(f).items()
                    }
            else:
                self.configs = {}
                self._save_configs()

            logger.info("Navigation configurations loaded")

        except Exception as e:
            logger.error(f"Failed to load navigation configurations: {str(e)}")
            raise

    def _save_configs(self):
        """Save navigation configurations."""
        try:
            config_file = self.config_dir / "nav_configs.json"

            with open(config_file, "w") as f:
                json.dump(
                    {name: vars(config) for name, config in self.configs.items()},
                    f,
                    indent=2,
                )

        except Exception as e:
            logger.error(f"Failed to save navigation configurations: {str(e)}")

    def _init_history(self):
        """Initialize navigation history."""
        self.history = []
        self.current_index = -1

    def create_config(self, config: NavConfig) -> bool:
        """Create a new navigation configuration.

        Args:
            config: Navigation configuration

        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False

            self.configs[config.name] = config
            self._save_configs()

            logger.info(f"Created navigation configuration {config.name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to create navigation configuration {config.name}: {str(e)}"
            )
            return False

    def update_config(self, name: str, config: NavConfig) -> bool:
        """Update an existing navigation configuration.

        Args:
            name: Configuration name
            config: New navigation configuration

        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False

            self.configs[name] = config
            self._save_configs()

            logger.info(f"Updated navigation configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update navigation configuration {name}: {str(e)}")
            return False

    def delete_config(self, name: str) -> bool:
        """Delete a navigation configuration.

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

            logger.info(f"Deleted navigation configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete navigation configuration {name}: {str(e)}")
            return False

    def get_config(self, name: str) -> Optional[NavConfig]:
        """Get navigation configuration.

        Args:
            name: Configuration name

        Returns:
            Navigation configuration if found
        """
        return self.configs.get(name)

    def list_configs(self) -> List[str]:
        """List all navigation configurations.

        Returns:
            List of configuration names
        """
        return list(self.configs.keys())

    def navigate_to(
        self, config_name: str, route: str, params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Navigate to a route.

        Args:
            config_name: Configuration name
            route: Route to navigate to
            params: Optional route parameters

        Returns:
            bool: True if navigation was successful
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return False

            if route not in config.routes:
                logger.error(f"Route {route} not found in configuration {config_name}")
                return False

            # Add to history
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "route": route,
                "params": params,
            }

            # Remove future history if we're not at the end
            if self.current_index < len(self.history) - 1:
                self.history = self.history[: self.current_index + 1]

            self.history.append(history_entry)
            self.current_index = len(self.history) - 1

            # Trim history if needed
            if len(self.history) > config.history_size:
                self.history = self.history[-config.history_size :]
                self.current_index = len(self.history) - 1

            logger.info(f"Navigated to route {route} in configuration {config_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to navigate to route {route}: {str(e)}")
            return False

    def go_back(self, config_name: str) -> bool:
        """Navigate back in history.

        Args:
            config_name: Configuration name

        Returns:
            bool: True if navigation was successful
        """
        try:
            if self.current_index <= 0:
                logger.error("No history to go back to")
                return False

            self.current_index -= 1
            history_entry = self.history[self.current_index]

            logger.info(f"Navigated back to route {history_entry['route']}")
            return True

        except Exception as e:
            logger.error(f"Failed to navigate back: {str(e)}")
            return False

    def go_forward(self, config_name: str) -> bool:
        """Navigate forward in history.

        Args:
            config_name: Configuration name

        Returns:
            bool: True if navigation was successful
        """
        try:
            if self.current_index >= len(self.history) - 1:
                logger.error("No history to go forward to")
                return False

            self.current_index += 1
            history_entry = self.history[self.current_index]

            logger.info(f"Navigated forward to route {history_entry['route']}")
            return True

        except Exception as e:
            logger.error(f"Failed to navigate forward: {str(e)}")
            return False

    def switch_tab(self, config_name: str, tab_id: str) -> bool:
        """Switch to a different tab.

        Args:
            config_name: Configuration name
            tab_id: Tab ID to switch to

        Returns:
            bool: True if tab switch was successful
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return False

            # Find tab
            tab = next((t for t in config.tabs if t.get("id") == tab_id), None)
            if not tab:
                logger.error(f"Tab {tab_id} not found in configuration {config_name}")
                return False

            logger.info(f"Switched to tab {tab_id} in configuration {config_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to switch to tab {tab_id}: {str(e)}")
            return False

    def get_current_route(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Get current route information.

        Args:
            config_name: Configuration name

        Returns:
            Current route information if available
        """
        try:
            if not self.history or self.current_index < 0:
                return None

            return self.history[self.current_index]

        except Exception as e:
            logger.error(f"Failed to get current route: {str(e)}")
            return None

    def get_navigation_history(self, config_name: str) -> List[Dict[str, Any]]:
        """Get navigation history.

        Args:
            config_name: Configuration name

        Returns:
            List of navigation history entries
        """
        return self.history.copy()


# Example usage
if __name__ == "__main__":
    manager = NavigationManager()

    # Create navigation configuration
    config = NavConfig(
        name="main",
        routes={"home": "/home", "settings": "/settings", "profile": "/profile"},
        transitions={"fade": {"duration": 0.3, "easing": "ease-in-out"}},
        tabs=[
            {"id": "dashboard", "name": "Dashboard", "icon": "dashboard.svg"},
            {"id": "tasks", "name": "Tasks", "icon": "tasks.svg"},
        ],
        default_route="home",
        default_tab="dashboard",
    )
    manager.create_config(config)

    # Navigate to a route
    manager.navigate_to("main", "settings", {"section": "general"})

    # Switch tabs
    manager.switch_tab("main", "tasks")

    # Get current route
    current_route = manager.get_current_route("main")
    print("Current route:", current_route)
