"""
Data import/export utilities for SecondBrain application.
Handles data serialization, encryption, and format conversion.
"""

import os
import json
import csv
import logging
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from cryptography.fernet import Fernet
from ..security.encryption_utils import EncryptionUtils

logger = logging.getLogger(__name__)


class DataIO:
    """Handles data import and export operations."""

    def __init__(self, encryption_key_path: str = "config/encryption_key.key"):
        """Initialize the data I/O manager.

        Args:
            encryption_key_path: Path to the encryption key file
        """
        self.encryption = EncryptionUtils(encryption_key_path)
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging for the data I/O system."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def export_json(self, data: Any, path: str, encrypt: bool = False) -> bool:
        """Export data to a JSON file.

        Args:
            data: Data to export
            path: Path to save the file
            encrypt: Whether to encrypt the data

        Returns:
            bool: True if export was successful
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Convert data to JSON
            json_data = json.dumps(data, indent=2)

            if encrypt:
                # Encrypt the data
                json_data = self.encryption.encrypt(json_data)

            # Write to file
            with open(path, "w" if not encrypt else "wb") as f:
                f.write(json_data)

            logger.info(f"Exported data to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export JSON: {str(e)}")
            return False

    def import_json(self, path: str, encrypted: bool = False) -> Optional[Any]:
        """Import data from a JSON file.

        Args:
            path: Path to the file
            encrypted: Whether the data is encrypted

        Returns:
            Optional[Any]: Imported data if successful
        """
        try:
            if not os.path.exists(path):
                logger.error(f"File not found: {path}")
                return None

            # Read from file
            with open(path, "r" if not encrypted else "rb") as f:
                data = f.read()

            if encrypted:
                # Decrypt the data
                data = self.encryption.decrypt(data)

            # Parse JSON
            return json.loads(data)

        except Exception as e:
            logger.error(f"Failed to import JSON: {str(e)}")
            return None

    def export_csv(self, data: List[Dict], path: str, encrypt: bool = False) -> bool:
        """Export data to a CSV file.

        Args:
            data: List of dictionaries to export
            path: Path to save the file
            encrypt: Whether to encrypt the data

        Returns:
            bool: True if export was successful
        """
        try:
            if not data:
                logger.error("No data to export")
                return False

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Get field names
            fieldnames = data[0].keys()

            # Write to CSV
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            if encrypt:
                # Encrypt the file
                with open(path, "rb") as f:
                    data = f.read()

                encrypted_data = self.encryption.encrypt(data)

                with open(path, "wb") as f:
                    f.write(encrypted_data)

            logger.info(f"Exported data to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")
            return False

    def import_csv(self, path: str, encrypted: bool = False) -> Optional[List[Dict]]:
        """Import data from a CSV file.

        Args:
            path: Path to the file
            encrypted: Whether the data is encrypted

        Returns:
            Optional[List[Dict]]: Imported data if successful
        """
        try:
            if not os.path.exists(path):
                logger.error(f"File not found: {path}")
                return None

            if encrypted:
                # Decrypt the file
                with open(path, "rb") as f:
                    data = f.read()

                decrypted_data = self.encryption.decrypt(data)

                # Write decrypted data to temporary file
                temp_path = f"{path}.temp"
                with open(temp_path, "wb") as f:
                    f.write(decrypted_data)

                path = temp_path

            # Read CSV
            data = []
            with open(path, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(dict(row))

            if encrypted:
                # Clean up temporary file
                os.remove(path)

            return data

        except Exception as e:
            logger.error(f"Failed to import CSV: {str(e)}")
            return None

    def export_journal(
        self, data: Dict, path: str = "export/journal_backup.json"
    ) -> bool:
        """Export journal data.

        Args:
            data: Journal data to export
            path: Path to save the file

        Returns:
            bool: True if export was successful
        """
        try:
            # Add metadata
            export_data = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "data": data,
            }

            return self.export_json(export_data, path, encrypt=True)

        except Exception as e:
            logger.error(f"Failed to export journal: {str(e)}")
            return False

    def import_journal(self, path: str) -> Optional[Dict]:
        """Import journal data.

        Args:
            path: Path to the file

        Returns:
            Optional[Dict]: Imported journal data if successful
        """
        try:
            data = self.import_json(path, encrypted=True)

            if not data:
                return None

            # Verify version
            if data.get("version") != "1.0":
                logger.error(f"Unsupported journal version: {data.get('version')}")
                return None

            return data.get("data")

        except Exception as e:
            logger.error(f"Failed to import journal: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    data_io = DataIO()

    # Export journal data
    journal_data = {
        "entries": [
            {"date": "2025-01-01", "content": "Test entry 1"},
            {"date": "2025-01-02", "content": "Test entry 2"},
        ]
    }

    if data_io.export_journal(journal_data):
        print("Journal exported successfully")

    # Import journal data
    imported_data = data_io.import_journal("export/journal_backup.json")
    if imported_data:
        print("Journal imported successfully")
        print(f"Entries: {len(imported_data['entries'])}")
