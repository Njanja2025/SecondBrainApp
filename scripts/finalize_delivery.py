"""
Final package preparation and distribution script.
"""

import os
import sys
import json
import shutil
import hashlib
import requests
from pathlib import Path
from datetime import datetime


def load_config():
    """Load delivery configuration."""
    try:
        with open("config/delivery_config.json", "r") as f:
            config = json.load(f)

        # Expand environment variables in paths
        for storage in config["cloud_storage"].values():
            if "path" in storage:
                storage["path"] = os.path.expandvars(storage["path"])

        if "path" in config["website"]:
            config["website"]["path"] = os.path.expandvars(config["website"]["path"])

        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


def ensure_app_structure():
    """Create basic app structure if it doesn't exist."""
    try:
        # Create necessary directories
        dirs = [
            "dist/SecondBrainApp.app/Contents/MacOS",
            "dist/SecondBrainApp.app/Contents/Resources",
            "src/secondbrain/phantom",
            "src/secondbrain/agents",
            "src/secondbrain/voice",
            "src/secondbrain/automation",
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

        # Create Info.plist if it doesn't exist
        info_plist = "dist/SecondBrainApp.app/Contents/Info.plist"
        if not os.path.exists(info_plist):
            with open(info_plist, "w") as f:
                f.write(
                    """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>SecondBrain</string>
    <key>CFBundleExecutable</key>
    <string>SecondBrain</string>
    <key>CFBundleIdentifier</key>
    <string>com.njanja.secondbrain</string>
    <key>CFBundleName</key>
    <string>SecondBrain</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
</dict>
</plist>"""
                )

        print("Basic app structure created")
        return True
    except Exception as e:
        print(f"Error creating app structure: {e}")
        return False


def create_package():
    """Create the final delivery package."""
    try:
        # Ensure app structure exists
        if not ensure_app_structure():
            return None

        # Create package directory
        package_dir = Path("delivery_package")
        package_dir.mkdir(exist_ok=True)

        # Copy .app
        print("Copying SecondBrainApp.app...")
        shutil.copytree(
            "dist/SecondBrainApp.app",
            package_dir / "SecondBrainApp.app",
            dirs_exist_ok=True,
        )

        # Copy core modules
        print("Copying core modules...")
        modules = [
            "src/secondbrain/phantom",
            "src/secondbrain/agents",
            "src/secondbrain/voice",
            "src/secondbrain/automation",
        ]
        for module in modules:
            if os.path.exists(module):
                dest = package_dir / Path(module).relative_to("src/secondbrain")
                dest.parent.mkdir(parents=True, exist_ok=True)
                if os.path.isdir(module):
                    shutil.copytree(module, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(module, dest)

        # Create version info
        version_info = {
            "version": "1.0.0",
            "build_date": datetime.now().isoformat(),
            "platform": "macOS",
            "python_version": sys.version,
        }
        with open(package_dir / "version.json", "w") as f:
            json.dump(version_info, f, indent=2)

        # Create ZIP archive
        print("Creating ZIP archive...")
        archive_name = f"SecondBrainApp_Package_{datetime.now().strftime('%Y%m%d')}.zip"
        shutil.make_archive(archive_name.rstrip(".zip"), "zip", package_dir)

        # Generate checksum
        print("Generating package hash...")
        sha256_hash = hashlib.sha256()
        with open(archive_name, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()

        # Save checksum
        with open(f"{archive_name}.sha256", "w") as f:
            f.write(checksum)

        return {
            "package": archive_name,
            "checksum": checksum,
            "version": version_info["version"],
        }

    except Exception as e:
        print(f"Error creating package: {e}")
        return None


def upload_to_cloud(package_info, config):
    """Upload package to cloud storage."""
    if not package_info or not config:
        return False

    try:
        package_file = package_info["package"]
        success = True

        # Upload to each configured cloud destination
        for cloud, storage in config["cloud_storage"].items():
            if not storage.get("enabled", False):
                continue

            try:
                path = storage["path"]
                os.makedirs(path, exist_ok=True)
                dest = os.path.join(path, package_file)
                shutil.copy2(package_file, dest)
                print(f"Uploaded to {cloud}: {dest}")
            except Exception as e:
                print(f"Failed to upload to {cloud}: {e}")
                success = False

        return success

    except Exception as e:
        print(f"Error uploading to cloud: {e}")
        return False


def create_github_release(package_info, config):
    """Create GitHub release."""
    if not package_info or not config:
        return False

    try:
        github_config = config["github"]
        token = github_config["token"]
        if token == "your_github_token_here":
            print("GitHub token not configured. Skipping release creation.")
            return False

        repo = github_config["repo"]
        api_url = f"https://api.github.com/repos/{repo}/releases"

        release_data = {
            "tag_name": f"v{package_info['version']}",
            "name": f"SecondBrain App v{package_info['version']}",
            "body": f"Release {package_info['version']}\n\nChecksum (SHA-256): {package_info['checksum']}",
            "draft": False,
            "prerelease": False,
        }

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.post(api_url, json=release_data, headers=headers)
        if response.status_code != 201:
            print(f"Error creating release: {response.text}")
            return False

        print(f"Created GitHub release: v{package_info['version']}")
        return True

    except Exception as e:
        print(f"Error creating GitHub release: {e}")
        return False


def update_website(package_info, config):
    """Update phantom.njanja.net website."""
    if not package_info or not config:
        return False

    try:
        website_config = config["website"]
        if not website_config.get("enabled", False):
            print("Website updates disabled in config")
            return False

        website_path = website_config["path"]
        if not website_path:
            print("Website path not configured")
            return False

        # Update download link
        download_info = {
            "version": package_info["version"],
            "file": package_info["package"],
            "checksum": package_info["checksum"],
            "date": datetime.now().isoformat(),
        }

        os.makedirs(website_path, exist_ok=True)
        with open(os.path.join(website_path, "download.json"), "w") as f:
            json.dump(download_info, f, indent=2)

        print("Updated website download information")
        return True

    except Exception as e:
        print(f"Error updating website: {e}")
        return False


def main():
    """Main delivery process."""
    print("Starting delivery process...")

    # Load configuration
    config = load_config()
    if not config:
        print("Failed to load configuration")
        return

    # Create package
    package_info = create_package()
    if not package_info:
        print("Failed to create package")
        return

    # Upload to cloud
    if upload_to_cloud(package_info, config):
        print("Cloud upload complete")
    else:
        print("Cloud upload failed")

    # Create GitHub release
    if create_github_release(package_info, config):
        print("GitHub release created")
    else:
        print("GitHub release failed")

    # Update website
    if update_website(package_info, config):
        print("Website updated")
    else:
        print("Website update failed")

    print("\nDelivery Summary:")
    print(f"Package: {package_info['package']}")
    print(f"Version: {package_info['version']}")
    print(f"Checksum: {package_info['checksum']}")
    print("\nDelivery channels:")
    print(f"- Dropbox: SecondBrain_2025_Deploy/{package_info['package']}")
    print("- Google Drive: Shared with:")
    for recipient in config["email"]["recipients"]:
        print(f"  * {recipient}")
    print(
        f"- GitHub: https://github.com/{config['github']['repo']}/releases/tag/v{package_info['version']}"
    )
    print(f"- Website: https://{config['website']['domain']}")


if __name__ == "__main__":
    main()
