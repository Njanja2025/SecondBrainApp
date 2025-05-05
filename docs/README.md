# SecondBrain App Delivery System

## Overview
The SecondBrain App delivery system provides automated packaging, distribution, and maintenance of the SecondBrain application. It includes backup systems, auto-updates, security scanning, and multi-channel distribution.

## Components

### 1. Automated Backup System
- Daily versioned backups
- Security scanning before backup
- Cloud storage synchronization
- Retention policy management
- Encrypted backup support

### 2. Auto-Update System
- GitHub release monitoring
- Automatic update downloads
- Package integrity verification
- Safe update application
- Rollback capability

### 3. Security Features
- Pre-backup security scanning
- Package integrity verification
- Encrypted storage
- Network activity monitoring
- Process monitoring

### 4. Distribution Channels
- GitHub Releases
- Dropbox Storage
- Google Drive Integration
- Custom Domain (phantom.njanja.net)

## Setup Instructions

### 1. Configuration
1. Copy `config/delivery_config.example.json` to `config/delivery_config.json`
2. Set your GitHub token in the config
3. Configure cloud storage paths
4. Set up website domain settings

### 2. Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up backup directories
mkdir -p backups/daily
mkdir -p backups/weekly
mkdir -p logs/backup

# Generate encryption key
openssl genpkey -algorithm RSA -out config/backup_key.pem -pkeyopt rsa_keygen_bits:4096
```

### 3. Running the System

#### Package Creation and Delivery
```bash
python3 scripts/finalize_delivery.py
```

#### Automated Backups
```bash
# Start backup service
python3 src/secondbrain/phantom/auto_backup.py

# Manual backup
python3 scripts/run_backup.py --type full
```

#### Update Checks
```bash
python3 src/secondbrain/phantom/auto_updater.py --check
```

## Monitoring

### Metrics Available
- System resource usage
- Backup operations
- Update checks
- Security incidents
- API requests
- Blockchain transactions
- Voice commands

### Logging
- All operations are logged to `logs/`
- Security events in `logs/security/`
- Backup logs in `logs/backup/`
- Update logs in `logs/updates/`

## Security

### Features
- SHA-256 package verification
- RSA encryption for sensitive data
- Process monitoring
- Network activity scanning
- File integrity checking

### Best Practices
1. Regularly rotate encryption keys
2. Monitor security logs
3. Keep GitHub tokens secure
4. Use secure communication channels
5. Regular security audits

## Troubleshooting

### Common Issues
1. Cloud upload failures
   - Check storage permissions
   - Verify paths in config
   - Check network connectivity

2. Update failures
   - Verify GitHub token
   - Check version format
   - Ensure clean working directory

3. Backup issues
   - Check disk space
   - Verify encryption key
   - Check file permissions

### Support
For issues or questions:
- GitHub Issues: [SecondBrain-App Issues](https://github.com/lloydkavhanda/SecondBrain-App/issues)
- Email: support@njanja.net
- Website: https://phantom.njanja.net/support

## License
Copyright © 2025 Njanja Technologies. All rights reserved. 