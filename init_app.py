#!/usr/bin/env python3
"""
Initialize SecondBrain application environment
"""
import os
import sys
import json
import shutil
from pathlib import Path


def create_directory_structure():
    """Create required directory structure."""
    base_dir = os.path.expanduser("~/secondbrain")
    directories = [
        "dashboard",
        "backups",
        "logs",
        "config",
        "memory",
        "exports",
        "cache",
        "temp",
    ]

    for dir_name in directories:
        dir_path = Path(base_dir) / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")


def copy_config_files():
    """Copy configuration files to the config directory."""
    base_dir = os.path.expanduser("~/secondbrain")
    config_dir = Path(base_dir) / "config"

    # Copy configuration files
    source_files = [
        "config/alerts.json",
        "config/backup_config.json",
        "config/health_check.json",
    ]

    for file_path in source_files:
        if Path(file_path).exists():
            dest_path = config_dir / Path(file_path).name
            shutil.copy2(file_path, dest_path)
            print(f"Copied config file: {dest_path}")


def main():
    """Initialize the application environment."""
    try:
        print("Initializing SecondBrain application environment...")

        # Create directory structure
        create_directory_structure()

        # Copy configuration files
        copy_config_files()

        print("\nInitialization completed successfully!")
        print(
            "\nPlease set up your environment variables in a .env file with the following:"
        )
        print(
            """
# Email Configuration
SMTP_USERNAME=your.email@gmail.com
SMTP_APP_PASSWORD=your-gmail-app-password
ALERT_FROM_EMAIL=your.email@gmail.com
ALERT_TO_EMAIL=recipient.email@example.com

# Cloud Storage Configuration
DROPBOX_API_KEY=your-dropbox-api-key
DROPBOX_APP_SECRET=your-dropbox-app-secret
GDRIVE_CLIENT_ID=your-gdrive-client-id
GDRIVE_CLIENT_SECRET=your-gdrive-client-secret
GITHUB_ACCESS_TOKEN=your-github-personal-access-token

# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your-webhook-url

# Application Settings
SECONDBRAIN_BASE_DIR=~/secondbrain
ENABLE_GUI=true
ENABLE_ALERTS=true
ENABLE_EMAIL_ALERTS=true
ENABLE_HEALTH_CHECKS=true
LOG_LEVEL=INFO
        """
        )

    except Exception as e:
        print(f"Error during initialization: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
