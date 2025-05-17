import os
import sys
import argparse
from pathlib import Path
import dropbox
from dropbox.exceptions import AuthError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import yaml
import logging
from datetime import datetime

class CloudUploader:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_cloud_services()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("CloudUploader")
        
    def load_config(self):
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
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
            
    def upload_to_dropbox(self, file_path, version):
        """Upload file to Dropbox"""
        try:
            if not self.dropbox_client:
                self.logger.error("Dropbox client not initialized")
                return False
                
            file_name = Path(file_path).name
            dropbox_path = f"/BaddyAgent/v{version}/{file_name}"
            
            with open(file_path, 'rb') as f:
                self.dropbox_client.files_upload(
                    f.read(),
                    dropbox_path,
                    mode=dropbox.files.WriteMode.overwrite
                )
                
            self.logger.info(f"Uploaded {file_name} to Dropbox")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload to Dropbox: {e}")
            return False
            
    def upload_to_gdrive(self, file_path, version):
        """Upload file to Google Drive"""
        try:
            if not self.gdrive_service:
                self.logger.error("Google Drive service not initialized")
                return False
                
            file_name = Path(file_path).name
            file_metadata = {
                'name': file_name,
                'parents': [self.config.get('google_drive_folder_id', '')]
            }
            
            media = MediaFileUpload(
                file_path,
                mimetype='application/octet-stream',
                resumable=True
            )
            
            file = self.gdrive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            self.logger.info(f"Uploaded {file_name} to Google Drive")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload to Google Drive: {e}")
            return False
            
    def upload_files(self, dropbox_file=None, gdrive_file=None, version=None):
        """Upload files to cloud services"""
        if not version:
            version = self.config.get('version', '1.0.0')
            
        success = True
        
        if dropbox_file and self.config.get('dropbox_enabled'):
            if not self.upload_to_dropbox(dropbox_file, version):
                success = False
                
        if gdrive_file and self.config.get('google_drive_enabled'):
            if not self.upload_to_gdrive(gdrive_file, version):
                success = False
                
        return success

def main():
    parser = argparse.ArgumentParser(description='Upload Baddy Agent files to cloud services')
    parser.add_argument('--dropbox', help='File to upload to Dropbox')
    parser.add_argument('--gdrive', help='File to upload to Google Drive')
    parser.add_argument('--version', help='Version number for cloud organization')
    
    args = parser.parse_args()
    
    uploader = CloudUploader()
    success = uploader.upload_files(
        dropbox_file=args.dropbox,
        gdrive_file=args.gdrive,
        version=args.version
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 