#!/bin/bash

# Function to check system requirements
check_requirements() {
    echo "Checking system requirements..."
    
    # Check Python 3 installation
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is not installed"
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$python_version < 3.8" | bc -l) )); then
        echo "Error: Python 3.8 or higher is required"
        exit 1
    fi
    
    # Check available memory
    if [[ "$OSTYPE" == "darwin"* ]]; then
        total_mem=$(sysctl hw.memsize | awk '{print $2}')
        total_mem_gb=$(echo "scale=2; $total_mem/1024/1024/1024" | bc)
    else
        total_mem=$(free -b | awk '/^Mem:/{print $2}')
        total_mem_gb=$(echo "scale=2; $total_mem/1024/1024/1024" | bc)
    fi
    
    if (( $(echo "$total_mem_gb < 4" | bc -l) )); then
        echo "Warning: Less than 4GB of RAM available"
    fi
    
    # Check disk space
    if [[ "$OSTYPE" == "darwin"* ]]; then
        free_space=$(df -k . | awk 'NR==2 {print $4}')
        free_space_gb=$(echo "scale=2; $free_space/1024/1024" | bc)
    else
        free_space=$(df -k . | awk 'NR==2 {print $4}')
        free_space_gb=$(echo "scale=2; $free_space/1024/1024" | bc)
    fi
    
    if (( $(echo "$free_space_gb < 1" | bc -l) )); then
        echo "Warning: Less than 1GB of free disk space"
    fi
    
    # Check for portaudio (required for PyAudio)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! brew list portaudio &> /dev/null; then
            echo "Installing portaudio..."
            brew install portaudio
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if ! dpkg -l | grep -q portaudio19-dev; then
            echo "Installing portaudio..."
            sudo apt-get update
            sudo apt-get install -y portaudio19-dev
        fi
    fi
    
    # Check for Node.js and npm (required for mobile app)
    if ! command -v node &> /dev/null; then
        echo "Error: Node.js is not installed"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo "Error: npm is not installed"
        exit 1
    fi
    
    # Check Node.js version
    node_version=$(node -v | cut -d'v' -f2)
    if (( $(echo "$node_version < 16" | bc -l) )); then
        echo "Error: Node.js 16 or higher is required"
        exit 1
    fi
}

# Function to create requirements.txt
create_requirements() {
    echo "Creating requirements.txt..."
    cat > requirements.txt << EOL
flask==2.0.1
flask-login==0.5.0
werkzeug==2.0.1
psutil==5.8.0
pyotp==2.6.0
qrcode==7.3
pillow==8.3.1
authlib==1.2.0
flask-limiter==3.5.0
pyjwt==2.8.0
requests==2.31.0
python-dotenv==1.0.0
flask-mobility==0.1.1
pdfkit==1.0.0
pandas==2.0.0
numpy==1.24.0
python-telegram-bot==13.7
SpeechRecognition==3.8.1
PyAudio==0.2.11
EOL
}

# Function to create .env file
create_env_file() {
    echo "Creating .env file..."
    if [ ! -f .env ]; then
        cat > .env << EOL
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_REDIRECT_URI=http://localhost:5000/login/microsoft/callback

# JWT Settings
JWT_SECRET=your_jwt_secret_key

# Telegram Settings
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
EOL
        echo "Please update the .env file with your credentials"
    fi
}

# Function to install required packages
install_packages() {
    echo "Installing required packages..."
    
    # Install Python packages
    pip3 install -r requirements.txt
    
    # Install wkhtmltopdf for PDF generation
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! brew list wkhtmltopdf &> /dev/null; then
            echo "Installing wkhtmltopdf..."
            brew install wkhtmltopdf
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if ! dpkg -l | grep -q wkhtmltopdf; then
            echo "Installing wkhtmltopdf..."
            sudo apt-get update
            sudo apt-get install -y wkhtmltopdf
        fi
    elif [[ "$OSTYPE" == "msys" ]]; then
        if ! command -v wkhtmltopdf &> /dev/null; then
            echo "Please install wkhtmltopdf from https://wkhtmltopdf.org/downloads.html"
        fi
    fi
    
    # Install React Native CLI
    if ! command -v react-native &> /dev/null; then
        echo "Installing React Native CLI..."
        npm install -g react-native-cli
    fi
    
    # Install mobile app dependencies
    if [ -d "src/secondbrain/mobile" ]; then
        echo "Installing mobile app dependencies..."
        cd src/secondbrain/mobile
        npm install
        cd ../../..
    fi
}

# Function to run tests
run_tests() {
    echo "Running tests..."
    python3 -m unittest discover -s tests
}

# Function to start monitoring
start_monitoring() {
    echo "Starting monitoring..."
    
    # Start voice system
    PYTHONPATH=. /usr/bin/python3 src/secondbrain/cli/voice_trigger.py &
    VOICE_PID=$!
    
    # Start web dashboard
    PYTHONPATH=. /usr/bin/python3 src/secondbrain/cli/web_dashboard.py &
    DASHBOARD_PID=$!
    
    # Start mobile app development server
    if [ -d "src/secondbrain/mobile" ]; then
        echo "Starting mobile app development server..."
        cd src/secondbrain/mobile
        npm start &
        MOBILE_PID=$!
        cd ../../..
    fi
    
    # Open dashboard in browser
    sleep 2
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:5000
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open http://localhost:5000
    elif [[ "$OSTYPE" == "msys" ]]; then
        start http://localhost:5000
    fi
    
    # Set up cleanup on exit
    if [ -n "$MOBILE_PID" ]; then
        trap "kill $VOICE_PID $DASHBOARD_PID $MOBILE_PID; exit" INT TERM EXIT
    else
        trap "kill $VOICE_PID $DASHBOARD_PID; exit" INT TERM EXIT
    fi
    
    # Keep script running
    wait
}

# Main execution
check_requirements
create_requirements
create_env_file
install_packages
run_tests
start_monitoring 