"""
Tests for the companion journaling backup system.
"""

import os
import json
import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from src.secondbrain.backup.companion_journaling_backup import (
    CompanionJournalingBackup,
    BackupStats,
)


@pytest.fixture
def backup_system(tmp_path):
    """Create a backup system instance with temporary paths."""
    # Create test data directories
    data_dir = tmp_path / "data"
    journal_dir = data_dir / "journal"
    emotional_dir = data_dir / "logs" / "emotional"
    memory_dir = data_dir / "memory"
    pattern_dir = data_dir / "patterns"

    for dir_path in [journal_dir, emotional_dir, memory_dir, pattern_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Create test data
    _create_test_journal_entries(journal_dir)
    _create_test_emotional_logs(emotional_dir)
    _create_test_memory_entries(memory_dir)
    _create_test_interaction_patterns(pattern_dir)

    # Create backup system with test paths
    backup = CompanionJournalingBackup(
        backup_root=str(tmp_path / "backups"), enable_cloud_sync=False
    )

    # Override paths for testing
    backup.paths = {
        "journal_entries": journal_dir,
        "emotional_logs": emotional_dir,
        "memory_entries": memory_dir,
        "interaction_patterns": pattern_dir,
    }

    return backup


def _create_test_journal_entries(journal_dir: Path):
    """Create test journal entries."""
    entries = [
        {
            "type": "daily",
            "content": "Test journal entry 1",
            "timestamp": datetime.now().isoformat(),
        },
        {
            "type": "reflection",
            "content": "Test journal entry 2",
            "timestamp": datetime.now().isoformat(),
        },
    ]

    for i, entry in enumerate(entries):
        with open(journal_dir / f"entry_{i}.json", "w") as f:
            json.dump(entry, f)


def _create_test_emotional_logs(emotional_dir: Path):
    """Create test emotional logs."""
    logs = [
        {"emotion": "happy", "intensity": 0.8, "timestamp": datetime.now().isoformat()},
        {"emotion": "calm", "intensity": 0.6, "timestamp": datetime.now().isoformat()},
    ]

    with open(emotional_dir / "emotional_log.json", "w") as f:
        json.dump(logs, f)


def _create_test_memory_entries(memory_dir: Path):
    """Create test memory entries."""
    memories = [
        {
            "type": "interaction",
            "content": "Test memory 1",
            "timestamp": datetime.now().isoformat(),
        },
        {
            "type": "learning",
            "content": "Test memory 2",
            "timestamp": datetime.now().isoformat(),
        },
    ]

    with open(memory_dir / "memories.json", "w") as f:
        json.dump(memories, f)


def _create_test_interaction_patterns(pattern_dir: Path):
    """Create test interaction patterns."""
    patterns = [
        {
            "type": "conversation",
            "pattern": "greeting",
            "timestamp": datetime.now().isoformat(),
        },
        {
            "type": "task",
            "pattern": "completion",
            "timestamp": datetime.now().isoformat(),
        },
    ]

    with open(pattern_dir / "patterns.json", "w") as f:
        json.dump(patterns, f)


@pytest.mark.asyncio
async def test_create_backup(backup_system):
    """Test creating a complete backup."""
    result = await backup_system.create_backup()

    assert result["status"] == "success"
    assert "backup_path" in result
    assert "manifest" in result
    assert "duration" in result

    # Verify backup files exist
    backup_path = Path(result["backup_path"])
    assert backup_path.exists()

    # Verify manifest contents
    manifest = result["manifest"]
    assert manifest["components"]["journal_entries"]["total_entries"] == 2
    assert manifest["components"]["emotional_logs"]["total_entries"] == 2
    assert manifest["components"]["memory_entries"]["total_entries"] == 2
    assert manifest["components"]["interaction_patterns"]["total_entries"] == 2


@pytest.mark.asyncio
async def test_backup_journal_entries(backup_system):
    """Test backing up journal entries."""
    backup_dir = backup_system._create_backup_directory()
    stats = await backup_system._backup_journal_entries(backup_dir)

    assert stats.success
    assert stats.total_entries == 2
    assert len(stats.entry_types) == 2
    assert "daily" in stats.entry_types
    assert "reflection" in stats.entry_types


@pytest.mark.asyncio
async def test_backup_emotional_logs(backup_system):
    """Test backing up emotional logs."""
    backup_dir = backup_system._create_backup_directory()
    stats = await backup_system._backup_emotional_logs(backup_dir)

    assert stats.success
    assert stats.total_entries == 2
    assert len(stats.entry_types) == 2
    assert "happy" in stats.entry_types
    assert "calm" in stats.entry_types


@pytest.mark.asyncio
async def test_backup_memory_entries(backup_system):
    """Test backing up memory entries."""
    backup_dir = backup_system._create_backup_directory()
    stats = await backup_system._backup_memory_entries(backup_dir)

    assert stats.success
    assert stats.total_entries == 2
    assert len(stats.entry_types) == 2
    assert "interaction" in stats.entry_types
    assert "learning" in stats.entry_types


@pytest.mark.asyncio
async def test_backup_interaction_patterns(backup_system):
    """Test backing up interaction patterns."""
    backup_dir = backup_system._create_backup_directory()
    stats = await backup_system._backup_interaction_patterns(backup_dir)

    assert stats.success
    assert stats.total_entries == 2
    assert len(stats.entry_types) == 2
    assert "conversation" in stats.entry_types
    assert "task" in stats.entry_types


def test_cleanup_old_backups(backup_system):
    """Test cleaning up old backups."""
    # Create some test backup files
    backup_dir = backup_system.backup_root
    for i in range(5):
        (backup_dir / f"journaling_backup_2023010{i}.zip").touch()

    # Set max_backups to 3
    backup_system.max_backups = 3

    # Run cleanup
    backup_system._cleanup_old_backups()

    # Verify only 3 most recent backups remain
    remaining_backups = list(backup_dir.glob("journaling_backup_*.zip"))
    assert len(remaining_backups) == 3
