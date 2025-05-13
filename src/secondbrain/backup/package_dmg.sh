#!/bin/bash

# SecondBrain Backup System DMG Packaging Script
set -e

# Configuration
APP_NAME="SecondBrain Backup"
VERSION="1.0.0"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
TEMP_DIR="/tmp/secondbrain_package"
APP_DIR="${TEMP_DIR}/${APP_NAME}.app"
CONTENTS_DIR="${APP_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"

# Create temporary directory structure
echo "Creating package structure..."
rm -rf "${TEMP_DIR}"
mkdir -p "${MACOS_DIR}" "${RESOURCES_DIR}"

# Copy application files
echo "Copying application files..."
cp -r src "${RESOURCES_DIR}/"
cp -r README.md LICENSE "${RESOURCES_DIR}/"

# Create Info.plist
cat > "${CONTENTS_DIR}/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.secondbrain.backup</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleExecutable</key>
    <string>secondbrain_backup</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create launcher script
cat > "${MACOS_DIR}/secondbrain_backup" << EOF
#!/bin/bash
cd "\$(dirname "\$0")/../Resources"
PYTHONPATH=src python3 src/secondbrain/backup/backup_cli.py "\$@"
EOF

chmod +x "${MACOS_DIR}/secondbrain_backup"

# Create DMG
echo "Creating DMG..."
hdiutil create -volname "${APP_NAME}" -srcfolder "${TEMP_DIR}" -ov -format UDZO "${DMG_NAME}"

# Clean up
echo "Cleaning up..."
rm -rf "${TEMP_DIR}"

echo "✅ Package created: ${DMG_NAME}" 