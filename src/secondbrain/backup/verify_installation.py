#!/usr/bin/env python3

import os
import json
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/secondbrain_verify.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


def check_file_exists(file_path, description):
    """Check if a file exists and log the result."""
    exists = os.path.exists(file_path)
    status = "✅" if exists else "❌"
    logging.info(f"{status} {description}: {file_path}")
    return exists


def check_directory_exists(dir_path, description):
    """Check if a directory exists and log the result."""
    exists = os.path.isdir(dir_path)
    status = "✅" if exists else "❌"
    logging.info(f"{status} {description}: {dir_path}")
    return exists


def verify_config_files():
    """Verify all configuration files exist and are valid JSON."""
    config_files = {
        "voice_config.json": "Voice configuration",
        "cloud_config.json": "Cloud configuration",
    }

    all_valid = True
    for file_name, description in config_files.items():
        file_path = os.path.join("src/secondbrain/backup", file_name)
        if check_file_exists(file_path, description):
            try:
                with open(file_path, "r") as f:
                    json.load(f)
                logging.info(f"✅ {description} is valid JSON")
            except json.JSONDecodeError:
                logging.error(f"❌ {description} contains invalid JSON")
                all_valid = False
        else:
            all_valid = False

    return all_valid


def verify_launch_agents():
    """Verify LaunchAgent files exist."""
    launch_agents = {
        "com.secondbrain.backup.plist": "Backup LaunchAgent",
        "com.secondbrain.health.plist": "Health Monitor LaunchAgent",
    }

    all_exist = True
    for agent_name, description in launch_agents.items():
        agent_path = os.path.expanduser(f"~/Library/LaunchAgents/{agent_name}")
        if not check_file_exists(agent_path, description):
            all_exist = False

    return all_exist


def verify_backup_directories():
    """Verify backup directories exist."""
    directories = {
        "~/Documents/.secondbrain/backups": "Local backup directory",
        "~/Documents/SecondBrain_Backups": "Documentation backup directory",
    }

    all_exist = True
    for dir_path, description in directories.items():
        expanded_path = os.path.expanduser(dir_path)
        if not check_directory_exists(expanded_path, description):
            all_exist = False

    return all_exist


def verify_dmg():
    """Verify DMG file exists."""
    dmg_path = "SecondBrain Backup-1.0.0.dmg"
    return check_file_exists(dmg_path, "DMG package")


def main():
    """Main verification function."""
    logging.info("Starting SecondBrain installation verification...")

    checks = {
        "Configuration Files": verify_config_files(),
        "LaunchAgents": verify_launch_agents(),
        "Backup Directories": verify_backup_directories(),
        "DMG Package": verify_dmg(),
    }

    logging.info("\nVerification Summary:")
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        logging.info(f"{status} {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        logging.info("\n✅ All verifications passed successfully!")
    else:
        logging.error("\n❌ Some verifications failed. Please check the logs above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
