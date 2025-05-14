"""
Voice Patch Runner - Handles voice system updates and enhancements
"""

import os
import sys
import json
import logging
import subprocess
from typing import Dict, List, Optional
from datetime import datetime
import requests
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("voice_patch.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class VoicePatchRunner:
    def __init__(self, config_path: str = "config/voice_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.voice_dir = Path(self.config.get("voice_dir", "voices"))
        self.models_dir = Path(self.config.get("models_dir", "models"))
        self.backup_dir = Path(self.config.get("backup_dir", "backups/voices"))

        # Ensure directories exist
        self.voice_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

    def _load_config(self) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found. Using defaults.")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in config file {self.config_path}")
            return {}

    def backup_voice_system(self) -> bool:
        """Create a backup of the voice system."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"voice_system_{timestamp}"

            # Create backup directory
            backup_path.mkdir(exist_ok=True)

            # Backup voice files
            for voice_file in self.voice_dir.glob("**/*"):
                if voice_file.is_file():
                    rel_path = voice_file.relative_to(self.voice_dir)
                    backup_file = backup_path / rel_path
                    backup_file.parent.mkdir(exist_ok=True)
                    shutil.copy2(voice_file, backup_file)

            # Backup model files
            for model_file in self.models_dir.glob("**/*"):
                if model_file.is_file():
                    rel_path = model_file.relative_to(self.models_dir)
                    backup_file = backup_path / rel_path
                    backup_file.parent.mkdir(exist_ok=True)
                    shutil.copy2(model_file, backup_file)

            logger.info(f"Created voice system backup at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup voice system: {str(e)}")
            return False

    def apply_voice_patch(self, patch_file: str) -> bool:
        """Apply a voice system patch."""
        try:
            # Backup current system
            if not self.backup_voice_system():
                return False

            # Extract patch
            patch_path = Path(patch_file)
            if not patch_path.exists():
                logger.error(f"Patch file {patch_file} not found")
                return False

            # Apply patch
            subprocess.run(
                ["unzip", "-o", str(patch_path), "-d", str(self.voice_dir)], check=True
            )

            # Update voice settings
            settings_file = self.voice_dir / "voice_settings.json"
            if settings_file.exists():
                with open(settings_file, "r") as f:
                    settings = json.load(f)

                # Update settings
                settings["last_update"] = datetime.now().isoformat()
                settings["patch_version"] = patch_path.stem

                with open(settings_file, "w") as f:
                    json.dump(settings, f, indent=2)

            logger.info(f"Successfully applied voice patch {patch_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply voice patch: {str(e)}")
            return False

    def verify_voice_system(self) -> bool:
        """Verify the voice system is working correctly."""
        try:
            # Check voice files
            for voice_file in self.voice_dir.glob("**/*.wav"):
                if not voice_file.is_file():
                    logger.error(f"Missing voice file: {voice_file}")
                    return False

            # Check model files
            for model_file in self.models_dir.glob("**/*.model"):
                if not model_file.is_file():
                    logger.error(f"Missing model file: {model_file}")
                    return False

            # Run voice test
            test_script = self.voice_dir / "test_voice.py"
            if test_script.exists():
                result = subprocess.run(
                    [sys.executable, str(test_script)], capture_output=True, text=True
                )
                if result.returncode != 0:
                    logger.error(f"Voice test failed: {result.stderr}")
                    return False

            logger.info("Voice system verification successful")
            return True
        except Exception as e:
            logger.error(f"Failed to verify voice system: {str(e)}")
            return False

    def rollback_voice_system(self) -> bool:
        """Rollback the voice system to its previous state."""
        try:
            # Find latest backup
            backups = sorted(
                self.backup_dir.glob("voice_system_*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            if not backups:
                logger.error("No voice system backups found")
                return False

            latest_backup = backups[0]

            # Restore voice files
            for backup_file in latest_backup.glob("**/*"):
                if backup_file.is_file():
                    rel_path = backup_file.relative_to(latest_backup)
                    target_file = self.voice_dir / rel_path
                    target_file.parent.mkdir(exist_ok=True)
                    shutil.copy2(backup_file, target_file)

            logger.info(f"Successfully rolled back voice system to {latest_backup}")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback voice system: {str(e)}")
            return False

    def get_voice_system_status(self) -> Dict:
        """Get the current status of the voice system."""
        try:
            status = {
                "voice_files": len(list(self.voice_dir.glob("**/*.wav"))),
                "model_files": len(list(self.models_dir.glob("**/*.model"))),
                "last_update": None,
                "patch_version": None,
                "health": "unknown",
            }

            # Get last update time
            settings_file = self.voice_dir / "voice_settings.json"
            if settings_file.exists():
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                    status["last_update"] = settings.get("last_update")
                    status["patch_version"] = settings.get("patch_version")

            # Check health
            if self.verify_voice_system():
                status["health"] = "healthy"
            else:
                status["health"] = "unhealthy"

            return status
        except Exception as e:
            logger.error(f"Failed to get voice system status: {str(e)}")
            return {"error": str(e)}


def main():
    """Main entry point for the voice patch runner."""
    runner = VoicePatchRunner()

    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python voice_patch_runner.py <patch_file>")
        sys.exit(1)

    patch_file = sys.argv[1]

    # Apply patch
    if runner.apply_voice_patch(patch_file):
        # Verify system
        if runner.verify_voice_system():
            print("Successfully applied and verified voice patch")
        else:
            print("Voice system verification failed")
            # Rollback if verification fails
            if runner.rollback_voice_system():
                print("Successfully rolled back voice system")
            else:
                print("Failed to rollback voice system")
    else:
        print(f"Failed to apply voice patch {patch_file}")


if __name__ == "__main__":
    main()
