"""
Data encryption module for secure data handling.
"""
import os
import base64
import logging
from typing import Optional, Tuple, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)

class DataEncryption:
    def __init__(self, key_path: Optional[str] = None):
        """Initialize encryption system with optional key path."""
        self.key_path = key_path or os.path.expanduser('~/.secondbrain/keys')
        os.makedirs(self.key_path, exist_ok=True)
        
        self._symmetric_key = None
        self._asymmetric_keys = None
        self._fernet = None
        
    def generate_symmetric_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Generate a symmetric encryption key from password."""
        salt = salt or os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self._symmetric_key = key
        self._fernet = Fernet(key)
        return salt
        
    def generate_asymmetric_keys(self) -> Tuple[bytes, bytes]:
        """Generate asymmetric key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        self._asymmetric_keys = (private_key, public_key)
        return private_pem, public_pem
        
    def save_keys(self, identifier: str):
        """Save current keys to storage."""
        try:
            if self._symmetric_key:
                path = os.path.join(self.key_path, f"{identifier}_symmetric.key")
                with open(path, 'wb') as f:
                    f.write(self._symmetric_key)
                    
            if self._asymmetric_keys:
                private_path = os.path.join(self.key_path, f"{identifier}_private.pem")
                public_path = os.path.join(self.key_path, f"{identifier}_public.pem")
                
                private_pem = self._asymmetric_keys[0].private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                public_pem = self._asymmetric_keys[1].public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                
                with open(private_path, 'wb') as f:
                    f.write(private_pem)
                with open(public_path, 'wb') as f:
                    f.write(public_pem)
                    
        except Exception as e:
            logger.error(f"Failed to save keys: {str(e)}")
            raise
            
    def load_keys(self, identifier: str):
        """Load keys from storage."""
        try:
            # Load symmetric key
            sym_path = os.path.join(self.key_path, f"{identifier}_symmetric.key")
            if os.path.exists(sym_path):
                with open(sym_path, 'rb') as f:
                    self._symmetric_key = f.read()
                    self._fernet = Fernet(self._symmetric_key)
                    
            # Load asymmetric keys
            private_path = os.path.join(self.key_path, f"{identifier}_private.pem")
            public_path = os.path.join(self.key_path, f"{identifier}_public.pem")
            
            if os.path.exists(private_path) and os.path.exists(public_path):
                with open(private_path, 'rb') as f:
                    private_pem = f.read()
                with open(public_path, 'rb') as f:
                    public_pem = f.read()
                    
                private_key = serialization.load_pem_private_key(
                    private_pem,
                    password=None
                )
                public_key = serialization.load_pem_public_key(public_pem)
                
                self._asymmetric_keys = (private_key, public_key)
                
        except Exception as e:
            logger.error(f"Failed to load keys: {str(e)}")
            raise
            
    def encrypt_symmetric(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data using symmetric encryption."""
        if not self._fernet:
            raise ValueError("Symmetric key not initialized")
            
        if isinstance(data, str):
            data = data.encode()
            
        return self._fernet.encrypt(data)
        
    def decrypt_symmetric(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using symmetric encryption."""
        if not self._fernet:
            raise ValueError("Symmetric key not initialized")
            
        return self._fernet.decrypt(encrypted_data)
        
    def encrypt_asymmetric(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data using asymmetric encryption."""
        if not self._asymmetric_keys:
            raise ValueError("Asymmetric keys not initialized")
            
        if isinstance(data, str):
            data = data.encode()
            
        return self._asymmetric_keys[1].encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
    def decrypt_asymmetric(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using asymmetric encryption."""
        if not self._asymmetric_keys:
            raise ValueError("Asymmetric keys not initialized")
            
        return self._asymmetric_keys[0].decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
    def clear_keys(self):
        """Clear all loaded keys from memory."""
        self._symmetric_key = None
        self._asymmetric_keys = None
        self._fernet = None 