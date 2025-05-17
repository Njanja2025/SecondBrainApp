import os
import sys
import plistlib
from pathlib import Path
import logging
import subprocess
import shutil

class AutoLaunchManager:
    def __init__(self):
        self.setup_logging()
        self.app_name = "BaddyAgent"
        self.launch_agent_name = f"com.{self.app_name.lower()}.launcher"
        self.launch_agent_dir = Path.home() / "Library/LaunchAgents"
        self.app_path = self._get_app_path()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("AutoLaunchManager")
        
    def _get_app_path(self):
        """Get the path to the BaddyAgent.app bundle"""
        # First check if we're running from the app bundle
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent.parent
        else:
            # Look for the app in common locations
            possible_locations = [
                Path("/Applications") / f"{self.app_name}.app",
                Path.home() / "Applications" / f"{self.app_name}.app"
            ]
            for location in possible_locations:
                if location.exists():
                    return location
        return None
        
    def create_launch_agent(self):
        """Create a LaunchAgent plist file for auto-starting the app"""
        try:
            if not self.app_path:
                self.logger.error("Could not find BaddyAgent.app")
                return False
                
            # Create LaunchAgents directory if it doesn't exist
            self.launch_agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Create the plist content
            plist_content = {
                'Label': self.launch_agent_name,
                'ProgramArguments': [
                    str(self.app_path / "Contents/MacOS/BaddyAgent")
                ],
                'RunAtLoad': True,
                'KeepAlive': True,
                'StandardErrorPath': str(Path.home() / f"Library/Logs/{self.app_name}/launch_agent.err"),
                'StandardOutPath': str(Path.home() / f"Library/Logs/{self.app_name}/launch_agent.out")
            }
            
            # Write the plist file
            plist_path = self.launch_agent_dir / f"{self.launch_agent_name}.plist"
            with open(plist_path, 'wb') as f:
                plistlib.dump(plist_content, f)
                
            # Set proper permissions
            os.chmod(plist_path, 0o644)
            
            self.logger.info(f"Created LaunchAgent at {plist_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create LaunchAgent: {e}")
            return False
            
    def remove_launch_agent(self):
        """Remove the LaunchAgent plist file"""
        try:
            plist_path = self.launch_agent_dir / f"{self.launch_agent_name}.plist"
            if plist_path.exists():
                plist_path.unlink()
                self.logger.info(f"Removed LaunchAgent at {plist_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove LaunchAgent: {e}")
            return False
            
    def load_launch_agent(self):
        """Load the LaunchAgent into launchd"""
        try:
            subprocess.run([
                'launchctl',
                'load',
                str(self.launch_agent_dir / f"{self.launch_agent_name}.plist")
            ], check=True)
            self.logger.info("Loaded LaunchAgent into launchd")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to load LaunchAgent: {e}")
            return False
            
    def unload_launch_agent(self):
        """Unload the LaunchAgent from launchd"""
        try:
            subprocess.run([
                'launchctl',
                'unload',
                str(self.launch_agent_dir / f"{self.launch_agent_name}.plist")
            ], check=True)
            self.logger.info("Unloaded LaunchAgent from launchd")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to unload LaunchAgent: {e}")
            return False
            
    def setup_auto_launch(self):
        """Setup auto-launch functionality"""
        if self.create_launch_agent():
            return self.load_launch_agent()
        return False
        
    def disable_auto_launch(self):
        """Disable auto-launch functionality"""
        if self.unload_launch_agent():
            return self.remove_launch_agent()
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Manage BaddyAgent auto-launch functionality')
    parser.add_argument('--enable', action='store_true', help='Enable auto-launch')
    parser.add_argument('--disable', action='store_true', help='Disable auto-launch')
    
    args = parser.parse_args()
    
    manager = AutoLaunchManager()
    
    if args.enable:
        success = manager.setup_auto_launch()
    elif args.disable:
        success = manager.disable_auto_launch()
    else:
        parser.print_help()
        sys.exit(1)
        
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 