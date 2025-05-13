# SecondBrain Backup System

A robust, voice-enabled backup system for SecondBrain journaling with cloud sync and health monitoring.

## Features

- 🎤 Voice announcements using Samantha
- 🔄 Automatic daily backups
- ☁️ Cloud sync with Dropbox
- 🔒 Encrypted vault storage
- 📊 Health monitoring and reporting
- 📧 Email notifications
- ✅ Backup verification

## Installation

1. Download the latest release from the [Releases](https://github.com/yourusername/secondbrain/releases) page
2. Mount the DMG file
3. Drag SecondBrain Backup to your Applications folder
4. Launch the application to complete setup

## Configuration

### Voice Settings
Edit `src/secondbrain/backup/voice_config.json`:
```json
{
    "voice_enabled": true,
    "voice_name": "Samantha",
    "confirmation_message": "Backup completed and synced successfully.",
    "error_message": "There was an error during the backup process.",
    "play_audio": true,
    "audio_file": "src/secondbrain/voice/NjanjaIntro.aiff",
    "intro_enabled": true,
    "intro_message": "Starting SecondBrain backup process."
}
```

### Cloud Settings
Edit `src/secondbrain/backup/cloud_config.json`:
```json
{
    "use_cloud": true,
    "provider": "dropbox",
    "access_token": "YOUR_DROPBOX_TOKEN",
    "local_vault_path": "~/Documents/.secondbrain/backups",
    "cloud_path": "/SecondBrain_Backups"
}
```

## Usage

### Manual Backup
```bash
python3 src/secondbrain/backup/backup_cli.py --auto --verify
```

### Verify Backups
```bash
python3 src/secondbrain/backup/vault_verifier.py
```

### Health Monitoring
```bash
python3 src/secondbrain/backup/monitor_backup_health.py
```

## System Requirements

- macOS 10.15 or later
- Python 3.7+
- Dropbox account (for cloud sync)
- Email account (for notifications)

## Dependencies

- pyttsx3 (voice synthesis)
- dropbox (cloud sync)
- cryptography (encryption)
- requests (API communication)

## Security

- All backups are encrypted using AES-256
- Cloud sync uses OAuth2 authentication
- Local vault is protected by system permissions
- No sensitive data is stored in logs

## Monitoring

The system includes:
- Daily health checks
- Email notifications
- Backup verification
- Cloud sync status
- Voice confirmations

## Troubleshooting

1. Check logs in `/tmp/secondbrain_backup.log`
2. Verify voice configuration
3. Test cloud connection
4. Run health check

## License

MIT License - see LICENSE file for details

## Support

For support, please:
1. Check the [Wiki](https://github.com/yourusername/secondbrain/wiki)
2. Open an [Issue](https://github.com/yourusername/secondbrain/issues)
3. Contact support@secondbrain.ai

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Acknowledgments

- Samantha voice by Apple
- Dropbox API
- Python community 