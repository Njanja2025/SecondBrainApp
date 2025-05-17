import os
import sys
import argparse
from pathlib import Path
import logging
import subprocess
import shutil
from datetime import datetime
import yaml
from github_release import GitHubRelease
from cloud_upload import CloudUploader

class ReleaseManager:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_components()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("ReleaseManager")
        
    def load_config(self):
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
    def setup_components(self):
        """Setup release components"""
        self.github = GitHubRelease()
        self.cloud = CloudUploader()
        
    def create_dmg(self, app_path, output_path):
        """Create a DMG installer for the app"""
        try:
            # Create temporary directory for DMG contents
            temp_dir = Path("temp_dmg")
            temp_dir.mkdir(exist_ok=True)
            
            # Copy app to temp directory
            shutil.copytree(app_path, temp_dir / "BaddyAgent.app")
            
            # Create DMG
            subprocess.run([
                'create-dmg',
                '--volname', 'BaddyAgent',
                '--volicon', 'assets/icon.icns',
                '--window-pos', '200', '120',
                '--window-size', '800', '400',
                '--icon-size', '100',
                '--icon', 'BaddyAgent.app', '200', '190',
                '--hide-extension', 'BaddyAgent.app',
                '--app-drop-link', '600', '185',
                str(output_path),
                str(temp_dir)
            ], check=True)
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            self.logger.info(f"Created DMG at {output_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create DMG: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to create DMG: {e}")
            return False
            
    def create_zip(self, app_path, output_path):
        """Create a ZIP archive of the app"""
        try:
            shutil.make_archive(
                str(output_path.with_suffix('')),
                'zip',
                app_path.parent,
                app_path.name
            )
            self.logger.info(f"Created ZIP at {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create ZIP: {e}")
            return False
            
    def release(self, version, app_path, release_notes_path):
        """Perform a complete release"""
        try:
            # Create release artifacts
            dmg_path = Path(f"BaddyAgent-v{version}.dmg")
            zip_path = Path(f"BaddyAgent-v{version}.zip")
            
            if not self.create_dmg(app_path, dmg_path):
                return False
                
            if not self.create_zip(app_path, zip_path):
                return False
                
            # Create GitHub release
            with open(release_notes_path, 'r') as f:
                release_notes = f.read()
                
            if not self.github.create_release_with_assets(
                version,
                release_notes,
                [dmg_path, zip_path]
            ):
                return False
                
            # Upload to cloud services
            if not self.cloud.upload_files(
                dropbox_file=dmg_path,
                gdrive_file=dmg_path,
                version=version
            ):
                return False
                
            self.logger.info("Release completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Release failed: {e}")
            return False
        finally:
            # Cleanup
            for path in [dmg_path, zip_path]:
                if path.exists():
                    path.unlink()

def main():
    parser = argparse.ArgumentParser(description='Create a BaddyAgent release')
    parser.add_argument('--version', required=True, help='Version number')
    parser.add_argument('--app', required=True, help='Path to BaddyAgent.app')
    parser.add_argument('--notes', required=True, help='Path to release notes file')
    
    args = parser.parse_args()
    
    manager = ReleaseManager()
    success = manager.release(
        args.version,
        Path(args.app),
        Path(args.notes)
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 