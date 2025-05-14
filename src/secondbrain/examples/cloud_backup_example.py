"""
Example usage of cloud backup features for memory engine.
"""

import asyncio
import logging
import os
from pathlib import Path

from ..memory.memory_engine import MemoryEngine
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def main():
    """Example usage of cloud backup features."""
    try:
        # Initialize memory engine with cloud backup enabled
        memory = MemoryEngine(
            memory_file="example_cloud_backup.json", enable_cloud_backup=True
        )

        # Example 1: Configure Dropbox backup
        logger.info("Example 1: Configuring Dropbox backup")
        memory.configure_cloud_backup(
            "dropbox",
            {
                "access_token": os.getenv("DROPBOX_ACCESS_TOKEN"),
                "backup_path": "/samantha/backups",
            },
        )

        # Example 2: Configure Google Drive backup
        logger.info("\nExample 2: Configuring Google Drive backup")
        memory.configure_cloud_backup(
            "google_drive",
            {
                "credentials_json": "config/google_credentials.json",
                "folder_id": os.getenv("GOOGLE_DRIVE_FOLDER_ID"),
            },
        )

        # Example 3: Configure AWS S3 backup
        logger.info("\nExample 3: Configuring AWS S3 backup")
        memory.configure_cloud_backup(
            "aws",
            {
                "bucket": os.getenv("AWS_BUCKET_NAME"),
                "access_key": os.getenv("AWS_ACCESS_KEY"),
                "secret_key": os.getenv("AWS_SECRET_KEY"),
                "region": os.getenv("AWS_REGION", "us-east-1"),
                "object_prefix": "samantha/memory_backups",
            },
        )

        # Example 4: Add some test data
        logger.info("\nExample 4: Adding test data")
        memory.remember_mood("excited", context={"source": "cloud_backup_test"})

        # Example 5: Trigger manual backup
        logger.info("\nExample 5: Triggering manual backup")
        backup_results = await memory.backup_to_cloud()
        logger.info("Backup results:")
        for service, success in backup_results.items():
            logger.info(f"- {service}: {'Success' if success else 'Failed'}")

        # Example 6: Update DNS (if configured)
        if os.getenv("NAMECHEAP_API_USER") and os.getenv("NAMECHEAP_API_KEY"):
            logger.info("\nExample 6: Updating DNS")
            dns_success = await memory.update_dns(
                api_user=os.getenv("NAMECHEAP_API_USER"),
                api_key=os.getenv("NAMECHEAP_API_KEY"),
                domain=os.getenv("DOMAIN_NAME", "example.com"),
                subdomain="samantha",
                ip_address=os.getenv("SERVER_IP"),
            )
            logger.info(f"DNS update: {'Success' if dns_success else 'Failed'}")

    except Exception as e:
        logger.error(f"Error in example: {e}")


if __name__ == "__main__":
    # Create example .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(
                """# Cloud Service Credentials
DROPBOX_ACCESS_TOKEN=your_dropbox_token
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
AWS_BUCKET_NAME=your_bucket_name
AWS_ACCESS_KEY=your_access_key
AWS_SECRET_KEY=your_secret_key
AWS_REGION=us-east-1

# Namecheap DNS Configuration
NAMECHEAP_API_USER=your_api_user
NAMECHEAP_API_KEY=your_api_key
DOMAIN_NAME=example.com
SERVER_IP=your_server_ip
"""
            )

    asyncio.run(main())
