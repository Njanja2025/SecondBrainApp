"""
Cloud backup module for memory engine data.
"""

import logging
from pathlib import Path
from typing import Optional, Dict
import json
import boto3
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import dropbox
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class CloudBackupManager:
    """Manages cloud backups to multiple services."""

    def __init__(
        self,
        backup_config_file: str = "config/cloud_backup.json",
        backup_dir: str = "backups",
    ):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = Path(backup_config_file)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load cloud service configurations."""
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    return json.load(f)
            return {
                "dropbox": {"enabled": False},
                "google_drive": {"enabled": False},
                "aws": {"enabled": False},
                "namecheap": {"enabled": False},
            }
        except Exception as e:
            logger.error(f"Failed to load cloud config: {e}")
            return {}

    async def backup_to_dropbox(
        self, file_path: str, access_token: str, backup_path: Optional[str] = None
    ) -> bool:
        """
        Backup file to Dropbox.

        Args:
            file_path: Path to file to backup
            access_token: Dropbox access token
            backup_path: Optional custom path in Dropbox

        Returns:
            bool: True if backup successful
        """
        try:
            dbx = dropbox.Dropbox(access_token)

            # Generate backup path if not provided
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"/samantha/memory_backup_{timestamp}.json"

            # Upload file
            with open(file_path, "rb") as f:
                dbx.files_upload(
                    f.read(), backup_path, mode=dropbox.files.WriteMode.overwrite
                )

            logger.info(f"Successfully backed up to Dropbox: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to backup to Dropbox: {e}")
            return False

    async def backup_to_drive(
        self, file_path: str, credentials_json: str, folder_id: Optional[str] = None
    ) -> bool:
        """
        Backup file to Google Drive.

        Args:
            file_path: Path to file to backup
            credentials_json: Path to service account credentials
            folder_id: Optional Google Drive folder ID

        Returns:
            bool: True if backup successful
        """
        try:
            SCOPES = ["https://www.googleapis.com/auth/drive.file"]
            creds = service_account.Credentials.from_service_account_file(
                credentials_json, scopes=SCOPES
            )

            service = build("drive", "v3", credentials=creds)

            # Prepare file metadata
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_metadata = {
                "name": f"samantha_memory_backup_{timestamp}.json",
                "mimeType": "application/json",
            }

            # If folder specified, add to metadata
            if folder_id:
                file_metadata["parents"] = [folder_id]

            # Upload file
            media = MediaFileUpload(
                file_path, mimetype="application/json", resumable=True
            )

            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )

            logger.info(f"Successfully backed up to Google Drive: {file.get('id')}")
            return True

        except Exception as e:
            logger.error(f"Failed to backup to Google Drive: {e}")
            return False

    async def backup_to_s3(
        self,
        file_path: str,
        bucket: str,
        aws_access_key: str,
        aws_secret_key: str,
        region: str = "us-east-1",
        object_prefix: str = "samantha/memory",
    ) -> bool:
        """
        Backup file to AWS S3.

        Args:
            file_path: Path to file to backup
            bucket: S3 bucket name
            aws_access_key: AWS access key
            aws_secret_key: AWS secret key
            region: AWS region
            object_prefix: Prefix for S3 object key

        Returns:
            bool: True if backup successful
        """
        try:
            s3 = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=region,
            )

            # Generate object key with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_key = f"{object_prefix}/backup_{timestamp}.json"

            # Upload file
            with open(file_path, "rb") as f:
                s3.upload_fileobj(f, bucket, object_key)

            logger.info(f"Successfully backed up to S3: {bucket}/{object_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to backup to S3: {e}")
            return False

    async def update_namecheap_dns(
        self, api_user: str, api_key: str, domain: str, subdomain: str, ip_address: str
    ) -> bool:
        """
        Update Namecheap DNS records.

        Args:
            api_user: Namecheap API username
            api_key: Namecheap API key
            domain: Domain name
            subdomain: Subdomain to update
            ip_address: IP address to point to

        Returns:
            bool: True if update successful
        """
        try:
            # Split domain into SLD and TLD
            domain_parts = domain.split(".")
            if len(domain_parts) != 2:
                raise ValueError("Domain must be in format: example.com")

            sld, tld = domain_parts

            # Prepare API request
            url = "https://api.namecheap.com/xml.response"
            params = {
                "ApiUser": api_user,
                "ApiKey": api_key,
                "UserName": api_user,
                "Command": "namecheap.domains.dns.setHosts",
                "ClientIp": ip_address,
                "SLD": sld,
                "TLD": tld,
                "HostName1": subdomain,
                "RecordType1": "A",
                "Address1": ip_address,
                "TTL1": "1800",
            }

            # Make API request
            response = requests.get(url, params=params)

            if response.status_code == 200 and "<Status>OK</Status>" in response.text:
                logger.info(f"Successfully updated DNS for {subdomain}.{domain}")
                return True
            else:
                logger.error(f"Failed to update DNS: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to update Namecheap DNS: {e}")
            return False

    def save_config(self):
        """Save current configuration."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save cloud config: {e}")

    def update_config(self, service: str, config: Dict):
        """Update configuration for a specific service."""
        if service in self.config:
            self.config[service].update(config)
            self.save_config()
