#!/bin/bash

# Script to generate SecondBrain application icon

# Exit on error
set -e

# Configuration
ICON_DIR="build/SecondBrain.app/Contents/Resources"
ICON_SIZES=(16 32 64 128 256 512 1024)

# Create icon directory
mkdir -p "$ICON_DIR"

# Create temporary SVG file
cat > "$ICON_DIR/icon.svg" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<svg width="1024" height="1024" version="1.1" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#4A90E2"/>
            <stop offset="100%" style="stop-color:#2C3E50"/>
        </linearGradient>
    </defs>
    <circle cx="512" cy="512" r="512" fill="url(#gradient)"/>
    <path d="M 512 256 L 768 512 L 512 768 L 256 512 Z" fill="white" opacity="0.9"/>
    <circle cx="512" cy="512" r="128" fill="white" opacity="0.7"/>
</svg>
EOF

# Convert SVG to PNG for each size
for size in "${ICON_SIZES[@]}"; do
    echo "Generating ${size}x${size} icon..."
    convert -background none -size "${size}x${size}" "$ICON_DIR/icon.svg" "$ICON_DIR/icon_${size}.png"
done

# Create ICNS file
echo "Creating ICNS file..."
mkdir -p "$ICON_DIR/icon.iconset"
cp "$ICON_DIR/icon_16.png" "$ICON_DIR/icon.iconset/icon_16x16.png"
cp "$ICON_DIR/icon_32.png" "$ICON_DIR/icon.iconset/icon_16x16@2x.png"
cp "$ICON_DIR/icon_32.png" "$ICON_DIR/icon.iconset/icon_32x32.png"
cp "$ICON_DIR/icon_64.png" "$ICON_DIR/icon.iconset/icon_32x32@2x.png"
cp "$ICON_DIR/icon_128.png" "$ICON_DIR/icon.iconset/icon_128x128.png"
cp "$ICON_DIR/icon_256.png" "$ICON_DIR/icon.iconset/icon_128x128@2x.png"
cp "$ICON_DIR/icon_256.png" "$ICON_DIR/icon.iconset/icon_256x256.png"
cp "$ICON_DIR/icon_512.png" "$ICON_DIR/icon.iconset/icon_256x256@2x.png"
cp "$ICON_DIR/icon_512.png" "$ICON_DIR/icon.iconset/icon_512x512.png"
cp "$ICON_DIR/icon_1024.png" "$ICON_DIR/icon.iconset/icon_512x512@2x.png"

iconutil -c icns "$ICON_DIR/icon.iconset" -o "$ICON_DIR/AppIcon.icns"

# Clean up temporary files
rm -rf "$ICON_DIR/icon.iconset"
rm "$ICON_DIR/icon.svg"
rm "$ICON_DIR/icon_"*.png

echo "Icon generation complete!" 