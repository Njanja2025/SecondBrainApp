#!/bin/zsh

echo "Starting voice system troubleshooting..."

# Check Python version
echo "\nChecking Python version..."
python3 --version

# Check pip packages
echo "\nChecking installed packages..."
pip list | grep -E "pyobjc|pyttsx3"

# Check voice synthesis
echo "\nTesting voice synthesis..."
python3 -c "
import pyttsx3
import sys
try:
    engine = pyttsx3.init(driverName='nsss')
    engine.say('Testing voice synthesis')
    engine.runAndWait()
    print('Voice synthesis test successful')
except Exception as e:
    print(f'Voice synthesis test failed: {e}')
    sys.exit(1)
"

# Check system permissions
echo "\nChecking system permissions..."
ls -l /System/Library/Speech/Voices/

# Check log files
echo "\nChecking voice system logs..."
if [ -f /tmp/secondbrain_voice.log ]; then
    echo "Recent voice system logs:"
    tail -n 20 /tmp/secondbrain_voice.log
else
    echo "No voice system logs found"
fi

echo "\nTroubleshooting complete. If you see any errors above, please report them." 