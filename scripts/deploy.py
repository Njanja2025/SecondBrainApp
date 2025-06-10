#!/usr/bin/env python3

import os
import sys
import json
import logging
import subprocess
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import requests
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deploy.log'),
        logging.StreamHandler()
    ]
)

class Deployer:
    def __init__(self, config_path='deploy_config.json'):
        self.config = self.load_config(config_path)
        self.setup_environment()

    def load_config(self, config_path):
        """Load deployment configuration."""
        default_config = {
            'source_path': '/Users/mac/Documents/Applications/BaddyAgent.app/Contents/Resources/SecondBrainApp',
            'target_paths': [
                '/Users/mac/Documents/Applications/BaddyAgent.app/Contents/Resources/SecondBrainApp'
            ],
            'backup_path': 'deploy_backups',
            'components': {
                'memory_engine': {
                    'files': [
                        'brain/memory_engine.py',
                        'brain/tests/test_memory_engine.py',
                        'brain/tests/test_memory_engine_advanced.py',
                        'brain/README.md'
                    ],
                    'dependencies': [
                        'requirements.txt',
                        'requirements-dev.txt'
                    ]
                }
            },
            'pre_deploy_checks': [
                'run_tests',
                'check_dependencies',
                'verify_permissions'
            ],
            'post_deploy_checks': [
                'verify_installation',
                'run_smoke_tests',
                'check_logs'
            ],
            'notifications': {
                'webhook': {
                    'enabled': False,
                    'url': '',
                    'headers': {}
                }
            }
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return {**default_config, **json.load(f)}
        return default_config

    def setup_environment(self):
        """Set up deployment environment."""
        os.makedirs(self.config['backup_path'], exist_ok=True)

    def run_tests(self):
        """Run test suite."""
        try:
            subprocess.run([
                'python', '-m', 'pytest',
                'brain/tests/test_memory_engine.py',
                'brain/tests/test_memory_engine_advanced.py',
                '-v'
            ], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Tests failed: {e}")
            return False

    def check_dependencies(self):
        """Check and install dependencies."""
        try:
            # Install requirements
            subprocess.run([
                'pip', 'install', '-r', 'requirements.txt'
            ], check=True)
            
            # Install dev requirements
            subprocess.run([
                'pip', 'install', '-r', 'requirements-dev.txt'
            ], check=True)
            
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Dependency installation failed: {e}")
            return False

    def verify_permissions(self):
        """Verify file permissions."""
        try:
            for target_path in self.config['target_paths']:
                if not os.access(target_path, os.W_OK):
                    logging.error(f"No write permission for {target_path}")
                    return False
            return True
        except Exception as e:
            logging.error(f"Permission check failed: {e}")
            return False

    def create_backup(self, target_path):
        """Create backup of target directory."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(
            self.config['backup_path'],
            f'backup_{timestamp}'
        )
        
        try:
            shutil.copytree(target_path, backup_dir)
            logging.info(f"Created backup at {backup_dir}")
            return True
        except Exception as e:
            logging.error(f"Backup failed: {e}")
            return False

    def deploy_files(self, target_path):
        """Deploy files to target directory."""
        try:
            # Create target directories
            for component in self.config['components'].values():
                for file_path in component['files']:
                    target_file = os.path.join(target_path, file_path)
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            # Copy files
            for component in self.config['components'].values():
                for file_path in component['files']:
                    source_file = os.path.join(self.config['source_path'], file_path)
                    target_file = os.path.join(target_path, file_path)
                    shutil.copy2(source_file, target_file)
                    logging.info(f"Deployed {file_path}")
            
            return True
        except Exception as e:
            logging.error(f"Deployment failed: {e}")
            return False

    def verify_installation(self, target_path):
        """Verify the installation."""
        try:
            # Check if files exist
            for component in self.config['components'].values():
                for file_path in component['files']:
                    target_file = os.path.join(target_path, file_path)
                    if not os.path.exists(target_file):
                        logging.error(f"Missing file: {target_file}")
                        return False
            
            # Run basic functionality test
            subprocess.run([
                'python', '-c',
                'from brain.memory_engine import initialize_memory_db; initialize_memory_db()'
            ], cwd=target_path, check=True)
            
            return True
        except Exception as e:
            logging.error(f"Verification failed: {e}")
            return False

    def run_smoke_tests(self, target_path):
        """Run smoke tests."""
        try:
            subprocess.run([
                'python', '-m', 'pytest',
                'brain/tests/test_memory_engine.py',
                '-v'
            ], cwd=target_path, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Smoke tests failed: {e}")
            return False

    def check_logs(self, target_path):
        """Check deployment logs."""
        try:
            log_file = os.path.join(target_path, 'deploy.log')
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = f.read()
                    if 'error' in logs.lower():
                        logging.error("Errors found in logs")
                        return False
            return True
        except Exception as e:
            logging.error(f"Log check failed: {e}")
            return False

    def send_notification(self, message, status):
        """Send deployment notification."""
        if self.config['notifications']['webhook']['enabled']:
            try:
                response = requests.post(
                    self.config['notifications']['webhook']['url'],
                    json={
                        'message': message,
                        'status': status,
                        'timestamp': datetime.now().isoformat()
                    },
                    headers=self.config['notifications']['webhook']['headers']
                )
                response.raise_for_status()
            except Exception as e:
                logging.error(f"Failed to send notification: {e}")

    def deploy(self):
        """Perform deployment."""
        logging.info("Starting deployment...")
        
        # Run pre-deploy checks
        for check in self.config['pre_deploy_checks']:
            if not getattr(self, check)():
                logging.error(f"Pre-deploy check failed: {check}")
                self.send_notification("Deployment failed: pre-deploy checks", "failed")
                return False
        
        # Deploy to each target
        for target_path in self.config['target_paths']:
            # Create backup
            if not self.create_backup(target_path):
                continue
            
            # Deploy files
            if not self.deploy_files(target_path):
                continue
            
            # Run post-deploy checks
            for check in self.config['post_deploy_checks']:
                if not getattr(self, check)(target_path):
                    logging.error(f"Post-deploy check failed: {check}")
                    self.send_notification("Deployment failed: post-deploy checks", "failed")
                    return False
        
        logging.info("Deployment completed successfully")
        self.send_notification("Deployment completed successfully", "success")
        return True

def main():
    parser = argparse.ArgumentParser(description='Memory Engine Deployer')
    parser.add_argument('--config', default='deploy_config.json',
                      help='Path to configuration file')
    args = parser.parse_args()
    
    deployer = Deployer(args.config)
    deployer.deploy()

if __name__ == "__main__":
    main() 