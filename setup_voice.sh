#!/bin/zsh

# Install required packages
pip install pyobjc pyobjc-framework-Cocoa pyobjc-framework-Speech pyttsx3

# Set up environment and run voice trigger
cd /Users/mac/Documents/Cursor_SecondBrain_Release_Package
PYTHONPATH=src python3 src/secondbrain/cli/voice_trigger.py 