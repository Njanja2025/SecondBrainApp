# Windows packaging script for SecondBrainApp
# Requires: pyinstaller, python3, and all dependencies installed

import os
import sys
import subprocess
from pathlib import Path

APP_NAME = "SecondBrainApp"
ENTRY_SCRIPT = "src/main.py"
ICON_PATH = "resources/icon.ico"  # Update if you have a Windows icon

# Build command
pyinstaller_cmd = [
    "pyinstaller",
    "--noconfirm",
    "--onefile",
    f"--name={APP_NAME}",
]

if Path(ICON_PATH).exists():
    pyinstaller_cmd.append(f"--icon={ICON_PATH}")
pyinstaller_cmd.append(ENTRY_SCRIPT)

print("Running:", " ".join(pyinstaller_cmd))
subprocess.run(pyinstaller_cmd, check=True)

print(f"\nBuild complete. Your Windows .exe is in 'dist/{APP_NAME}.exe'")
print("To test, run:")
print(f"  dist\\{APP_NAME}.exe")
