#!/bin/bash

# Configuration
APP_NAME="SecondBrain"
VERSION="2025"
BUILD_DIR="build"
APP_BUNDLE="$BUILD_DIR/$APP_NAME.app"
APP_CONTENTS="$APP_BUNDLE/Contents"
APP_MACOS="$APP_CONTENTS/MacOS"
APP_RESOURCES="$APP_CONTENTS/Resources"
APP_FRAMEWORKS="$APP_CONTENTS/Frameworks"
APP_PLUGINS="$APP_CONTENTS/PlugIns"
APP_SHARED_SUPPORT="$APP_CONTENTS/SharedSupport"

# Logging function
log() {
    local level=$1
    local message=$2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message"
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
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.secondbrain.app</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
EOF
    
    # Create launcher script
    cat > "$APP_MACOS/$APP_NAME" << EOF
#!/bin/bash
cd "\$(dirname "\$0")/../Resources"
exec python3.11 launcher/main.py "\$@"
EOF
    chmod +x "$APP_MACOS/$APP_NAME"
    
    # Copy resources
    cp -r "resources" "$APP_RESOURCES/"
    cp -r "launcher" "$APP_RESOURCES/"
    cp -r "config" "$APP_RESOURCES/"
    cp -r "models" "$APP_RESOURCES/"
    cp -r "voices" "$APP_RESOURCES/"
    
    # Copy frameworks
    cp -r "venv/lib/python3.11/site-packages" "$APP_FRAMEWORKS/"
    
    # Create PkgInfo
    echo "APPL????" > "$APP_CONTENTS/PkgInfo"
}

# Create DMG
create_dmg() {
    log "INFO" "Creating DMG..."
    local dmg_path="$BUILD_DIR/$APP_NAME-$VERSION.dmg"
    
    # Create temporary directory for DMG
    local temp_dir="$BUILD_DIR/dmg_temp"
    mkdir -p "$temp_dir"
    
    # Copy app bundle
    cp -r "$APP_BUNDLE" "$temp_dir/"
    
    # Create DMG
    hdiutil create -volname "$APP_NAME" -srcfolder "$temp_dir" -ov -format UDZO "$dmg_path"
    
    # Cleanup
    rm -rf "$temp_dir"
}

# Create zip archive
create_zip() {
    log "INFO" "Creating zip archive..."
    local zip_path="$BUILD_DIR/$APP_NAME-$VERSION.zip"
    
    # Create zip
    cd "$BUILD_DIR"
    zip -r "$zip_path" "$APP_NAME.app"
    cd - > /dev/null
}

# Main packaging process
main() {
    log "INFO" "Starting packaging process for $APP_NAME v$VERSION"
    
    # Create build directory if it doesn't exist
    mkdir -p "$BUILD_DIR"
    
    # Create app bundle
    create_app_bundle
    
    # Create distribution
    create_dmg
    create_zip
    
    log "INFO" "Packaging complete!"
    echo "Distribution files are available in: $BUILD_DIR"
    echo "- $APP_NAME-$VERSION.dmg"
    echo "- $APP_NAME-$VERSION.zip"
}

# Run main function
main 