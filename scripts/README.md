# Memory Engine Scripts

This directory contains various scripts for managing, monitoring, and maintaining the Memory Engine system.

## Scripts Overview

### 1. Advanced Automation (`advanced_automation.py`)
- Manages automated tasks for the Memory Engine
- Features:
  - Automated backups
  - Log cleanup
  - Git synchronization
  - Email and webhook notifications
  - Multi-threaded task processing

### 2. Deployment (`deploy.py`)
- Handles deployment of Memory Engine components
- Features:
  - Pre-deployment checks
  - Component deployment
  - Post-deployment verification
  - Backup creation
  - Rollback support
  - Email and webhook notifications

### 3. Monitoring (`monitor.py`)
- Monitors Memory Engine performance and health
- Features:
  - Database size monitoring
  - Memory usage tracking
  - CPU usage monitoring
  - Disk usage tracking
  - Database health checks
  - Query performance monitoring
  - Alert system with email and webhook notifications
  - Metrics retention management

### 4. Backup (`backup.py`)
- Manages database backups
- Features:
  - Full and incremental backups
  - Backup compression
  - Backup encryption
  - Backup verification
  - Retention management
  - Email and webhook notifications

## Configuration

All scripts use a central configuration file (`config.json`) that contains settings for:
- File paths
- Schedule intervals
- Thresholds
- Notification settings
- Retention policies
- Security settings

## Usage

### Running Scripts

1. Advanced Automation:
```bash
python advanced_automation.py [--config config.json]
```

2. Deployment:
```bash
python deploy.py [--config config.json]
```

3. Monitoring:
```bash
python monitor.py [--config config.json]
```

4. Backup:
```bash
python backup.py [--config config.json]
```

### Configuration

1. Copy the example configuration:
```bash
cp config.json.example config.json
```

2. Edit `config.json` to match your environment:
- Update file paths
- Configure notification settings
- Adjust thresholds and intervals
- Set up security options

## Dependencies

Required Python packages:
```
psutil
requests
cryptography
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Security Considerations

1. Backup Encryption:
- Enable encryption in `config.json`
- Generate and securely store encryption keys
- Regularly rotate encryption keys

2. Notifications:
- Use secure SMTP for email notifications
- Use HTTPS for webhook notifications
- Store credentials securely

3. File Permissions:
- Restrict access to configuration files
- Use appropriate file permissions for backups
- Secure log files

## Maintenance

1. Log Rotation:
- Logs are automatically rotated based on size
- Old logs are cleaned up based on retention policy

2. Backup Management:
- Full backups are created weekly
- Incremental backups are created daily
- Old backups are automatically cleaned up

3. Monitoring:
- Metrics are stored for 30 days
- Alerts are sent for critical issues
- Performance data is collected hourly

## Troubleshooting

1. Check logs:
- `automation.log`
- `deploy.log`
- `monitor.log`
- `backup.log`

2. Common Issues:
- Permission denied: Check file permissions
- Connection failed: Verify network settings
- Backup failed: Check disk space
- Monitoring alerts: Review thresholds

## Contributing

1. Follow Python style guide (PEP 8)
2. Add tests for new features
3. Update documentation
4. Submit pull requests

## License

This project is licensed under the MIT License - see the LICENSE file for details. 