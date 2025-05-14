"""
Vault Manager - Secure Storage System
Handles secure storage and retrieval of sensitive data.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class VaultManager:
    """Manages secure storage of sensitive data."""

    def __init__(self, vault_path: Optional[str] = None):
        """Initialize the vault manager."""
        self.vault_path = Path(vault_path or os.path.expanduser("~/.secondbrain/vault"))
        self.key_path = self.vault_path / ".key"
        self.fernet = None
        self._setup()

    def _setup(self) -> None:
        """Set up the vault and encryption."""
        try:
            # Create vault directory if it doesn't exist
            self.vault_path.mkdir(parents=True, exist_ok=True)

            # Generate or load encryption key
            if not self.key_path.exists():
                key = Fernet.generate_key()
                self.key_path.write_bytes(key)
            else:
                key = self.key_path.read_bytes()

            self.fernet = Fernet(key)
            logger.info("Vault initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vault: {e}")
            raise

    def store(self, key: str, data: Any) -> bool:
        """Store data securely in the vault."""
        try:
            # Convert data to JSON and encrypt
            json_data = json.dumps(data)
            encrypted_data = self.fernet.encrypt(json_data.encode())

            # Store encrypted data
            data_path = self.vault_path / f"{key}.enc"
            data_path.write_bytes(encrypted_data)
            return True
        except Exception as e:
            logger.error(f"Failed to store data: {e}")
            return False

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from the vault."""
        try:
            data_path = self.vault_path / f"{key}.enc"
            if not data_path.exists():
                return None

            # Read and decrypt data
            encrypted_data = data_path.read_bytes()
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to retrieve data: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete data from the vault."""
        try:
            data_path = self.vault_path / f"{key}.enc"
            if data_path.exists():
                data_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete data: {e}")
            return False

    def list_keys(self) -> list:
        """List all keys in the vault."""
        try:
            return [f.stem for f in self.vault_path.glob("*.enc")]
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            return []
