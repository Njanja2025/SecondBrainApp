"""
Companion Journaling Backup System for SecondBrain.
Handles comprehensive backup of journal entries, emotional logs, memory entries, and interaction patterns.
"""

import os
import json
import shutil
import logging
import hashlib
import gzip
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
from dataclasses import dataclass
import schedule

from ..memory.agent_memory import AgentMemory
from ..memory.persona_memory import MemoryEngine
from ..persona.emotion_adapter import EmotionAdapter
from ..cloud.log_reporter import BackupLogReport
from ..memory.cloud_backup import CloudBackupManager

logger = logging.getLogger(__name__)


@dataclass
class BackupStats:
    """Statistics for a backup operation."""

    total_entries: int
    total_size: int
    entry_types: Dict[str, int]
    backup_duration: float
    compression_ratio: float
    success: bool
    error_message: Optional[str] = None


class CompanionJournalingBackup:
    """Manages comprehensive backup of companion journaling data."""

    def __init__(
        self,
        backup_root: str = "backups/journaling",
        enable_cloud_sync: bool = True,
        max_backups: int = 30,
    ):
        """Initialize the companion journaling backup system."""
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.enable_cloud_sync = enable_cloud_sync
        self.max_backups = max_backups

        # Initialize components
        self.cloud_backup = CloudBackupManager() if enable_cloud_sync else None
        self.log_reporter = BackupLogReport()

        # Backup paths
        self.paths = {
            "journal_entries": Path("data/journal"),
            "emotional_logs": Path("logs/emotional"),
            "memory_entries": Path("data/memory"),
            "interaction_patterns": Path("data/patterns"),
        }

        # Ensure all directories exist
        for path in self.paths.values():
            path.mkdir(parents=True, exist_ok=True)

    async def create_backup(self) -> Dict[str, Any]:
        """Create a comprehensive backup of all journaling data."""
        start_time = datetime.now()
        backup_dir = self._create_backup_directory()

        try:
            # Backup journal entries
            journal_stats = await self._backup_journal_entries(backup_dir)

            # Backup emotional logs
            emotional_stats = await self._backup_emotional_logs(backup_dir)

            # Backup memory entries
            memory_stats = await self._backup_memory_entries(backup_dir)

            # Backup interaction patterns
            pattern_stats = await self._backup_interaction_patterns(backup_dir)

            # Create backup manifest
            manifest = self._create_backup_manifest(
                backup_dir, journal_stats, emotional_stats, memory_stats, pattern_stats
            )

            # Create archive
            archive_path = self._create_archive(backup_dir)

            # Sync to cloud if enabled
            if self.enable_cloud_sync:
                await self._sync_to_cloud(archive_path)

            # Cleanup old backups
            self._cleanup_old_backups()

            duration = (datetime.now() - start_time).total_seconds()

            return {
                "status": "success",
                "backup_path": str(archive_path),
                "manifest": manifest,
                "duration": duration,
            }

        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def _create_backup_directory(self) -> Path:
        """Create a new backup directory with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    async def _backup_journal_entries(self, backup_dir: Path) -> BackupStats:
        """Backup journal entries with compression."""
        try:
            journal_dir = backup_dir / "journal_entries"
            journal_dir.mkdir(exist_ok=True)

            total_entries = 0
            entry_types = {}

            # Copy and compress journal entries
            for entry_file in self.paths["journal_entries"].glob("*.json"):
                if entry_file.is_file():
                    with open(entry_file) as f:
                        entry = json.load(f)
                        entry_type = entry.get("type", "unknown")
                        entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
                        total_entries += 1

                        # Save to backup with compression
                        backup_file = journal_dir / f"{entry_file.stem}.json.gz"
                        with gzip.open(backup_file, "wt") as gzf:
                            json.dump(entry, gzf)

            total_size = sum(f.stat().st_size for f in journal_dir.glob("*"))

            return BackupStats(
                total_entries=total_entries,
                total_size=total_size,
                entry_types=entry_types,
                backup_duration=0.0,  # Will be calculated in main backup
                compression_ratio=0.0,  # Will be calculated in main backup
                success=True,
            )

        except Exception as e:
            logger.error(f"Failed to backup journal entries: {e}")
            return BackupStats(
                total_entries=0,
                total_size=0,
                entry_types={},
                backup_duration=0.0,
                compression_ratio=0.0,
                success=False,
                error_message=str(e),
            )

    async def _backup_emotional_logs(self, backup_dir: Path) -> BackupStats:
        """Backup emotional logs with analysis."""
        try:
            emotional_dir = backup_dir / "emotional_logs"
            emotional_dir.mkdir(exist_ok=True)

            total_entries = 0
            entry_types = {}

            # Copy and analyze emotional logs
            for log_file in self.paths["emotional_logs"].glob("*.json"):
                if log_file.is_file():
                    with open(log_file) as f:
                        logs = json.load(f)
                        total_entries += len(logs)

                        # Analyze emotional patterns
                        for entry in logs:
                            emotion_type = entry.get("emotion", "unknown")
                            entry_types[emotion_type] = (
                                entry_types.get(emotion_type, 0) + 1
                            )

                        # Save to backup
                        backup_file = emotional_dir / log_file.name
                        shutil.copy2(log_file, backup_file)

            total_size = sum(f.stat().st_size for f in emotional_dir.glob("*"))

            return BackupStats(
                total_entries=total_entries,
                total_size=total_size,
                entry_types=entry_types,
                backup_duration=0.0,
                compression_ratio=0.0,
                success=True,
            )

        except Exception as e:
            logger.error(f"Failed to backup emotional logs: {e}")
            return BackupStats(
                total_entries=0,
                total_size=0,
                entry_types={},
                backup_duration=0.0,
                compression_ratio=0.0,
                success=False,
                error_message=str(e),
            )

    async def _backup_memory_entries(self, backup_dir: Path) -> BackupStats:
        """Backup memory entries with compression."""
        try:
            memory_dir = backup_dir / "memory_entries"
            memory_dir.mkdir(exist_ok=True)

            total_entries = 0
            entry_types = {}

            # Copy and compress memory entries
            for memory_file in self.paths["memory_entries"].glob("*.json"):
                if memory_file.is_file():
                    with open(memory_file) as f:
                        memories = json.load(f)
                        total_entries += len(memories)

                        # Analyze memory types
                        for entry in memories:
                            memory_type = entry.get("type", "unknown")
                            entry_types[memory_type] = (
                                entry_types.get(memory_type, 0) + 1
                            )

                        # Save to backup with compression
                        backup_file = memory_dir / f"{memory_file.stem}.json.gz"
                        with gzip.open(backup_file, "wt") as gzf:
                            json.dump(memories, gzf)

            total_size = sum(f.stat().st_size for f in memory_dir.glob("*"))

            return BackupStats(
                total_entries=total_entries,
                total_size=total_size,
                entry_types=entry_types,
                backup_duration=0.0,
                compression_ratio=0.0,
                success=True,
            )

        except Exception as e:
            logger.error(f"Failed to backup memory entries: {e}")
            return BackupStats(
                total_entries=0,
                total_size=0,
                entry_types={},
                backup_duration=0.0,
                compression_ratio=0.0,
                success=False,
                error_message=str(e),
            )

    async def _backup_interaction_patterns(self, backup_dir: Path) -> BackupStats:
        """Backup interaction patterns with analysis."""
        try:
            pattern_dir = backup_dir / "interaction_patterns"
            pattern_dir.mkdir(exist_ok=True)

            total_entries = 0
            entry_types = {}

            # Copy and analyze interaction patterns
            for pattern_file in self.paths["interaction_patterns"].glob("*.json"):
                if pattern_file.is_file():
                    with open(pattern_file) as f:
                        patterns = json.load(f)
                        total_entries += len(patterns)

                        # Analyze pattern types
                        for entry in patterns:
                            pattern_type = entry.get("type", "unknown")
                            entry_types[pattern_type] = (
                                entry_types.get(pattern_type, 0) + 1
                            )

                        # Save to backup
                        backup_file = pattern_dir / pattern_file.name
                        shutil.copy2(pattern_file, backup_file)

            total_size = sum(f.stat().st_size for f in pattern_dir.glob("*"))

            return BackupStats(
                total_entries=total_entries,
                total_size=total_size,
                entry_types=entry_types,
                backup_duration=0.0,
                compression_ratio=0.0,
                success=True,
            )

        except Exception as e:
            logger.error(f"Failed to backup interaction patterns: {e}")
            return BackupStats(
                total_entries=0,
                total_size=0,
                entry_types={},
                backup_duration=0.0,
                compression_ratio=0.0,
                success=False,
                error_message=str(e),
            )

    def _create_backup_manifest(
        self,
        backup_dir: Path,
        journal_stats: BackupStats,
        emotional_stats: BackupStats,
        memory_stats: BackupStats,
        pattern_stats: BackupStats,
    ) -> Dict[str, Any]:
        """Create a comprehensive backup manifest."""
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "backup_id": backup_dir.name,
            "components": {
                "journal_entries": {
                    "total_entries": journal_stats.total_entries,
                    "total_size": journal_stats.total_size,
                    "entry_types": journal_stats.entry_types,
                    "success": journal_stats.success,
                    "error": journal_stats.error_message,
                },
                "emotional_logs": {
                    "total_entries": emotional_stats.total_entries,
                    "total_size": emotional_stats.total_size,
                    "entry_types": emotional_stats.entry_types,
                    "success": emotional_stats.success,
                    "error": emotional_stats.error_message,
                },
                "memory_entries": {
                    "total_entries": memory_stats.total_entries,
                    "total_size": memory_stats.total_size,
                    "entry_types": memory_stats.entry_types,
                    "success": memory_stats.success,
                    "error": memory_stats.error_message,
                },
                "interaction_patterns": {
                    "total_entries": pattern_stats.total_entries,
                    "total_size": pattern_stats.total_size,
                    "entry_types": pattern_stats.entry_types,
                    "success": pattern_stats.success,
                    "error": pattern_stats.error_message,
                },
            },
            "total_size": sum(
                stats.total_size
                for stats in [
                    journal_stats,
                    emotional_stats,
                    memory_stats,
                    pattern_stats,
                ]
            ),
            "total_entries": sum(
                stats.total_entries
                for stats in [
                    journal_stats,
                    emotional_stats,
                    memory_stats,
                    pattern_stats,
                ]
            ),
        }

        # Save manifest
        manifest_path = backup_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return manifest

    def _create_archive(self, backup_dir: Path) -> Path:
        """Create a compressed archive of the backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = self.backup_root / f"journaling_backup_{timestamp}.zip"

        shutil.make_archive(str(archive_path.with_suffix("")), "zip", str(backup_dir))

        return archive_path

    async def _sync_to_cloud(self, archive_path: Path):
        """Sync backup to configured cloud services."""
        if not self.cloud_backup:
            return

        try:
            # Sync to Dropbox
            if os.getenv("DROPBOX_ACCESS_TOKEN"):
                await self.cloud_backup.backup_to_dropbox(
                    str(archive_path), os.getenv("DROPBOX_ACCESS_TOKEN")
                )

            # Sync to Google Drive
            if os.getenv("GOOGLE_DRIVE_CREDENTIALS"):
                await self.cloud_backup.backup_to_drive(
                    str(archive_path), os.getenv("GOOGLE_DRIVE_CREDENTIALS")
                )

            logger.info(f"Successfully synced backup to cloud: {archive_path}")

        except Exception as e:
            logger.error(f"Failed to sync backup to cloud: {e}")

    def _cleanup_old_backups(self, *_):
        """Clean up old backups, keeping only the specified number."""
        try:
            backups = sorted(self.backup_root.glob("journaling_backup_*.zip"))
            if len(backups) > self.max_backups:
                for backup in backups[: -self.max_backups]:
                    backup.unlink()
                    logger.info(f"Removed old backup: {backup}")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

    def schedule_backup(self, time: str = "00:00"):
        """Schedule daily backup at specified time."""

        def backup_job():
            asyncio.run(self.create_backup())

        schedule.every().day.at(time).do(backup_job)

        while True:
            schedule.run_pending()
            time.sleep(60)
