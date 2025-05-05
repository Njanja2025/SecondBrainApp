#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "Setting up SecondBrain development environment..."

# Check Python version
python3 --version || {
    echo -e "${RED}Python 3 is required but not found${NC}"
    exit 1
}

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
cat > .pre-commit-config.yaml << EOL
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
-   repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
    -   id: black
-   repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
    -   id: flake8
EOL

pip install pre-commit
pre-commit install

# Create .env file template
echo "Creating .env template..."
cat > .env.template << EOL
# SecondBrain Environment Configuration

# Application Settings
APP_NAME=SecondBrain
DEBUG=False
LOG_LEVEL=INFO

# Voice Settings
VOICE_ENABLED=True
WAKE_WORD="hey brain"
VOICE_RATE=175

# GUI Settings
GUI_ENABLED=True
THEME=light

# API Keys (Replace with your own)
OPENAI_API_KEY=your_key_here
GOOGLE_CLOUD_API_KEY=your_key_here
EOL

# Setup complete
echo -e "${GREEN}Development environment setup complete!${NC}"
echo "To activate the virtual environment, run: source venv/bin/activate" 