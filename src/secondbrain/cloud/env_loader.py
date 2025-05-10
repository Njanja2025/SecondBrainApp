"""
Secure environment variable loader and validator.
"""
import os
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class EnvironmentLoader:
    """Manages secure loading and validation of environment variables."""
    
    REQUIRED_VARS = {
        'cloud': [
            'DROPBOX_ACCESS_TOKEN',
            'GOOGLE_DRIVE_CREDENTIALS',
            'GOOGLE_DRIVE_FOLDER_ID',
            'AWS_ACCESS_KEY',
            'AWS_SECRET_KEY',
            'AWS_BUCKET_NAME',
            'AWS_REGION'
        ],
        'dns': [
            'NAMECHEAP_API_USER',
            'NAMECHEAP_API_KEY',
            'SERVER_IP'
        ]
    }

    def __init__(self, env_path: Optional[str] = None):
        """Initialize environment loader.
        
        Args:
            env_path: Optional path to .env file. If not provided,
                     will look in project root.
        """
        self.env_path = env_path or self._find_env_file()
        self._load_env()

    def _find_env_file(self) -> str:
        """Find .env file in project root."""
        current_dir = Path.cwd()
        while current_dir.parent != current_dir:
            env_path = current_dir / '.env'
            if env_path.exists():
                return str(env_path)
            current_dir = current_dir.parent
        return '.env'  # Default to current directory

    def _load_env(self):
        """Load environment variables from .env file."""
        if not load_dotenv(self.env_path):
            logger.warning(f"No .env file found at {self.env_path}")

    def validate_cloud_vars(self) -> Dict[str, str]:
        """Validate and return cloud-related environment variables."""
        return self._validate_vars('cloud')

    def validate_dns_vars(self) -> Dict[str, str]:
        """Validate and return DNS-related environment variables."""
        return self._validate_vars('dns')

    def _validate_vars(self, category: str) -> Dict[str, str]:
        """Validate required environment variables for a category."""
        missing_vars = []
        env_vars = {}

        for var in self.REQUIRED_VARS[category]:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            else:
                env_vars[var] = value

        if missing_vars:
            raise EnvironmentError(
                f"Missing required {category} environment variables: "
                f"{', '.join(missing_vars)}"
            )

        return env_vars

    def get_all_vars(self) -> Dict[str, Dict[str, str]]:
        """Get all validated environment variables."""
        return {
            'cloud': self.validate_cloud_vars(),
            'dns': self.validate_dns_vars()
        }

    @staticmethod
    def generate_template(output_path: str = '.env.template'):
        """Generate a template .env file."""
        template = """# Cloud Storage Credentials
DROPBOX_ACCESS_TOKEN=your_dropbox_token_here
GOOGLE_DRIVE_CREDENTIALS=path_to_google_drive_credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here

# AWS Credentials
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
AWS_BUCKET_NAME=your-s3-bucket
AWS_REGION=us-east-1

# Namecheap DNS Credentials
NAMECHEAP_API_USER=your_api_user
NAMECHEAP_API_KEY=your_api_key
SERVER_IP=your_server_ip
"""
        with open(output_path, 'w') as f:
            f.write(template)
        logger.info(f"Generated environment template at {output_path}") 