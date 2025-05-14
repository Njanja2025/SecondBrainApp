"""
SecondBrain Backup CLI with voice integration.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import asyncio
from pathlib import Path
from secondbrain.backup.companion_journaling_backup import CompanionJournalingBackup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/secondbrain_backup.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class VoiceController:
    def __init__(self):
        self.voice_config = self._load_config("voice_config.json")
        self.voice_name = self.voice_config.get("voice_name", "Samantha")

    def _load_config(self, config_file):
        config_path = Path(__file__).parent / config_file
        with open(config_path) as f:
            return json.load(f)

    def _speak(self, message):
        try:
            subprocess.run(["say", "-v", self.voice_name, message])
        except Exception as e:
            logger.error(f"Error with 'say' command: {e}")

    def play_intro(self):
        if self.voice_config.get("intro_enabled", False):
            try:
                audio_path = Path(self.voice_config["audio_file"])
                if audio_path.exists():
                    subprocess.run(["afplay", str(audio_path)])
                self._speak(self.voice_config.get("intro_message", "Starting backup."))
            except Exception as e:
                logger.error(f"Error playing intro: {e}")

    def announce_success(self):
        if self.voice_config.get("voice_enabled", False):
            self._speak(
                self.voice_config.get(
                    "confirmation_message", "Backup completed and synced successfully."
                )
            )

    def announce_error(self):
        if self.voice_config.get("voice_enabled", False):
            self._speak(
                self.voice_config.get(
                    "error_message", "There was an error during the backup process."
                )
            )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="SecondBrain Backup CLI")
    parser.add_argument("--auto", action="store_true", help="Run backup automatically")
    parser.add_argument(
        "--verify", action="store_true", help="Verify backup after completion"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    try:
        # Initialize voice controller
        voice = VoiceController()
        voice.play_intro()

        # Initialize backup system
        backup = CompanionJournalingBackup()

        # Create backup
        backup_file = asyncio.run(backup.create_backup())

        if backup_file:
            # Verify backup
            if args.verify:
                verify_backup_integrity(backup_file)

            # Sync to cloud
            backup.sync_to_cloud()

            # Announce success
            voice.announce_success()
            return 0
        else:
            voice.announce_error()
            return 1

    except Exception as e:
        logger.error(f"Error during backup: {e}")
        voice.announce_error()
        return 1


if __name__ == "__main__":
    sys.exit(main())
