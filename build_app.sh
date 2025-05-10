#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting SecondBrainApp build process...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3 is not installed. Please install pip3 first.${NC}"
    exit 1
fi

# Install PyInstaller if not already installed
echo -e "${GREEN}Checking PyInstaller installation...${NC}"
if ! pip3 show pyinstaller &> /dev/null; then
    echo -e "${GREEN}Installing PyInstaller...${NC}"
    pip3 install pyinstaller
fi

# Install requirements
echo -e "${GREEN}Installing requirements...${NC}"
pip3 install -r requirements.txt

# Run the build
echo -e "${GREEN}Building SecondBrainApp...${NC}"
python3 setup.py --build-app

# Check if build was successful
if [ -d "dist/SecondBrainApp2025.app" ]; then
    echo -e "${GREEN}Build successful!${NC}"
    echo -e "${GREEN}App location: dist/SecondBrainApp2025.app${NC}"
    echo -e "${GREEN}Package location: SecondBrainApp_Package.zip${NC}"
else
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

# Optional: Create checksum
echo -e "${GREEN}Creating checksum...${NC}"
shasum -a 256 SecondBrainApp_Package.zip > SecondBrainApp_Package.zip.sha256

echo -e "${GREEN}Build process completed!${NC}" 