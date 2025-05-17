#!/bin/zsh

# Baddy Agent Launcher
# This script launches both the tray app and voice trigger

# Set working directory
cd /Users/mac/Documents/Cursor_SecondBrain_Release_Package

# Activate virtual environment
source venv/bin/activate

# Start the tray app in the background
python3 src/ai_agent/tray_app.py &

# Wait a moment for the tray app to initialize
sleep 2

# Start the voice trigger
python3 src/ai_agent/baddy_agent.py 