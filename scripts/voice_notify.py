#!/usr/bin/env python3

import os
import sys
import subprocess
from datetime import datetime

def speak(message):
    """Use macOS say command for voice notifications"""
    try:
        subprocess.run(['say', '-v', 'Samantha', message])
        log_notification(message)
    except Exception as e:
        print(f"Error in voice notification: {e}")

def log_notification(message):
    """Log voice notifications to file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    with open(f"{log_dir}/voice_alerts.log", "a") as f:
        f.write(f"[{timestamp}] {message}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        speak(message)
    else:
        speak("Phantom system activated. Streamlit assistant running.") 