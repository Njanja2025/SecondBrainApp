#!/bin/bash

# Main build script for SecondBrain macOS application

# Exit on error
set -e

# Configuration
APP_NAME="SecondBrain"
VERSION="2025"
BUILD_DIR="build"
REQUIRED_PYTHON_VERSION="3.8"
CLEANUP_FILES=()
LOG_FILE="build.log"
BACKUP_DIR="backups"
CONFIG_FILE="build_config.json"
DRY_RUN=false
VERBOSE=false
QUIET=false
ROLLBACK_POINTS=()

# App packaging configuration
APP_BUNDLE="$BUILD_DIR/$APP_NAME.app"
APP_CONTENTS="$APP_BUNDLE/Contents"
APP_MACOS="$APP_CONTENTS/MacOS"
APP_RESOURCES="$APP_CONTENTS/Resources"
APP_FRAMEWORKS="$APP_CONTENTS/Frameworks"
APP_PLUGINS="$APP_CONTENTS/PlugIns"
APP_SHARED_SUPPORT="$APP_CONTENTS/SharedSupport"

# Suppress warnings
export PYTHONWARNINGS="ignore"
export KMP_DUPLICATE_LIB_OK="True"

# Enhanced logging function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    local exit_code=$1
    local error_message=$2
    log "ERROR" "$error_message"
    
    # Attempt rollback if available
    if [ ${#ROLLBACK_POINTS[@]} -gt 0 ]; then
        local last_point="${ROLLBACK_POINTS[${#ROLLBACK_POINTS[@]}-1]}"
        log "INFO" "Attempting rollback to $last_point"
        rollback "$last_point"
    fi
    
    exit "$exit_code"
}

# Rollback function
rollback() {
    local point=$1
    log "INFO" "Rolling back to $point"
    if [ -d "$point" ]; then
        rm -rf "$APP_BUNDLE"
        cp -R "$point" "$APP_BUNDLE"
        log "INFO" "Rollback completed successfully"
    else
        log "ERROR" "Rollback point $point not found"
    fi
}

# Create backup
create_backup() {
    local backup_name="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S)"
    log "INFO" "Creating backup: $backup_name"
    mkdir -p "$BACKUP_DIR"
    if [ -d "$APP_BUNDLE" ]; then
        cp -R "$APP_BUNDLE" "$backup_name"
        ROLLBACK_POINTS+=("$backup_name")
    fi
}

# Validate Python version
validate_python() {
    local python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [ "$(printf '%s\n' "$REQUIRED_PYTHON_VERSION" "$python_version" | sort -V | head -n1)" != "$REQUIRED_PYTHON_VERSION" ]; then
        handle_error 1 "Python version $REQUIRED_PYTHON_VERSION or higher is required. Found $python_version"
    fi
}

# Create app bundle structure
create_app_bundle() {
    log "INFO" "Creating app bundle structure..."
    
    # Create directory structure
    mkdir -p "$APP_MACOS"
    mkdir -p "$APP_RESOURCES"
    mkdir -p "$APP_FRAMEWORKS"
    mkdir -p "$APP_PLUGINS"
    mkdir -p "$APP_SHARED_SUPPORT"
    
    # Create Info.plist
    cat > "$APP_CONTENTS/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.secondbrain.app</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
    
    # Create launcher script
    cat > "$APP_MACOS/$APP_NAME" << EOF
#!/bin/bash
cd "\$(dirname "\$0")/../Resources"
exec python3 main.py "\$@"
EOF
    
    chmod +x "$APP_MACOS/$APP_NAME"
    
    # Create README
    cat > "$APP_BUNDLE/README.txt" << EOF
SecondBrainApp $VERSION macOS .app build - Final Release
Built: $(date)
Status: Ready
EOF
}

# Copy resources with validation
copy_resources() {
    log "INFO" "Copying resources..."
    
    # Validate source directories
    for dir in resources launcher config models voices; do
        if [ ! -d "$dir" ]; then
            handle_error 1 "Required directory $dir not found"
        fi
    done
    
    # Copy main resources with progress
    for dir in resources launcher config models voices; do
        log "INFO" "Copying $dir..."
        cp -R "$dir" "$APP_RESOURCES/" || handle_error 1 "Failed to copy $dir"
    done
    
    # Copy Python site-packages with validation
    local site_packages="venv/lib/python3.11/site-packages"
    if [ ! -d "$site_packages" ]; then
        handle_error 1 "Python site-packages not found at $site_packages"
    fi
    cp -R "$site_packages" "$APP_FRAMEWORKS/" || handle_error 1 "Failed to copy site-packages"
}

# Create DMG with validation
create_dmg() {
    log "INFO" "Creating DMG..."
    local dmg_path="$BUILD_DIR/$APP_NAME-$VERSION.dmg"
    
    # Validate app bundle
    if [ ! -d "$APP_BUNDLE" ]; then
        handle_error 1 "App bundle not found at $APP_BUNDLE"
    fi
    
    # Create DMG
    hdiutil create -volname "$APP_NAME-$VERSION" -srcfolder "$APP_BUNDLE" -ov -format UDZO "$dmg_path" 2>/dev/null || handle_error 1 "Failed to create DMG"
    
    # Validate DMG
    if [ ! -f "$dmg_path" ]; then
        handle_error 1 "DMG creation failed"
    fi
    
    log "INFO" "DMG created successfully: $dmg_path"
}

# Create zip archive with validation
create_zip() {
    log "INFO" "Creating zip archive..."
    local zip_path="$BUILD_DIR/$APP_NAME-$VERSION.zip"
    local current_dir=$(pwd)
    
    # Create zip
    cd "$BUILD_DIR" || handle_error 1 "Failed to change to build directory"
    zip -r "$APP_NAME-$VERSION.zip" "$APP_NAME.app" >/dev/null 2>&1 || handle_error 1 "Failed to create zip archive"
    cd "$current_dir" || handle_error 1 "Failed to return to original directory"
    
    # Validate zip
    if [ ! -f "$zip_path" ]; then
        handle_error 1 "Zip creation failed"
    fi
    
    log "INFO" "Zip archive created successfully: $zip_path"
}

# Cleanup function
cleanup() {
    log "INFO" "Cleaning up temporary files..."
    for file in "${CLEANUP_FILES[@]}"; do
        if [ -f "$file" ]; then
            rm -f "$file"
        fi
    done
}

# Main build process
main() {
    # Initialize logging
    > "$LOG_FILE"
    log "INFO" "Starting build process for $APP_NAME v$VERSION"
    
    # Validate Python version
    validate_python
    
    # Create build directory
    mkdir -p "$BUILD_DIR"
    
    # Create backup
    create_backup
    
    # Create app bundle
    create_app_bundle
    
    # Copy resources
    copy_resources
    
    # Run Python packager
    log "INFO" "Running Python packager..."
    if ! python3 package_app.py; then
        handle_error 1 "Python packaging failed"
    fi
    
    # Cleanup
    cleanup
    
    log "INFO" "Build complete!"
    echo "Distribution files are available in $BUILD_DIR/dist"
    echo "- $APP_NAME-$VERSION.dmg"
    echo "- $APP_NAME-$VERSION.zip"
    echo "- $APP_NAME-$VERSION-manifest.json"
}

# Trap errors
trap 'handle_error $? "An error occurred"' ERR

# Run main function
main