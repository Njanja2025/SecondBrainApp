"""
Rollback management system for SecondBrain application.
Handles version backups, recovery, and rollback operations.
"""

import os
import json
import shutil
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class BackupInfo:
    """Information about a backup version."""

    version: str
    timestamp: str
    backup_path: str
    build_hash: str
    notes: str
    status: str  # 'stable', 'testing', 'failed'


class RollbackManager:
    """Manages application version backups and rollbacks."""

    def __init__(self, app_name: str, backup_dir: str = "backups"):
        """Initialize the rollback manager.

        Args:
            app_name: Name of the application
            backup_dir: Directory for backups
        """
        self.app_name = app_name
        self.backup_dir = Path(backup_dir)
        self.backup_info_file = self.backup_dir / "backup_info.json"

        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Load backup information
        self.backups = self._load_backup_info()

    def _load_backup_info(self) -> Dict[str, BackupInfo]:
        """Load backup information from file.

        Returns:
            Dictionary of backup information
        """
        if not self.backup_info_file.exists():
            return {}

        try:
            with open(self.backup_info_file) as f:
                data = json.load(f)
                return {version: BackupInfo(**info) for version, info in data.items()}
        except Exception as e:
            logger.error(f"Failed to load backup info: {str(e)}")
            return {}

    def _save_backup_info(self) -> None:
        """Save backup information to file."""
        try:
            with open(self.backup_info_file, "w") as f:
                json.dump(
                    {version: asdict(info) for version, info in self.backups.items()},
                    f,
                    indent=4,
                )
        except Exception as e:
            logger.error(f"Failed to save backup info: {str(e)}")

    def create_backup(
        self, version: str, build_hash: str, notes: str = ""
    ) -> Optional[str]:
        """Create a backup of the current version.

        Args:
            version: Version number
            build_hash: Hash of the build
            notes: Additional notes about the backup

        Returns:
            Path to the backup if successful, None otherwise
        """
        try:
            # Create backup directory
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{self.app_name}_{timestamp}"

            # Copy application files
            shutil.copytree(
                f"dist/{self.app_name}.app", backup_path, dirs_exist_ok=True
            )

            # Create backup info
            backup_info = BackupInfo(
                version=version,
                timestamp=timestamp,
                backup_path=str(backup_path),
                build_hash=build_hash,
                notes=notes,
                status="stable",
            )

            # Save backup info
            self.backups[version] = backup_info
            self._save_backup_info()

            logger.info(f"Created backup for version {version}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return None

    def rollback(self, version: str) -> bool:
        """Rollback to a specific version.

        Args:
            version: Version to rollback to

        Returns:
            True if rollback was successful, False otherwise
        """
        try:
            if version not in self.backups:
                logger.error(f"Version {version} not found in backups")
                return False

            backup_info = self.backups[version]
            backup_path = Path(backup_info.backup_path)

            if not backup_path.exists():
                logger.error(f"Backup path {backup_path} does not exist")
                return False

            # Remove current version
            current_path = Path(f"dist/{self.app_name}.app")
            if current_path.exists():
                shutil.rmtree(current_path)

            # Restore backup
            shutil.copytree(backup_path, current_path)

            logger.info(f"Rolled back to version {version}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback: {str(e)}")
            return False

    def list_backups(self) -> List[Dict[str, str]]:
        """List all available backups.

        Returns:
            List of backup information
        """
        return [
            {
                "version": info.version,
                "timestamp": info.timestamp,
                "status": info.status,
                "notes": info.notes,
            }
            for info in sorted(
                self.backups.values(), key=lambda x: x.timestamp, reverse=True
            )
        ]

    def get_backup_info(self, version: str) -> Optional[BackupInfo]:
        """Get information about a specific backup.

        Args:
            version: Version to get information for

        Returns:
            BackupInfo object if found, None otherwise
        """
        return self.backups.get(version)

    def update_backup_status(self, version: str, status: str) -> bool:
        """Update the status of a backup.

        Args:
            version: Version to update
            status: New status

        Returns:
            True if update was successful, False otherwise
        """
        if version not in self.backups:
            return False

        self.backups[version].status = status
        self._save_backup_info()
        return True

    def cleanup_old_backups(self, keep_count: int = 5) -> None:
        """Remove old backups, keeping only the specified number.

        Args:
            keep_count: Number of backups to keep
        """
        try:
            # Sort backups by timestamp
            sorted_backups = sorted(
                self.backups.values(), key=lambda x: x.timestamp, reverse=True
            )

            # Remove old backups
            for backup in sorted_backups[keep_count:]:
                backup_path = Path(backup.backup_path)
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                del self.backups[backup.version]

            self._save_backup_info()
            logger.info(f"Cleaned up old backups, keeping {keep_count} latest versions")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {str(e)}")


# Create global instance
rollback_manager = RollbackManager("SecondBrainApp2025")

# Example usage
if __name__ == "__main__":
    # Create a backup
    backup_path = rollback_manager.create_backup(
        version="1.0.0", build_hash="abc123", notes="Initial release"
    )

    # List backups
    backups = rollback_manager.list_backups()
    print(f"Available backups: {backups}")

    # Rollback to a version
    if backups:
        version = backups[0]["version"]
        success = rollback_manager.rollback(version)
        print(f"Rollback to {version}: {'successful' if success else 'failed'}")

    # Cleanup old backups
    rollback_manager.cleanup_old_backups(keep_count=3)
