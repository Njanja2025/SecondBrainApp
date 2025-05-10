#!/bin/bash

# Exit on error
set -e

# Configuration
APP_NAME="SecondBrainApp2025"
VERSION=$(date +'%Y.%m.%d')
PACKAGE_NAME="${APP_NAME}_${VERSION}"
DEPLOY_DIR="deploy"
README_FILE="README.md"
LICENSE_FILE="LICENSE"
CHANGELOG_FILE="CHANGELOG.md"

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

# Check if build exists
check_build() {
    log "Checking build..."
    if [ ! -d "dist/$APP_NAME.app" ]; then
        error "Build not found. Please run build_app.sh first"
    fi
}

# Create deployment directory
create_deploy_dir() {
    log "Creating deployment directory..."
    rm -rf "$DEPLOY_DIR"
    mkdir -p "$DEPLOY_DIR"
}

# Copy application files
copy_files() {
    log "Copying application files..."
    
    # Copy app bundle
    cp -R "dist/$APP_NAME.app" "$DEPLOY_DIR/"
    
    # Copy documentation
    if [ -f "$README_FILE" ]; then
        cp "$README_FILE" "$DEPLOY_DIR/"
    else
        warn "README file not found: $README_FILE"
    fi
    
    if [ -f "$LICENSE_FILE" ]; then
        cp "$LICENSE_FILE" "$DEPLOY_DIR/"
    else
        warn "License file not found: $LICENSE_FILE"
    fi
    
    if [ -f "$CHANGELOG_FILE" ]; then
        cp "$CHANGELOG_FILE" "$DEPLOY_DIR/"
    else
        warn "Changelog file not found: $CHANGELOG_FILE"
    fi
    
    # Copy requirements
    if [ -f "requirements.txt" ]; then
        cp "requirements.txt" "$DEPLOY_DIR/"
    fi
}

# Create ZIP package
create_zip() {
    log "Creating ZIP package..."
    
    # Remove old package if exists
    rm -f "${PACKAGE_NAME}.zip"
    
    # Create ZIP
    cd "$DEPLOY_DIR"
    zip -r "../${PACKAGE_NAME}.zip" .
    cd ..
    
    # Verify ZIP
    if [ ! -f "${PACKAGE_NAME}.zip" ]; then
        error "Failed to create ZIP package"
    fi
    
    # Calculate checksum
    SHA256=$(shasum -a 256 "${PACKAGE_NAME}.zip" | cut -d' ' -f1)
    echo "$SHA256" > "${PACKAGE_NAME}.zip.sha256"
}

# Clean up
cleanup() {
    log "Cleaning up..."
    rm -rf "$DEPLOY_DIR"
}

# Main execution
main() {
    log "Starting packaging process for $APP_NAME..."
    
    # Run packaging steps
    check_build
    create_deploy_dir
    copy_files
    create_zip
    cleanup
    
    log "Packaging complete!"
    log "Package: ${PACKAGE_NAME}.zip"
    log "SHA256: $(cat "${PACKAGE_NAME}.zip.sha256")"
}

# Run main function
main 