"""
Hotkey management module for SecondBrain
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
import keyboard
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Hotkey:
    """Manages global hotkeys for the application"""

    def __init__(self):
        self._hotkeys: Dict[str, Callable] = {}

    def register(self, key: str, callback: Callable) -> None:
        """Register a new hotkey"""
        if key in self._hotkeys:
            raise ValueError(f"Hotkey {key} is already registered")
        self._hotkeys[key] = callback
        keyboard.add_hotkey(key, callback)

    def unregister(self, key: str) -> None:
        """Unregister a hotkey"""
        if key in self._hotkeys:
            keyboard.remove_hotkey(key)
            del self._hotkeys[key]

    def clear(self) -> None:
        """Clear all registered hotkeys"""
        for key in list(self._hotkeys.keys()):
            self.unregister(key)

    def get_callback(self, key: str) -> Optional[Callable]:
        """Get the callback for a hotkey"""
        return self._hotkeys.get(key)

    def load_state(self):
        """Load hotkey state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    self.hotkeys = json.load(f)
                logger.info("Loaded hotkey state from file")
        except Exception as e:
            logger.error(f"Failed to load hotkey state: {e}")

    def save_state(self):
        """Save hotkey state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(self.hotkeys, f, indent=2)
            logger.info("Saved hotkey state to file")
        except Exception as e:
            logger.error(f"Failed to save hotkey state: {e}")

    def enable(self, name: str) -> bool:
        """
        Enable a hotkey.

        Args:
            name: Name of the hotkey to enable

        Returns:
            bool: True if enabling was successful
        """
        try:
            if name not in self.hotkeys:
                logger.warning(f"Hotkey {name} not found")
                return False

            if self.hotkeys[name]["enabled"]:
                logger.info(f"Hotkey {name} is already enabled")
                return True

            # Re-register with keyboard library
            keyboard.add_hotkey(
                self.hotkeys[name]["key_combination"], self.callbacks[name]
            )

            self.hotkeys[name]["enabled"] = True
            self.save_state()

            logger.info(f"Enabled hotkey {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to enable hotkey {name}: {e}")
            return False

    def disable(self, name: str) -> bool:
        """
        Disable a hotkey.

        Args:
            name: Name of the hotkey to disable

        Returns:
            bool: True if disabling was successful
        """
        try:
            if name not in self.hotkeys:
                logger.warning(f"Hotkey {name} not found")
                return False

            if not self.hotkeys[name]["enabled"]:
                logger.info(f"Hotkey {name} is already disabled")
                return True

            # Remove from keyboard library
            keyboard.remove_hotkey(self.hotkeys[name]["key_combination"])

            self.hotkeys[name]["enabled"] = False
            self.save_state()

            logger.info(f"Disabled hotkey {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to disable hotkey {name}: {e}")
            return False

    def trigger(self, name: str) -> bool:
        """
        Manually trigger a hotkey.

        Args:
            name: Name of the hotkey to trigger

        Returns:
            bool: True if trigger was successful
        """
        try:
            if name not in self.hotkeys:
                logger.warning(f"Hotkey {name} not found")
                return False

            if not self.hotkeys[name]["enabled"]:
                logger.warning(f"Hotkey {name} is disabled")
                return False

            # Call the callback
            self.callbacks[name]()

            # Update last triggered time
            self.hotkeys[name]["last_triggered"] = datetime.now().isoformat()
            self.save_state()

            logger.info(f"Triggered hotkey {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to trigger hotkey {name}: {e}")
            return False

    def get_hotkey(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a hotkey.

        Args:
            name: Name of the hotkey

        Returns:
            Optional[Dict[str, Any]]: Hotkey information if found
        """
        return self.hotkeys.get(name)

    def get_all_hotkeys(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all hotkeys.

        Returns:
            Dict[str, Dict[str, Any]]: All hotkey information
        """
        return self.hotkeys

    def get_enabled_hotkeys(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about enabled hotkeys.

        Returns:
            Dict[str, Dict[str, Any]]: Enabled hotkey information
        """
        return {name: info for name, info in self.hotkeys.items() if info["enabled"]}

    def get_disabled_hotkeys(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about disabled hotkeys.

        Returns:
            Dict[str, Dict[str, Any]]: Disabled hotkey information
        """
        return {
            name: info for name, info in self.hotkeys.items() if not info["enabled"]
        }

    def reset(self):
        """Reset all hotkeys."""
        try:
            # Remove all hotkeys from keyboard library
            for name in list(self.hotkeys.keys()):
                self.unregister(name)

            self.hotkeys = {}
            self.callbacks = {}
            self.save_state()

            logger.info("Reset all hotkeys")

        except Exception as e:
            logger.error(f"Failed to reset hotkeys: {e}")

    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            # Remove all hotkeys from keyboard library
            for name in list(self.hotkeys.keys()):
                self.unregister(name)
        except Exception as e:
            logger.error(f"Failed to cleanup hotkeys: {e}")
