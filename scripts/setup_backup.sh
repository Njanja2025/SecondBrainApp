#!/bin/bash

# Setup script for SecondBrain automated backup system

echo "Setting up SecondBrain automated backup system..."

# Create necessary directories
mkdir -p backups
mkdir -p logs/backup

# Install required Python packages
pip install schedule prometheus_client datadog

# Set up environment variables
cat >> ~/.zshrc << EOL

# SecondBrain Backup Configuration
export DROPBOX_BACKUP_PATH="${HOME}/Dropbox/SecondBrain/backups"
export GDRIVE_BACKUP_PATH="${HOME}/Google Drive/SecondBrain/backups"
export GITHUB_REPO_PATH="lloydkavhanda/SecondBrain-App"
export ENABLE_ENCRYPTION=true
export ENCRYPTION_KEY="$(openssl rand -hex 32)"
EOL

# Source the updated profile
source ~/.zshrc

# Set up backup service
cat > ~/Library/LaunchAgents/com.secondbrain.backup.plist << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.secondbrain.backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>${PWD}/src/secondbrain/automation/automated_backup.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>0</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>${PWD}/logs/backup/backup.log</string>
    <key>StandardErrorPath</key>
    <string>${PWD}/logs/backup/backup.error.log</string>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOL

# Load the launch agent
launchctl load ~/Library/LaunchAgents/com.secondbrain.backup.plist

echo "Backup system setup complete!"
echo "Daily backups will run at midnight and sync to configured cloud storage."
echo "Logs are available in logs/backup/"
echo "Configuration can be modified in config/backup_config.json" 