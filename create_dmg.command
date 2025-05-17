#!/bin/zsh

# Baddy Agent DMG Creator
# This script creates a DMG installer for offline/USB distribution

# Set working directory
cd /Users/mac/Documents/Cursor_SecondBrain_Release_Package

# Activate virtual environment
source venv/bin/activate

# Create app bundle first
sh create_app_bundle.command

# Create DMG
python3 src/ai_agent/create_dmg.py

echo "DMG creation completed. Check BaddyAgent.dmg in the current directory." 