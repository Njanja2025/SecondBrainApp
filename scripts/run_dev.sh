#!/bin/bash

# Exit on error
set -e

# Configuration
PYTHON_VERSION="3.9"
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"
DEV_REQUIREMENTS_FILE="requirements-dev.txt"
WATCH_DIRS="src tests"
TEST_DIR="tests"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check Python version
check_python() {
    log "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
    fi
    
    PYTHON_VERSION_ACTUAL=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [ "$(printf '%s\n' "$PYTHON_VERSION" "$PYTHON_VERSION_ACTUAL" | sort -V | head -n1)" != "$PYTHON_VERSION" ]; then
        error "Python version $PYTHON_VERSION or higher is required. Found $PYTHON_VERSION_ACTUAL"
    fi
    log "Python version $PYTHON_VERSION_ACTUAL detected"
}

# Setup virtual environment
setup_venv() {
    log "Setting up virtual environment..."
    
    # Check if venv exists
    if [ ! -d "$VENV_DIR" ]; then
        log "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "$REQUIREMENTS_FILE" ]; then
        log "Installing requirements..."
        pip install -r "$REQUIREMENTS_FILE"
    else
        warn "Requirements file not found: $REQUIREMENTS_FILE"
    fi
    
    # Install development requirements
    if [ -f "$DEV_REQUIREMENTS_FILE" ]; then
        log "Installing development requirements..."
        pip install -r "$DEV_REQUIREMENTS_FILE"
    fi
}

# Check for required directories
check_directories() {
    log "Checking required directories..."
    
    # Create required directories if they don't exist
    mkdir -p config logs data tests
    
    # Set permissions
    chmod 755 config logs data tests
}

# Run tests
run_tests() {
    log "Running tests..."
    pytest "$TEST_DIR" -v --cov=src --cov-report=term-missing
}

# Run linters
run_linters() {
    log "Running linters..."
    
    # Run black
    black "$WATCH_DIRS"
    
    # Run flake8
    flake8 "$WATCH_DIRS"
    
    # Run mypy
    mypy "$WATCH_DIRS"
    
    # Run isort
    isort "$WATCH_DIRS"
}

# Run the application with hot reloading
run_app() {
    log "Starting SecondBrainApp in development mode..."
    
    # Set environment variables
    export PYTHONPATH=$PYTHONPATH:$(pwd)
    export SECOND_BRAIN_ENV=development
    
    # Run the application with watchdog for hot reloading
    watchmedo auto-restart --directory="$WATCH_DIRS" --pattern="*.py" --recursive -- python main.py
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    deactivate 2>/dev/null || true
}

# Main execution
main() {
    log "Starting development environment setup..."
    
    # Set up trap for cleanup
    trap cleanup EXIT
    
    # Run setup steps
    check_python
    setup_venv
    check_directories
    
    # Run tests and linters
    run_tests
    run_linters
    
    # Run the application
    run_app
}

# Run main function
main 