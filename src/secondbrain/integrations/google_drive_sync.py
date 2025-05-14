"""
Google Drive integration for SecondBrain application.
Handles file synchronization, backup, and restore operations.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError

logger = logging.getLogger(__name__)


class GoogleDriveSync:
    """Handles Google Drive synchronization."""

    SCOPES = ["https://www.googleapis.com/auth/drive.file"]
    CREDENTIALS_FILE = "credentials.json"
    TOKEN_FILE = "token.json"
    APP_FOLDER = "SecondBrainApp"

    def __init__(self, app_name: str):
        """Initialize the Google Drive sync manager.

        Args:
            app_name: Name of the application
        """
        self.app_name = app_name
        self.service = None
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging for the sync system."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def authenticate(self) -> bool:
        """Authenticate with Google Drive.

        Returns:
            bool: True if authentication was successful
        """
        try:
            creds = None

            # Load existing credentials
            if os.path.exists(self.TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(
                    self.TOKEN_FILE, self.SCOPES
                )

            # Refresh credentials if expired
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    creds = None

            # Get new credentials if needed
            if not creds:
                if not os.path.exists(self.CREDENTIALS_FILE):
                    logger.error(f"Credentials file not found: {self.CREDENTIALS_FILE}")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

                # Save credentials
                with open(self.TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())

            # Build service
            self.service = build("drive", "v3", credentials=creds)
            logger.info("Successfully authenticated with Google Drive")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def _get_app_folder_id(self) -> Optional[str]:
        """Get the ID of the application folder in Google Drive.

        Returns:
            Optional[str]: Folder ID if found, None otherwise
        """
        try:
            if not self.service:
                return None

            # Search for the app folder
            results = (
                self.service.files()
                .list(
                    q=f"name='{self.APP_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                    spaces="drive",
                    fields="files(id, name)",
                )
                .execute()
            )

            items = results.get("files", [])

            if items:
                return items[0]["id"]

            # Create folder if it doesn't exist
            folder_metadata = {
                "name": self.APP_FOLDER,
                "mimeType": "application/vnd.google-apps.folder",
            }

            folder = (
                self.service.files().create(body=folder_metadata, fields="id").execute()
            )

            return folder.get("id")

        except Exception as e:
            logger.error(f"Failed to get app folder: {str(e)}")
            return None

    def upload_file(self, file_path: str, file_name: Optional[str] = None) -> bool:
        """Upload a file to Google Drive.

        Args:
            file_path: Path to the file to upload
            file_name: Optional name for the file in Drive

        Returns:
            bool: True if upload was successful
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return False

            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False

            file_name = file_name or file_path.name
            folder_id = self._get_app_folder_id()

            if not folder_id:
                logger.error("Failed to get app folder ID")
                return False

            # Create file metadata
            file_metadata = {"name": file_name, "parents": [folder_id]}

            # Upload file
            media = MediaFileUpload(str(file_path), resumable=True)

            file = (
                self.service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )

            logger.info(f"Uploaded {file_name} to Google Drive")
            return True

        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            return False

    def download_file(self, file_name: str, target_path: str) -> bool:
        """Download a file from Google Drive.

        Args:
            file_name: Name of the file in Drive
            target_path: Path to save the file

        Returns:
            bool: True if download was successful
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return False

            folder_id = self._get_app_folder_id()

            if not folder_id:
                logger.error("Failed to get app folder ID")
                return False

            # Search for the file
            results = (
                self.service.files()
                .list(
                    q=f"name='{file_name}' and '{folder_id}' in parents and trashed=false",
                    spaces="drive",
                    fields="files(id, name)",
                )
                .execute()
            )

            items = results.get("files", [])

            if not items:
                logger.error(f"File not found in Drive: {file_name}")
                return False

            file_id = items[0]["id"]

            # Download file
            request = self.service.files().get_media(fileId=file_id)

            with open(target_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

            logger.info(f"Downloaded {file_name} from Google Drive")
            return True

        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
            return False

    def list_files(self) -> List[Dict]:
        """List files in the app folder.

        Returns:
            List[Dict]: List of file information
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return []

            folder_id = self._get_app_folder_id()

            if not folder_id:
                logger.error("Failed to get app folder ID")
                return []

            # List files
            results = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    spaces="drive",
                    fields="files(id, name, createdTime, size)",
                )
                .execute()
            )

            return results.get("files", [])

        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []

    def delete_file(self, file_name: str) -> bool:
        """Delete a file from Google Drive.

        Args:
            file_name: Name of the file to delete

        Returns:
            bool: True if deletion was successful
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return False

            folder_id = self._get_app_folder_id()

            if not folder_id:
                logger.error("Failed to get app folder ID")
                return False

            # Search for the file
            results = (
                self.service.files()
                .list(
                    q=f"name='{file_name}' and '{folder_id}' in parents and trashed=false",
                    spaces="drive",
                    fields="files(id, name)",
                )
                .execute()
            )

            items = results.get("files", [])

            if not items:
                logger.error(f"File not found in Drive: {file_name}")
                return False

            file_id = items[0]["id"]

            # Delete file
            self.service.files().delete(fileId=file_id).execute()

            logger.info(f"Deleted {file_name} from Google Drive")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    sync = GoogleDriveSync("SecondBrainApp2025")

    # Authenticate
    if sync.authenticate():
        # List files
        files = sync.list_files()
        print("\nFiles in Google Drive:")
        for file in files:
            print(f"- {file['name']} ({file['size']} bytes)")

        # Upload a file
        if sync.upload_file("backup.zip", "SecondBrainApp_Backup.zip"):
            print("Backup uploaded successfully")

        # Download a file
        if sync.download_file("SecondBrainApp_Backup.zip", "restored_backup.zip"):
            print("Backup downloaded successfully")
