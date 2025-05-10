#!/bin/bash

# Configuration
APP_NAME="SecondBrain"
VERSION="2025"
BUILD_DIR="build"

# Logging function
log() {
    local level=$1
    local message=$2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message"
}

# Create directory structure
create_directories() {
    log "INFO" "Creating directory structure..."
    
    # Create main directories
    mkdir -p resources
    mkdir -p launcher
    mkdir -p config
    mkdir -p models
    mkdir -p voices
    
    # Create subdirectories
    mkdir -p resources/icons
    mkdir -p resources/sounds
    mkdir -p resources/images
    mkdir -p launcher/scripts
    mkdir -p config/settings
    mkdir -p models/voice
    mkdir -p models/ai
    mkdir -p voices/en
    mkdir -p voices/other
}

# Create launcher files
create_launcher_files() {
    log "INFO" "Creating launcher files..."
    
    # Create main.py
    cat > launcher/main.py << EOF
#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

# Suppress warnings and noise
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress specific module logging
logging.getLogger("moviepy").setLevel(logging.ERROR)
logging.getLogger("matplotlib").setLevel(logging.ERROR)
logging.getLogger("PIL").setLevel(logging.ERROR)

def main():
    try:
        logger.info("Starting SecondBrain application...")
        # Add your main application code here
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF
    
    # Create __init__.py
    touch launcher/__init__.py
}

# Create config files
create_config_files() {
    log "INFO" "Creating config files..."
    
    # Create settings.json
    cat > config/settings/settings.json << EOF
{
    "app": {
        "name": "SecondBrain",
        "version": "2025",
        "debug": false
    },
    "voice": {
        "enabled": true,
        "engine": "pyttsx3",
        "rate": 150,
        "volume": 1.0
    },
    "audio": {
        "sample_rate": 44100,
        "channels": 2,
        "bit_depth": 16
    }
}
EOF
}

# Create virtual environment
create_virtual_env() {
    log "INFO" "Creating virtual environment..."
    
    # Create venv
    python3 -m venv venv
    
    # Activate venv and install requirements
    source venv/bin/activate
    pip install --quiet pyttsx3 numpy scipy sounddevice pyaudio
    deactivate
}

# Install VS Code Python extension
install_vscode_extension() {
    log "INFO" "Installing VS Code Python extension..."
    if command -v code &> /dev/null; then
        code --install-extension ms-python.python --force
    fi
}

# Main setup process
main() {
    log "INFO" "Starting setup process for $APP_NAME v$VERSION"
    
    # Create directory structure
    create_directories
    
    # Create launcher files
    create_launcher_files
    
    # Create config files
    create_config_files
    
    # Create virtual environment
    create_virtual_env
    
    # Install VS Code extension
    install_vscode_extension
    
    log "INFO" "Setup complete!"
    echo "Application structure is ready for packaging"
}

# Run main function
main 