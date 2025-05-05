#!/bin/bash

echo "Setting up SecondBrain AI Agent with Phantom MCP..."

# Check for Python 3.8+
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check for Homebrew (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install ffmpeg using Homebrew
    echo "Installing ffmpeg..."
    brew install ffmpeg
fi

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install PyAudio system dependencies if needed
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install portaudio
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update
    sudo apt-get install -y python3-pyaudio portaudio19-dev
fi

# Create necessary directories
echo "Creating system directories..."
mkdir -p ~/.secondbrain/backups
mkdir -p ~/.secondbrain/models
mkdir -p ~/.secondbrain/logs

# Download Whisper model
echo "Downloading Whisper model..."
python3 -c "import whisper; whisper.load_model('base')"

# Set up environment variables
echo "Setting up environment variables..."
if [ ! -f .env ]; then
    cat > .env << EOL
# OpenAI API Key (required for some features)
OPENAI_API_KEY=your_api_key_here

# Blockchain settings
INFURA_API_KEY=your_infura_key_here
PRIVATE_KEY=your_private_key_here

# System settings
LOG_LEVEL=INFO
ENABLE_VOICE=true
ENABLE_GUI=true
EOL
fi

# Initialize the system
echo "Initializing the system..."
python3 -c "
from src.secondbrain.core.phantom_mcp import PhantomMCP
import asyncio

async def init():
    mcp = PhantomMCP()
    await mcp.initialize()
    
asyncio.run(init())
"

echo "Setup complete! To start the system, run: python3 main.py" 