"""
Security management for SecondBrain
"""

import os
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurityManager:
    """Security manager for SecondBrain."""

    def __init__(self, key_file: str = "config/security.json"):
        """Initialize security manager."""
        self.key_file = key_file
        self.fernet: Optional[Fernet] = None
        self.key_data: Dict[str, Any] = {}
        self._load_or_generate_key()

    def _load_or_generate_key(self) -> None:
        """Load existing key or generate new one."""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, "r") as f:
                    self.key_data = json.load(f)

                # Check if key needs rotation
                if self._should_rotate_key():
                    self._rotate_key()
            else:
                self._generate_new_key()

            # Initialize Fernet with current key
            self.fernet = Fernet(self.key_data["key"].encode())

        except Exception as e:
            print(f"Error in key management: {e}")
            self._generate_new_key()

    def _generate_new_key(self) -> None:
        """Generate new encryption key."""
        key = Fernet.generate_key()
        self.key_data = {
            "key": key.decode(),
            "created_at": datetime.now().isoformat(),
            "rotation_count": 0,
        }
        self._save_key()

    def _rotate_key(self) -> None:
        """Rotate encryption key."""
        old_key = self.key_data["key"]
        self._generate_new_key()
        self.key_data["rotation_count"] += 1
        self._save_key()

    def _should_rotate_key(self) -> bool:
        """Check if key should be rotated."""
        created_at = datetime.fromisoformat(self.key_data["created_at"])
        rotation_days = 30  # Configurable
        return datetime.now() - created_at > timedelta(days=rotation_days)

    def _save_key(self) -> None:
        """Save key data to file."""
        try:
            os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
            with open(self.key_file, "w") as f:
                json.dump(self.key_data, f, indent=4)
        except Exception as e:
            print(f"Error saving key: {e}")

    def encrypt(self, data: str) -> str:
        """
        Encrypt data.

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data
        """
        if not self.fernet:
            raise RuntimeError("Encryption not initialized")
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data.

        Args:
            encrypted_data: Data to decrypt

        Returns:
            Decrypted data
        """
        if not self.fernet:
            raise RuntimeError("Encryption not initialized")
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def hash_password(
        self, password: str, salt: Optional[bytes] = None
    ) -> tuple[bytes, bytes]:
        """
        Hash password with salt.

        Args:
            password: Password to hash
            salt: Optional salt bytes

        Returns:
            Tuple of (salt, hashed_password)
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return salt, key

    def verify_password(self, password: str, salt: bytes, hashed: bytes) -> bool:
        """
        Verify password against hash.

        Args:
            password: Password to verify
            salt: Salt used in hashing
            hashed: Hashed password

        Returns:
            True if password matches hash
        """
        _, new_hash = self.hash_password(password, salt)
        return new_hash == hashed
