#!/bin/zsh

# Baddy Agent Release Script
# This script handles all distribution options for Baddy Agent

# Set working directory
cd /Users/mac/Documents/Cursor_SecondBrain_Release_Package

# Create build directory
BUILD_DIR="$HOME/Desktop/BaddyAgent_FullBuild"
mkdir -p "$BUILD_DIR"

echo "🚀 Starting Baddy Agent Release Process..."

# Function to get version from config
get_version() {
    python3 -c "import yaml; print(yaml.safe_load(open('src/ai_agent/config.yaml'))['version'])"
}

# Function to create GitHub release
create_github_release() {
    echo "📤 Creating GitHub Release..."
    VERSION=$(get_version)
    
    # Create release notes
    cat > "$BUILD_DIR/release_notes.md" << EOF
# Baddy Agent v$VERSION

## What's New
- Enhanced tray interface
- Improved voice recognition
- Phantom Mode enhancements
- Cloud sync improvements
- System monitoring updates

## Installation
1. Download the appropriate package:
   - BaddyAgent.app (macOS App)
   - BaddyAgent.dmg (macOS Installer)
   - BaddyAgent.zip (Portable Version)

2. Run the installation script:
   \`\`\`bash
   ./install_baddy_agent.command
   \`\`\`

## Documentation
- [User Guide](https://github.com/Njanja2025/SecondBrainApp/wiki)
- [API Reference](https://github.com/Njanja2025/SecondBrainApp/wiki/API)
- [Troubleshooting](https://github.com/Njanja2025/SecondBrainApp/wiki/Troubleshooting)
EOF

    # Create release using GitHub CLI
    gh release create "v$VERSION" \
        "$BUILD_DIR/BaddyAgent.app" \
        "$BUILD_DIR/BaddyAgent.dmg" \
        "$BUILD_DIR/BaddyAgent.zip" \
        --title "Baddy Agent v$VERSION" \
        --notes-file "$BUILD_DIR/release_notes.md"
}

# Function to upload to cloud services
upload_to_cloud() {
    echo "☁️ Uploading to cloud services..."
    python3 src/ai_agent/cloud_upload.py \
        --dropbox "$BUILD_DIR/BaddyAgent.zip" \
        --gdrive "$BUILD_DIR/BaddyAgent.dmg" \
        --version "$(get_version)"
}

# Function to create DMG
create_dmg() {
    echo "💿 Creating DMG Installer..."
    sh create_dmg.command
    if [ -f "BaddyAgent.dmg" ]; then
        cp BaddyAgent.dmg "$BUILD_DIR/"
        echo "✅ DMG created successfully"
    else
        echo "❌ Failed to create DMG"
        return 1
    fi
}

# Function to create ZIP
create_zip() {
    echo "📦 Creating ZIP Archive..."
    if [ -d "BaddyAgent.app" ]; then
        zip -r "$BUILD_DIR/BaddyAgent.zip" BaddyAgent.app
        echo "✅ ZIP created successfully"
    else
        echo "❌ Failed to create ZIP"
        return 1
    fi
}

# Function to setup auto-launch
setup_auto_launch() {
    echo "🔄 Setting up auto-launch..."
    osascript <<EOF
    tell application "System Events"
        make new login item at end with properties {path:"/Applications/BaddyAgent.app", hidden:true}
    end tell
EOF
    echo "✅ Auto-launch configured"
}

# Main release process
echo "🔍 Starting release process..."

# Create all distribution packages
create_dmg
create_zip

# Ask for distribution options
echo "
Please choose distribution options:
1) GitHub Release
2) Cloud Distribution (Dropbox + Google Drive)
3) Both
4) Local Only
"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        create_github_release
        ;;
    2)
        upload_to_cloud
        ;;
    3)
        create_github_release
        upload_to_cloud
        ;;
    4)
        echo "📦 Keeping files local only"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Ask about auto-launch
echo "
Would you like to setup auto-launch?
1) Yes
2) No
"

read -p "Enter your choice (1-2): " launch_choice

case $launch_choice in
    1)
        setup_auto_launch
        ;;
    2)
        echo "⏭️ Skipping auto-launch setup"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo "
🎉 Release process completed!

Your Baddy Agent files are available at:
$BUILD_DIR

Distribution Summary:
- App Bundle: $BUILD_DIR/BaddyAgent.app
- DMG Installer: $BUILD_DIR/BaddyAgent.dmg
- ZIP Archive: $BUILD_DIR/BaddyAgent.zip

To start Baddy Agent:
1. Double-click BaddyAgent.app in Applications
2. Or use the tray icon in the menu bar

For support, visit:
https://github.com/Njanja2025/SecondBrainApp
"

# Open the build directory
open "$BUILD_DIR" 