"""
Domain and SSL Setup Script for SecondBrainApp SaaS Portal
"""

import os
import sys
import logging
import subprocess
import socket
import dns.resolver
from pathlib import Path
import requests
from typing import Optional, Tuple
from deploy_config import DeployConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DomainSetup:
    """Handle domain and SSL setup."""

    def __init__(self, config: DeployConfig):
        """Initialize domain setup."""
        self.config = config
        self.domain = config.domain
        self.email = config.admin_email

    def check_dns(self) -> Tuple[bool, str]:
        """
        Check if DNS records are properly configured.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check A record
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(self.domain, "A")
            ip_addresses = [str(rdata) for rdata in answers]

            # Verify IP is reachable
            for ip in ip_addresses:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((ip, 80))
                    sock.close()

                    if result == 0:
                        logger.info(f"DNS A record is configured correctly: {ip}")
                        return True, f"DNS A record points to {ip}"
                except Exception as e:
                    logger.warning(f"Failed to connect to {ip}: {e}")

            return False, "No reachable IP addresses found"

        except dns.resolver.NXDOMAIN:
            return False, f"Domain {self.domain} does not exist"
        except dns.resolver.NoAnswer:
            return False, f"No A record found for {self.domain}"
        except Exception as e:
            logger.error(f"Failed to check DNS: {e}")
            return False, str(e)

    def check_ssl(self) -> Tuple[bool, str]:
        """
        Check if SSL certificate is valid.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check certificate files
            cert_path = Path(self.config.ssl_cert_path)
            key_path = Path(self.config.ssl_key_path)

            if not cert_path.exists():
                return False, f"SSL certificate not found at {cert_path}"
            if not key_path.exists():
                return False, f"SSL key not found at {key_path}"

            # Verify certificate
            cmd = ["openssl", "x509", "-in", str(cert_path), "-noout", "-text"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return False, f"Invalid SSL certificate: {result.stderr}"

            # Check expiration
            cmd = ["openssl", "x509", "-in", str(cert_path), "-noout", "-enddate"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return False, f"Failed to check certificate expiration: {result.stderr}"

            logger.info("SSL certificate is valid")
            return True, "SSL certificate is valid"

        except Exception as e:
            logger.error(f"Failed to check SSL: {e}")
            return False, str(e)

    def setup_ssl(self) -> Tuple[bool, str]:
        """
        Set up SSL certificate using certbot.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Install certbot if not present
            try:
                subprocess.run(["which", "certbot"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                logger.info("Installing certbot...")
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "certbot"], check=True
                )

            # Check if certificate already exists
            success, message = self.check_ssl()
            if success:
                return True, "SSL certificate already exists"

            # Obtain SSL certificate
            cmd = [
                "sudo",
                "certbot",
                "certonly",
                "--standalone",
                "-d",
                self.domain,
                "--email",
                self.email,
                "--agree-tos",
                "--non-interactive",
                "--preferred-challenges",
                "http",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return False, f"Failed to obtain SSL certificate: {result.stderr}"

            logger.info("SSL certificate obtained successfully")
            return True, "SSL certificate obtained successfully"

        except Exception as e:
            logger.error(f"Failed to setup SSL: {e}")
            return False, str(e)

    def configure_nginx(self) -> Tuple[bool, str]:
        """
        Configure Nginx with SSL.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if Nginx is installed
            try:
                subprocess.run(["which", "nginx"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                logger.info("Installing Nginx...")
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "nginx"], check=True
                )

            # Create Nginx config
            config = f"""
server {{
    listen 80;
    server_name {self.domain};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.domain};
    
    ssl_certificate {self.config.ssl_cert_path};
    ssl_certificate_key {self.config.ssl_key_path};
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Proxy settings
    location / {{
        proxy_pass http://localhost:{self.config.port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}
    
    # Static files
    location /static {{
        alias /var/www/{self.domain}/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }}
}}
"""
            # Write config
            config_path = f"/etc/nginx/sites-available/{self.domain}"
            with open(config_path, "w") as f:
                f.write(config)

            # Enable site
            subprocess.run(
                [
                    "sudo",
                    "ln",
                    "-sf",
                    config_path,
                    f"/etc/nginx/sites-enabled/{self.domain}",
                ],
                check=True,
            )

            # Test and reload Nginx
            result = subprocess.run(
                ["sudo", "nginx", "-t"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return False, f"Nginx configuration test failed: {result.stderr}"

            subprocess.run(["sudo", "systemctl", "reload", "nginx"], check=True)

            logger.info("Nginx configured successfully")
            return True, "Nginx configured successfully"

        except Exception as e:
            logger.error(f"Failed to configure Nginx: {e}")
            return False, str(e)

    def setup(self) -> Tuple[bool, str]:
        """
        Run complete domain and SSL setup.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check DNS
            success, message = self.check_dns()
            if not success:
                return False, f"DNS check failed: {message}"

            # Setup SSL
            success, message = self.setup_ssl()
            if not success:
                return False, f"SSL setup failed: {message}"

            # Configure Nginx
            success, message = self.configure_nginx()
            if not success:
                return False, f"Nginx configuration failed: {message}"

            logger.info("Domain and SSL setup completed successfully")
            return True, "Domain and SSL setup completed successfully"

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False, str(e)


def main():
    """Run domain setup."""
    try:
        # Load configuration
        config = DeployConfig.from_env()

        # Initialize setup
        setup = DomainSetup(config)

        # Run setup
        success, message = setup.setup()

        if success:
            logger.info(message)
            sys.exit(0)
        else:
            logger.error(message)
            sys.exit(1)

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
