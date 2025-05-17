import os
import subprocess
import shutil
from pathlib import Path
import plistlib
import json
from datetime import datetime

def create_dmg():
    """Create a DMG installer for Baddy Agent"""
    try:
        # Get the current directory
        current_dir = Path(__file__).parent.parent.parent
        app_path = current_dir / "BaddyAgent.app"
        dmg_path = current_dir / "BaddyAgent.dmg"
        
        # Create a temporary directory for DMG contents
        temp_dir = current_dir / "temp_dmg"
        temp_dir.mkdir(exist_ok=True)
        
        # Copy the app to temp directory
        shutil.copytree(app_path, temp_dir / "BaddyAgent.app", dirs_exist_ok=True)
        
        # Create a symbolic link to Applications
        os.symlink("/Applications", temp_dir / "Applications")
        
        # Create DMG
        subprocess.run([
            "hdiutil", "create",
            "-volname", "Baddy Agent Installer",
            "-srcfolder", str(temp_dir),
            "-ov",
            "-format", "UDZO",
            str(dmg_path)
        ], check=True)
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        print(f"DMG created successfully at: {dmg_path}")
        return str(dmg_path)
        
    except Exception as e:
        print(f"Error creating DMG: {e}")
        return None

if __name__ == "__main__":
    create_dmg() 