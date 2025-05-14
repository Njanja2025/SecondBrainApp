"""
Njax Forge Sync - Handles synchronization of Njax dashboard and components
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
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("njax_sync.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class NjaxForgeSync:
    def __init__(self, config_path: str = "config/njax_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.njax_dir = Path(self.config.get("njax_dir", "njax"))
        self.components_dir = Path(self.config.get("components_dir", "njax/components"))
        self.backup_dir = Path(self.config.get("backup_dir", "backups/njax"))

        # Ensure directories exist
        self.njax_dir.mkdir(exist_ok=True)
        self.components_dir.mkdir(exist_ok=True)
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

    def backup_njax_system(self) -> bool:
        """Create a backup of the Njax system."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"njax_system_{timestamp}"

            # Create backup directory
            backup_path.mkdir(exist_ok=True)

            # Backup Njax files
            for njax_file in self.njax_dir.glob("**/*"):
                if njax_file.is_file():
                    rel_path = njax_file.relative_to(self.njax_dir)
                    backup_file = backup_path / rel_path
                    backup_file.parent.mkdir(exist_ok=True)
                    shutil.copy2(njax_file, backup_file)

            # Backup component files
            for component_file in self.components_dir.glob("**/*"):
                if component_file.is_file():
                    rel_path = component_file.relative_to(self.components_dir)
                    backup_file = backup_path / rel_path
                    backup_file.parent.mkdir(exist_ok=True)
                    shutil.copy2(component_file, backup_file)

            logger.info(f"Created Njax system backup at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup Njax system: {str(e)}")
            return False

    def sync_components(self, component_list: Optional[List[str]] = None) -> bool:
        """Synchronize Njax components."""
        try:
            # Backup current system
            if not self.backup_njax_system():
                return False

            # Get components to sync
            if component_list is None:
                component_list = [
                    d.name for d in self.components_dir.iterdir() if d.is_dir()
                ]

            for component in component_list:
                component_path = self.components_dir / component
                if not component_path.exists():
                    logger.error(f"Component {component} not found")
                    continue

                # Run component sync script
                sync_script = component_path / "sync.py"
                if sync_script.exists():
                    result = subprocess.run(
                        [sys.executable, str(sync_script)],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode != 0:
                        logger.error(
                            f"Failed to sync component {component}: {result.stderr}"
                        )
                        continue

                # Update component manifest
                manifest_file = component_path / "manifest.json"
                if manifest_file.exists():
                    with open(manifest_file, "r") as f:
                        manifest = json.load(f)

                    # Update manifest
                    manifest["last_sync"] = datetime.now().isoformat()
                    manifest["version"] = self._get_component_version(component_path)

                    with open(manifest_file, "w") as f:
                        json.dump(manifest, f, indent=2)

            logger.info("Successfully synchronized Njax components")
            return True
        except Exception as e:
            logger.error(f"Failed to sync components: {str(e)}")
            return False

    def _get_component_version(self, component_path: Path) -> str:
        """Get the version of a component based on its files."""
        try:
            # Calculate hash of component files
            hasher = hashlib.sha256()
            for file_path in sorted(component_path.glob("**/*")):
                if file_path.is_file():
                    with open(file_path, "rb") as f:
                        hasher.update(f.read())
            return hasher.hexdigest()[:8]
        except Exception as e:
            logger.error(f"Failed to get component version: {str(e)}")
            return "unknown"

    def verify_sync(self) -> bool:
        """Verify that the Njax system is properly synchronized."""
        try:
            # Check component manifests
            for component_path in self.components_dir.iterdir():
                if not component_path.is_dir():
                    continue

                manifest_file = component_path / "manifest.json"
                if not manifest_file.exists():
                    logger.error(
                        f"Missing manifest for component {component_path.name}"
                    )
                    return False

                # Verify component files
                with open(manifest_file, "r") as f:
                    manifest = json.load(f)

                for file_info in manifest.get("files", []):
                    file_path = component_path / file_info["path"]
                    if not file_path.exists():
                        logger.error(
                            f"Missing file {file_path} in component {component_path.name}"
                        )
                        return False

            # Run Njax tests
            test_script = self.njax_dir / "tests.py"
            if test_script.exists():
                result = subprocess.run(
                    [sys.executable, str(test_script)], capture_output=True, text=True
                )
                if result.returncode != 0:
                    logger.error(f"Njax tests failed: {result.stderr}")
                    return False

            logger.info("Njax system verification successful")
            return True
        except Exception as e:
            logger.error(f"Failed to verify Njax system: {str(e)}")
            return False

    def rollback_sync(self) -> bool:
        """Rollback the Njax system to its previous state."""
        try:
            # Find latest backup
            backups = sorted(
                self.backup_dir.glob("njax_system_*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            if not backups:
                logger.error("No Njax system backups found")
                return False

            latest_backup = backups[0]

            # Restore Njax files
            for backup_file in latest_backup.glob("**/*"):
                if backup_file.is_file():
                    rel_path = backup_file.relative_to(latest_backup)
                    target_file = self.njax_dir / rel_path
                    target_file.parent.mkdir(exist_ok=True)
                    shutil.copy2(backup_file, target_file)

            logger.info(f"Successfully rolled back Njax system to {latest_backup}")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback Njax system: {str(e)}")
            return False

    def get_sync_status(self) -> Dict:
        """Get the current status of the Njax system."""
        try:
            status = {"components": {}, "last_sync": None, "health": "unknown"}

            # Get component status
            for component_path in self.components_dir.iterdir():
                if not component_path.is_dir():
                    continue

                manifest_file = component_path / "manifest.json"
                if manifest_file.exists():
                    with open(manifest_file, "r") as f:
                        manifest = json.load(f)
                        status["components"][component_path.name] = {
                            "version": manifest.get("version"),
                            "last_sync": manifest.get("last_sync"),
                        }

            # Get last sync time
            sync_file = self.njax_dir / "sync_status.json"
            if sync_file.exists():
                with open(sync_file, "r") as f:
                    sync_status = json.load(f)
                    status["last_sync"] = sync_status.get("last_sync")

            # Check health
            if self.verify_sync():
                status["health"] = "healthy"
            else:
                status["health"] = "unhealthy"

            return status
        except Exception as e:
            logger.error(f"Failed to get Njax system status: {str(e)}")
            return {"error": str(e)}


def main():
    """Main entry point for the Njax forge sync system."""
    sync = NjaxForgeSync()

    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python njax_forge_sync.py [component1 component2 ...]")
        sys.exit(1)

    components = sys.argv[1:] if len(sys.argv) > 1 else None

    # Sync components
    if sync.sync_components(components):
        # Verify sync
        if sync.verify_sync():
            print("Successfully synchronized and verified Njax system")
        else:
            print("Njax system verification failed")
            # Rollback if verification fails
            if sync.rollback_sync():
                print("Successfully rolled back Njax system")
            else:
                print("Failed to rollback Njax system")
    else:
        print("Failed to synchronize Njax system")


if __name__ == "__main__":
    main()
