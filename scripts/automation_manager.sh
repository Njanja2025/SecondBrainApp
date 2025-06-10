#!/bin/bash
set -e

# Configuration
REPO_PATH="/Users/mac/Documents/Applications/BaddyAgent.app/Contents/Resources/SecondBrainApp"
BRANCH="main"
VENV_PATH="venv"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[✓] $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}[✗] $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to setup virtual environment
setup_venv() {
    print_status "Setting up virtual environment..."
    if [ ! -d "$VENV_PATH" ]; then
        python3 -m venv "$VENV_PATH"
    fi
    source "$VENV_PATH/bin/activate"
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    print_status "Virtual environment setup complete"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    python -m pytest brain/tests/ -v --cov=brain
    print_status "Tests completed"
}

# Function to run security checks
run_security_checks() {
    print_status "Running security checks..."
    bandit -r brain/
    safety check
    print_status "Security checks completed"
}

# Function to sync with remote
sync_with_remote() {
    print_status "Syncing with remote repository..."
    git fetch origin
    git reset --hard origin/$BRANCH
    git clean -fd
    print_status "Sync completed"
}

# Function to update dependencies
update_dependencies() {
    print_status "Updating dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    print_status "Dependencies updated"
}

# Function to check system health
check_system_health() {
    print_status "Checking system health..."
    
    # Check Python version
    python --version
    
    # Check pip version
    pip --version
    
    # Check git version
    git --version
    
    # Check disk space
    df -h
    
    # Check memory usage
    top -l 1 | head -n 10
    
    print_status "System health check completed"
}

# Function to backup database
backup_database() {
    print_status "Backing up database..."
    if [ -f "brain/memory_engine.db" ]; then
        cp brain/memory_engine.db "brain/memory_engine.db.backup.$(date +%Y%m%d_%H%M%S)"
        print_status "Database backup completed"
    else
        print_warning "No database file found to backup"
    fi
}

# Function to restore database
restore_database() {
    print_status "Restoring database..."
    latest_backup=$(ls -t brain/memory_engine.db.backup.* | head -n 1)
    if [ -n "$latest_backup" ]; then
        cp "$latest_backup" brain/memory_engine.db
        print_status "Database restored from $latest_backup"
    else
        print_error "No backup found to restore"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [option]"
    echo "Options:"
    echo "  setup      - Setup virtual environment and install dependencies"
    echo "  test       - Run tests"
    echo "  security   - Run security checks"
    echo "  sync       - Sync with remote repository"
    echo "  update     - Update dependencies"
    echo "  health     - Check system health"
    echo "  backup     - Backup database"
    echo "  restore    - Restore database"
    echo "  all        - Run all checks and updates"
    echo "  help       - Show this help message"
}

# Main script
case "$1" in
    "setup")
        setup_venv
        ;;
    "test")
        run_tests
        ;;
    "security")
        run_security_checks
        ;;
    "sync")
        sync_with_remote
        ;;
    "update")
        update_dependencies
        ;;
    "health")
        check_system_health
        ;;
    "backup")
        backup_database
        ;;
    "restore")
        restore_database
        ;;
    "all")
        setup_venv
        run_tests
        run_security_checks
        sync_with_remote
        update_dependencies
        check_system_health
        backup_database
        ;;
    "help"|"")
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac 