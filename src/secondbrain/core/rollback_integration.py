"""
Integration module for SecondBrain rollback system.
Connects the rollback system with the main application.
"""

import os
import sys
import logging
from typing import Optional, Callable

from ..monitoring.rollback_manager import rollback_manager
from ..gui.recovery_dialog import RecoveryDialog

logger = logging.getLogger(__name__)


class RollbackIntegration:
    """Integration class for rollback system."""

    def __init__(self, app_name: str, version: str):
        """Initialize the rollback integration.

        Args:
            app_name: Name of the application
            version: Current version of the application
        """
        self.app_name = app_name
        self.version = version
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging for the rollback system."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def create_backup(self, notes: Optional[str] = None) -> bool:
        """Create a backup of the current version.

        Args:
            notes: Optional notes for the backup

        Returns:
            bool: True if backup was successful, False otherwise
        """
        try:
            success = rollback_manager.create_backup(notes=notes)
            if success:
                logger.info(f"Created backup of version {self.version}")
            else:
                logger.error(f"Failed to create backup of version {self.version}")
            return success
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return False

    def show_recovery_dialog(self, parent=None) -> Optional[str]:
        """Show the recovery dialog.

        Args:
            parent: Parent widget for the dialog

        Returns:
            Optional[str]: Version that was restored, if any
        """
        try:
            dialog = RecoveryDialog(parent)
            dialog.rollback_performed.connect(self._on_rollback)
            dialog.exec_()
            return (
                dialog.restored_version if hasattr(dialog, "restored_version") else None
            )
        except Exception as e:
            logger.error(f"Error showing recovery dialog: {str(e)}")
            return None

    def _on_rollback(self, version: str):
        """Handle rollback event.

        Args:
            version: Version that was restored
        """
        logger.info(f"Rolled back to version {version}")
        # Add any additional rollback handling here

    def cleanup_old_backups(self, keep_count: int = 5) -> bool:
        """Clean up old backups.

        Args:
            keep_count: Number of backups to keep

        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        try:
            success = rollback_manager.cleanup_old_backups(keep_count)
            if success:
                logger.info(f"Cleaned up old backups, keeping {keep_count} most recent")
            else:
                logger.error("Failed to clean up old backups")
            return success
        except Exception as e:
            logger.error(f"Error cleaning up backups: {str(e)}")
            return False

    def get_backup_info(self, version: str) -> Optional[dict]:
        """Get information about a specific backup.

        Args:
            version: Version to get information for

        Returns:
            Optional[dict]: Backup information if found, None otherwise
        """
        try:
            return rollback_manager.get_backup_info(version)
        except Exception as e:
            logger.error(f"Error getting backup info: {str(e)}")
            return None

    def list_backups(self) -> list:
        """List all available backups.

        Returns:
            list: List of backup information dictionaries
        """
        try:
            return rollback_manager.list_backups()
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            return []


# Example usage
if __name__ == "__main__":
    integration = RollbackIntegration("SecondBrain", "1.0.0")

    # Create a backup
    integration.create_backup("Initial backup")

    # List backups
    backups = integration.list_backups()
    print("\nAvailable Backups:")
    for backup in backups:
        print(f"Version: {backup['version']}")
        print(f"Timestamp: {backup['timestamp']}")
        print(f"Status: {backup['status']}")
        print(f"Notes: {backup['notes']}")
        print("-" * 40)

    # Clean up old backups
    integration.cleanup_old_backups(keep_count=3)
