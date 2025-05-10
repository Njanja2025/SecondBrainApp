"""
Configuration management for SecondBrainApp
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    """Configuration management class."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager."""
        self.config_file = config_file or "config.json"
        self.config: Dict[str, Any] = {}
        self.load_config()
        
    def load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                self.config = self.get_default_config()
                self.save_config()
                logger.info(f"Created default configuration at {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = self.get_default_config()
            
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "app": {
                "name": "SecondBrainApp",
                "version": "1.0.0",
                "debug": False
            },
            "gui": {
                "theme": "dark",
                "font_size": 12,
                "window_size": [800, 600]
            },
            "hotkeys": {
                "enabled": True,
                "default_combinations": {
                    "toggle_app": "ctrl+shift+space",
                    "quick_note": "ctrl+shift+n",
                    "search": "ctrl+shift+f"
                }
            },
            "storage": {
                "base_dir": os.path.expanduser("~/secondbrain"),
                "backup_dir": "backups",
                "max_backups": 10
            },
            "logging": {
                "level": "INFO",
                "file": "secondbrain.log",
                "max_size": 10485760,  # 10MB
                "backup_count": 5
            },
            "notifications": {
                "enabled": True,
                "sound": True,
                "desktop": True
            },
            "sync": {
                "enabled": False,
                "interval": 300,  # 5 minutes
                "cloud_provider": "none"
            },
            "security": {
                "encryption_enabled": False,
                "password_hash": "sha256",
                "session_timeout": 3600  # 1 hour
            }
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        try:
            value = self.config
            for k in key.split("."):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            value: Value to set
            
        Returns:
            bool: True if successful
        """
        try:
            keys = key.split(".")
            target = self.config
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            target[keys[-1]] = value
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"Failed to set configuration {key}: {e}")
            return False
            
    def delete(self, key: str) -> bool:
        """
        Delete configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            
        Returns:
            bool: True if successful
        """
        try:
            keys = key.split(".")
            target = self.config
            for k in keys[:-1]:
                if k not in target:
                    return False
                target = target[k]
            del target[keys[-1]]
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"Failed to delete configuration {key}: {e}")
            return False
            
    def has(self, key: str) -> bool:
        """
        Check if configuration key exists.
        
        Args:
            key: Configuration key (dot notation supported)
            
        Returns:
            bool: True if key exists
        """
        try:
            value = self.config
            for k in key.split("."):
                value = value[k]
            return True
        except (KeyError, TypeError):
            return False
            
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dict[str, Any]: All configuration values
        """
        return self.config.copy()
        
    def update(self, config: Dict[str, Any]) -> bool:
        """
        Update multiple configuration values.
        
        Args:
            config: Dictionary of configuration values
            
        Returns:
            bool: True if successful
        """
        try:
            self.config.update(config)
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False
            
    def reset(self):
        """Reset configuration to defaults."""
        try:
            self.config = self.get_default_config()
            self.save_config()
            logger.info("Reset configuration to defaults")
        except Exception as e:
            logger.error(f"Failed to reset configuration: {e}")
            
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate configuration.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, list of errors)
        """
        errors = []
        
        # Check required sections
        required_sections = ["app", "gui", "storage", "logging"]
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required section: {section}")
                
        # Check app section
        if "app" in self.config:
            app = self.config["app"]
            if "name" not in app:
                errors.append("Missing app name")
            if "version" not in app:
                errors.append("Missing app version")
                
        # Check storage section
        if "storage" in self.config:
            storage = self.config["storage"]
            if "base_dir" not in storage:
                errors.append("Missing storage base directory")
                
        # Check logging section
        if "logging" in self.config:
            logging_config = self.config["logging"]
            if "level" not in logging_config:
                errors.append("Missing logging level")
            if "file" not in logging_config:
                errors.append("Missing logging file")
                
        return len(errors) == 0, errors 