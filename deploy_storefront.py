"""
Script to deploy the Njanja Storefront package with Dropbox sync
"""

import os
import shutil
import zipfile
from pathlib import Path
import logging
import subprocess
import platform
from datetime import datetime
import json
import hashlib
import requests
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StorefrontDeployer:
    def __init__(self, base_dir: str = "storefront"):
        """Initialize the deployer with base directory."""
        self.base_dir = os.path.abspath(base_dir)
        self.package_name = "NjanjaStorefront_Package.zip"
        self.dropbox_path = os.path.expanduser("~/Dropbox/NjanjaStore")
        self.version_file = "version.json"

    def calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def get_version_info(self) -> dict:
        """Get current version information."""
        version_path = os.path.join(self.base_dir, self.version_file)
        if os.path.exists(version_path):
            with open(version_path, "r") as f:
                return json.load(f)
        return {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "checksum": None,
        }

    def update_version_info(self, checksum: str) -> None:
        """Update version information."""
        version_info = self.get_version_info()
        version_parts = version_info["version"].split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        version_info.update(
            {
                "version": ".".join(version_parts),
                "last_updated": datetime.now().isoformat(),
                "checksum": checksum,
            }
        )

        version_path = os.path.join(self.base_dir, self.version_file)
        with open(version_path, "w") as f:
            json.dump(version_info, f, indent=2)

    def sync_to_dropbox(self) -> Tuple[bool, str]:
        """Sync package to Dropbox."""
        try:
            # Create Dropbox directory if it doesn't exist
            os.makedirs(self.dropbox_path, exist_ok=True)

            # Calculate checksum
            package_path = os.path.join(os.getcwd(), self.package_name)
            checksum = self.calculate_checksum(package_path)

            # Update version info
            self.update_version_info(checksum)

            # Copy package to Dropbox
            dropbox_package_path = os.path.join(self.dropbox_path, self.package_name)
            shutil.copy2(package_path, dropbox_package_path)

            # Copy version info
            shutil.copy2(
                os.path.join(self.base_dir, self.version_file),
                os.path.join(self.dropbox_path, self.version_file),
            )

            logger.info(f"Synced package to Dropbox: {dropbox_package_path}")
            return True, dropbox_package_path

        except Exception as e:
            logger.error(f"Failed to sync to Dropbox: {e}")
            return False, str(e)

    def verify_package(self) -> Tuple[bool, str]:
        """Verify package integrity."""
        try:
            package_path = os.path.join(os.getcwd(), self.package_name)
            if not os.path.exists(package_path):
                return False, "Package file not found"

            # Verify zip file
            with zipfile.ZipFile(package_path, "r") as zipf:
                if zipf.testzip() is not None:
                    return False, "Package integrity check failed"

            # Verify required files
            required_files = [
                "README.md",
                "products/ai_business_starter_pack/description.md",
                "products/ai_business_starter_pack/price.txt",
                "products/ai_business_starter_pack/assets/cover_mockup.jpg",
                "voice_scripts/homepage_intro.mp3",
                "paystack_test_checkout.html",
            ]

            with zipfile.ZipFile(package_path, "r") as zipf:
                for file in required_files:
                    if file not in zipf.namelist():
                        return False, f"Required file missing: {file}"

            return True, "Package verification successful"

        except Exception as e:
            logger.error(f"Package verification failed: {e}")
            return False, str(e)

    def deploy(self) -> bool:
        """Deploy the package."""
        try:
            # Verify package
            verify_success, verify_message = self.verify_package()
            if not verify_success:
                print(f"\nPackage verification failed: {verify_message}")
                return False

            print("\nPackage verification successful")

            # Sync to Dropbox
            sync_success, sync_message = self.sync_to_dropbox()
            if not sync_success:
                print(f"\nDropbox sync failed: {sync_message}")
                return False

            print(f"\nPackage synced to Dropbox: {sync_message}")

            # Print deployment summary
            version_info = self.get_version_info()
            print("\nDeployment Summary:")
            print(f"- Version: {version_info['version']}")
            print(f"- Last Updated: {version_info['last_updated']}")
            print(f"- Checksum: {version_info['checksum']}")
            print(f"- Dropbox Path: {sync_message}")

            return True

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            print(f"\nDeployment failed: {e}")
            return False


def main():
    """Main function to deploy the package."""
    deployer = StorefrontDeployer()

    if deployer.deploy():
        print("\nDeployment completed successfully!")
        print("\nNext steps:")
        print("1. Verify the package in Dropbox")
        print("2. Share the Dropbox link with your team")
        print("3. Monitor for any sync issues")
    else:
        print("\nDeployment failed. Check the logs for details.")


if __name__ == "__main__":
    main()
