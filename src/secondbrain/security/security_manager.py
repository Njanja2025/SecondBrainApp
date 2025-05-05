"""
Enhanced security management system.
"""
import os
import json
import logging
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization

from ..phantom.phantom_core import PhantomCore
from .security_scanner import SecurityScanner

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self, phantom: PhantomCore):
        """Initialize security manager."""
        self.phantom = phantom
        self.scanner = SecurityScanner(phantom)
        self.security_log_path = Path("logs/security")
        self.security_log_path.mkdir(parents=True, exist_ok=True)
        
        # Load security config
        self.config = self._load_security_config()
        
        # Initialize encryption
        self._init_encryption()
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration."""
        try:
            with open("config/security_config.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default config
            config = {
                "encryption": {
                    "enabled": True,
                    "key_rotation_days": 30,
                    "algorithm": "RSA"
                },
                "monitoring": {
                    "process_check_interval": 300,
                    "network_check_interval": 300,
                    "file_check_interval": 3600
                },
                "alerts": {
                    "email_enabled": True,
                    "slack_enabled": False,
                    "threshold": "WARNING"
                },
                "scanning": {
                    "enabled": True,
                    "scan_schedule": "hourly",
                    "quarantine_enabled": True
                }
            }
            os.makedirs("config", exist_ok=True)
            with open("config/security_config.json", "w") as f:
                json.dump(config, f, indent=2)
            return config
    
    def _init_encryption(self):
        """Initialize encryption system."""
        key_file = Path("config/backup_key.pem")
        if not key_file.exists():
            # Generate new RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096
            )
            
            # Save private key
            with open(key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Save public key
            with open(key_file.with_suffix(".pub"), "wb") as f:
                f.write(private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
    
    def encrypt_file(self, file_path: Path) -> Path:
        """Encrypt a file using RSA."""
        try:
            # Load public key
            with open("config/backup_key.pub", "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())
            
            # Generate random Fernet key
            fernet_key = Fernet.generate_key()
            
            # Encrypt file with Fernet key
            with open(file_path, "rb") as f:
                data = f.read()
            fernet = Fernet(fernet_key)
            encrypted_data = fernet.encrypt(data)
            
            # Encrypt Fernet key with RSA
            encrypted_key = public_key.encrypt(
                fernet_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Save encrypted file
            encrypted_path = file_path.with_suffix(".encrypted")
            with open(encrypted_path, "wb") as f:
                f.write(len(encrypted_key).to_bytes(8, "big"))
                f.write(encrypted_key)
                f.write(encrypted_data)
            
            return encrypted_path
            
        except Exception as e:
            self.phantom.log_event(
                "Security",
                f"Encryption failed: {str(e)}",
                "ERROR"
            )
            return None
    
    def decrypt_file(self, encrypted_path: Path) -> Path:
        """Decrypt an encrypted file."""
        try:
            # Load private key
            with open("config/backup_key.pem", "rb") as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
            
            # Read encrypted file
            with open(encrypted_path, "rb") as f:
                key_size = int.from_bytes(f.read(8), "big")
                encrypted_key = f.read(key_size)
                encrypted_data = f.read()
            
            # Decrypt Fernet key
            fernet_key = private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Decrypt data
            fernet = Fernet(fernet_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Save decrypted file
            decrypted_path = encrypted_path.with_suffix(".decrypted")
            with open(decrypted_path, "wb") as f:
                f.write(decrypted_data)
            
            return decrypted_path
            
        except Exception as e:
            self.phantom.log_event(
                "Security",
                f"Decryption failed: {str(e)}",
                "ERROR"
            )
            return None
    
    def verify_file_integrity(self, file_path: Path, expected_hash: str) -> bool:
        """Verify file integrity using SHA-256."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            actual_hash = sha256_hash.hexdigest()
            return actual_hash == expected_hash
            
        except Exception as e:
            self.phantom.log_event(
                "Security",
                f"Integrity check failed: {str(e)}",
                "ERROR"
            )
            return False
    
    def scan_system(self) -> Dict[str, Any]:
        """Perform comprehensive system security scan."""
        try:
            scan_results = {
                "timestamp": datetime.now().isoformat(),
                "file_scan": self.scanner.scan_directory("."),
                "process_scan": self.scanner.scan_running_processes(),
                "network_scan": self.scanner.scan_network_activity()
            }
            
            # Log scan results
            log_file = self.security_log_path / f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_file, "w") as f:
                json.dump(scan_results, f, indent=2)
            
            return scan_results
            
        except Exception as e:
            self.phantom.log_event(
                "Security",
                f"System scan failed: {str(e)}",
                "ERROR"
            )
            return None
    
    def quarantine_file(self, file_path: Path) -> bool:
        """Move suspicious file to quarantine."""
        try:
            quarantine_dir = Path("security/quarantine")
            quarantine_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file to quarantine
            quarantine_path = quarantine_dir / file_path.name
            shutil.move(file_path, quarantine_path)
            
            self.phantom.log_event(
                "Security",
                f"File quarantined: {file_path}",
                "WARNING"
            )
            return True
            
        except Exception as e:
            self.phantom.log_event(
                "Security",
                f"Quarantine failed: {str(e)}",
                "ERROR"
            )
            return False
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status."""
        return {
            "timestamp": datetime.now().isoformat(),
            "encryption_enabled": self.config["encryption"]["enabled"],
            "monitoring_active": True,
            "last_scan": self.scan_system(),
            "quarantined_files": len(list(Path("security/quarantine").glob("*"))),
            "security_incidents": len(list(self.security_log_path.glob("*.json")))
        } 