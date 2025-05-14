"""
Script to generate voice-over and deploy the Njanja Storefront package
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
from typing import Optional, Tuple, Dict
import tempfile
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VoiceGenerator:
    def __init__(self):
        """Initialize voice generator."""
        self.voice = "Samantha"
        self.temp_dir = tempfile.mkdtemp()

    def __del__(self):
        """Clean up temporary directory."""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory: {e}")

    def check_ffmpeg(self) -> bool:
        """Check if ffmpeg is installed."""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def generate_voice(self, text: str, output_path: str) -> Tuple[bool, str]:
        """Generate voice-over using macOS say command."""
        try:
            if platform.system() != "Darwin":
                return False, "Voice generation requires macOS"

            # Create temporary AIFF file
            temp_aiff = os.path.join(self.temp_dir, "temp_voice.aiff")

            # Generate voice using say command
            say_cmd = ["say", "-v", self.voice, "-o", temp_aiff, text]
            subprocess.run(say_cmd, check=True)

            # Convert to MP3 if ffmpeg is available
            if self.check_ffmpeg():
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    temp_aiff,
                    "-codec:a",
                    "libmp3lame",
                    "-qscale:a",
                    "2",
                    output_path,
                ]
                subprocess.run(ffmpeg_cmd, check=True)
            else:
                # If ffmpeg is not available, just rename the AIFF file
                shutil.copy2(temp_aiff, output_path)
                logger.warning("ffmpeg not found. Using AIFF format instead of MP3.")

            # Verify the output file
            if not os.path.exists(output_path):
                return False, "Failed to create output file"

            # Get file duration using ffmpeg
            if self.check_ffmpeg():
                duration_cmd = [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    output_path,
                ]
                duration = float(subprocess.check_output(duration_cmd).decode().strip())
                logger.info(f"Generated voice-over duration: {duration:.2f} seconds")

            return True, output_path

        except Exception as e:
            logger.error(f"Voice generation failed: {e}")
            return False, str(e)


class StorefrontDeployer:
    def __init__(self, base_dir: str = "storefront"):
        """Initialize the deployer with base directory."""
        self.base_dir = os.path.abspath(base_dir)
        self.package_name = "NjanjaStorefront_Package.zip"
        self.dropbox_path = os.path.expanduser("~/Dropbox/NjanjaStore")
        self.version_file = "version.json"
        self.voice_generator = VoiceGenerator()

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
            "voice_over": {"generated": False, "duration": None, "checksum": None},
        }

    def update_version_info(self, checksum: str, voice_info: Dict = None) -> None:
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

        if voice_info:
            version_info["voice_over"] = voice_info

        version_path = os.path.join(self.base_dir, self.version_file)
        with open(version_path, "w") as f:
            json.dump(version_info, f, indent=2)

    def generate_voice_over(self) -> Tuple[bool, str]:
        """Generate voice-over for the homepage intro."""
        try:
            # Read the voice script
            script_path = os.path.join(
                self.base_dir, "voice_scripts/homepage_intro.txt"
            )
            with open(script_path, "r") as f:
                text = f.read().strip()

            # Generate voice-over
            output_path = os.path.join(
                self.base_dir, "voice_scripts/homepage_intro.mp3"
            )
            success, result = self.voice_generator.generate_voice(text, output_path)

            if success:
                # Calculate voice-over checksum
                checksum = self.calculate_checksum(output_path)

                # Get file duration
                duration = None
                if self.voice_generator.check_ffmpeg():
                    duration_cmd = [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "default=noprint_wrappers=1:nokey=1",
                        output_path,
                    ]
                    duration = float(
                        subprocess.check_output(duration_cmd).decode().strip()
                    )

                # Update version info with voice-over details
                voice_info = {
                    "generated": True,
                    "duration": duration,
                    "checksum": checksum,
                }
                self.update_version_info(None, voice_info)

                return True, output_path
            else:
                return False, result

        except Exception as e:
            logger.error(f"Voice-over generation failed: {e}")
            return False, str(e)

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

            # Wait for Dropbox sync
            self._wait_for_dropbox_sync()

            logger.info(f"Synced package to Dropbox: {dropbox_package_path}")
            return True, dropbox_package_path

        except Exception as e:
            logger.error(f"Failed to sync to Dropbox: {e}")
            return False, str(e)

    def _wait_for_dropbox_sync(self, timeout: int = 60) -> bool:
        """Wait for Dropbox sync to complete."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if file exists and has been synced
                dropbox_package_path = os.path.join(
                    self.dropbox_path, self.package_name
                )
                if os.path.exists(dropbox_package_path):
                    # Check if file size matches
                    local_size = os.path.getsize(
                        os.path.join(os.getcwd(), self.package_name)
                    )
                    dropbox_size = os.path.getsize(dropbox_package_path)
                    if local_size == dropbox_size:
                        return True
            except Exception:
                pass
            time.sleep(1)
        return False

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
                "version.json",
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
            # Generate voice-over
            print("\nGenerating voice-over...")
            voice_success, voice_result = self.generate_voice_over()
            if not voice_success:
                print(f"\nVoice-over generation failed: {voice_result}")
                return False
            print(f"\nVoice-over generated successfully: {voice_result}")

            # Verify package
            print("\nVerifying package...")
            verify_success, verify_message = self.verify_package()
            if not verify_success:
                print(f"\nPackage verification failed: {verify_message}")
                return False
            print("\nPackage verification successful")

            # Sync to Dropbox
            print("\nSyncing to Dropbox...")
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
            print(f"- Package Checksum: {version_info['checksum']}")
            print(
                f"- Voice-over Duration: {version_info['voice_over']['duration']:.2f} seconds"
            )
            print(f"- Voice-over Checksum: {version_info['voice_over']['checksum']}")
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
        print("4. Test the voice-over playback")
    else:
        print("\nDeployment failed. Check the logs for details.")


if __name__ == "__main__":
    main()
