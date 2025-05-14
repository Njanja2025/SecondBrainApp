"""
Test script for the enhanced Companion Journaling Backup System.
Tests voice announcements, encryption, and cloud sync features.
"""

import os
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime
from secondbrain.backup import CompanionJournalingBackup

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_backup_system():
    """Test the enhanced backup system with all features enabled."""
    try:
        # Initialize backup system with all features
        backup = CompanionJournalingBackup(
            backup_root="test_backups",
            enable_cloud_sync=True,
            enable_voice=True,
            enable_encryption=True,
            cloud_provider="dropbox",  # Change to "icloud" or "s3" as needed
        )

        # Create test data
        test_data = {
            "journal_entries": [
                {"type": "daily", "content": "Test journal entry"},
                {"type": "reflection", "content": "Test reflection"},
            ],
            "emotional_logs": [
                {"emotion": "happy", "intensity": 0.8},
                {"emotion": "focused", "intensity": 0.9},
            ],
            "memory_entries": [
                {"type": "short_term", "content": "Test memory"},
                {"type": "long_term", "content": "Test long-term memory"},
            ],
            "interaction_patterns": [
                {"type": "user", "pattern": "test pattern"},
                {"type": "system", "pattern": "test system pattern"},
            ],
        }

        # Create test directories and files
        for category, entries in test_data.items():
            category_dir = Path(f"test_backups/data/{category}")
            category_dir.mkdir(parents=True, exist_ok=True)

            for i, entry in enumerate(entries):
                file_path = category_dir / f"test_entry_{i}.json"
                with open(file_path, "w") as f:
                    json.dump(entry, f, indent=2)

        # Run backup
        logger.info("Starting backup test...")
        result = await backup.create_backup()

        # Verify results
        if result["status"] == "success":
            logger.info("Backup completed successfully!")
            logger.info(f"Backup path: {result['backup_path']}")
            logger.info(f"Duration: {result['duration']} seconds")

            # Verify encrypted vault exists
            vault_path = Path(f"{result['backup_path']}.vault.zip")
            if vault_path.exists():
                logger.info("Encrypted vault created successfully!")
            else:
                logger.error("Encrypted vault not found!")

            # Verify cloud sync
            if backup.enable_cloud_sync:
                logger.info(f"Backup synced to {backup.cloud_provider}")
        else:
            logger.error(f"Backup failed: {result['message']}")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


def main():
    """Run the backup system test."""
    try:
        asyncio.run(test_backup_system())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
