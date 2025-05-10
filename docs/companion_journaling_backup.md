# Companion Journaling Backup System

The Companion Journaling Backup System provides a robust solution for backing up all journaling-related data in the SecondBrain application. This includes journal entries, emotional logs, memory entries, and interaction patterns.

## Features

- **Comprehensive Backup**: Backs up all journaling-related data including:
  - Journal entries
  - Emotional logs
  - Memory entries
  - Interaction patterns
- **Versioning**: Maintains multiple backup versions with automatic cleanup
- **Cloud Sync**: Optional cloud synchronization of backups
- **Compression**: Efficient storage using gzip compression
- **Manifest**: Detailed backup manifest with statistics
- **CLI Interface**: Easy-to-use command-line interface

## Installation

The backup system is included in the SecondBrain package. No additional installation is required.

## Usage

### Command Line Interface

The backup system can be used through the command-line interface:

```bash
# Create a backup
python -m src.secondbrain.cli.backup_cli

# List existing backups
python -m src.secondbrain.cli.backup_cli --list

# Clean up old backups
python -m src.secondbrain.cli.backup_cli --cleanup

# Create backup with custom settings
python -m src.secondbrain.cli.backup_cli --backup-root /path/to/backups --max-backups 10 --enable-cloud-sync
```

### Command Line Options

- `--backup-root`: Root directory for backups (default: ~/.secondbrain/backups)
- `--max-backups`: Maximum number of backups to keep (default: 5)
- `--enable-cloud-sync`: Enable cloud synchronization of backups
- `--list`: List existing backups
- `--cleanup`: Clean up old backups

### Programmatic Usage

The backup system can also be used programmatically:

```python
from src.secondbrain.backup.companion_journaling_backup import CompanionJournalingBackup

# Create backup instance
backup = CompanionJournalingBackup(
    backup_root="/path/to/backups",
    max_backups=5,
    enable_cloud_sync=True
)

# Run backup
result = await backup.create_backup()
```

## Backup Structure

Each backup is stored as a compressed ZIP file with the following structure:

```
journaling_backup_YYYYMMDD_HHMMSS.zip
├── manifest.json
├── journal_entries/
│   └── *.json
├── emotional_logs/
│   └── *.json
├── memory_entries/
│   └── *.json
└── interaction_patterns/
    └── *.json
```

### Manifest

The backup manifest (`manifest.json`) contains metadata about the backup:

```json
{
    "timestamp": "2024-01-01T12:00:00",
    "version": "1.0.0",
    "components": {
        "journal_entries": {
            "total_entries": 10,
            "entry_types": ["daily", "reflection"]
        },
        "emotional_logs": {
            "total_entries": 5,
            "entry_types": ["happy", "calm"]
        },
        "memory_entries": {
            "total_entries": 8,
            "entry_types": ["interaction", "learning"]
        },
        "interaction_patterns": {
            "total_entries": 3,
            "entry_types": ["conversation", "task"]
        }
    }
}
```

## Cloud Synchronization

When cloud synchronization is enabled, backups are automatically synced to the configured cloud storage service. The system supports:

- Google Drive
- Dropbox
- OneDrive

To enable cloud sync, configure the appropriate credentials in the application settings.

## Error Handling

The backup system includes comprehensive error handling:

- File system errors
- Compression errors
- Cloud sync errors
- Invalid data format errors

All errors are logged with detailed information for debugging.

## Best Practices

1. **Regular Backups**: Schedule regular backups to ensure data safety
2. **Cloud Sync**: Enable cloud sync for off-site backup
3. **Cleanup**: Regularly clean up old backups to manage storage
4. **Testing**: Test backup restoration periodically
5. **Monitoring**: Monitor backup success/failure through logs

## Troubleshooting

Common issues and solutions:

1. **Backup Fails**
   - Check disk space
   - Verify file permissions
   - Check cloud sync credentials

2. **Cloud Sync Fails**
   - Verify internet connection
   - Check cloud service status
   - Verify credentials

3. **Corrupted Backup**
   - Use the most recent backup
   - Check backup manifest for integrity
   - Contact support if needed

## Contributing

Contributions to the backup system are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

The Companion Journaling Backup System is part of the SecondBrain project and is licensed under the MIT License. 