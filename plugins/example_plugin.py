"""
Example Plugin - Demonstrates the Forge Plugin System
A sample plugin that shows how to create and register plugins.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ExamplePlugin:
    """Example plugin demonstrating plugin capabilities."""

    is_plugin = True  # Required for plugin detection

    def __init__(self):
        """Initialize the example plugin."""
        self.name = "Example Plugin"
        self.version = "1.0.0"
        self.description = "A sample plugin for demonstration"
        self._setup()

    def _setup(self) -> None:
        """Set up the plugin."""
        try:
            logger.info(f"Initializing {self.name} v{self.version}")
            # Add any initialization code here
        except Exception as e:
            logger.error(f"Failed to initialize plugin: {e}")
            raise

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
        }

    def process_data(self, data: Any) -> Optional[Any]:
        """Process data through the plugin."""
        try:
            # Example data processing
            if isinstance(data, str):
                return data.upper()
            elif isinstance(data, (int, float)):
                return data * 2
            return None
        except Exception as e:
            logger.error(f"Failed to process data: {e}")
            return None

    def register_commands(self, voice_assistant: Any) -> None:
        """Register voice commands for this plugin."""
        try:
            voice_assistant.register_command("example", self._handle_example_command)
            voice_assistant.register_command("version", self._handle_version_command)
        except Exception as e:
            logger.error(f"Failed to register commands: {e}")

    def _handle_example_command(self) -> str:
        """Handle the 'example' voice command."""
        return "This is an example plugin command!"

    def _handle_version_command(self) -> str:
        """Handle the 'version' voice command."""
        return f"{self.name} version {self.version}"
