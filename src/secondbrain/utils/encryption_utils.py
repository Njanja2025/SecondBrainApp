"""
Encryption utilities for SecondBrain application.
Provides secure encryption and decryption functionality using Fernet symmetric encryption.
"""

import os
from pathlib import Path
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.exceptions import InvalidToken


class EncryptionError(Exception):
    """Custom exception for encryption-related errors."""

    pass


class EncryptionUtils:
    def __init__(self, key_path: Optional[str] = None):
        """
        Initialize encryption utilities.

        Args:
            key_path: Optional path to store the encryption key. If not provided,
                     will use a default location in the config directory.
        """
        self.key_path = key_path or str(Path("config/encryption.key"))
        self._ensure_key_exists()
        self.fernet = Fernet(self._load_key())

    def _ensure_key_exists(self) -> None:
        """Ensure encryption key exists, generate if it doesn't."""
        if not os.path.exists(self.key_path):
            os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as key_file:
                key_file.write(key)

    def _load_key(self) -> bytes:
        """Load encryption key from file."""
        try:
            with open(self.key_path, "rb") as key_file:
                return key_file.read()
        except Exception as e:
            raise EncryptionError(f"Failed to load encryption key: {str(e)}")

    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        Encrypt data using Fernet symmetric encryption.

        Args:
            data: String or bytes to encrypt

        Returns:
            Encrypted data as a string

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            if isinstance(data, str):
                data = data.encode()
            encrypted_data = self.fernet.encrypt(data)
            return encrypted_data.decode()
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted_data: Union[str, bytes]) -> str:
        """
        Decrypt data using Fernet symmetric encryption.

        Args:
            encrypted_data: Encrypted string or bytes to decrypt

        Returns:
            Decrypted data as a string

        Raises:
            EncryptionError: If decryption fails
            InvalidToken: If the encrypted data is invalid or corrupted
        """
        try:
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode()
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return decrypted_data.decode()
        except InvalidToken:
            raise EncryptionError("Invalid or corrupted encrypted data")
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Initialize encryption utilities
    enc_utils = EncryptionUtils()

    # Example data
    sample_data = "This is a confidential journal backup entry."

    # Encrypt
    encrypted = enc_utils.encrypt(sample_data)
    print(f"Encrypted: {encrypted}")

    # Decrypt
    decrypted = enc_utils.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")

    # Verify
    assert decrypted == sample_data, "Encryption/decryption verification failed"
