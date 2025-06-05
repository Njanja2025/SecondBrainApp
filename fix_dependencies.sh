#!/bin/bash

# Backup existing requirements.txt
cp requirements.txt requirements_backup_$(date +%Y%m%d%H%M%S).txt

# Update/add fixed package versions in requirements.txt
grep -vE '^(typing-extensions|pytest-asyncio|torch|pyyaml)==' requirements.txt > temp_requirements.txt
echo "typing-extensions==4.5.0" >> temp_requirements.txt
echo "pytest-asyncio==0.23.2" >> temp_requirements.txt
echo "torch==2.0.1" >> temp_requirements.txt
echo "pyyaml==6.0" >> temp_requirements.txt

# Replace original requirements.txt
mv temp_requirements.txt requirements.txt

# Upgrade pip and install dependencies with force reinstall
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --force-reinstall

# Force install exact versions required by SecondBrainApp
pip install fastapi==0.104.1 \
            httpx==0.25.2 \
            prometheus-client==0.19.0 \
            psutil==5.9.6 \
            pyaudio==0.2.13 \
            pydantic==2.5.2 \
            python-dotenv==1.0.0 \
            pyttsx3==2.90 \
            schedule==1.2.0 \
            SpeechRecognition==3.10.0 \
            tenacity==8.2.3 \
            uvicorn==0.24.0 \
            websockets==12.0 \
            typing-extensions==4.5.0

# Optionally, re-install other core dependencies
pip install boto3 dropbox pyicloud

echo "Dependencies fixed and reinstalled successfully."
