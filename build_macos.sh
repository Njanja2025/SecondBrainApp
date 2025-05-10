#!/bin/bash

# Build script for SecondBrain macOS .app bundle

# Exit on error
set -e

# Configuration
APP_NAME="SecondBrain"
VERSION="1.0.0"
BUILD_DIR="build"
APP_DIR="$BUILD_DIR/$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
FRAMEWORKS_DIR="$CONTENTS_DIR/Frameworks"

# Create directory structure
echo "Creating directory structure..."
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"
mkdir -p "$FRAMEWORKS_DIR"

# Copy Python files
echo "Copying Python files..."
cp -r src "$MACOS_DIR/"
cp -r tests "$MACOS_DIR/"
cp -r docs "$MACOS_DIR/"

# Create Info.plist
echo "Creating Info.plist..."
cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>secondbrain</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.secondbrain.app</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
EOF

# Create launcher script
echo "Creating launcher script..."
cat > "$MACOS_DIR/secondbrain" << EOF
#!/bin/bash
DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )" && pwd )"
cd "\$DIR"
python3 -m src.secondbrain.cli.backup_cli "\$@"
EOF

# Make launcher executable
chmod +x "$MACOS_DIR/secondbrain"

# Create requirements.txt
echo "Creating requirements.txt..."
cat > "$MACOS_DIR/requirements.txt" << EOF
schedule>=1.1.0
dropbox>=11.36.0
google-api-python-client>=2.0.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=0.4.0
EOF

# Create setup script
echo "Creating setup script..."
cat > "$MACOS_DIR/setup.sh" << EOF
#!/bin/bash
DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )" && pwd )"
cd "\$DIR"
python3 -m pip install -r requirements.txt
EOF

# Make setup script executable
chmod +x "$MACOS_DIR/setup.sh"

# Create README
echo "Creating README..."
cat > "$MACOS_DIR/README.txt" << EOF
SecondBrain Backup System
=======================

This is the macOS application bundle for the SecondBrain Backup System.

Installation
-----------
1. Run the setup script to install dependencies:
   ./setup.sh

2. Run the application:
   ./secondbrain

For more information, see the documentation in the docs directory.
EOF

# Create .app bundle
echo "Creating .app bundle..."
cd "$BUILD_DIR"
zip -r "$APP_NAME-$VERSION.zip" "$APP_NAME.app"

echo "Build complete! The .app bundle is located at: $APP_DIR"
echo "A zip archive is available at: $BUILD_DIR/$APP_NAME-$VERSION.zip" 