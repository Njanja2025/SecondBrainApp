"""
Enhanced cloud synchronization module for Samantha's memory and logs.
"""
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional, List, Union
import json
import dropbox
import boto3
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from datetime import datetime

logger = logging.getLogger(__name__)

class CloudSync:
    """Manages cloud synchronization across multiple services."""
    
    def __init__(
        self,
        config_path: str = "config/cloud_sync.json",
        backup_dir: str = "backups"
    ):
        self.config_path = Path(config_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize service clients
        self._dropbox_client = None
        self._drive_service = None
        self._s3_client = None
        
    def _load_config(self) -> Dict:
        """Load cloud service configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    return json.load(f)
            return {
                "dropbox": {
                    "enabled": False,
                    "backup_frequency": "daily",
                    "retention_days": 30
                },
                "google_drive": {
                    "enabled": False,
                    "backup_frequency": "weekly",
                    "retention_days": 90
                },
                "aws": {
                    "enabled": False,
                    "backup_frequency": "daily",
                    "retention_days": 60
                }
            }
        except Exception as e:
            logger.error(f"Failed to load cloud config: {e}")
            return {}
            
    async def upload_to_dropbox(
        self,
        file_path: Union[str, Path],
        access_token: str,
        backup_path: Optional[str] = None,
        retain_versions: bool = True
    ) -> bool:
        """
        Upload file to Dropbox with versioning support.
        
        Args:
            file_path: Path to file to upload
            access_token: Dropbox access token
            backup_path: Optional custom path in Dropbox
            retain_versions: Whether to keep file versions
            
        Returns:
            bool: True if upload successful
        """
        try:
            if not self._dropbox_client:
                self._dropbox_client = dropbox.Dropbox(access_token)
                
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Generate backup path if not provided
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
                backup_path = f"/samantha/backups/{filename}"
                
            # Upload file
            mode = (
                dropbox.files.WriteMode.add
                if retain_versions
                else dropbox.files.WriteMode.overwrite
            )
            
            with open(file_path, "rb") as f:
                self._dropbox_client.files_upload(
                    f.read(),
                    backup_path,
                    mode=mode,
                    mute=True
                )
                
            logger.info(f"Successfully uploaded to Dropbox: {backup_path}")
            
            # Clean up old versions if needed
            if retain_versions:
                await self._cleanup_dropbox_versions(
                    Path(backup_path).parent,
                    self.config["dropbox"]["retention_days"]
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload to Dropbox: {e}")
            return False
            
    async def upload_to_drive(
        self,
        file_path: Union[str, Path],
        credentials_json: str,
        folder_id: Optional[str] = None,
        retain_versions: bool = True
    ) -> bool:
        """
        Upload file to Google Drive with versioning support.
        
        Args:
            file_path: Path to file to upload
            credentials_json: Path to service account credentials
            folder_id: Optional Google Drive folder ID
            retain_versions: Whether to keep file versions
            
        Returns:
            bool: True if upload successful
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
                
            if not self._drive_service:
                SCOPES = ['https://www.googleapis.com/auth/drive.file']
                creds = service_account.Credentials.from_service_account_file(
                    credentials_json,
                    scopes=SCOPES
                )
                self._drive_service = build('drive', 'v3', credentials=creds)
                
            # Prepare file metadata
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_metadata = {
                'name': f"{file_path.stem}_{timestamp}{file_path.suffix}",
                'mimeType': 'application/json'
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
                
            # Upload file
            media = MediaFileUpload(
                str(file_path),
                mimetype='application/json',
                resumable=True
            )
            
            file = self._drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            logger.info(f"Successfully uploaded to Google Drive: {file.get('id')}")
            
            # Clean up old versions if needed
            if retain_versions and folder_id:
                await self._cleanup_drive_versions(
                    folder_id,
                    self.config["google_drive"]["retention_days"]
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload to Google Drive: {e}")
            return False
            
    async def upload_to_s3(
        self,
        file_path: Union[str, Path],
        bucket: str,
        aws_access_key: str,
        aws_secret_key: str,
        region: str = "us-east-1",
        prefix: str = "samantha/backups",
        retain_versions: bool = True
    ) -> bool:
        """
        Upload file to AWS S3 with versioning support.
        
        Args:
            file_path: Path to file to upload
            bucket: S3 bucket name
            aws_access_key: AWS access key
            aws_secret_key: AWS secret key
            region: AWS region
            prefix: S3 key prefix
            retain_versions: Whether to enable versioning
            
        Returns:
            bool: True if upload successful
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
                
            if not self._s3_client:
                self._s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=region
                )
                
            # Generate object key
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_key = (
                f"{prefix}/{file_path.stem}_{timestamp}{file_path.suffix}"
                if retain_versions
                else f"{prefix}/{file_path.name}"
            )
            
            # Upload file
            with open(file_path, "rb") as f:
                self._s3_client.upload_fileobj(f, bucket, object_key)
                
            logger.info(f"Successfully uploaded to S3: {bucket}/{object_key}")
            
            # Enable bucket versioning if needed
            if retain_versions:
                self._s3_client.put_bucket_versioning(
                    Bucket=bucket,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                
                # Clean up old versions
                await self._cleanup_s3_versions(
                    bucket,
                    prefix,
                    self.config["aws"]["retention_days"]
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            return False
            
    async def _cleanup_dropbox_versions(
        self,
        folder_path: str,
        retention_days: int
    ):
        """Clean up old Dropbox file versions."""
        try:
            if not self._dropbox_client:
                return
                
            cutoff = datetime.now().timestamp() - (retention_days * 86400)
            
            # List folder contents
            result = self._dropbox_client.files_list_folder(folder_path)
            
            # Delete old files
            for entry in result.entries:
                if (
                    isinstance(entry, dropbox.files.FileMetadata)
                    and entry.server_modified.timestamp() < cutoff
                ):
                    self._dropbox_client.files_delete_v2(entry.path_lower)
                    
        except Exception as e:
            logger.error(f"Failed to cleanup Dropbox versions: {e}")
            
    async def _cleanup_drive_versions(
        self,
        folder_id: str,
        retention_days: int
    ):
        """Clean up old Google Drive file versions."""
        try:
            if not self._drive_service:
                return
                
            cutoff = datetime.now().timestamp() - (retention_days * 86400)
            
            # List folder contents
            results = self._drive_service.files().list(
                q=f"'{folder_id}' in parents",
                fields="files(id, name, createdTime)"
            ).execute()
            
            # Delete old files
            for file in results.get('files', []):
                created_time = datetime.fromisoformat(
                    file['createdTime'].replace('Z', '+00:00')
                )
                if created_time.timestamp() < cutoff:
                    self._drive_service.files().delete(
                        fileId=file['id']
                    ).execute()
                    
        except Exception as e:
            logger.error(f"Failed to cleanup Drive versions: {e}")
            
    async def _cleanup_s3_versions(
        self,
        bucket: str,
        prefix: str,
        retention_days: int
    ):
        """Clean up old S3 object versions."""
        try:
            if not self._s3_client:
                return
                
            cutoff = datetime.now().timestamp() - (retention_days * 86400)
            
            # List object versions
            paginator = self._s3_client.get_paginator('list_object_versions')
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                # Delete old versions
                delete_keys = []
                
                for version in page.get('Versions', []):
                    if version['LastModified'].timestamp() < cutoff:
                        delete_keys.append({
                            'Key': version['Key'],
                            'VersionId': version['VersionId']
                        })
                        
                if delete_keys:
                    self._s3_client.delete_objects(
                        Bucket=bucket,
                        Delete={'Objects': delete_keys}
                    )
                    
        except Exception as e:
            logger.error(f"Failed to cleanup S3 versions: {e}")
            
    def save_config(self):
        """Save current configuration."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            
    def update_config(self, service: str, config: Dict):
        """Update configuration for a specific service."""
        if service in self.config:
            self.config[service].update(config)
            self.save_config() 