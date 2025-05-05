"""
Automated backup system with security scanning and monitoring.
"""
import os
import sys
import time
import shutil
import logging
import schedule
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..security.security_scanner import SecurityScanner
from ..monitoring.metrics_collector import MetricsCollector
from ..phantom.phantom_core import PhantomCore

logger = logging.getLogger(__name__)

class AutomatedBackup:
    def __init__(self, phantom: PhantomCore):
        """Initialize automated backup system."""
        self.phantom = phantom
        self.security_scanner = SecurityScanner(phantom)
        self.metrics_collector = MetricsCollector()
        
        # Configure backup paths
        self.backup_root = Path("backups")
        self.backup_root.mkdir(exist_ok=True)
        
        # Configure cloud paths
        self.cloud_paths = {
            "dropbox": os.getenv("DROPBOX_BACKUP_PATH"),
            "gdrive": os.getenv("GDRIVE_BACKUP_PATH"),
            "github": os.getenv("GITHUB_REPO_PATH")
        }
        
        # Initialize metrics
        self.backup_counter = self.metrics_collector.Counter(
            'backup_operations_total',
            'Total number of backup operations'
        )
        self.backup_duration = self.metrics_collector.Histogram(
            'backup_duration_seconds',
            'Backup operation duration'
        )
        
    def generate_package_hash(self, package_path: str) -> str:
        """Generate SHA-256 hash of the package."""
        sha256_hash = hashlib.sha256()
        with open(package_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def verify_package_integrity(self, package_path: str, stored_hash: str) -> bool:
        """Verify package integrity using stored hash."""
        current_hash = self.generate_package_hash(package_path)
        return current_hash == stored_hash
    
    def encrypt_package(self, package_path: str, encryption_key: str) -> str:
        """Encrypt the package using provided key."""
        encrypted_path = f"{package_path}.encrypted"
        # TODO: Implement encryption logic
        return encrypted_path
    
    def perform_security_scan(self) -> Dict[str, Any]:
        """Perform comprehensive security scan."""
        app_path = "dist/SecondBrainApp.app"
        
        scan_results = {
            "file_scan": self.security_scanner.scan_directory(app_path),
            "process_scan": self.security_scanner.scan_running_processes(),
            "network_scan": self.security_scanner.scan_network_activity()
        }
        
        # Log any security issues
        if scan_results["file_scan"]["threats_found"] > 0:
            self.phantom.log_event(
                "Backup Security",
                f"Found {scan_results['file_scan']['threats_found']} threats during pre-backup scan",
                "WARNING"
            )
        
        return scan_results
    
    def create_backup(self) -> Dict[str, Any]:
        """Create a new backup with security verification."""
        start_time = time.time()
        
        try:
            # Perform security scan
            security_scan = self.perform_security_scan()
            
            # Generate timestamp for backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backup_root / timestamp
            backup_dir.mkdir(exist_ok=True)
            
            # Copy .app package
            app_path = Path("dist/SecondBrainApp.app")
            backup_app_path = backup_dir / "SecondBrainApp.app"
            shutil.copytree(app_path, backup_app_path)
            
            # Generate package hash
            package_hash = self.generate_package_hash(str(backup_app_path))
            
            # Create backup manifest
            manifest = {
                "timestamp": timestamp,
                "package_hash": package_hash,
                "security_scan": security_scan,
                "system_metrics": self.metrics_collector.collect_system_metrics()
            }
            
            # Save manifest
            with open(backup_dir / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            
            # Create zip archive
            archive_path = backup_dir / f"SecondBrainApp_Package_{timestamp}.zip"
            shutil.make_archive(
                str(archive_path.with_suffix('')),
                'zip',
                str(backup_dir)
            )
            
            # Optional: Encrypt package
            if os.getenv("ENABLE_ENCRYPTION"):
                encrypted_path = self.encrypt_package(
                    str(archive_path),
                    os.getenv("ENCRYPTION_KEY")
                )
                archive_path = Path(encrypted_path)
            
            # Update metrics
            self.backup_counter.inc()
            duration = time.time() - start_time
            self.backup_duration.observe(duration)
            
            # Log success
            self.phantom.log_event(
                "Backup",
                f"Successfully created backup: {timestamp}",
                "INFO"
            )
            
            return {
                "status": "success",
                "timestamp": timestamp,
                "backup_path": str(archive_path),
                "package_hash": package_hash,
                "duration": duration
            }
            
        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            self.phantom.log_event("Backup", error_msg, "ERROR")
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    def sync_to_cloud(self, backup_result: Dict[str, Any]):
        """Sync backup to configured cloud storage."""
        if backup_result["status"] != "success":
            return
        
        backup_path = Path(backup_result["backup_path"])
        
        # Sync to each configured cloud destination
        for cloud, path in self.cloud_paths.items():
            if path:
                try:
                    cloud_backup_path = Path(path) / backup_path.name
                    shutil.copy2(backup_path, cloud_backup_path)
                    
                    self.phantom.log_event(
                        "Cloud Sync",
                        f"Synced backup to {cloud}: {cloud_backup_path}",
                        "INFO"
                    )
                except Exception as e:
                    self.phantom.log_event(
                        "Cloud Sync",
                        f"Failed to sync to {cloud}: {str(e)}",
                        "ERROR"
                    )
    
    def cleanup_old_backups(self, max_backups: int = 7):
        """Clean up old backups, keeping only the specified number."""
        backups = sorted(self.backup_root.glob("*"))
        if len(backups) > max_backups:
            for backup in backups[:-max_backups]:
                shutil.rmtree(backup)
                self.phantom.log_event(
                    "Backup Cleanup",
                    f"Removed old backup: {backup.name}",
                    "INFO"
                )
    
    def schedule_daily_backup(self, time: str = "00:00"):
        """Schedule daily backup at specified time."""
        def backup_job():
            backup_result = self.create_backup()
            self.sync_to_cloud(backup_result)
            self.cleanup_old_backups()
        
        schedule.every().day.at(time).do(backup_job)
        
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    phantom = PhantomCore()
    backup_system = AutomatedBackup(phantom)
    backup_system.schedule_daily_backup() 