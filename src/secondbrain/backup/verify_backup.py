"""
Backup verification script for the Companion Journaling Backup System.
Verifies backup integrity, cloud sync status, and file consistency.
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import dropbox
from dropbox.exceptions import ApiError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackupVerifier:
    def __init__(self):
        self.cloud_config = self._load_config('cloud_config.json')
        self.backup_root = Path(os.path.expanduser(self.cloud_config['local_vault_path']))
        
    def _load_config(self, config_file):
        config_path = Path(__file__).parent / config_file
        with open(config_path) as f:
            return json.load(f)
    
    def calculate_file_hash(self, file_path):
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def verify_backup_integrity(self, backup_file):
        """Verify the integrity of a backup file."""
        try:
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Check file size
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            if size_mb < 0.1:  # Less than 100KB
                logger.error(f"Backup file suspiciously small: {size_mb:.2f}MB")
                return False
            
            # Calculate and store hash
            file_hash = self.calculate_file_hash(backup_file)
            hash_file = backup_file.with_suffix('.sha256')
            
            if hash_file.exists():
                # Verify against stored hash
                with open(hash_file) as f:
                    stored_hash = f.read().strip()
                if file_hash != stored_hash:
                    logger.error("Backup file hash mismatch!")
                    return False
            else:
                # Store new hash
                with open(hash_file, 'w') as f:
                    f.write(file_hash)
            
            logger.info(f"Backup integrity verified: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying backup integrity: {e}")
            return False
    
    def verify_cloud_sync(self, backup_file):
        """Verify that backup is properly synced to cloud."""
        try:
            dbx = dropbox.Dropbox(self.cloud_config['access_token'])
            cloud_path = f"{self.cloud_config['cloud_path']}/{backup_file.name}"
            
            # Check if file exists in cloud
            try:
                metadata = dbx.files_get_metadata(cloud_path)
                logger.info(f"Backup found in cloud: {cloud_path}")
                
                # Verify cloud file size matches local
                if metadata.size != backup_file.stat().st_size:
                    logger.error("Cloud file size mismatch!")
                    return False
                
                return True
                
            except ApiError as e:
                logger.error(f"Backup not found in cloud: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying cloud sync: {e}")
            return False
    
    def verify_recent_backups(self, days=7):
        """Verify all backups from the last N days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            all_ok = True
            
            for backup_file in self.backup_root.glob('*.zip'):
                # Check backup date
                backup_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if backup_date < cutoff_date:
                    continue
                
                logger.info(f"\nVerifying backup: {backup_file}")
                
                # Verify integrity
                integrity_ok = self.verify_backup_integrity(backup_file)
                if not integrity_ok:
                    all_ok = False
                    continue
                
                # Verify cloud sync
                sync_ok = self.verify_cloud_sync(backup_file)
                if not sync_ok:
                    all_ok = False
            
            return all_ok
            
        except Exception as e:
            logger.error(f"Error verifying recent backups: {e}")
            return False

def main():
    """Run backup verification."""
    verifier = BackupVerifier()
    
    logger.info("Starting backup verification...")
    
    # Verify recent backups
    if verifier.verify_recent_backups():
        logger.info("\n✅ All recent backups verified successfully!")
        return 0
    else:
        logger.error("\n❌ Some backups failed verification. Please check the logs above.")
        return 1

if __name__ == "__main__":
    exit(main()) 