#!/bin/bash

# Backup rotation script for SecondBrain

BACKUP_DIR="/home/ubuntu/secondbrain/backups"
MAX_BACKUPS=7  # Keep a week's worth of backups

echo "Starting backup rotation..."

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create new backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/secondbrain_$TIMESTAMP.tar.gz"

# Backup application files
tar -czf $BACKUP_FILE \
    /home/ubuntu/secondbrain/data \
    /home/ubuntu/secondbrain/logs \
    /var/log/nginx/secondbrain.* \
    /etc/nginx/sites-available/secondbrain.conf

# Remove old backups
cd $BACKUP_DIR
ls -t | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm

# Upload to cloud storage
if [ -f /home/ubuntu/secondbrain/venv/bin/python ]; then
    /home/ubuntu/secondbrain/venv/bin/python << 'EOF'
import boto3
import os
from datetime import datetime

# AWS S3 upload
s3 = boto3.client('s3')
bucket = os.getenv('AWS_BUCKET_NAME')
backup_file = f"secondbrain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
s3.upload_file(backup_file, bucket, f"backups/{backup_file}")

# Cleanup old S3 backups
backups = s3.list_objects_v2(Bucket=bucket, Prefix='backups/')
if 'Contents' in backups:
    sorted_backups = sorted(backups['Contents'], key=lambda x: x['LastModified'], reverse=True)
    for old_backup in sorted_backups[7:]:  # Keep last 7 backups
        s3.delete_object(Bucket=bucket, Key=old_backup['Key'])
EOF
fi

echo "Backup rotation completed successfully!" 