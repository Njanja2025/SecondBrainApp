"""
Module manager for SecondBrain application.
Handles module operations, lifecycle, and state management.
"""

import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..config.system_map import SystemMap, ModuleConfig

logger = logging.getLogger(__name__)


class ModuleManager:
    """Manages module operations and lifecycle."""

    def __init__(self, system_map: SystemMap):
        """Initialize the module manager.

        Args:
            system_map: System map instance
        """
        self.system_map = system_map
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging for the module manager."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def initialize_module(self, module_id: str) -> bool:
        """Initialize a module with required structure.

        Args:
            module_id: Module identifier

        Returns:
            bool: True if initialization was successful
        """
        try:
            module_path = self.system_map.get_module_path(module_id)

            # Create module directory
            module_path.mkdir(parents=True, exist_ok=True)

            # Create standard subdirectories
            (module_path / "src").mkdir(exist_ok=True)
            (module_path / "tests").mkdir(exist_ok=True)
            (module_path / "docs").mkdir(exist_ok=True)
            (module_path / "config").mkdir(exist_ok=True)

            # Create module configuration
            config = {
                "id": module_id,
                "name": self.system_map.modules[module_id].name,
                "description": self.system_map.modules[module_id].description,
                "dependencies": self.system_map.modules[module_id].dependencies,
                "status": "initialized",
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0",
            }

            # Save configuration
            with open(module_path / "config" / "module.json", "w") as f:
                json.dump(config, f, indent=2)

            logger.info(f"Initialized module {module_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize module {module_id}: {str(e)}")
            return False

    def update_module(self, module_id: str, updates: Dict[str, Any]) -> bool:
        """Update module configuration.

        Args:
            module_id: Module identifier
            updates: Dictionary of updates to apply

        Returns:
            bool: True if update was successful
        """
        try:
            module_path = self.system_map.get_module_path(module_id)
            config_path = module_path / "config" / "module.json"

            if not config_path.exists():
                logger.error(f"Module configuration not found: {module_id}")
                return False

            # Load current configuration
            with open(config_path, "r") as f:
                config = json.load(f)

            # Apply updates
            config.update(updates)
            config["last_updated"] = datetime.now().isoformat()

            # Save updated configuration
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            logger.info(f"Updated module {module_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update module {module_id}: {str(e)}")
            return False

    def backup_module(self, module_id: str, backup_dir: str = "backups") -> bool:
        """Create a backup of a module.

        Args:
            module_id: Module identifier
            backup_dir: Directory to store backups

        Returns:
            bool: True if backup was successful
        """
        try:
            module_path = self.system_map.get_module_path(module_id)
            backup_path = (
                Path(backup_dir)
                / f"{module_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)

            # Copy module contents
            shutil.copytree(module_path, backup_path / module_id, dirs_exist_ok=True)

            logger.info(f"Created backup of module {module_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to backup module {module_id}: {str(e)}")
            return False

    def restore_module(self, module_id: str, backup_path: str) -> bool:
        """Restore a module from backup.

        Args:
            module_id: Module identifier
            backup_path: Path to backup directory

        Returns:
            bool: True if restore was successful
        """
        try:
            module_path = self.system_map.get_module_path(module_id)
            backup_dir = Path(backup_path)

            if not backup_dir.exists():
                logger.error(f"Backup not found: {backup_path}")
                return False

            # Remove current module
            if module_path.exists():
                shutil.rmtree(module_path)

            # Restore from backup
            shutil.copytree(backup_dir / module_id, module_path)

            logger.info(f"Restored module {module_id} from backup")
            return True

        except Exception as e:
            logger.error(f"Failed to restore module {module_id}: {str(e)}")
            return False

    def validate_module(self, module_id: str) -> List[str]:
        """Validate module structure and configuration.

        Args:
            module_id: Module identifier

        Returns:
            List of validation issues found
        """
        issues = []
        module_path = self.system_map.get_module_path(module_id)

        # Check required directories
        required_dirs = ["src", "tests", "docs", "config"]
        for dir_name in required_dirs:
            if not (module_path / dir_name).exists():
                issues.append(f"Missing required directory: {dir_name}")

        # Check configuration
        config_path = module_path / "config" / "module.json"
        if not config_path.exists():
            issues.append("Missing module configuration")
        else:
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)

                # Validate configuration fields
                required_fields = [
                    "id",
                    "name",
                    "description",
                    "dependencies",
                    "status",
                    "version",
                ]
                for field in required_fields:
                    if field not in config:
                        issues.append(
                            f"Missing required field in configuration: {field}"
                        )

            except Exception as e:
                issues.append(f"Invalid configuration: {str(e)}")

        return issues

    def get_module_status(self, module_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a module.

        Args:
            module_id: Module identifier

        Returns:
            Dictionary containing module status information
        """
        try:
            module_path = self.system_map.get_module_path(module_id)
            config_path = module_path / "config" / "module.json"

            if not config_path.exists():
                return None

            with open(config_path, "r") as f:
                config = json.load(f)

            # Get directory sizes
            src_size = sum(
                f.stat().st_size
                for f in (module_path / "src").rglob("*")
                if f.is_file()
            )
            test_size = sum(
                f.stat().st_size
                for f in (module_path / "tests").rglob("*")
                if f.is_file()
            )
            doc_size = sum(
                f.stat().st_size
                for f in (module_path / "docs").rglob("*")
                if f.is_file()
            )

            return {
                "id": module_id,
                "name": config["name"],
                "status": config["status"],
                "version": config["version"],
                "last_updated": config["last_updated"],
                "src_size": src_size,
                "test_size": test_size,
                "doc_size": doc_size,
                "total_size": src_size + test_size + doc_size,
            }

        except Exception as e:
            logger.error(f"Failed to get module status {module_id}: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    system_map = SystemMap()
    manager = ModuleManager(system_map)

    # Initialize a module
    if manager.initialize_module("01_Security"):
        print("Security module initialized")

    # Get module status
    status = manager.get_module_status("01_Security")
    if status:
        print("Module Status:", status)

    # Validate module
    issues = manager.validate_module("01_Security")
    if issues:
        print("Validation Issues:", issues)
    else:
        print("Module validation passed")
