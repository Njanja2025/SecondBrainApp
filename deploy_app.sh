#!/bin/bash

echo "Starting SecondBrainApp deployment..."

# Step 1: Clean previous environment
echo "Removing old virtual environment if exists..."
rm -rf venv

# Step 2: Recreate virtual environment with Python 3.11
/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv venv

# Step 3: Activate virtual environment
source venv/bin/activate

# Step 4: Upgrade pip and install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install fake-useragent pyttsx3

# Step 5: macOS voice fallback confirmation
say -v "Samantha" "Voice output is now active"

# Step 6: Launch core system
python src/secondbrain/darkops/stealth_research.py

echo "Deployment complete." 