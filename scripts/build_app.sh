#!/bin/bash

# Exit on error
set -e

# Configuration
APP_NAME="SecondBrainApp2025"
ICON_PATH="assets/secondbrain.icns"
REQUIREMENTS_FILE="requirements.txt"
PYTHON_VERSION="3.9"  # Minimum required Python version
BACKUP_DIR="backups"
VERSION_FILE="version.txt"

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

# Check and install dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        error "pip3 is not installed"
    fi
    
    # Check if PyInstaller is installed
    if ! pip3 show pyinstaller &> /dev/null; then
        log "Installing PyInstaller..."
        pip3 install pyinstaller
    fi
    
    # Install requirements
    if [ -f "$REQUIREMENTS_FILE" ]; then
        log "Installing requirements..."
        pip3 install -r "$REQUIREMENTS_FILE"
    else
        warn "Requirements file not found: $REQUIREMENTS_FILE"
    fi
}

# Check for required files and directories
check_files() {
    log "Checking required files and directories..."
    
    # Check main Python file
    if [ ! -f "main.py" ]; then
        error "main.py not found"
    fi
    
    # Check icon file
    if [ ! -f "$ICON_PATH" ]; then
        warn "Icon file not found: $ICON_PATH"
    fi
    
    # Create required directories if they don't exist
    mkdir -p config logs data "$BACKUP_DIR"
}

# Get current version
get_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE"
    else
        echo "1.0.0"
    fi
}

# Create backup of current version
create_backup() {
    log "Creating backup of current version..."
    
    if [ -d "dist/$APP_NAME.app" ]; then
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_path="$BACKUP_DIR/${APP_NAME}_${timestamp}"
        
        # Create backup
        cp -r "dist/$APP_NAME.app" "$backup_path"
        
        # Create backup info
        version=$(get_version)
        echo "{
            \"version\": \"$version\",
            \"timestamp\": \"$timestamp\",
            \"backup_path\": \"$backup_path\",
            \"status\": \"stable\"
        }" > "$backup_path/info.json"
        
        log "Backup created at $backup_path"
    else
        warn "No current version to backup"
    fi
}

# Clean previous builds
clean_build() {
    log "Cleaning previous builds..."
    rm -rf build dist
    rm -f *.spec
}

# Build the application
build_app() {
    log "Building $APP_NAME..."
    
    # Build command
    pyinstaller main.py \
        --name "$APP_NAME" \
        --windowed \
        --clean \
        --add-data "config:config" \
        --add-data "assets:assets" \
        --add-data "logs:logs" \
        --add-data "data:data" \
        --add-data "src:src" \
        --hidden-import=PyQt5 \
        --hidden-import=PyQt5.QtCore \
        --hidden-import=PyQt5.QtGui \
        --hidden-import=PyQt5.QtWidgets \
        --hidden-import=cryptography \
        --hidden-import=jwt \
        --hidden-import=sqlite3 \
        --icon "$ICON_PATH" \
        --noconfirm
    
    # Check if build was successful
    if [ ! -d "dist/$APP_NAME.app" ]; then
        error "Build failed: dist/$APP_NAME.app not found"
    fi
}

# Verify the build
verify_build() {
    log "Verifying build..."
    
    # Check if the app bundle exists
    if [ ! -d "dist/$APP_NAME.app" ]; then
        error "Build verification failed: dist/$APP_NAME.app not found"
    fi
    
    # Check if the executable exists
    if [ ! -f "dist/$APP_NAME.app/Contents/MacOS/$APP_NAME" ]; then
        error "Build verification failed: Executable not found"
    fi
    
    log "Build verification successful"
}

# Cleanup old backups
cleanup_backups() {
    log "Cleaning up old backups..."
    
    # Keep only the last 5 backups
    ls -t "$BACKUP_DIR"/*.app 2>/dev/null | tail -n +6 | xargs -r rm -rf
}

# Main execution
main() {
    log "Starting build process for $APP_NAME..."
    
    # Run checks and build steps
    check_python
    check_dependencies
    check_files
    create_backup
    clean_build
    build_app
    verify_build
    cleanup_backups
    
    log "Build complete! Application bundle is in dist/$APP_NAME.app"
    log "You can now run package_zip.sh to create a distributable package"
}

# Run main function
main 