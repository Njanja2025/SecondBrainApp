#!/bin/bash

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
APP_NAME="SecondBrainApp"
VERSION="2025"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$APP_DIR/dist"
BUILD_DIR="$APP_DIR/build"

# Function to print status
print_status() {
    echo -e "${2}$(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

# Function to check command existence
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_status "❌ Error: $1 is required but not installed." "$RED"
        case "$1" in
            "platypus")
                print_status "To install Platypus, you can use Homebrew:" "$BLUE"
                print_status "  brew install platypus" "$YELLOW"
                print_status "Then link the command-line tool:" "$BLUE"
                print_status "  sudo ln -sf /Applications/Platypus.app/Contents/Resources/platypus_clt /usr/local/bin/platypus" "$YELLOW"
                ;;
            "zip")
                print_status "To install zip:" "$BLUE"
                print_status "  brew install zip" "$YELLOW"
                ;;
        esac
        return 1
    fi
    return 0
}

# Function to verify directory existence
verify_directory() {
    if [ ! -d "$1" ]; then
        print_status "Creating directory: $1" "$YELLOW"
        mkdir -p "$1" || {
            print_status "❌ Failed to create directory: $1" "$RED"
            exit 1
        }
    fi
}

# Function to verify file existence
verify_file() {
    if [ ! -f "$1" ]; then
        print_status "❌ Required file not found: $1" "$RED"
        return 1
    fi
    return 0
}

# Check required tools
print_status "🔍 Checking required tools..." "$YELLOW"
TOOLS_MISSING=0
for tool in "platypus" "zip"; do
    if ! check_command "$tool"; then
        TOOLS_MISSING=1
    fi
done

if [ $TOOLS_MISSING -eq 1 ]; then
    print_status "Please install missing tools and try again" "$RED"
    exit 1
fi

# Verify required directories and files
print_status "🔍 Verifying project structure..." "$YELLOW"
verify_directory "$APP_DIR"
verify_directory "$APP_DIR/assets"
verify_directory "$APP_DIR/logs"

REQUIRED_FILES=(
    "$APP_DIR/SecondBrainApp.code-workspace"
    "$APP_DIR/start_assistant.sh"
    "$APP_DIR/requirements.txt"
    "$APP_DIR/SecondBrainApp.platypus"
)

FILES_MISSING=0
for file in "${REQUIRED_FILES[@]}"; do
    if ! verify_file "$file"; then
        FILES_MISSING=1
    fi
done

if [ $FILES_MISSING -eq 1 ]; then
    print_status "Please ensure all required files are present and try again" "$RED"
    exit 1
fi

# Create distribution directories
verify_directory "$DIST_DIR"
verify_directory "$BUILD_DIR"

# Clean previous builds
print_status "🧹 Cleaning previous builds..." "$YELLOW"
rm -rf "$DIST_DIR"/* "$BUILD_DIR"/*

# Build macOS app using Platypus
print_status "🔨 Building macOS app..." "$YELLOW"
platypus -P "$APP_DIR/SecondBrainApp.platypus" "$BUILD_DIR/$APP_NAME.app" || {
    print_status "❌ Failed to build macOS app" "$RED"
    print_status "Check Platypus configuration and try again" "$YELLOW"
    exit 1
}

# Create ZIP archive
print_status "📦 Creating ZIP archive..." "$YELLOW"
zip -r "$DIST_DIR/${APP_NAME}_${VERSION}.zip" \
    "$BUILD_DIR/$APP_NAME.app" \
    "$APP_DIR/SecondBrainApp.code-workspace" \
    "$APP_DIR/README.md" \
    "$APP_DIR/start_assistant.sh" \
    "$APP_DIR/requirements.txt" \
    "$APP_DIR/assets" || {
    print_status "❌ Failed to create ZIP archive" "$RED"
    exit 1
}

# Create desktop shortcut
print_status "🔗 Creating desktop shortcut..." "$YELLOW"
if cp "$APP_DIR/Launch_SecondBrainApp.command" "$HOME/Desktop/"; then
    chmod +x "$HOME/Desktop/Launch_SecondBrainApp.command"
    print_status "✅ Desktop shortcut created" "$GREEN"
else
    print_status "❌ Failed to create desktop shortcut" "$RED"
fi

# Final status report
print_status "\n📋 Build Summary:" "$BLUE"
print_status "✨ Package creation complete!" "$GREEN"
print_status "📍 Distribution files: $DIST_DIR" "$GREEN"
if [ -f "$HOME/Desktop/Launch_SecondBrainApp.command" ]; then
    print_status "🚀 Desktop shortcut: $HOME/Desktop/Launch_SecondBrainApp.command" "$GREEN"
fi

print_status "\n📦 Distribution package includes:" "$BLUE"
print_status "- macOS App Bundle" "$YELLOW"
print_status "- Workspace configuration" "$YELLOW"
print_status "- Documentation" "$YELLOW"
print_status "- Launch scripts" "$YELLOW"
print_status "- Assets and resources" "$YELLOW"

print_status "\n📝 Next steps:" "$BLUE"
print_status "1. Install the app from: $BUILD_DIR/$APP_NAME.app" "$YELLOW"
print_status "2. Test the desktop shortcut" "$YELLOW" 