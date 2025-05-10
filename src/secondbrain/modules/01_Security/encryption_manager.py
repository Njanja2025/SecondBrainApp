"""
Encryption manager for SecondBrain application.
Handles data encryption, decryption, and key management.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Manages encryption operations and key management."""
    
    def __init__(self, key_dir: str = "config/keys"):
        """Initialize the encryption manager.
        
        Args:
            key_dir: Directory to store encryption keys
        """
        self.key_dir = Path(key_dir)
        self.key_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._initialize_keys()
    
    def _setup_logging(self):
        """Set up logging for the encryption manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _initialize_keys(self):
        """Initialize encryption keys."""
        try:
            # Generate or load symmetric key
            self.symmetric_key_path = self.key_dir / "symmetric.key"
            if not self.symmetric_key_path.exists():
                self.symmetric_key = Fernet.generate_key()
                with open(self.symmetric_key_path, 'wb') as f:
                    f.write(self.symmetric_key)
            else:
                with open(self.symmetric_key_path, 'rb') as f:
                    self.symmetric_key = f.read()
            
            # Generate or load asymmetric key pair
            self.private_key_path = self.key_dir / "private.pem"
            self.public_key_path = self.key_dir / "public.pem"
            
            if not self.private_key_path.exists():
                # Generate new key pair
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048
                )
                
                # Save private key
                with open(self.private_key_path, 'wb') as f:
                    f.write(private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ))
                
                # Save public key
                public_key = private_key.public_key()
                with open(self.public_key_path, 'wb') as f:
                    f.write(public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ))
            
            logger.info("Encryption keys initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption keys: {str(e)}")
            raise
    
    def encrypt_symmetric(self, data: bytes) -> bytes:
        """Encrypt data using symmetric encryption.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        try:
            f = Fernet(self.symmetric_key)
            return f.encrypt(data)
        except Exception as e:
            logger.error(f"Failed to encrypt data: {str(e)}")
            raise
    
    def decrypt_symmetric(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using symmetric encryption.
        
        Args:
            encrypted_data: Data to decrypt
            
        Returns:
            Decrypted data
        """
        try:
            f = Fernet(self.symmetric_key)
            return f.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Failed to decrypt data: {str(e)}")
            raise
    
    def encrypt_asymmetric(self, data: bytes) -> bytes:
        """Encrypt data using asymmetric encryption.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        try:
            with open(self.public_key_path, 'rb') as f:
                public_key = serialization.load_pem_public_key(f.read())
            
            return public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        except Exception as e:
            logger.error(f"Failed to encrypt data: {str(e)}")
            raise
    
    def decrypt_asymmetric(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using asymmetric encryption.
        
        Args:
            encrypted_data: Data to decrypt
            
        Returns:
            Decrypted data
        """
        try:
            with open(self.private_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
            
            return private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        except Exception as e:
            logger.error(f"Failed to decrypt data: {str(e)}")
            raise
    
    def generate_key_derivation(self, password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """Generate a key from a password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Optional salt for key derivation
            
        Returns:
            Tuple of (derived key, salt)
        """
        try:
            if salt is None:
                salt = os.urandom(16)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            
            key = kdf.derive(password.encode())
            return key, salt
            
        except Exception as e:
            logger.error(f"Failed to derive key: {str(e)}")
            raise
    
    def rotate_keys(self):
        """Rotate encryption keys."""
        try:
            # Backup current keys
            backup_dir = self.key_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            for key_file in [self.symmetric_key_path, self.private_key_path, self.public_key_path]:
                if key_file.exists():
                    shutil.copy2(key_file, backup_dir / key_file.name)
            
            # Generate new keys
            self._initialize_keys()
            
            logger.info("Encryption keys rotated successfully")
            
        except Exception as e:
            logger.error(f"Failed to rotate keys: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    manager = EncryptionManager()
    
    # Test symmetric encryption
    test_data = b"Test data for encryption"
    encrypted = manager.encrypt_symmetric(test_data)
    decrypted = manager.decrypt_symmetric(encrypted)
    print("Symmetric encryption test:", test_data == decrypted)
    
    # Test asymmetric encryption
    encrypted = manager.encrypt_asymmetric(test_data)
    decrypted = manager.decrypt_asymmetric(encrypted)
    print("Asymmetric encryption test:", test_data == decrypted) 