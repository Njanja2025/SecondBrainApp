"""
Security manager for SecondBrain application.
Handles encryption, access control, audit logging, and security monitoring.
"""
import os
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import jwt
from dataclasses import dataclass
import sqlite3
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """Security event data structure."""
    timestamp: datetime
    event_type: str
    user_id: str
    action: str
    resource: str
    status: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    session_id: Optional[str] = None

class SecurityManager:
    """Manages security features for the SecondBrain application."""
    
    def __init__(self, config_path: str = 'config/security_config.json'):
        """Initialize security manager."""
        self.config_path = config_path
        self.config = self._load_config()
        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self._init_database()
        self._start_monitoring()
        
        # Generate or load RSA keys
        self.private_key, self.public_key = self._setup_rsa_keys()
        
        # Initialize rate limiting
        self.rate_limits = {}
        self.rate_limit_lock = threading.Lock()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load security configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default config if not exists
            default_config = {
                'encryption': {
                    'algorithm': 'AES-256',
                    'key_rotation_days': 30
                },
                'access_control': {
                    'token_expiry_hours': 24,
                    'max_failed_attempts': 3,
                    'lockout_duration_minutes': 30
                },
                'audit': {
                    'log_retention_days': 90,
                    'critical_events': ['login_failed', 'permission_denied', 'data_access']
                },
                'monitoring': {
                    'check_interval_seconds': 300,
                    'alert_thresholds': {
                        'failed_logins_per_hour': 10,
                        'api_requests_per_minute': 100
                    }
                }
            }
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
    
    def _init_database(self):
        """Initialize security database."""
        conn = sqlite3.connect('data/security.db')
        c = conn.cursor()
        
        # Create security events table
        c.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                event_type TEXT,
                user_id TEXT,
                action TEXT,
                resource TEXT,
                status TEXT,
                details TEXT,
                ip_address TEXT,
                session_id TEXT
            )
        ''')
        
        # Create access control table
        c.execute('''
            CREATE TABLE IF NOT EXISTS access_control (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE,
                failed_attempts INTEGER DEFAULT 0,
                last_failed_attempt TIMESTAMP,
                locked_until TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key."""
        try:
            with open('config/encryption.key', 'rb') as f:
                return f.read()
        except FileNotFoundError:
            key = Fernet.generate_key()
            os.makedirs('config', exist_ok=True)
            with open('config/encryption.key', 'wb') as f:
                f.write(key)
            return key
    
    def _setup_rsa_keys(self) -> tuple:
        """Setup RSA keys for asymmetric encryption."""
        key_path = Path('config/rsa_keys')
        key_path.mkdir(parents=True, exist_ok=True)
        
        private_key_path = key_path / 'private.pem'
        public_key_path = key_path / 'public.pem'
        
        if not private_key_path.exists() or not public_key_path.exists():
            # Generate new key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            
            # Save private key
            with open(private_key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Save public key
            with open(public_key_path, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
        else:
            # Load existing keys
            with open(private_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
            with open(public_key_path, 'rb') as f:
                public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
        
        return private_key, public_key
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet (symmetric encryption)."""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet (symmetric encryption)."""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def asymmetric_encrypt(self, data: str) -> bytes:
        """Encrypt data using RSA (asymmetric encryption)."""
        return self.public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def asymmetric_decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data using RSA (asymmetric encryption)."""
        return self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        ).decode()
    
    def generate_token(self, user_id: str, permissions: List[str]) -> str:
        """Generate JWT token for user authentication."""
        expiry = datetime.utcnow() + datetime.timedelta(
            hours=self.config['access_control']['token_expiry_hours']
        )
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': expiry
        }
        return jwt.encode(payload, self.encryption_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload."""
        try:
            return jwt.decode(token, self.encryption_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def check_permission(self, token: str, required_permission: str) -> bool:
        """Check if token has required permission."""
        try:
            payload = self.verify_token(token)
            return required_permission in payload['permissions']
        except ValueError:
            return False
    
    def log_security_event(self, event: SecurityEvent):
        """Log security event to database."""
        conn = sqlite3.connect('data/security.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO security_events 
            (timestamp, event_type, user_id, action, resource, status, details, ip_address, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.timestamp,
            event.event_type,
            event.user_id,
            event.action,
            event.resource,
            event.status,
            json.dumps(event.details),
            event.ip_address,
            event.session_id
        ))
        
        conn.commit()
        conn.close()
        
        # Log critical events
        if event.event_type in self.config['audit']['critical_events']:
            logger.warning(f"Critical security event: {event}")
    
    def _start_monitoring(self):
        """Start security monitoring in a background thread."""
        def monitor_security():
            while True:
                try:
                    self._check_security_metrics()
                    time.sleep(self.config['monitoring']['check_interval_seconds'])
                except Exception as e:
                    logger.error(f"Error in security monitoring: {e}")
                    time.sleep(60)  # Sleep for 1 minute on error
        
        thread = threading.Thread(target=monitor_security, daemon=True)
        thread.start()
    
    def _check_security_metrics(self):
        """Check security metrics and generate alerts."""
        conn = sqlite3.connect('data/security.db')
        c = conn.cursor()
        
        # Check failed login attempts
        c.execute('''
            SELECT COUNT(*) FROM security_events
            WHERE event_type = 'login_failed'
            AND timestamp >= datetime('now', '-1 hour')
        ''')
        failed_logins = c.fetchone()[0]
        
        if failed_logins >= self.config['monitoring']['alert_thresholds']['failed_logins_per_hour']:
            logger.warning(f"High number of failed login attempts: {failed_logins} in the last hour")
        
        # Check API request rate
        c.execute('''
            SELECT COUNT(*) FROM security_events
            WHERE event_type = 'api_request'
            AND timestamp >= datetime('now', '-1 minute')
        ''')
        api_requests = c.fetchone()[0]
        
        if api_requests >= self.config['monitoring']['alert_thresholds']['api_requests_per_minute']:
            logger.warning(f"High API request rate: {api_requests} requests/minute")
        
        conn.close()
    
    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limit is exceeded."""
        with self.rate_limit_lock:
            now = time.time()
            if key not in self.rate_limits:
                self.rate_limits[key] = []
            
            # Remove old timestamps
            self.rate_limits[key] = [ts for ts in self.rate_limits[key] if ts > now - window]
            
            # Check if limit is exceeded
            if len(self.rate_limits[key]) >= limit:
                return False
            
            # Add new timestamp
            self.rate_limits[key].append(now)
            return True
    
    def rotate_encryption_key(self):
        """Rotate encryption key."""
        # Generate new key
        new_key = Fernet.generate_key()
        new_fernet = Fernet(new_key)
        
        # Re-encrypt all sensitive data with new key
        # This would need to be implemented based on your data storage
        
        # Save new key
        with open('config/encryption.key', 'wb') as f:
            f.write(new_key)
        
        # Update current key
        self.encryption_key = new_key
        self.fernet = new_fernet
    
    def cleanup_old_logs(self):
        """Clean up old security logs."""
        conn = sqlite3.connect('data/security.db')
        c = conn.cursor()
        
        retention_days = self.config['audit']['log_retention_days']
        c.execute('''
            DELETE FROM security_events
            WHERE timestamp < datetime('now', ?)
        ''', (f'-{retention_days} days',))
        
        conn.commit()
        conn.close()

# Create singleton instance
security_manager = SecurityManager() 