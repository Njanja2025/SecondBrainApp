"""
Deployment script for SecondBrainApp SaaS
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from deploy_config import DeployConfig
from setup_domain import DomainSetup
from generate_payment_links import PaymentSetup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Deployer:
    """Handle complete deployment process."""
    
    def __init__(self, config: DeployConfig):
        """Initialize deployer."""
        self.config = config
        self.domain_setup = DomainSetup(config)
        self.payment_setup = PaymentSetup(config)
        
    def check_prerequisites(self) -> Tuple[bool, str]:
        """
        Check deployment prerequisites.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
                return False, f"Python 3.8+ required, found {python_version.major}.{python_version.minor}"
                
            # Check required packages
            required_packages = [
                "flask",
                "flask-sqlalchemy",
                "flask-login",
                "flask-mail",
                "stripe",
                "paypalrestsdk",
                "dnspython",
                "requests"
            ]
            
            for package in required_packages:
                try:
                    __import__(package.replace("-", "_"))
                except ImportError:
                    return False, f"Required package {package} not installed"
                    
            # Check environment variables
            required_vars = [
                "FLASK_SECRET_KEY",
                "STRIPE_API_KEY",
                "PAYPAL_CLIENT_ID",
                "PAYPAL_CLIENT_SECRET",
                "SMTP_USERNAME",
                "SMTP_PASSWORD"
            ]
            
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                return False, f"Missing environment variables: {', '.join(missing_vars)}"
                
            return True, "All prerequisites satisfied"
            
        except Exception as e:
            logger.error(f"Failed to check prerequisites: {e}")
            return False, str(e)
            
    def setup_database(self) -> Tuple[bool, str]:
        """
        Set up database.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create database directory
            db_dir = Path("instance")
            db_dir.mkdir(exist_ok=True)
            
            # Initialize database
            from src.secondbrain.saas.portal import app, db
            with app.app_context():
                db.create_all()
                
            return True, "Database setup completed successfully"
            
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            return False, str(e)
            
    def setup_static_files(self) -> Tuple[bool, str]:
        """
        Set up static files.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create static directory
            static_dir = Path(f"/var/www/{self.config.domain}/static")
            static_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy static files
            source_dir = Path("src/secondbrain/saas/static")
            if source_dir.exists():
                subprocess.run(["sudo", "cp", "-r", str(source_dir), str(static_dir.parent)], check=True)
                
            return True, "Static files setup completed successfully"
            
        except Exception as e:
            logger.error(f"Failed to setup static files: {e}")
            return False, str(e)
            
    def setup_systemd(self) -> Tuple[bool, str]:
        """
        Set up systemd service.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create service file
            service_content = f"""[Unit]
Description=SecondBrainApp SaaS Portal
After=network.target

[Service]
User={os.getenv('USER')}
WorkingDirectory={os.getcwd()}
Environment="PATH={os.getenv('PATH')}"
Environment="PYTHONPATH={os.getcwd()}"
Environment="FLASK_APP=saas_portal.py"
Environment="FLASK_ENV=production"
ExecStart=/usr/bin/python3 saas_portal.py
Restart=always

[Install]
WantedBy=multi-user.target
"""
            service_path = "/etc/systemd/system/secondbrain-saas.service"
            with open(service_path, "w") as f:
                f.write(service_content)
                
            # Reload systemd and enable service
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", "secondbrain-saas"], check=True)
            
            return True, "Systemd service setup completed successfully"
            
        except Exception as e:
            logger.error(f"Failed to setup systemd service: {e}")
            return False, str(e)
            
    def deploy(self) -> Tuple[bool, str]:
        """
        Run complete deployment process.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check prerequisites
            success, message = self.check_prerequisites()
            if not success:
                return False, f"Prerequisites check failed: {message}"
                
            # Setup domain and SSL
            success, message = self.domain_setup.setup()
            if not success:
                return False, f"Domain setup failed: {message}"
                
            # Setup payment gateways
            success, message = self.payment_setup.setup()
            if not success:
                return False, f"Payment setup failed: {message}"
                
            # Setup database
            success, message = self.setup_database()
            if not success:
                return False, f"Database setup failed: {message}"
                
            # Setup static files
            success, message = self.setup_static_files()
            if not success:
                return False, f"Static files setup failed: {message}"
                
            # Setup systemd service
            success, message = self.setup_systemd()
            if not success:
                return False, f"Systemd setup failed: {message}"
                
            return True, "Deployment completed successfully"
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False, str(e)

def main():
    """Run deployment."""
    try:
        # Load configuration
        config = DeployConfig.from_env()
        
        # Initialize deployer
        deployer = Deployer(config)
        
        # Run deployment
        success, message = deployer.deploy()
        
        if success:
            logger.info(message)
            sys.exit(0)
        else:
            logger.error(message)
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 