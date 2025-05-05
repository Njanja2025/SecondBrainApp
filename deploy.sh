#!/bin/bash

# SecondBrain Deployment Script

echo "Starting SecondBrain deployment process..."

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Load environment variables
if [ -f ".env" ]; then
    source .env
fi

# Check for required environment variables
if [ "$1" == "--upload" ]; then
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        echo "Error: AWS credentials not found in .env file"
        exit 1
    fi
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "Error: GitHub token not found in .env file"
        exit 1
    fi
fi

# Create necessary directories
mkdir -p dist
mkdir -p build
mkdir -p phantom_logs

# Install required packages
echo "Installing required packages..."
pip3 install py2app cryptography web3 gtts whisper eth_account eth_utils
pip3 install awscli

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/*
rm -rf build/*

# Run py2app
echo "Building macOS app bundle..."
python3 setup.py py2app

# Check if build was successful
if [ ! -d "dist/SecondBrain.app" ]; then
    echo "Error: Build failed!"
    exit 1
fi

# Create distribution package
echo "Creating distribution package..."
cd dist
zip -r SecondBrainApp_Package.zip SecondBrain.app
cd ..

# Calculate checksums
echo "Calculating checksums..."
shasum -a 256 dist/SecondBrainApp_Package.zip > dist/SecondBrainApp_Package.sha256

# Create version file
VERSION="1.0.0"
echo $VERSION > dist/version.txt

echo "Deployment package created successfully!"
echo "Package: dist/SecondBrainApp_Package.zip"
echo "Checksum: dist/SecondBrainApp_Package.sha256"
echo "Version: $VERSION"

# Upload to distribution channels
if [ "$1" == "--upload" ]; then
    echo "Uploading to distribution channels..."
    
    # Upload to AWS S3
    echo "Uploading to AWS S3..."
    aws s3 cp dist/SecondBrainApp_Package.zip s3://njanja-phantom/releases/
    aws s3 cp dist/SecondBrainApp_Package.sha256 s3://njanja-phantom/releases/
    aws s3 cp dist/version.txt s3://njanja-phantom/releases/
    
    # Create GitHub release
    echo "Creating GitHub release..."
    GITHUB_API="https://api.github.com"
    REPO="yourusername/secondbrain"
    
    # Create release
    release_response=$(curl -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "$GITHUB_API/repos/$REPO/releases" \
        -d "{
            \"tag_name\": \"v$VERSION\",
            \"name\": \"SecondBrain v$VERSION\",
            \"body\": \"Release version $VERSION\",
            \"draft\": false,
            \"prerelease\": false
        }")
    
    # Extract release ID
    release_id=$(echo $release_response | jq -r '.id')
    
    # Upload assets
    curl -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Content-Type: application/zip" \
        --data-binary @dist/SecondBrainApp_Package.zip \
        "$GITHUB_API/repos/$REPO/releases/$release_id/assets?name=SecondBrainApp_Package.zip"
        
    curl -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Content-Type: text/plain" \
        --data-binary @dist/SecondBrainApp_Package.sha256 \
        "$GITHUB_API/repos/$REPO/releases/$release_id/assets?name=SecondBrainApp_Package.sha256"
    
    # Update website
    echo "Updating njanja.net/phantom..."
    aws s3 sync dist/ s3://njanja-phantom/website/
    
    echo "Upload complete!"
fi

echo "Deployment complete!" 