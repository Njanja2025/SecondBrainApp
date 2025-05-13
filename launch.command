#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 to run SecondBrain."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
if [ ! -f "venv/.requirements_installed" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
    touch venv/.requirements_installed
fi

# Launch the application
echo "Starting SecondBrain..."
python3 launch_secondbrain.py

# Keep the terminal window open if there's an error
if [ $? -ne 0 ]; then
    echo "An error occurred. Press Enter to exit..."
    read
fi 