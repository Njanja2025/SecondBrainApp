#!/bin/bash

# Setup script for SecondBrainApp
# This script handles the initial bootstrap and launch of the system

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[-]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    print_status "Virtual environment created and activated"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    print_status "Dependencies installed"
}

# Function to setup Git repository
setup_git() {
    print_status "Setting up Git repository..."
    if [ ! -d ".git" ]; then
        git init
        git remote add origin https://github.com/LloydKavhanda/SecondBrainApp_2025.git
        git fetch
        git checkout main
    else
        git fetch
        git pull origin main
    fi
    print_status "Git repository setup complete"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p backups/voices
    mkdir -p backups/njax
    mkdir -p config
    mkdir -p logs
    mkdir -p temp
    mkdir -p cache
    print_status "Directories created"
}

# Function to setup configuration files
setup_config() {
    print_status "Setting up configuration files..."
    
    # Create agent config
    cat > config/agent_config.json << EOF
{
    "repo_path": ".",
    "backup_dir": "backups",
    "modules_dir": "modules"
}
EOF

    # Create voice config
    cat > config/voice_config.json << EOF
{
    "voice_dir": "voices",
    "models_dir": "models",
    "backup_dir": "backups/voices"
}
EOF

    # Create Njax config
    cat > config/njax_config.json << EOF
{
    "njax_dir": "njax",
    "components_dir": "njax/components",
    "backup_dir": "backups/njax"
}
EOF

    print_status "Configuration files created"
}

# Function to setup Cursor configuration
setup_cursor() {
    print_status "Setting up Cursor configuration..."
    mkdir -p .cursor
    
    # Create Cursor settings
    cat > .cursor/settings.json << EOF
{
    "python.analysis.extraPaths": [
        "${PWD}/app_core",
        "${PWD}/plugins",
        "${PWD}/tests"
    ],
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true
}
EOF

    print_status "Cursor configuration created"
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Check Python version
    python_version=$(python3 --version)
    print_status "Python version: $python_version"
    
    # Check pip packages
    print_status "Installed packages:"
    pip list
    
    # Check Git status
    print_status "Git status:"
    git status
    
    print_status "Installation verification complete"
}

# Main setup process
main() {
    print_status "Starting SecondBrainApp setup..."
    
    # Check for required commands
    for cmd in python3 pip git; do
        if ! command_exists $cmd; then
            print_error "$cmd is required but not installed"
            exit 1
        fi
    done
    
    # Create virtual environment
    create_venv
    
    # Install dependencies
    install_dependencies
    
    # Setup Git repository
    setup_git
    
    # Create directories
    create_directories
    
    # Setup configuration files
    setup_config
    
    # Setup Cursor configuration
    setup_cursor
    
    # Verify installation
    verify_installation
    
    print_status "Setup complete. To run: source venv/bin/activate && python3 src/ai_agent/baddy_agent.py"
}

# Run main function
main 