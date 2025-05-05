"""
Enhanced automatic backup system with daily versioning.
"""
import shutil
import datetime
import os
from pathlib import Path
from typing import Dict, Any
from ..automation.automated_backup import AutomatedBackup
from ..phantom.phantom_core import PhantomCore

class PhantomBackupManager:
    def __init__(self, phantom: PhantomCore):
        """Initialize the Phantom backup manager."""
        self.phantom = phantom
        self.automated_backup = AutomatedBackup(phantom)
        
    def run_backup(self) -> Dict[str, Any]:
        """Run a complete backup of the SecondBrain app."""
        now = datetime.datetime.now()
        date_folder = Path("phantom_backups") / now.strftime("%Y/%m/%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        src = Path("dist/SecondBrainApp.app")
        dest = date_folder / f"SecondBrainApp_{now.strftime('%H-%M-%S')}.app"

        try:
            # Create versioned backup
            shutil.copytree(src, dest)
            self.phantom.log_event(
                "Phantom Backup",
                f"App backed up to {dest}",
                "INFO"
            )
            
            # Run full system backup
            backup_result = self.automated_backup.create_backup()
            
            # Sync to cloud if backup was successful
            if backup_result["status"] == "success":
                self.automated_backup.sync_to_cloud(backup_result)
                
            return {
                "status": "success",
                "local_backup": str(dest),
                "system_backup": backup_result
            }
            
        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            self.phantom.log_event("Phantom Backup", error_msg, "ERROR")
            return {
                "status": "error",
                "message": error_msg
            }
    
    def cleanup_old_backups(self, max_days: int = 30):
        """Clean up backups older than specified days."""
        try:
            backup_root = Path("phantom_backups")
            if not backup_root.exists():
                return
                
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=max_days)
            
            for year_dir in backup_root.glob("*"):
                if not year_dir.is_dir():
                    continue
                    
                for month_dir in year_dir.glob("*"):
                    if not month_dir.is_dir():
                        continue
                        
                    for day_dir in month_dir.glob("*"):
                        if not day_dir.is_dir():
                            continue
                            
                        dir_date = datetime.datetime.strptime(
                            f"{year_dir.name}/{month_dir.name}/{day_dir.name}",
                            "%Y/%m/%d"
                        )
                        
                        if dir_date < cutoff_date:
                            shutil.rmtree(day_dir)
                            self.phantom.log_event(
                                "Phantom Backup",
                                f"Cleaned up old backup: {day_dir}",
                                "INFO"
                            )
                            
        except Exception as e:
            self.phantom.log_event(
                "Phantom Backup",
                f"Cleanup failed: {str(e)}",
                "ERROR"
            ) 