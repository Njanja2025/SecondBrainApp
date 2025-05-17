import os
import sys
import shutil
from pathlib import Path
import plistlib
import subprocess
import base64

def create_app_bundle():
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    app_name = "BaddyAgent.app"
    app_path = base_dir / app_name
    contents_path = app_path / "Contents"
    macos_path = contents_path / "MacOS"
    resources_path = contents_path / "Resources"
    
    # Create directory structure
    for path in [contents_path, macos_path, resources_path]:
        path.mkdir(parents=True, exist_ok=True)
        
    # Create Info.plist with enhanced metadata
    info_plist = {
        "CFBundleName": "BaddyAgent",
        "CFBundleDisplayName": "Baddy Agent",
        "CFBundleIdentifier": "com.njanja.baddyagent",
        "CFBundleVersion": "1.0",
        "CFBundleShortVersionString": "1.0",
        "CFBundlePackageType": "APPL",
        "CFBundleSignature": "????",
        "LSMinimumSystemVersion": "10.13.0",
        "NSHighResolutionCapable": True,
        "LSUIElement": True,  # This makes it a background app
        "NSPrincipalClass": "NSApplication",
        "LSApplicationCategoryType": "public.app-category.utilities",
        "NSHumanReadableCopyright": "© 2024 Njanja",
        "NSAppleEventsUsageDescription": "Baddy Agent needs to control system functions for voice commands",
        "NSMicrophoneUsageDescription": "Baddy Agent needs microphone access for voice commands",
        "NSSystemAdministrationUsageDescription": "Baddy Agent needs system access for monitoring and control"
    }
    
    with open(contents_path / "Info.plist", "wb") as f:
        plistlib.dump(info_plist, f)
        
    # Create launcher script with enhanced error handling
    launcher_script = """#!/bin/zsh

# Error handling
set -e
trap 'echo "Error: $?" >&2' ERR

# Set up environment
cd "$(dirname "$0")/../Resources"
source venv/bin/activate

# Start the tray app
python3 src/ai_agent/tray_app.py &
TRAY_PID=$!

# Wait for tray app to initialize
sleep 2

# Start the voice trigger
python3 src/ai_agent/baddy_agent.py &
VOICE_PID=$!

# Handle cleanup on exit
trap 'kill $TRAY_PID $VOICE_PID 2>/dev/null' EXIT

# Keep the script running
wait
"""
    
    with open(macos_path / "BaddyAgent", "w") as f:
        f.write(launcher_script)
    os.chmod(macos_path / "BaddyAgent", 0o755)
    
    # Create a simple icon (you can replace this with your own icon)
    icon_script = """
    #!/usr/bin/env python3
    from PIL import Image, ImageDraw
    import os
    
    # Create a 1024x1024 icon
    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a robot face
    # Head
    draw.ellipse([size/4, size/4, 3*size/4, 3*size/4], fill='#2C3E50')
    # Eyes
    draw.ellipse([size/3, size/3, size/2, size/2], fill='#3498DB')
    draw.ellipse([size/2, size/3, 2*size/3, size/2], fill='#3498DB')
    # Mouth
    draw.arc([size/3, size/2, 2*size/3, 3*size/4], 0, 180, fill='#E74C3C', width=20)
    
    # Save as PNG
    img.save('icon.png')
    """
    
    icon_path = resources_path / "icon.png"
    with open(resources_path / "create_icon.py", "w") as f:
        f.write(icon_script)
    
    # Create and convert icon
    subprocess.run([sys.executable, str(resources_path / "create_icon.py")], cwd=str(resources_path))
    subprocess.run([
        "iconutil", "-c", "icns", str(resources_path / "icon.png"),
        "-o", str(contents_path / "Resources" / "BaddyAgent.icns")
    ])
    
    # Copy necessary files to Resources
    resources_dir = resources_path
    resources_dir.mkdir(exist_ok=True)
    
    # Copy the entire project to Resources
    for item in base_dir.iterdir():
        if item.name != app_name:
            if item.is_file():
                shutil.copy2(item, resources_dir)
            else:
                shutil.copytree(item, resources_dir / item.name, dirs_exist_ok=True)
                
    # Create virtual environment in Resources
    subprocess.run([
        "python3", "-m", "venv", str(resources_dir / "venv")
    ], cwd=str(resources_dir))
    
    # Install requirements
    subprocess.run([
        str(resources_dir / "venv" / "bin" / "pip"),
        "install", "-r", str(resources_dir / "requirements.txt")
    ], cwd=str(resources_dir))
    
    # Clean up temporary files
    os.remove(resources_path / "create_icon.py")
    os.remove(resources_path / "icon.png")
    
    print(f"App bundle created at: {app_path}")
    return app_path

if __name__ == "__main__":
    create_app_bundle() 