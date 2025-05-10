"""
Deployment script for the AI Business Starter Pack landing page and delivery system
"""
import os
import sys
import subprocess
import logging
import shutil
from pathlib import Path
import json
from typing import Dict, List, Tuple
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Deployer:
    def __init__(self):
        """Initialize the deployer."""
        self.base_dir = Path(os.getcwd())
        self.site_dir = self.base_dir / 'site'
        self.data_dir = self.site_dir / 'data'
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """Load deployment configuration."""
        config_path = self.site_dir / 'deploy_config.json'
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {
            'domain': 'njanja.net',
            'ssl_email': 'admin@njanja.net',
            'server_ip': None,
            'deploy_path': '/var/www/njanja.net',
            'nginx_config': '/etc/nginx/sites-available/njanja.net',
            'systemd_service': 'njanja-delivery',
            'required_packages': [
                'python3-pip',
                'nginx',
                'certbot',
                'python3-certbot-nginx'
            ]
        }
        
    def check_requirements(self) -> Tuple[bool, List[str]]:
        """Check system requirements."""
        missing_packages = []
        for package in self.config['required_packages']:
            try:
                subprocess.run(['dpkg', '-s', package], 
                             check=True, 
                             capture_output=True)
            except subprocess.CalledProcessError:
                missing_packages.append(package)
        return len(missing_packages) == 0, missing_packages
        
    def install_requirements(self, packages: List[str]) -> bool:
        """Install missing system requirements."""
        try:
            subprocess.run(['apt-get', 'update'], check=True)
            subprocess.run(['apt-get', 'install', '-y'] + packages, 
                         check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install packages: {e}")
            return False
            
    def setup_python_packages(self) -> bool:
        """Install required Python packages."""
        requirements = [
            'flask',
            'flask-cors',
            'pyjwt',
            'gunicorn'
        ]
        try:
            subprocess.run(['pip3', 'install'] + requirements, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Python packages: {e}")
            return False
            
    def setup_nginx(self) -> bool:
        """Configure Nginx."""
        try:
            # Create Nginx configuration
            nginx_config = f"""
            server {{
                listen 80;
                server_name {self.config['domain']};
                
                location / {{
                    root {self.config['deploy_path']};
                    index ai_starter_pack.html;
                }}
                
                location /api/ {{
                    proxy_pass http://localhost:5000;
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                }}
                
                location /downloads/ {{
                    internal;
                    alias {self.config['deploy_path']}/downloads/;
                }}
            }}
            """
            
            # Write Nginx configuration
            with open(self.config['nginx_config'], 'w') as f:
                f.write(nginx_config.strip())
                
            # Create symbolic link
            nginx_enabled = Path('/etc/nginx/sites-enabled/njanja.net')
            if not nginx_enabled.exists():
                nginx_enabled.symlink_to(self.config['nginx_config'])
                
            # Test Nginx configuration
            subprocess.run(['nginx', '-t'], check=True)
            
            # Reload Nginx
            subprocess.run(['systemctl', 'reload', 'nginx'], check=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure Nginx: {e}")
            return False
            
    def setup_ssl(self) -> bool:
        """Set up SSL with Let's Encrypt."""
        try:
            subprocess.run([
                'certbot', '--nginx',
                '-d', self.config['domain'],
                '--non-interactive',
                '--agree-tos',
                '-m', self.config['ssl_email']
            ], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to setup SSL: {e}")
            return False
            
    def setup_systemd(self) -> bool:
        """Configure systemd service."""
        try:
            service_config = f"""
            [Unit]
            Description=Njanja Delivery System
            After=network.target
            
            [Service]
            User=www-data
            WorkingDirectory={self.config['deploy_path']}
            Environment="PATH=/usr/local/bin"
            Environment="PYTHONPATH={self.config['deploy_path']}"
            ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:5000 delivery_backend:app
            Restart=always
            
            [Install]
            WantedBy=multi-user.target
            """
            
            # Write service configuration
            service_path = f"/etc/systemd/system/{self.config['systemd_service']}.service"
            with open(service_path, 'w') as f:
                f.write(service_config.strip())
                
            # Reload systemd and start service
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', self.config['systemd_service']], 
                         check=True)
            subprocess.run(['systemctl', 'start', self.config['systemd_service']], 
                         check=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure systemd service: {e}")
            return False
            
    def deploy_files(self) -> bool:
        """Deploy files to production directory."""
        try:
            # Create deployment directory
            deploy_path = Path(self.config['deploy_path'])
            deploy_path.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            shutil.copy2(self.site_dir / 'ai_starter_pack.html', 
                        deploy_path / 'ai_starter_pack.html')
            shutil.copy2(self.site_dir / 'delivery_backend.py', 
                        deploy_path / 'delivery_backend.py')
            
            # Create downloads directory
            downloads_dir = deploy_path / 'downloads'
            downloads_dir.mkdir(exist_ok=True)
            
            # Copy product package
            if Path('NjanjaStorefront_Package.zip').exists():
                shutil.copy2('NjanjaStorefront_Package.zip', 
                           downloads_dir / 'NjanjaStorefront_Package.zip')
            
            # Set permissions
            subprocess.run(['chown', '-R', 'www-data:www-data', 
                          str(deploy_path)], check=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy files: {e}")
            return False
            
    def verify_deployment(self) -> Tuple[bool, List[str]]:
        """Verify deployment status."""
        issues = []
        
        # Check Nginx status
        try:
            subprocess.run(['systemctl', 'is-active', '--quiet', 'nginx'])
        except subprocess.CalledProcessError:
            issues.append("Nginx is not running")
            
        # Check delivery system status
        try:
            subprocess.run(['systemctl', 'is-active', '--quiet', 
                          self.config['systemd_service']])
        except subprocess.CalledProcessError:
            issues.append("Delivery system is not running")
            
        # Check SSL certificate
        try:
            response = requests.get(f"https://{self.config['domain']}")
            if response.status_code != 200:
                issues.append("Website is not accessible via HTTPS")
        except requests.exceptions.SSLError:
            issues.append("SSL certificate is not valid")
        except requests.exceptions.RequestException:
            issues.append("Website is not accessible")
            
        return len(issues) == 0, issues
        
    def deploy(self) -> bool:
        """Run the complete deployment process."""
        try:
            # Check requirements
            print("\nChecking system requirements...")
            requirements_met, missing_packages = self.check_requirements()
            if not requirements_met:
                print(f"Installing missing packages: {', '.join(missing_packages)}")
                if not self.install_requirements(missing_packages):
                    return False
                    
            # Install Python packages
            print("\nInstalling Python packages...")
            if not self.setup_python_packages():
                return False
                
            # Deploy files
            print("\nDeploying files...")
            if not self.deploy_files():
                return False
                
            # Configure Nginx
            print("\nConfiguring Nginx...")
            if not self.setup_nginx():
                return False
                
            # Setup SSL
            print("\nSetting up SSL...")
            if not self.setup_ssl():
                return False
                
            # Configure systemd service
            print("\nConfiguring systemd service...")
            if not self.setup_systemd():
                return False
                
            # Verify deployment
            print("\nVerifying deployment...")
            deployment_ok, issues = self.verify_deployment()
            if not deployment_ok:
                print("Deployment verification failed:")
                for issue in issues:
                    print(f"- {issue}")
                return False
                
            print("\nDeployment completed successfully!")
            print(f"Website is available at: https://{self.config['domain']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

def main():
    """Main function to run deployment."""
    if os.geteuid() != 0:
        print("This script must be run as root")
        sys.exit(1)
        
    deployer = Deployer()
    
    if deployer.deploy():
        print("\nNext steps:")
        print("1. Configure environment variables in /etc/environment:")
        print("   - PAYSTACK_SECRET_KEY")
        print("   - JWT_SECRET_KEY")
        print("   - SMTP_USER")
        print("   - SMTP_PASS")
        print("2. Restart the delivery system:")
        print(f"   sudo systemctl restart {deployer.config['systemd_service']}")
        print("3. Monitor the logs:")
        print(f"   sudo journalctl -u {deployer.config['systemd_service']} -f")
    else:
        print("\nDeployment failed. Check the logs for details.")
        sys.exit(1)

if __name__ == '__main__':
    main() 