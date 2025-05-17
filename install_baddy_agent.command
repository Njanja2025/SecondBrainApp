#!/bin/zsh

# Baddy Agent Installation Script
# This script handles all deployment options for Baddy Agent

# Set working directory
cd /Users/mac/Documents/Cursor_SecondBrain_Release_Package

# Create build directory
BUILD_DIR="$HOME/Desktop/BaddyAgent_FullBuild"
mkdir -p "$BUILD_DIR"

echo "🚀 Starting Baddy Agent Installation..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to create app bundle
create_app_bundle() {
    echo "📦 Creating App Bundle..."
    sh create_app_bundle.command
    if [ -d "BaddyAgent.app" ]; then
        cp -R BaddyAgent.app "$BUILD_DIR/"
        echo "✅ App Bundle created successfully"
    else
        echo "❌ Failed to create App Bundle"
        return 1
    fi
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

# Function to install to Applications
install_to_applications() {
    echo "📥 Installing to Applications..."
    if [ -d "BaddyAgent.app" ]; then
        cp -R BaddyAgent.app /Applications/
        echo "✅ Installed to Applications"
    else
        echo "❌ Failed to install to Applications"
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

# Function to upload to cloud
upload_to_cloud() {
    echo "☁️ Uploading to cloud services..."
    python3 src/ai_agent/cloud_upload.py
    echo "✅ Cloud upload completed"
}

# Main installation process
echo "🔍 Checking requirements..."

# Check Python
if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Create all deployment options
create_app_bundle
create_dmg
create_zip

# Ask for installation type
echo "
Please choose installation type:
1) Quick Install (App Bundle only)
2) Full Install (App Bundle + Auto-launch)
3) Custom Install (Choose components)
"

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        install_to_applications
        ;;
    2)
        install_to_applications
        setup_auto_launch
        ;;
    3)
        echo "
Available components:
1) Install to Applications
2) Setup auto-launch
3) Upload to cloud services
"
        read -p "Enter components to install (comma-separated, e.g., 1,2): " components
        IFS=',' read -ra COMP <<< "$components"
        for i in "${COMP[@]}"; do
            case $i in
                1) install_to_applications ;;
                2) setup_auto_launch ;;
                3) upload_to_cloud ;;
            esac
        done
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo "
🎉 Installation completed!

Your Baddy Agent files are available at:
$BUILD_DIR

To start Baddy Agent:
1. Double-click BaddyAgent.app in Applications
2. Or use the tray icon in the menu bar

For support, visit:
https://github.com/Njanja2025/SecondBrainApp
"

# Open the build directory
open "$BUILD_DIR" 