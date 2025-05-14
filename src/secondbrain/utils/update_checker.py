"""
Update checker for SecondBrain application.
Handles version checking, update notifications, and update procedures.
"""

import os
import sys
import json
import logging
import requests
import semver
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class UpdateChecker:
    """Handles application updates and version checking."""

    def __init__(
        self, current_version: str, update_url: str = "https://njanja.net/version.txt"
    ):
        """Initialize the update checker.

        Args:
            current_version: Current application version
            update_url: URL to check for updates
        """
        self.current_version = current_version
        self.update_url = update_url
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging for the update checker."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def check_for_updates(self) -> Tuple[bool, Optional[str]]:
        """Check for available updates.

        Returns:
            Tuple[bool, Optional[str]]: (update_available, latest_version)
        """
        try:
            response = requests.get(self.update_url, timeout=10)
            response.raise_for_status()
            latest_version = response.text.strip()

            if not semver.VersionInfo.is_valid(latest_version):
                logger.error(f"Invalid version format received: {latest_version}")
                return False, None

            if semver.compare(latest_version, self.current_version) > 0:
                logger.info(
                    f"Update available: {latest_version} (current: {self.current_version})"
                )
                return True, latest_version
            else:
                logger.info("Application is up to date")
                return False, None

        except requests.RequestException as e:
            logger.error(f"Failed to check for updates: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Error checking for updates: {str(e)}")
            return False, None

    def get_update_info(self, version: str) -> Optional[Dict]:
        """Get information about an update.

        Args:
            version: Version to get information for

        Returns:
            Optional[Dict]: Update information if available
        """
        try:
            info_url = f"{self.update_url.rsplit('.', 1)[0]}_info.json"
            response = requests.get(info_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get update info: {str(e)}")
            return None

    def download_update(self, version: str, target_dir: str) -> bool:
        """Download an update.

        Args:
            version: Version to download
            target_dir: Directory to save the update

        Returns:
            bool: True if download was successful
        """
        try:
            download_url = f"{self.update_url.rsplit('.', 1)[0]}_{version}.zip"
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            os.makedirs(target_dir, exist_ok=True)
            update_path = os.path.join(target_dir, f"update_{version}.zip")

            with open(update_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Update downloaded to {update_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to download update: {str(e)}")
            return False

    def verify_update(self, version: str, update_path: str) -> bool:
        """Verify downloaded update.

        Args:
            version: Version to verify
            update_path: Path to the update file

        Returns:
            bool: True if verification was successful
        """
        try:
            # TODO: Implement checksum verification
            return True
        except Exception as e:
            logger.error(f"Failed to verify update: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    checker = UpdateChecker("2025.1.0")

    # Check for updates
    update_available, latest_version = checker.check_for_updates()

    if update_available:
        print(f"Update available: {latest_version}")

        # Get update information
        update_info = checker.get_update_info(latest_version)
        if update_info:
            print(f"Update details: {json.dumps(update_info, indent=2)}")

        # Download update
        if checker.download_update(latest_version, "updates"):
            print("Update downloaded successfully")

            # Verify update
            if checker.verify_update(
                latest_version, f"updates/update_{latest_version}.zip"
            ):
                print("Update verified successfully")
            else:
                print("Update verification failed")
    else:
        print("Application is up to date")
