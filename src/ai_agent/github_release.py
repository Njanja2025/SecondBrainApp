import os
import sys
import argparse
from pathlib import Path
import logging
import requests
import json
from datetime import datetime
import yaml

class GitHubRelease:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_github()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("GitHubRelease")
        
    def load_config(self):
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
    def setup_github(self):
        """Setup GitHub API connection"""
        self.github_token = self.config.get('github_token')
        if not self.github_token:
            self.logger.error("GitHub token not found in config")
            sys.exit(1)
            
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        self.owner = self.config.get('github_owner')
        self.repo = self.config.get('github_repo')
        if not self.owner or not self.repo:
            self.logger.error("GitHub owner or repo not found in config")
            sys.exit(1)
            
    def create_release(self, version, release_notes):
        """Create a new GitHub release"""
        try:
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases"
            data = {
                'tag_name': f"v{version}",
                'name': f"BaddyAgent v{version}",
                'body': release_notes,
                'draft': False,
                'prerelease': False
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            release_data = response.json()
            self.logger.info(f"Created release: {release_data['name']}")
            return release_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create release: {e}")
            return None
            
    def upload_asset(self, release_id, file_path):
        """Upload an asset to a GitHub release"""
        try:
            file_name = Path(file_path).name
            url = f"https://uploads.github.com/repos/{self.owner}/{self.repo}/releases/{release_id}/assets?name={file_name}"
            
            with open(file_path, 'rb') as f:
                response = requests.post(
                    url,
                    headers={
                        **self.headers,
                        'Content-Type': 'application/octet-stream'
                    },
                    data=f
                )
                response.raise_for_status()
                
            asset_data = response.json()
            self.logger.info(f"Uploaded asset: {asset_data['name']}")
            return asset_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to upload asset: {e}")
            return None
            
    def create_release_with_assets(self, version, release_notes, assets):
        """Create a release and upload assets"""
        release = self.create_release(version, release_notes)
        if not release:
            return False
            
        success = True
        for asset_path in assets:
            if not self.upload_asset(release['id'], asset_path):
                success = False
                
        return success

def main():
    parser = argparse.ArgumentParser(description='Create GitHub release with assets')
    parser.add_argument('--version', required=True, help='Version number')
    parser.add_argument('--notes', required=True, help='Release notes file')
    parser.add_argument('--assets', nargs='+', required=True, help='Asset files to upload')
    
    args = parser.parse_args()
    
    # Read release notes
    with open(args.notes, 'r') as f:
        release_notes = f.read()
        
    # Create release
    release = GitHubRelease()
    success = release.create_release_with_assets(
        args.version,
        release_notes,
        args.assets
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 