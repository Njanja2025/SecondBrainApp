"""
Agent Upgrade System - Handles remote module enhancements and updates
"""

import os
import sys
import json
import logging
import subprocess
from typing import Dict, List, Optional
from datetime import datetime
import requests
import git
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("agent_upgrade.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AgentUpgrader:
    def __init__(self, config_path: str = "config/agent_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.repo_path = Path(self.config.get("repo_path", "."))
        self.backup_dir = Path(self.config.get("backup_dir", "backups"))
        self.modules_dir = Path(self.config.get("modules_dir", "modules"))

        # Ensure directories exist
        self.backup_dir.mkdir(exist_ok=True)
        self.modules_dir.mkdir(exist_ok=True)

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

    def backup_module(self, module_name: str) -> bool:
        """Create a backup of a module before upgrading."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{module_name}_{timestamp}.zip"

            # Create backup using git archive
            subprocess.run(
                [
                    "git",
                    "archive",
                    "--format=zip",
                    f"--output={backup_path}",
                    "HEAD",
                    f"modules/{module_name}",
                ],
                check=True,
            )

            logger.info(f"Created backup of {module_name} at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup {module_name}: {str(e)}")
            return False

    def upgrade_module(self, module_name: str, version: Optional[str] = None) -> bool:
        """Upgrade a specific module to the specified version."""
        try:
            # Backup current version
            if not self.backup_module(module_name):
                return False

            # Pull latest changes
            repo = git.Repo(self.repo_path)
            repo.remotes.origin.pull()

            # Checkout specific version if provided
            if version:
                repo.git.checkout(version)

            # Run module-specific upgrade script if it exists
            upgrade_script = self.modules_dir / module_name / "upgrade.py"
            if upgrade_script.exists():
                subprocess.run([sys.executable, str(upgrade_script)], check=True)

            logger.info(
                f"Successfully upgraded {module_name} to version {version or 'latest'}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upgrade {module_name}: {str(e)}")
            return False

    def verify_upgrade(self, module_name: str) -> bool:
        """Verify that a module upgrade was successful."""
        try:
            # Run module tests
            test_script = self.modules_dir / module_name / "tests.py"
            if test_script.exists():
                result = subprocess.run(
                    [sys.executable, str(test_script)], capture_output=True, text=True
                )
                if result.returncode != 0:
                    logger.error(f"Module tests failed: {result.stderr}")
                    return False

            # Check module health
            health_script = self.modules_dir / module_name / "health_check.py"
            if health_script.exists():
                result = subprocess.run(
                    [sys.executable, str(health_script)], capture_output=True, text=True
                )
                if result.returncode != 0:
                    logger.error(f"Health check failed: {result.stderr}")
                    return False

            logger.info(f"Successfully verified upgrade of {module_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to verify upgrade of {module_name}: {str(e)}")
            return False

    def rollback_upgrade(self, module_name: str) -> bool:
        """Rollback a module to its previous version."""
        try:
            # Find latest backup
            backups = sorted(
                self.backup_dir.glob(f"{module_name}_*.zip"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            if not backups:
                logger.error(f"No backups found for {module_name}")
                return False

            latest_backup = backups[0]

            # Restore from backup
            subprocess.run(
                ["unzip", "-o", str(latest_backup), "-d", str(self.repo_path)],
                check=True,
            )

            logger.info(f"Successfully rolled back {module_name} to previous version")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback {module_name}: {str(e)}")
            return False

    def get_module_status(self, module_name: str) -> Dict:
        """Get the current status of a module."""
        try:
            status = {
                "name": module_name,
                "version": None,
                "last_upgrade": None,
                "health": "unknown",
            }

            # Get version from module
            version_file = self.modules_dir / module_name / "version.txt"
            if version_file.exists():
                with open(version_file, "r") as f:
                    status["version"] = f.read().strip()

            # Get last upgrade time from git
            repo = git.Repo(self.repo_path)
            for commit in repo.iter_commits(paths=f"modules/{module_name}"):
                status["last_upgrade"] = commit.committed_datetime.isoformat()
                break

            # Check health
            health_script = self.modules_dir / module_name / "health_check.py"
            if health_script.exists():
                result = subprocess.run(
                    [sys.executable, str(health_script)], capture_output=True, text=True
                )
                status["health"] = "healthy" if result.returncode == 0 else "unhealthy"

            return status
        except Exception as e:
            logger.error(f"Failed to get status for {module_name}: {str(e)}")
            return {"name": module_name, "error": str(e)}


def main():
    """Main entry point for the agent upgrade system."""
    upgrader = AgentUpgrader()

    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python agent_upgrader.py <module_name> [version]")
        sys.exit(1)

    module_name = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else None

    # Perform upgrade
    if upgrader.upgrade_module(module_name, version):
        # Verify upgrade
        if upgrader.verify_upgrade(module_name):
            print(f"Successfully upgraded and verified {module_name}")
        else:
            print(f"Upgrade verification failed for {module_name}")
            # Rollback if verification fails
            if upgrader.rollback_upgrade(module_name):
                print(f"Successfully rolled back {module_name}")
            else:
                print(f"Failed to rollback {module_name}")
    else:
        print(f"Failed to upgrade {module_name}")


if __name__ == "__main__":
    main()
