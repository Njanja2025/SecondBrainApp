"""
Basic ventilation protocol for SecondBrain app.
Handles system cleanup and maintenance.
"""
import os
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class VentilationProtocol:
    def __init__(self):
        """Initialize ventilation protocol."""
        self.temp_dir = Path("temp")
        self.log_dir = Path("logs")
        self.cache_dir = Path("cache")
        
        # Create directories
        for directory in [self.temp_dir, self.log_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
    def _clear_temp_files(self):
        """Clear temporary files."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(parents=True)
            logger.info("Cleared temporary files")
        except Exception as e:
            logger.error(f"Error clearing temp files: {e}")
            
    def _clear_cache_directories(self):
        """Clear cache directories."""
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True)
            logger.info("Cleared cache directories")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            
    def _archive_logs(self):
        """Archive log files."""
        try:
            if self.log_dir.exists():
                archive_dir = self.log_dir / "archive"
                archive_dir.mkdir(parents=True, exist_ok=True)
                
                # Move old logs to archive
                for log_file in self.log_dir.glob("*.log"):
                    if log_file.stat().st_mtime < (datetime.now().timestamp() - 86400):  # Older than 1 day
                        shutil.move(str(log_file), str(archive_dir / log_file.name))
                        
            logger.info("Archived old logs")
        except Exception as e:
            logger.error(f"Error archiving logs: {e}")
            
    def run(self):
        """Run ventilation protocol."""
        try:
            logger.info("Starting ventilation protocol...")
            
            # Clear temporary files
            self._clear_temp_files()
            
            # Clear cache
            self._clear_cache_directories()
            
            # Archive logs
            self._archive_logs()
            
            logger.info("Ventilation protocol completed")
            
        except Exception as e:
            logger.error(f"Error in ventilation protocol: {e}")

def ventilate():
    """Run ventilation protocol."""
    protocol = VentilationProtocol()
    protocol.run() 