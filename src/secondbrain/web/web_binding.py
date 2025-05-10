"""
Web binding configuration for SecondBrain AWS deployment.
"""
import os
import logging
from pathlib import Path
from typing import Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class WebBinding:
    """Manages web binding and AWS deployment configuration."""
    
    def __init__(self):
        """Initialize web binding configuration."""
        self.domain = "samantha.njanja.net"
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.ec2_instance_id = os.getenv("AWS_EC2_INSTANCE_ID")
        
        # Initialize AWS clients
        self.ec2_client = boto3.client('ec2', region_name=self.aws_region)
        self.route53_client = boto3.client('route53')
        
    def get_instance_public_ip(self) -> Optional[str]:
        """Get the public IP of the EC2 instance."""
        try:
            response = self.ec2_client.describe_instances(
                InstanceIds=[self.ec2_instance_id]
            )
            return response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        except Exception as e:
            logger.error(f"Failed to get instance IP: {e}")
            return None
            
    def create_health_check_file(self):
        """Create DNS health check file."""
        try:
            health_file = Path("/var/www/html/DNS_HEALTH.html")
            health_file.parent.mkdir(parents=True, exist_ok=True)
            
            content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SecondBrain Status</title>
            </head>
            <body>
                <h1>SecondBrain Status</h1>
                <p>Status: Online</p>
                <p>Domain: {self.domain}</p>
                <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </body>
            </html>
            """
            
            health_file.write_text(content)
            logger.info("Created DNS health check file")
            
        except Exception as e:
            logger.error(f"Failed to create health check file: {e}")
            
    def configure_nginx(self):
        """Configure Nginx for the web application."""
        try:
            nginx_config = f"""
            server {{
                listen 80;
                server_name {self.domain};
                
                location / {{
                    proxy_pass http://localhost:8000;
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                }}
                
                location /status {{
                    alias /var/www/html;
                    index DNS_HEALTH.html;
                }}
            }}
            """
            
            config_path = Path("/etc/nginx/sites-available/secondbrain")
            config_path.write_text(nginx_config)
            
            # Create symlink if it doesn't exist
            symlink = Path("/etc/nginx/sites-enabled/secondbrain")
            if not symlink.exists():
                symlink.symlink_to(config_path)
            
            logger.info("Nginx configuration updated")
            
        except Exception as e:
            logger.error(f"Failed to configure Nginx: {e}")
            
    def setup_ssl(self):
        """Setup SSL using Let's Encrypt."""
        try:
            # Install certbot if not present
            os.system("apt-get update && apt-get install -y certbot python3-certbot-nginx")
            
            # Obtain and install certificate
            os.system(f"certbot --nginx -d {self.domain} --non-interactive --agree-tos -m admin@njanja.net")
            logger.info("SSL certificate installed")
            
        except Exception as e:
            logger.error(f"Failed to setup SSL: {e}")
            
    def configure_security_group(self):
        """Configure EC2 security group for web access."""
        try:
            # Get security group ID
            response = self.ec2_client.describe_instances(
                InstanceIds=[self.ec2_instance_id]
            )
            security_group_id = response['Reservations'][0]['Instances'][0]['SecurityGroups'][0]['GroupId']
            
            # Add necessary inbound rules
            self.ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 443,
                        'ToPort': 443,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            logger.info("Security group configured")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                logger.info("Security group rules already exist")
            else:
                logger.error(f"Failed to configure security group: {e}")
        except Exception as e:
            logger.error(f"Failed to configure security group: {e}")
            
    def setup(self):
        """Complete web binding setup."""
        try:
            logger.info("Starting web binding setup...")
            
            # Create health check file
            self.create_health_check_file()
            
            # Configure Nginx
            self.configure_nginx()
            
            # Setup SSL
            self.setup_ssl()
            
            # Configure security group
            self.configure_security_group()
            
            logger.info("Web binding setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Web binding setup failed: {e}")
            return False 