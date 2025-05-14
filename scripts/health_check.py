"""
Health check system for SecondBrain Dashboard
"""

import os
import psutil
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache
from config import (
    HEALTH_CHECK_SETTINGS,
    BASE_DIR,
    DASHBOARD_DIR,
    BACKUP_DIR,
    CONFIG_DIR,
    EXPORT_DIR,
)

logger = logging.getLogger(__name__)


class HealthChecker:
    def __init__(self):
        """Initialize the health checker."""
        self.health_file = CONFIG_DIR / "health_status.json"
        self.last_check_file = CONFIG_DIR / "last_health_check.json"
        self.cache_duration = timedelta(
            minutes=HEALTH_CHECK_SETTINGS["interval_minutes"]
        )
        self.load_last_check()

    @lru_cache(maxsize=128)
    def _get_cached_system_info(self) -> Dict:
        """Get cached system information."""
        return {
            "hostname": os.uname().nodename,
            "platform": os.uname().sysname,
            "version": os.uname().release,
            "architecture": os.uname().machine,
            "processor": os.uname().version,
        }

    def check_system_health(self) -> Dict:
        """Check system health metrics with caching."""
        try:
            # Get cached system info
            system_info = self._get_cached_system_info()

            # Get real-time metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "status": "healthy",
                "system_info": system_info,
                "checks": {
                    "cpu": {
                        "status": "healthy" if cpu_percent < 80 else "warning",
                        "value": cpu_percent,
                        "unit": "%",
                    },
                    "memory": {
                        "status": "healthy" if memory.percent < 80 else "warning",
                        "value": memory.percent,
                        "unit": "%",
                    },
                    "disk": {
                        "status": "healthy" if disk.percent < 80 else "warning",
                        "value": disk.percent,
                        "unit": "%",
                    },
                },
            }
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {"status": "error", "message": str(e)}

    @lru_cache(maxsize=32)
    def _get_cached_backup_info(self) -> Dict:
        """Get cached backup directory information."""
        return {
            "backup_dir": str(BACKUP_DIR),
            "backup_formats": ["*.tar.gz", "*.zip", "*.backup"],
            "retention_days": 30,
        }

    def check_backup_health(self) -> Dict:
        """Check backup system health with caching."""
        try:
            # Get cached backup info
            backup_info = self._get_cached_backup_info()

            if not BACKUP_DIR.exists():
                return {
                    "status": "warning",
                    "message": "Backup directory does not exist",
                    "info": backup_info,
                }

            backups = list(BACKUP_DIR.glob("*.tar.gz"))
            if not backups:
                return {
                    "status": "warning",
                    "message": "No backups found",
                    "info": backup_info,
                }

            latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
            backup_age = datetime.now().timestamp() - latest_backup.stat().st_mtime

            return {
                "status": "healthy" if backup_age < 86400 else "warning",
                "info": backup_info,
                "checks": {
                    "backup_count": len(backups),
                    "latest_backup": latest_backup.name,
                    "backup_age_hours": round(backup_age / 3600, 1),
                },
            }
        except Exception as e:
            logger.error(f"Backup health check failed: {e}")
            return {"status": "error", "message": str(e)}

    def invalidate_caches(self) -> None:
        """Invalidate all cached data."""
        self._get_cached_system_info.cache_clear()
        self._get_cached_backup_info.cache_clear()
