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

# Function to handle errors
handle_error() {
    echo "Error: $1"
    exit 1
}

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv venv || handle_error "Failed to create virtual environment"
source venv/bin/activate || handle_error "Failed to activate virtual environment"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip || handle_error "Failed to upgrade pip"

# Install dependencies in groups
echo "Installing core dependencies..."
pip install flask==2.3.3 flask-sqlalchemy==3.1.1 gunicorn==21.2.0 requests==2.31.0 boto3==1.28.64 python-dotenv==1.0.0 || handle_error "Failed to install core dependencies"

echo "Installing quantum and phantom dependencies..."
pip install numpy==1.24.3 scipy==1.11.3 scikit-learn==1.3.0 matplotlib==3.7.2 pandas==2.1.0 || handle_error "Failed to install quantum dependencies"

echo "Installing security and authentication dependencies..."
pip install pyjwt==2.8.0 bcrypt==4.0.1 cryptography==41.0.3 || handle_error "Failed to install security dependencies"

echo "Installing database dependencies..."
pip install sqlalchemy==2.0.20 psycopg2-binary==2.9.7 redis==4.6.0 || handle_error "Failed to install database dependencies"

echo "Installing API and web dependencies..."
pip install fastapi==0.103.1 uvicorn==0.23.2 websockets==11.0.3 || handle_error "Failed to install API dependencies"

echo "Installing testing and development dependencies..."
pip install pytest==7.4.2 black==23.7.0 flake8==6.1.0 mypy==1.5.1 || handle_error "Failed to install testing dependencies"

echo "Installing monitoring and logging dependencies..."
pip install prometheus-client==0.17.1 python-json-logger==2.0.7 || handle_error "Failed to install monitoring dependencies"

echo "Installing additional utilities..."
pip install python-dateutil==2.8.2 pytz==2023.3 tqdm==4.66.1 || handle_error "Failed to install utility dependencies"

# Create necessary directories
echo "Creating system directories..."
mkdir -p ~/.secondbrain/backups
mkdir -p ~/.secondbrain/models
mkdir -p ~/.secondbrain/logs
mkdir -p SecondBrainApp/backend/guardian_alerts/{analytics,dashboards,insights} || handle_error "Failed to create guardian alerts directories"
mkdir -p SecondBrainApp/backend/logs || handle_error "Failed to create logs directory"
mkdir -p SecondBrainApp/backend/data || handle_error "Failed to create data directory"

# Download Whisper model
echo "Downloading Whisper model..."
python3 -c "import whisper; whisper.load_model('base')"

# Set up environment variables
echo "Setting up environment variables..."
if [ ! -f .env ]; then
    echo "Creating .env file..."
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

# Application Settings
FLASK_APP=SecondBrainApp/backend/app.py
FLASK_ENV=development
SECRET_KEY=$(openssl rand -hex 32)

# Database Settings
DATABASE_URL=sqlite:///SecondBrainApp/backend/data/app.db

# AWS Settings
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-west-2

# Quantum Settings
QUANTUM_BACKEND=ibmq_qasm_simulator
QUANTUM_TOKEN=your_quantum_token

# Security Settings
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Logging Settings
LOG_FILE=SecondBrainApp/backend/logs/app.log
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

# Initialize the database
echo "Initializing the database..."
python SecondBrainApp/backend/init_db.py || handle_error "Failed to initialize database"

# Run tests
echo "Running tests..."
pytest || handle_error "Tests failed"

echo "Setup completed successfully!"
echo "To start the system, run: python3 main.py" 