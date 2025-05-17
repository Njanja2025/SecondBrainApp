import os
import json
import logging
from pathlib import Path
from datetime import datetime
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import dropbox
from dropbox.exceptions import AuthError
import io
import yaml
import psutil

class LogIntegration:
    def __init__(self, config_path=None):
        self.config_path = config_path or Path(__file__).parent / "config.yaml"
        self.load_config()
        self.setup_logging()
        self.setup_cloud_services()
        
    def load_config(self):
        """Load configuration from YAML file"""
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger("BaddyAgent")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(log_dir / "baddy_agent.log")
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
    def setup_cloud_services(self):
        """Initialize cloud service connections"""
        # Google Drive setup
        self.gdrive_service = None
        if self.config.get('google_drive_enabled'):
            self.setup_google_drive()
            
        # Dropbox setup
        self.dropbox_client = None
        if self.config.get('dropbox_enabled'):
            self.setup_dropbox()
            
    def setup_google_drive(self):
        """Setup Google Drive API connection"""
        try:
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            creds = None
            
            # Load credentials from token.json if it exists
            token_path = Path(__file__).parent / "token.json"
            if token_path.exists():
                creds = Credentials.from_authorized_user_info(
                    json.loads(token_path.read_text()), SCOPES)
                
            # If credentials are invalid or don't exist, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                    
                # Save credentials
                token_path.write_text(creds.to_json())
                
            self.gdrive_service = build('drive', 'v3', credentials=creds)
            self.logger.info("Google Drive connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Google Drive: {e}")
            
    def setup_dropbox(self):
        """Setup Dropbox API connection"""
        try:
            dbx = dropbox.Dropbox(self.config.get('dropbox_access_token'))
            dbx.users_get_current_account()
            self.dropbox_client = dbx
            self.logger.info("Dropbox connection established")
        except AuthError as e:
            self.logger.error(f"Failed to authenticate with Dropbox: {e}")
        except Exception as e:
            self.logger.error(f"Failed to setup Dropbox: {e}")
            
    def sync_to_cloud(self, log_file_path):
        """Sync log file to configured cloud services"""
        try:
            # Read log file
            with open(log_file_path, 'r') as f:
                log_content = f.read()
                
            # Generate summary
            summary = self.generate_summary(log_file_path)
            
            # Upload to Google Drive
            if self.gdrive_service:
                # Upload log file
                file_metadata = {
                    'name': f'baddy_agent_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                    'parents': [self.config.get('google_drive_folder_id', '')]
                }
                media = MediaIoBaseUpload(
                    io.BytesIO(log_content.encode()),
                    mimetype='text/plain',
                    resumable=True
                )
                file = self.gdrive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                self.logger.info(f"Log synced to Google Drive: {file.get('id')}")
                
                # Upload summary
                summary_metadata = {
                    'name': f'baddy_agent_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                    'parents': [self.config.get('google_drive_folder_id', '')]
                }
                summary_media = MediaIoBaseUpload(
                    io.BytesIO(json.dumps(summary, indent=2).encode()),
                    mimetype='application/json',
                    resumable=True
                )
                self.gdrive_service.files().create(
                    body=summary_metadata,
                    media_body=summary_media,
                    fields='id'
                ).execute()
                
            # Upload to Dropbox
            if self.dropbox_client:
                # Upload log file
                dropbox_path = f"/logs/baddy_agent_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                self.dropbox_client.files_upload(
                    log_content.encode(),
                    dropbox_path
                )
                self.logger.info(f"Log synced to Dropbox: {dropbox_path}")
                
                # Upload summary
                summary_path = f"/logs/baddy_agent_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.dropbox_client.files_upload(
                    json.dumps(summary, indent=2).encode(),
                    summary_path
                )
                
            # Send to Njanja.net
            if self.config.get('njanja_net_webhook'):
                response = requests.post(
                    self.config['njanja_net_webhook'],
                    json={
                        'log_content': log_content,
                        'summary': summary,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'BaddyAgent'
                    }
                )
                if response.status_code == 200:
                    self.logger.info("Log synced to Njanja.net")
                else:
                    self.logger.error(f"Failed to sync to Njanja.net: {response.text}")
                    
        except Exception as e:
            self.logger.error(f"Failed to sync logs: {e}")
            
    def generate_summary(self, log_file_path):
        """Generate a summary of the log file"""
        try:
            with open(log_file_path, 'r') as f:
                logs = f.readlines()
                
            # Count different types of entries
            error_count = sum(1 for log in logs if 'ERROR' in log)
            warning_count = sum(1 for log in logs if 'WARNING' in log)
            info_count = sum(1 for log in logs if 'INFO' in log)
            
            # Get last command
            last_command = next((log for log in reversed(logs) if 'Command executed' in log), 'None')
            
            # Get system stats
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            summary = {
                'total_entries': len(logs),
                'error_count': error_count,
                'warning_count': warning_count,
                'info_count': info_count,
                'last_command': last_command,
                'system_stats': {
                    'cpu_usage': f"{cpu_percent}%",
                    'memory_usage': f"{memory.percent}%",
                    'disk_usage': f"{disk.percent}%"
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate log summary: {e}")
            return None

if __name__ == "__main__":
    # Example usage
    log_integration = LogIntegration()
    log_file = Path(__file__).parent.parent.parent / "logs" / "baddy_agent.log"
    
    if log_file.exists():
        log_integration.sync_to_cloud(log_file)
        summary = log_integration.generate_summary(log_file)
        print(json.dumps(summary, indent=2)) 