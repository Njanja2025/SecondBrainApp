"""
Backup manager for handling database backup and restore operations.
Manages database dumps, encryption, and restore operations.
"""

import os
import json
import logging
import time
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = logging.getLogger(__name__)


@dataclass
class BackupConfig:
    """Configuration for database backups."""

    name: str
    db_type: str  # postgresql, mysql, sqlite
    db_url: str
    backup_dir: str
    schedule: str = None  # cron expression
    retention_days: int = 30
    compression: bool = True
    encryption: bool = True
    encryption_key: str = None
    s3_bucket: str = None
    s3_prefix: str = None
    description: str = None


class BackupManager:
    """Manages database backup and restore operations."""

    def __init__(self, config_dir: str = "config/backups"):
        """Initialize the backup manager.

        Args:
            config_dir: Directory to store backup configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self._setup_encryption()

    def _setup_logging(self):
        """Set up logging for the backup manager."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _setup_encryption(self):
        """Set up encryption for backups."""
        try:
            key_file = self.config_dir / "encryption.key"

            if key_file.exists():
                with open(key_file, "rb") as f:
                    self.encryption_key = f.read()
            else:
                self.encryption_key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(self.encryption_key)

            self.cipher = Fernet(self.encryption_key)
            logger.info("Encryption setup completed")

        except Exception as e:
            logger.error(f"Failed to set up encryption: {str(e)}")
            raise

    def _load_configs(self):
        """Load backup configurations."""
        try:
            config_file = self.config_dir / "backup_configs.json"

            if config_file.exists():
                with open(config_file, "r") as f:
                    self.configs = {
                        name: BackupConfig(**config)
                        for name, config in json.load(f).items()
                    }
            else:
                self.configs = {}
                self._save_configs()

            logger.info("Backup configurations loaded")

        except Exception as e:
            logger.error(f"Failed to load backup configurations: {str(e)}")
            raise

    def _save_configs(self):
        """Save backup configurations."""
        try:
            config_file = self.config_dir / "backup_configs.json"

            with open(config_file, "w") as f:
                json.dump(
                    {name: vars(config) for name, config in self.configs.items()},
                    f,
                    indent=2,
                )

        except Exception as e:
            logger.error(f"Failed to save backup configurations: {str(e)}")

    def create_config(self, config: BackupConfig) -> bool:
        """Create a new backup configuration.

        Args:
            config: Backup configuration

        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False

            # Set encryption key if not provided
            if config.encryption and not config.encryption_key:
                config.encryption_key = self.encryption_key.decode()

            self.configs[config.name] = config
            self._save_configs()

            logger.info(f"Created backup configuration {config.name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to create backup configuration {config.name}: {str(e)}"
            )
            return False

    def update_config(self, name: str, config: BackupConfig) -> bool:
        """Update an existing backup configuration.

        Args:
            name: Configuration name
            config: New backup configuration

        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False

            # Set encryption key if not provided
            if config.encryption and not config.encryption_key:
                config.encryption_key = self.encryption_key.decode()

            self.configs[name] = config
            self._save_configs()

            logger.info(f"Updated backup configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update backup configuration {name}: {str(e)}")
            return False

    def delete_config(self, name: str) -> bool:
        """Delete a backup configuration.

        Args:
            name: Configuration name

        Returns:
            bool: True if configuration was deleted successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False

            del self.configs[name]
            self._save_configs()

            logger.info(f"Deleted backup configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup configuration {name}: {str(e)}")
            return False

    def get_config(self, name: str) -> Optional[BackupConfig]:
        """Get backup configuration.

        Args:
            name: Configuration name

        Returns:
            Backup configuration if found
        """
        return self.configs.get(name)

    def list_configs(self) -> List[str]:
        """List all backup configurations.

        Returns:
            List of configuration names
        """
        return list(self.configs.keys())

    def create_backup(self, config_name: str) -> Optional[str]:
        """Create a database backup.

        Args:
            config_name: Configuration name

        Returns:
            Path to backup file if successful
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return None

            # Create backup directory
            backup_dir = Path(config.backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{config_name}_{timestamp}"

            # Create backup based on database type
            if config.db_type == "postgresql":
                success = self._backup_postgresql(config, backup_file)
            elif config.db_type == "mysql":
                success = self._backup_mysql(config, backup_file)
            elif config.db_type == "sqlite":
                success = self._backup_sqlite(config, backup_file)
            else:
                logger.error(f"Unsupported database type: {config.db_type}")
                return None

            if not success:
                return None

            # Compress backup if enabled
            if config.compression:
                backup_file = self._compress_backup(backup_file)

            # Encrypt backup if enabled
            if config.encryption:
                backup_file = self._encrypt_backup(backup_file)

            # Upload to S3 if configured
            if config.s3_bucket:
                self._upload_to_s3(backup_file, config)

            # Clean up old backups
            self._cleanup_old_backups(config)

            logger.info(f"Created backup {backup_file}")
            return str(backup_file)

        except Exception as e:
            logger.error(f"Failed to create backup {config_name}: {str(e)}")
            return None

    def _backup_postgresql(self, config: BackupConfig, backup_file: Path) -> bool:
        """Create PostgreSQL backup.

        Args:
            config: Backup configuration
            backup_file: Path to backup file

        Returns:
            bool: True if backup was created successfully
        """
        try:
            # Parse database URL
            db_url = config.db_url.replace("postgresql://", "")
            user_pass, host_port_db = db_url.split("@")
            user, password = user_pass.split(":")
            host_port, db = host_port_db.split("/")
            host, port = host_port.split(":")

            # Create backup using pg_dump
            cmd = [
                "pg_dump",
                f"--host={host}",
                f"--port={port}",
                f"--username={user}",
                f"--dbname={db}",
                f"--file={backup_file}",
                "--format=custom",
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = password

            subprocess.run(cmd, env=env, check=True)
            return True

        except Exception as e:
            logger.error(f"Failed to create PostgreSQL backup: {str(e)}")
            return False

    def _backup_mysql(self, config: BackupConfig, backup_file: Path) -> bool:
        """Create MySQL backup.

        Args:
            config: Backup configuration
            backup_file: Path to backup file

        Returns:
            bool: True if backup was created successfully
        """
        try:
            # Parse database URL
            db_url = config.db_url.replace("mysql://", "")
            user_pass, host_port_db = db_url.split("@")
            user, password = user_pass.split(":")
            host_port, db = host_port_db.split("/")
            host, port = host_port.split(":")

            # Create backup using mysqldump
            cmd = [
                "mysqldump",
                f"--host={host}",
                f"--port={port}",
                f"--user={user}",
                f"--password={password}",
                db,
                f"--result-file={backup_file}",
            ]

            subprocess.run(cmd, check=True)
            return True

        except Exception as e:
            logger.error(f"Failed to create MySQL backup: {str(e)}")
            return False

    def _backup_sqlite(self, config: BackupConfig, backup_file: Path) -> bool:
        """Create SQLite backup.

        Args:
            config: Backup configuration
            backup_file: Path to backup file

        Returns:
            bool: True if backup was created successfully
        """
        try:
            # Parse database URL
            db_path = config.db_url.replace("sqlite:///", "")

            # Create backup by copying database file
            shutil.copy2(db_path, backup_file)
            return True

        except Exception as e:
            logger.error(f"Failed to create SQLite backup: {str(e)}")
            return False

    def _compress_backup(self, backup_file: Path) -> Path:
        """Compress backup file.

        Args:
            backup_file: Path to backup file

        Returns:
            Path to compressed backup file
        """
        try:
            compressed_file = backup_file.with_suffix(".gz")

            with open(backup_file, "rb") as f_in:
                with open(compressed_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            backup_file.unlink()
            return compressed_file

        except Exception as e:
            logger.error(f"Failed to compress backup: {str(e)}")
            return backup_file

    def _encrypt_backup(self, backup_file: Path) -> Path:
        """Encrypt backup file.

        Args:
            backup_file: Path to backup file

        Returns:
            Path to encrypted backup file
        """
        try:
            encrypted_file = backup_file.with_suffix(".enc")

            with open(backup_file, "rb") as f:
                data = f.read()

            encrypted_data = self.cipher.encrypt(data)

            with open(encrypted_file, "wb") as f:
                f.write(encrypted_data)

            backup_file.unlink()
            return encrypted_file

        except Exception as e:
            logger.error(f"Failed to encrypt backup: {str(e)}")
            return backup_file

    def _upload_to_s3(self, backup_file: Path, config: BackupConfig):
        """Upload backup to S3.

        Args:
            backup_file: Path to backup file
            config: Backup configuration
        """
        try:
            s3 = boto3.client("s3")

            # Generate S3 key
            s3_key = (
                f"{config.s3_prefix}/{backup_file.name}"
                if config.s3_prefix
                else backup_file.name
            )

            # Upload file
            s3.upload_file(str(backup_file), config.s3_bucket, s3_key)

            logger.info(f"Uploaded backup to s3://{config.s3_bucket}/{s3_key}")

        except Exception as e:
            logger.error(f"Failed to upload backup to S3: {str(e)}")

    def _cleanup_old_backups(self, config: BackupConfig):
        """Clean up old backups.

        Args:
            config: Backup configuration
        """
        try:
            backup_dir = Path(config.backup_dir)

            # Get all backup files
            backup_files = []
            for file in backup_dir.glob(f"{config.name}_*"):
                if file.suffix in [".gz", ".enc"]:
                    backup_files.append(file)

            # Sort by modification time
            backup_files.sort(key=lambda x: x.stat().st_mtime)

            # Remove old backups
            while len(backup_files) > config.retention_days:
                old_file = backup_files.pop(0)
                old_file.unlink()
                logger.info(f"Removed old backup {old_file}")

        except Exception as e:
            logger.error(f"Failed to clean up old backups: {str(e)}")

    def restore_backup(self, config_name: str, backup_file: str) -> bool:
        """Restore database from backup.

        Args:
            config_name: Configuration name
            backup_file: Path to backup file

        Returns:
            bool: True if restore was successful
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return False

            backup_path = Path(backup_file)

            # Download from S3 if needed
            if config.s3_bucket and not backup_path.exists():
                self._download_from_s3(backup_path, config)

            # Decrypt backup if needed
            if config.encryption:
                backup_path = self._decrypt_backup(backup_path)

            # Decompress backup if needed
            if config.compression:
                backup_path = self._decompress_backup(backup_path)

            # Restore backup based on database type
            if config.db_type == "postgresql":
                success = self._restore_postgresql(config, backup_path)
            elif config.db_type == "mysql":
                success = self._restore_mysql(config, backup_path)
            elif config.db_type == "sqlite":
                success = self._restore_sqlite(config, backup_path)
            else:
                logger.error(f"Unsupported database type: {config.db_type}")
                return False

            logger.info(f"Restored backup {backup_file}")
            return success

        except Exception as e:
            logger.error(f"Failed to restore backup {backup_file}: {str(e)}")
            return False

    def _download_from_s3(self, backup_file: Path, config: BackupConfig):
        """Download backup from S3.

        Args:
            backup_file: Path to backup file
            config: Backup configuration
        """
        try:
            s3 = boto3.client("s3")

            # Generate S3 key
            s3_key = (
                f"{config.s3_prefix}/{backup_file.name}"
                if config.s3_prefix
                else backup_file.name
            )

            # Download file
            s3.download_file(config.s3_bucket, s3_key, str(backup_file))

            logger.info(f"Downloaded backup from s3://{config.s3_bucket}/{s3_key}")

        except Exception as e:
            logger.error(f"Failed to download backup from S3: {str(e)}")

    def _decrypt_backup(self, backup_file: Path) -> Path:
        """Decrypt backup file.

        Args:
            backup_file: Path to backup file

        Returns:
            Path to decrypted backup file
        """
        try:
            decrypted_file = backup_file.with_suffix("")

            with open(backup_file, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self.cipher.decrypt(encrypted_data)

            with open(decrypted_file, "wb") as f:
                f.write(decrypted_data)

            backup_file.unlink()
            return decrypted_file

        except Exception as e:
            logger.error(f"Failed to decrypt backup: {str(e)}")
            return backup_file

    def _decompress_backup(self, backup_file: Path) -> Path:
        """Decompress backup file.

        Args:
            backup_file: Path to backup file

        Returns:
            Path to decompressed backup file
        """
        try:
            decompressed_file = backup_file.with_suffix("")

            with open(backup_file, "rb") as f_in:
                with open(decompressed_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            backup_file.unlink()
            return decompressed_file

        except Exception as e:
            logger.error(f"Failed to decompress backup: {str(e)}")
            return backup_file

    def _restore_postgresql(self, config: BackupConfig, backup_file: Path) -> bool:
        """Restore PostgreSQL backup.

        Args:
            config: Backup configuration
            backup_file: Path to backup file

        Returns:
            bool: True if restore was successful
        """
        try:
            # Parse database URL
            db_url = config.db_url.replace("postgresql://", "")
            user_pass, host_port_db = db_url.split("@")
            user, password = user_pass.split(":")
            host_port, db = host_port_db.split("/")
            host, port = host_port.split(":")

            # Restore backup using pg_restore
            cmd = [
                "pg_restore",
                f"--host={host}",
                f"--port={port}",
                f"--username={user}",
                f"--dbname={db}",
                f"--file={backup_file}",
                "--clean",
                "--if-exists",
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = password

            subprocess.run(cmd, env=env, check=True)
            return True

        except Exception as e:
            logger.error(f"Failed to restore PostgreSQL backup: {str(e)}")
            return False

    def _restore_mysql(self, config: BackupConfig, backup_file: Path) -> bool:
        """Restore MySQL backup.

        Args:
            config: Backup configuration
            backup_file: Path to backup file

        Returns:
            bool: True if restore was successful
        """
        try:
            # Parse database URL
            db_url = config.db_url.replace("mysql://", "")
            user_pass, host_port_db = db_url.split("@")
            user, password = user_pass.split(":")
            host_port, db = host_port_db.split("/")
            host, port = host_port.split(":")

            # Restore backup using mysql
            cmd = [
                "mysql",
                f"--host={host}",
                f"--port={port}",
                f"--user={user}",
                f"--password={password}",
                db,
                f"--execute=source {backup_file}",
            ]

            subprocess.run(cmd, check=True)
            return True

        except Exception as e:
            logger.error(f"Failed to restore MySQL backup: {str(e)}")
            return False

    def _restore_sqlite(self, config: BackupConfig, backup_file: Path) -> bool:
        """Restore SQLite backup.

        Args:
            config: Backup configuration
            backup_file: Path to backup file

        Returns:
            bool: True if restore was successful
        """
        try:
            # Parse database URL
            db_path = config.db_url.replace("sqlite:///", "")

            # Restore backup by copying database file
            shutil.copy2(backup_file, db_path)
            return True

        except Exception as e:
            logger.error(f"Failed to restore SQLite backup: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    manager = BackupManager()

    # Create backup configuration
    config = BackupConfig(
        name="main_db",
        db_type="postgresql",
        db_url="postgresql://user:password@localhost:5432/mydb",
        backup_dir="backups",
        schedule="0 0 * * *",  # Daily at midnight
        retention_days=30,
        compression=True,
        encryption=True,
        s3_bucket="my-backups",
        s3_prefix="database",
        description="Main database backup",
    )
    manager.create_config(config)

    # Create backup
    backup_file = manager.create_backup("main_db")
    if backup_file:
        print(f"Created backup: {backup_file}")

        # Restore backup
        if manager.restore_backup("main_db", backup_file):
            print("Restored backup successfully")
