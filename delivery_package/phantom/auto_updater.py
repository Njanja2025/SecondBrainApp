"""
Automatic update system with GitHub integration.
"""

import os
import json
import requests
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from ..phantom.phantom_core import PhantomCore


class PhantomUpdater:
    def __init__(self, phantom: PhantomCore):
        """Initialize the Phantom updater."""
        self.phantom = phantom
        self.github_repo = "lloydkavhanda/SecondBrain-App"
        self.update_url = (
            f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        )
        self.current_version = self._get_current_version()

    def _get_current_version(self) -> str:
        """Get current app version."""
        try:
            with open("config/version.json", "r") as f:
                version_data = json.load(f)
                return version_data.get("version", "0.0.0")
        except FileNotFoundError:
            return "0.0.0"

    def _update_version(self, new_version: str):
        """Update version file."""
        os.makedirs("config", exist_ok=True)
        with open("config/version.json", "w") as f:
            json.dump({"version": new_version}, f)
        self.current_version = new_version

    def check_for_updates(self) -> Dict[str, Any]:
        """Check GitHub for available updates."""
        try:
            # Check GitHub releases
            response = requests.get(self.update_url)
            if response.status_code != 200:
                raise Exception(f"GitHub API error: {response.status_code}")

            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip("v")

            if latest_version > self.current_version:
                self.phantom.log_event(
                    "Update Check", f"New version available: {latest_version}", "INFO"
                )
                return {
                    "status": "update_available",
                    "current_version": self.current_version,
                    "latest_version": latest_version,
                    "release_notes": release_data["body"],
                    "download_url": release_data["assets"][0]["browser_download_url"],
                }
            else:
                self.phantom.log_event("Update Check", "System is up to date", "INFO")
                return {"status": "up_to_date", "current_version": self.current_version}

        except Exception as e:
            error_msg = f"Update check failed: {str(e)}"
            self.phantom.log_event("Update Check", error_msg, "ERROR")
            return {"status": "error", "message": error_msg}

    def download_update(self, download_url: str) -> Optional[Path]:
        """Download update package."""
        try:
            response = requests.get(download_url, stream=True)
            if response.status_code != 200:
                raise Exception(f"Download failed: {response.status_code}")

            download_path = Path("updates") / "SecondBrainApp_latest.zip"
            download_path.parent.mkdir(exist_ok=True)

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.phantom.log_event(
                "Update Download",
                f"Update package downloaded to {download_path}",
                "INFO",
            )

            return download_path

        except Exception as e:
            error_msg = f"Update download failed: {str(e)}"
            self.phantom.log_event("Update Download", error_msg, "ERROR")
            return None

    def verify_update_package(self, package_path: Path, expected_hash: str) -> bool:
        """Verify update package integrity."""
        try:
            sha256_hash = hashlib.sha256()
            with open(package_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            actual_hash = sha256_hash.hexdigest()
            return actual_hash == expected_hash

        except Exception as e:
            self.phantom.log_event(
                "Update Verification", f"Package verification failed: {str(e)}", "ERROR"
            )
            return False

    def apply_update(self, package_path: Path) -> bool:
        """Apply downloaded update."""
        try:
            # TODO: Implement update application logic
            # This will involve:
            # 1. Backing up current installation
            # 2. Extracting update package
            # 3. Applying changes
            # 4. Updating version file
            return True

        except Exception as e:
            self.phantom.log_event(
                "Update Installation", f"Update installation failed: {str(e)}", "ERROR"
            )
            return False
