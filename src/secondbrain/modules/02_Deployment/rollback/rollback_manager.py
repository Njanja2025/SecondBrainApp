"""
Rollback manager for SecondBrain application.
Handles version control, backup management, and recovery procedures.
"""

import os
import json
import shutil
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class BackupInfo:
    """Represents backup information."""

    version: str
    timestamp: datetime
    backup_path: str
    build_hash: str
    notes: str
    status: str = "active"


class RollbackManager:
    """Manages deployment rollbacks and backups."""

    def __init__(
        self, backup_dir: str = "backups", config_dir: str = "config/deployment"
    ):
        """Initialize the rollback manager.

        Args:
            backup_dir: Directory to store backups
            config_dir: Directory to store deployment configuration
        """
        self.backup_dir = Path(backup_dir)
        self.config_dir = Path(config_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_backup_info()

    def _setup_logging(self):
        """Set up logging for the rollback manager."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_backup_info(self):
        """Load backup information."""
        try:
            info_file = self.config_dir / "backups.json"

            if info_file.exists():
                with open(info_file, "r") as f:
                    self.backups = {
                        version: BackupInfo(**data)
                        for version, data in json.load(f).items()
                    }
            else:
                self.backups = {}
                self._save_backup_info()

            logger.info("Backup information loaded")

        except Exception as e:
            logger.error(f"Failed to load backup information: {str(e)}")
            raise

    def _save_backup_info(self):
        """Save backup information."""
        try:
            info_file = self.config_dir / "backups.json"

            with open(info_file, "w") as f:
                json.dump(
                    {version: asdict(info) for version, info in self.backups.items()},
                    f,
                    indent=2,
                    default=str,
                )

        except Exception as e:
            logger.error(f"Failed to save backup information: {str(e)}")

    def _calculate_build_hash(self, build_path: str) -> str:
        """Calculate hash of build files.

        Args:
            build_path: Path to build files

        Returns:
            Build hash
        """
        try:
            build_hash = hashlib.sha256()

            for root, _, files in os.walk(build_path):
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    with open(file_path, "rb") as f:
                        build_hash.update(f.read())

            return build_hash.hexdigest()

        except Exception as e:
            logger.error(f"Failed to calculate build hash: {str(e)}")
            raise

    def create_backup(self, version: str, build_path: str, notes: str = "") -> bool:
        """Create a backup of the current version.

        Args:
            version: Version to backup
            build_path: Path to build files
            notes: Optional backup notes

        Returns:
            bool: True if backup was created successfully
        """
        try:
            if version in self.backups:
                logger.error(f"Backup for version {version} already exists")
                return False

            # Create backup directory
            backup_path = (
                self.backup_dir
                / f"backup_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            backup_path.mkdir(parents=True, exist_ok=True)

            # Copy build files
            shutil.copytree(build_path, backup_path / "build")

            # Calculate build hash
            build_hash = self._calculate_build_hash(build_path)

            # Create backup info
            backup_info = BackupInfo(
                version=version,
                timestamp=datetime.now(),
                backup_path=str(backup_path),
                build_hash=build_hash,
                notes=notes,
            )

            # Save backup info
            self.backups[version] = backup_info
            self._save_backup_info()

            logger.info(f"Created backup for version {version}")
            return True

        except Exception as e:
            logger.error(f"Failed to create backup for version {version}: {str(e)}")
            return False

    def rollback(self, version: str) -> bool:
        """Rollback to a specific version.

        Args:
            version: Version to rollback to

        Returns:
            bool: True if rollback was successful
        """
        try:
            if version not in self.backups:
                logger.error(f"No backup found for version {version}")
                return False

            backup_info = self.backups[version]
            backup_path = Path(backup_info.backup_path)

            if not backup_path.exists():
                logger.error(f"Backup directory not found: {backup_path}")
                return False

            # Verify backup integrity
            current_hash = self._calculate_build_hash(backup_path / "build")
            if current_hash != backup_info.build_hash:
                logger.error(f"Backup integrity check failed for version {version}")
                return False

            # Create rollback directory
            rollback_path = (
                self.backup_dir
                / f"rollback_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            rollback_path.mkdir(parents=True, exist_ok=True)

            # Copy current version to rollback directory
            shutil.copytree(backup_path / "build", rollback_path / "build")

            # Update backup status
            backup_info.status = "rolled_back"
            self._save_backup_info()

            logger.info(f"Rolled back to version {version}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback to version {version}: {str(e)}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups.

        Returns:
            List of backup information
        """
        return [asdict(info) for info in self.backups.values()]

    def get_backup_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific backup.

        Args:
            version: Version to get info for

        Returns:
            Backup information if found
        """
        if version in self.backups:
            return asdict(self.backups[version])
        return None

    def update_backup_status(self, version: str, status: str) -> bool:
        """Update backup status.

        Args:
            version: Version to update
            status: New status

        Returns:
            bool: True if status was updated successfully
        """
        try:
            if version not in self.backups:
                logger.error(f"No backup found for version {version}")
                return False

            valid_statuses = {"active", "inactive", "rolled_back", "deleted"}
            if status not in valid_statuses:
                logger.error(f"Invalid status: {status}")
                return False

            self.backups[version].status = status
            self._save_backup_info()

            logger.info(f"Updated status of backup {version} to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update backup status: {str(e)}")
            return False

    def cleanup_old_backups(self, keep_count: int = 5) -> bool:
        """Clean up old backups, keeping only the specified number.

        Args:
            keep_count: Number of backups to keep

        Returns:
            bool: True if cleanup was successful
        """
        try:
            # Sort backups by timestamp
            sorted_backups = sorted(
                self.backups.items(), key=lambda x: x[1].timestamp, reverse=True
            )

            # Keep only the specified number of backups
            for version, info in sorted_backups[keep_count:]:
                backup_path = Path(info.backup_path)
                if backup_path.exists():
                    shutil.rmtree(backup_path)

                del self.backups[version]

            self._save_backup_info()
            logger.info(f"Cleaned up old backups, keeping {keep_count} most recent")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    manager = RollbackManager()

    # Create a backup
    manager.create_backup(version="v1.2.3", build_path="build", notes="Initial release")

    # List backups
    backups = manager.list_backups()
    print("Available backups:", backups)

    # Rollback to a version
    manager.rollback("v1.2.3")

    # Cleanup old backups
    manager.cleanup_old_backups(keep_count=3)
