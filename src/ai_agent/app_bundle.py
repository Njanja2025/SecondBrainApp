import os
import sys
import shutil
from pathlib import Path
import plistlib
import subprocess

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
        
    # Create Info.plist
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
    }
    
    with open(contents_path / "Info.plist", "wb") as f:
        plistlib.dump(info_plist, f)
        
    # Create launcher script
    launcher_script = """#!/bin/zsh
cd "$(dirname "$0")/../Resources"
source venv/bin/activate
python3 src/ai_agent/tray_app.py &
sleep 2
python3 src/ai_agent/baddy_agent.py
"""
    
    with open(macos_path / "BaddyAgent", "w") as f:
        f.write(launcher_script)
    os.chmod(macos_path / "BaddyAgent", 0o755)
    
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
    
    print(f"App bundle created at: {app_path}")
    return app_path

if __name__ == "__main__":
    create_app_bundle() 