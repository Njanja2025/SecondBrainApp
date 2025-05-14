"""
Test script for the Companion Journaling Backup System with voice announcements and cloud sync.
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import pyttsx3
from secondbrain.backup import CompanionJournalingBackup

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VoiceAnnouncer:
    def __init__(self):
        self.voice_config = self._load_config("voice_config.json")
        self.engine = pyttsx3.init()
        self.engine.setProperty("voice", self.voice_config["voice_name"])

    def _load_config(self, config_file):
        config_path = Path(__file__).parent / config_file
        with open(config_path) as f:
            return json.load(f)

    def announce_success(self):
        """Announce successful backup."""
        if self.voice_config["voice_enabled"]:
            self.engine.say(self.voice_config["confirmation_message"])
            self.engine.runAndWait()

    def announce_error(self):
        """Announce backup error."""
        if self.voice_config["voice_enabled"]:
            self.engine.say(self.voice_config["error_message"])
            self.engine.runAndWait()


async def test_backup_system():
    """Test the backup system with voice announcements and cloud sync."""
    try:
        # Initialize backup system and voice announcer
        backup = CompanionJournalingBackup(
            backup_root="test_backups", enable_cloud_sync=True, enable_voice=True
        )
        announcer = VoiceAnnouncer()

        # Create test data
        test_data = {
            "journal_entries": [
                {"type": "daily", "content": "Test journal entry"},
                {"type": "reflection", "content": "Test reflection"},
            ]
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

        # Handle results
        if result["status"] == "success":
            announcer.announce_success()
            logger.info("Backup completed successfully!")
            logger.info(f"Backup path: {result['backup_path']}")
            logger.info(f"Duration: {result['duration']} seconds")
        else:
            announcer.announce_error()
            logger.error(f"Backup failed: {result['message']}")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        announcer.announce_error()
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
