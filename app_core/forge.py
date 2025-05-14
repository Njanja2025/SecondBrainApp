"""
Forge Manager - Customization and Extension System
Handles plugins, extensions, and customization of the SecondBrain app.
"""

import logging
import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class ForgeManager:
    """Manages plugins, extensions, and customization."""

    def __init__(self, plugins_dir: Optional[str] = None):
        """Initialize the forge manager."""
        self.plugins_dir = Path(plugins_dir or "plugins")
        self.plugins: Dict[str, Any] = {}
        self.extensions: Dict[str, Any] = {}
        self._setup()

    def _setup(self) -> None:
        """Set up the forge system."""
        try:
            # Create plugins directory if it doesn't exist
            self.plugins_dir.mkdir(parents=True, exist_ok=True)

            # Load any existing plugins
            self._load_plugins()
            logger.info("Forge manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize forge manager: {e}")
            raise

    def _load_plugins(self) -> None:
        """Load all plugins from the plugins directory."""
        try:
            for plugin_file in self.plugins_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue

                module_name = plugin_file.stem
                try:
                    module = importlib.import_module(f"plugins.{module_name}")
                    self._register_plugin(module)
                except Exception as e:
                    logger.error(f"Failed to load plugin {module_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to load plugins: {e}")

    def _register_plugin(self, module: Any) -> None:
        """Register a plugin module."""
        try:
            # Look for plugin class in module
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and hasattr(obj, "is_plugin") and obj.is_plugin:
                    self.plugins[name] = obj()
                    logger.info(f"Registered plugin: {name}")
        except Exception as e:
            logger.error(f"Failed to register plugin: {e}")

    def register_extension(self, name: str, extension: Any) -> bool:
        """Register a new extension."""
        try:
            self.extensions[name] = extension
            logger.info(f"Registered extension: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register extension: {e}")
            return False

    def get_plugin(self, name: str) -> Optional[Any]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def get_extension(self, name: str) -> Optional[Any]:
        """Get an extension by name."""
        return self.extensions.get(name)

    def list_plugins(self) -> List[str]:
        """List all registered plugins."""
        return list(self.plugins.keys())

    def list_extensions(self) -> List[str]:
        """List all registered extensions."""
        return list(self.extensions.keys())
