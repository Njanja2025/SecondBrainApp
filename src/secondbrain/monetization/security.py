"""
Security manager for handling API key encryption and webhook verification.
"""
import os
import json
import logging
import hmac
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SecurityManager:
    """Manages security features for the payment system."""
    
    def __init__(self, config_path: str = "config/payment_config.json"):
        """Initialize the security manager."""
        self.config_path = config_path
        self.config = self._load_config()
        self._initialize_encryption()
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file: {self.config_path}")
            raise
    
    def _initialize_encryption(self):
        """Initialize encryption key."""
        key_file = Path("config/encryption.key")
        if key_file.exists():
            with open(key_file, "rb") as f:
                self.encryption_key = f.read()
        else:
            self.encryption_key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, "wb") as f:
                f.write(self.encryption_key)
        
        self.cipher_suite = Fernet(self.encryption_key)
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key."""
        return self.cipher_suite.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key."""
        return self.cipher_suite.decrypt(encrypted_key.encode()).decode()
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature."""
        try:
            # Get webhook secret
            webhook_secret = self.config["webhook_secret"]
            
            # Compute HMAC
            expected_signature = hmac.new(
                webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Failed to verify webhook signature: {e}")
            return False
    
    def log_failed_attempt(self, attempt_type: str, details: str):
        """Log failed security attempt."""
        if not self.config["security"].get("log_failed_attempts", True):
            return
        
        log_file = Path(self.config["logging"]["file"])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, "a") as f:
            f.write(f"[{datetime.now()}] Failed {attempt_type}: {details}\n")
        
        # Check if we should send an alert
        if self._should_send_alert(attempt_type):
            self._send_security_alert(attempt_type, details)
    
    def _should_send_alert(self, attempt_type: str) -> bool:
        """Check if we should send a security alert."""
        threshold = self.config["security"].get("alert_threshold", 3)
        # Implement alert threshold logic here
        return False
    
    def _send_security_alert(self, attempt_type: str, details: str):
        """Send security alert."""
        # Implement alert sending logic here
        logger.warning(f"Security alert: {attempt_type} - {details}")
    
    def get_encrypted_config(self) -> Dict:
        """Get configuration with encrypted API keys."""
        config = self.config.copy()
        if self.config["security"].get("api_key_encryption", True):
            config["stripe_secret_key"] = self.encrypt_api_key(config["stripe_secret_key"])
        return config 