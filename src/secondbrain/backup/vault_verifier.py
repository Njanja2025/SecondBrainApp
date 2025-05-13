"""
Vault verification script for SecondBrain Backup System.
"""
import os
import json
import logging
import datetime
from pathlib import Path
import zipfile
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_vault_path():
    """Get the vault directory path."""
    config_path = Path(__file__).parent / 'cloud_config.json'
    with open(config_path) as f:
        config = json.load(f)
    return Path(os.path.expanduser(config['local_vault_path']))

def calculate_hash(file_path):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_backup_integrity(backup_file):
    """Verify the integrity of a backup file."""
    try:
        # Check if file exists
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        # Check file size
        size_mb = backup_file.stat().st_size / (1024 * 1024)
        if size_mb < 0.1:  # Less than 100KB
            logger.error(f"Backup file suspiciously small: {size_mb:.2f}MB")
            return False
        
        # Verify ZIP structure
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                if not zipf.testzip():
                    logger.info("ZIP file structure verified")
                else:
                    logger.error("ZIP file is corrupted")
                    return False
        except zipfile.BadZipFile:
            logger.error("Invalid ZIP file")
            return False
        
        # Check hash if available
        hash_file = backup_file.with_suffix('.sha256')
        if hash_file.exists():
            with open(hash_file) as f:
                stored_hash = f.read().strip()
            current_hash = calculate_hash(backup_file)
            if current_hash != stored_hash:
                logger.error("Backup file hash mismatch!")
                return False
            logger.info("Backup hash verified")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying backup integrity: {e}")
        return False

def verify_latest_backup():
    """Verify the latest backup in the vault."""
    vault_dir = get_vault_path()
    
    try:
        # Get all backup files
        backup_files = sorted(
            [f for f in vault_dir.glob('*.zip')],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not backup_files:
            logger.error("No backups found in vault")
            return False
        
        # Get latest backup
        latest_backup = backup_files[0]
        mod_time = datetime.datetime.fromtimestamp(latest_backup.stat().st_mtime)
        
        logger.info(f"Latest backup: {latest_backup.name}")
        logger.info(f"Modified: {mod_time}")
        
        # Verify integrity
        if verify_backup_integrity(latest_backup):
            logger.info("✅ Latest backup verified successfully")
            return True
        else:
            logger.error("❌ Latest backup verification failed")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying latest backup: {e}")
        return False

def main():
    """Run vault verification."""
    logger.info("Starting vault verification...")
    
    if verify_latest_backup():
        logger.info("Vault verification completed successfully")
        return 0
    else:
        logger.error("Vault verification failed")
        return 1

if __name__ == "__main__":
    exit(main()) 