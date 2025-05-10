"""
Deployment configuration for SecondBrainApp SaaS
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class DeployConfig:
    """Deployment configuration settings."""
    
    # Domain settings
    domain: str = "saas.njanja.net"
    admin_email: str = "admin@njanja.net"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    
    # Database settings
    db_url: str = "sqlite:///saas.db"
    
    # SSL settings
    ssl_enabled: bool = True
    ssl_cert_path: str = "/etc/letsencrypt/live/saas.njanja.net/fullchain.pem"
    ssl_key_path: str = "/etc/letsencrypt/live/saas.njanja.net/privkey.pem"
    
    # Email settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Payment settings
    stripe_api_key: Optional[str] = None
    paypal_client_id: Optional[str] = None
    paypal_client_secret: Optional[str] = None
    
    # Security settings
    secret_key: str = os.getenv("FLASK_SECRET_KEY", "your-secret-key")
    session_lifetime: int = 3600  # 1 hour
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "saas.log"
    
    @classmethod
    def from_env(cls) -> 'DeployConfig':
        """Create config from environment variables."""
        return cls(
            domain=os.getenv("SAAS_DOMAIN", cls.domain),
            admin_email=os.getenv("ADMIN_EMAIL", cls.admin_email),
            host=os.getenv("PORTAL_HOST", cls.host),
            port=int(os.getenv("PORTAL_PORT", str(cls.port))),
            debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
            db_url=os.getenv("DATABASE_URL", cls.db_url),
            ssl_enabled=os.getenv("SSL_ENABLED", "true").lower() == "true",
            smtp_username=os.getenv("SMTP_USERNAME"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            stripe_api_key=os.getenv("STRIPE_API_KEY"),
            paypal_client_id=os.getenv("PAYPAL_CLIENT_ID"),
            paypal_client_secret=os.getenv("PAYPAL_CLIENT_SECRET"),
            secret_key=os.getenv("FLASK_SECRET_KEY", cls.secret_key),
            log_level=os.getenv("LOG_LEVEL", cls.log_level),
            log_file=os.getenv("LOG_FILE", cls.log_file)
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "domain": self.domain,
            "admin_email": self.admin_email,
            "host": self.host,
            "port": self.port,
            "debug": self.debug,
            "db_url": self.db_url,
            "ssl_enabled": self.ssl_enabled,
            "ssl_cert_path": self.ssl_cert_path,
            "ssl_key_path": self.ssl_key_path,
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "smtp_username": self.smtp_username,
            "smtp_password": "***" if self.smtp_password else None,
            "stripe_api_key": "***" if self.stripe_api_key else None,
            "paypal_client_id": "***" if self.paypal_client_id else None,
            "paypal_client_secret": "***" if self.paypal_client_secret else None,
            "secret_key": "***" if self.secret_key else None,
            "session_lifetime": self.session_lifetime,
            "log_level": self.log_level,
            "log_file": self.log_file
        } 