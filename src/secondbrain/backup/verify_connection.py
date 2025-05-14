"""
Verification script for the Companion Journaling Backup System.
Tests Dropbox connection, voice configuration, and cloud sync settings.
"""

import os
import json
import logging
from pathlib import Path
import dropbox
from dropbox.exceptions import AuthError
import pyttsx3

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SystemVerifier:
    def __init__(self):
        self.cloud_config = self._load_config("cloud_config.json")
        self.voice_config = self._load_config("voice_config.json")

    def _load_config(self, config_file):
        config_path = Path(__file__).parent / config_file
        with open(config_path) as f:
            return json.load(f)

    def verify_dropbox_connection(self):
        """Verify Dropbox connection and permissions."""
        try:
            dbx = dropbox.Dropbox(self.cloud_config["access_token"])
            # Test connection by getting account info
            account = dbx.users_get_current_account()
            logger.info(
                f"Successfully connected to Dropbox as: {account.name.display_name}"
            )

            # Test folder access
            try:
                dbx.files_list_folder(self.cloud_config["cloud_path"])
                logger.info(
                    f"Successfully accessed cloud path: {self.cloud_config['cloud_path']}"
                )
                return True
            except dropbox.exceptions.ApiError as e:
                logger.error(f"Failed to access cloud path: {e}")
                return False

        except AuthError as e:
            logger.error(f"Dropbox authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Dropbox verification: {e}")
            return False

    def verify_voice_config(self):
        """Verify voice configuration and audio file."""
        try:
            # Test voice engine
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            voice_found = False

            for voice in voices:
                if self.voice_config["voice_name"].lower() in voice.name.lower():
                    voice_found = True
                    break

            if not voice_found:
                logger.error(f"Voice '{self.voice_config['voice_name']}' not found")
                return False

            # Test audio file
            audio_path = Path(self.voice_config["audio_file"])
            if not audio_path.exists():
                logger.error(f"Audio file not found: {audio_path}")
                return False

            logger.info("Voice configuration verified successfully")
            return True

        except Exception as e:
            logger.error(f"Error verifying voice configuration: {e}")
            return False

    def verify_local_paths(self):
        """Verify local backup paths exist and are writable."""
        try:
            local_path = Path(os.path.expanduser(self.cloud_config["local_vault_path"]))
            local_path.mkdir(parents=True, exist_ok=True)

            # Test write permission
            test_file = local_path / ".write_test"
            test_file.touch()
            test_file.unlink()

            logger.info(f"Local backup path verified: {local_path}")
            return True

        except Exception as e:
            logger.error(f"Error verifying local paths: {e}")
            return False


def main():
    """Run all verification checks."""
    verifier = SystemVerifier()

    logger.info("Starting system verification...")

    # Run all checks
    dropbox_ok = verifier.verify_dropbox_connection()
    voice_ok = verifier.verify_voice_config()
    paths_ok = verifier.verify_local_paths()

    # Summary
    logger.info("\nVerification Summary:")
    logger.info(f"Dropbox Connection: {'✅' if dropbox_ok else '❌'}")
    logger.info(f"Voice Configuration: {'✅' if voice_ok else '❌'}")
    logger.info(f"Local Paths: {'✅' if paths_ok else '❌'}")

    if all([dropbox_ok, voice_ok, paths_ok]):
        logger.info("All systems verified successfully!")
        return 0
    else:
        logger.error("Some verifications failed. Please check the logs above.")
        return 1


if __name__ == "__main__":
    exit(main())
