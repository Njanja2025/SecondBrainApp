#!/bin/bash

# Go to root of project
cd "$(dirname "$0")"/.. || exit

# Get full path to Python and project scripts
PYTHON_PATH=$(which python3)
PHANTOM_SCRIPT="guardian_phantomCore/phantom_map_admin.py"
PHANTOM_COMMAND="@reboot $PYTHON_PATH $(pwd)/$PHANTOM_SCRIPT >> /tmp/phantom_cron.log 2>&1"

# Add cron job if not already present
(crontab -l 2>/dev/null | grep -v "$PHANTOM_SCRIPT"; echo "$PHANTOM_COMMAND") | crontab -

echo "✅ Phantom cron job added!" 