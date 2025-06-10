#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import shutil
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import threading
import queue
import smtplib
from email.mime.text import MIMEText
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

class MemoryEngineBackup:
    def __init__(self, config_path='backup_config.json'):
        self.config = self.load_config(config_path)
        self.backup_queue = queue.Queue()
        self.running = True

    def load_config(self, config_path):
        """Load backup configuration."""
        default_config = {
            'db_path': '/Users/mac/Documents/Applications/BaddyAgent.app/Contents/Resources/SecondBrainApp/brain/memory_engine.db',
            'backup_path': 'backups',
            'schedule': {
                'full_backup': {
                    'interval_days': 7,
                    'retention_days': 30
                },
                'incremental_backup': {
                    'interval_hours': 24,
                    'retention_days': 7
                }
            },
            'compression': {
                'enabled': True,
                'format': 'zip'
            },
            'encryption': {
                'enabled': False,
                'key_file': ''
            },
            'verification': {
                'enabled': True,
                'checksum': True
            },
            'notifications': {
                'email': {
                    'enabled': False,
                    'smtp_server': '',
                    'smtp_port': 587,
                    'sender': '',
                    'recipients': []
                },
                'webhook': {
                    'enabled': False,
                    'url': '',
                    'headers': {}
                }
            }
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return {**default_config, **json.load(f)}
        return default_config

    def create_backup_dir(self):
        """Create backup directory structure."""
        os.makedirs(self.config['backup_path'], exist_ok=True)
        os.makedirs(os.path.join(self.config['backup_path'], 'full'), exist_ok=True)
        os.makedirs(os.path.join(self.config['backup_path'], 'incremental'), exist_ok=True)

    def get_last_backup_time(self, backup_type):
        """Get timestamp of last backup."""
        backup_dir = os.path.join(self.config['backup_path'], backup_type)
        if not os.path.exists(backup_dir):
            return None
        
        backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        if not backups:
            return None
        
        return max(os.path.getctime(os.path.join(backup_dir, f)) for f in backups)

    def should_backup(self, backup_type):
        """Check if backup should be performed."""
        last_backup = self.get_last_backup_time(backup_type)
        if not last_backup:
            return True
        
        if backup_type == 'full':
            interval = timedelta(days=self.config['schedule']['full_backup']['interval_days'])
        else:
            interval = timedelta(hours=self.config['schedule']['incremental_backup']['interval_hours'])
        
        return datetime.now() - datetime.fromtimestamp(last_backup) >= interval

    def create_full_backup(self):
        """Create a full backup of the database."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(
                self.config['backup_path'],
                'full',
                f'full_backup_{timestamp}.db'
            )
            
            # Copy database file
            shutil.copy2(self.config['db_path'], backup_file)
            
            # Compress if enabled
            if self.config['compression']['enabled']:
                if self.config['compression']['format'] == 'zip':
                    shutil.make_archive(backup_file, 'zip', os.path.dirname(backup_file), os.path.basename(backup_file))
                    os.remove(backup_file)
                    backup_file += '.zip'
            
            # Encrypt if enabled
            if self.config['encryption']['enabled']:
                self.encrypt_backup(backup_file)
            
            # Verify backup
            if self.config['verification']['enabled']:
                if not self.verify_backup(backup_file):
                    raise Exception("Backup verification failed")
            
            logging.info(f"Created full backup: {backup_file}")
            return backup_file
        except Exception as e:
            logging.error(f"Full backup failed: {e}")
            return None

    def create_incremental_backup(self):
        """Create an incremental backup of the database."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(
                self.config['backup_path'],
                'incremental',
                f'incremental_backup_{timestamp}.db'
            )
            
            # Get last backup time
            last_backup = self.get_last_backup_time('incremental')
            if not last_backup:
                logging.warning("No previous backup found, creating full backup instead")
                return self.create_full_backup()
            
            # Connect to database
            conn = sqlite3.connect(self.config['db_path'])
            cursor = conn.cursor()
            
            # Get changes since last backup
            cursor.execute("""
                SELECT * FROM memory_engine 
                WHERE timestamp > ?
            """, (datetime.fromtimestamp(last_backup).isoformat(),))
            
            changes = cursor.fetchall()
            conn.close()
            
            # Create backup file with changes
            with sqlite3.connect(backup_file) as backup_conn:
                backup_cursor = backup_conn.cursor()
                backup_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memory_engine (
                        id INTEGER PRIMARY KEY,
                        timestamp TEXT,
                        data TEXT
                    )
                """)
                backup_cursor.executemany(
                    "INSERT INTO memory_engine VALUES (?, ?, ?)",
                    changes
                )
                backup_conn.commit()
            
            # Compress if enabled
            if self.config['compression']['enabled']:
                if self.config['compression']['format'] == 'zip':
                    shutil.make_archive(backup_file, 'zip', os.path.dirname(backup_file), os.path.basename(backup_file))
                    os.remove(backup_file)
                    backup_file += '.zip'
            
            # Encrypt if enabled
            if self.config['encryption']['enabled']:
                self.encrypt_backup(backup_file)
            
            # Verify backup
            if self.config['verification']['enabled']:
                if not self.verify_backup(backup_file):
                    raise Exception("Backup verification failed")
            
            logging.info(f"Created incremental backup: {backup_file}")
            return backup_file
        except Exception as e:
            logging.error(f"Incremental backup failed: {e}")
            return None

    def encrypt_backup(self, backup_file):
        """Encrypt backup file."""
        try:
            import cryptography
            from cryptography.fernet import Fernet
            
            # Load encryption key
            with open(self.config['encryption']['key_file'], 'rb') as f:
                key = f.read()
            
            # Encrypt file
            fernet = Fernet(key)
            with open(backup_file, 'rb') as f:
                data = f.read()
            
            encrypted_data = fernet.encrypt(data)
            with open(backup_file, 'wb') as f:
                f.write(encrypted_data)
            
            logging.info(f"Encrypted backup: {backup_file}")
        except Exception as e:
            logging.error(f"Encryption failed: {e}")
            raise

    def verify_backup(self, backup_file):
        """Verify backup integrity."""
        try:
            # Check if file exists
            if not os.path.exists(backup_file):
                return False
            
            # Verify checksum if enabled
            if self.config['verification']['checksum']:
                import hashlib
                with open(backup_file, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                
                # Store checksum
                checksum_file = backup_file + '.sha256'
                with open(checksum_file, 'w') as f:
                    f.write(file_hash)
            
            # Try to open database
            if backup_file.endswith('.db'):
                conn = sqlite3.connect(backup_file)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM memory_engine")
                count = cursor.fetchone()[0]
                conn.close()
                
                if count < 0:
                    return False
            
            return True
        except Exception as e:
            logging.error(f"Verification failed: {e}")
            return False

    def cleanup_old_backups(self):
        """Clean up old backups."""
        try:
            # Clean up full backups
            full_retention = timedelta(days=self.config['schedule']['full_backup']['retention_days'])
            full_dir = os.path.join(self.config['backup_path'], 'full')
            if os.path.exists(full_dir):
                for file in os.listdir(full_dir):
                    file_path = os.path.join(full_dir, file)
                    if os.path.getctime(file_path) < (datetime.now() - full_retention).timestamp():
                        os.remove(file_path)
                        logging.info(f"Removed old full backup: {file}")
            
            # Clean up incremental backups
            inc_retention = timedelta(days=self.config['schedule']['incremental_backup']['retention_days'])
            inc_dir = os.path.join(self.config['backup_path'], 'incremental')
            if os.path.exists(inc_dir):
                for file in os.listdir(inc_dir):
                    file_path = os.path.join(inc_dir, file)
                    if os.path.getctime(file_path) < (datetime.now() - inc_retention).timestamp():
                        os.remove(file_path)
                        logging.info(f"Removed old incremental backup: {file}")
        except Exception as e:
            logging.error(f"Cleanup failed: {e}")

    def send_notification(self, message, status):
        """Send backup notification."""
        if self.config['notifications']['email']['enabled']:
            self.send_email_notification(message, status)
        
        if self.config['notifications']['webhook']['enabled']:
            self.send_webhook_notification(message, status)

    def send_email_notification(self, message, status):
        """Send email notification."""
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"Backup {status}"
            msg['From'] = self.config['notifications']['email']['sender']
            msg['To'] = ', '.join(self.config['notifications']['email']['recipients'])
            
            with smtplib.SMTP(
                self.config['notifications']['email']['smtp_server'],
                self.config['notifications']['email']['smtp_port']
            ) as server:
                server.starttls()
                server.send_message(msg)
        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")

    def send_webhook_notification(self, message, status):
        """Send webhook notification."""
        try:
            response = requests.post(
                self.config['notifications']['webhook']['url'],
                json={
                    'message': message,
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                },
                headers=self.config['notifications']['webhook']['headers']
            )
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to send webhook notification: {e}")

    def backup_worker(self):
        """Worker thread to process backups."""
        while self.running:
            try:
                backup_type = self.backup_queue.get(timeout=1)
                
                if backup_type == 'full':
                    backup_file = self.create_full_backup()
                else:
                    backup_file = self.create_incremental_backup()
                
                if backup_file:
                    self.send_notification(
                        f"Backup completed: {backup_file}",
                        "success"
                    )
                else:
                    self.send_notification(
                        "Backup failed",
                        "failed"
                    )
                
                self.backup_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Backup worker error: {e}")

    def start(self):
        """Start the backup system."""
        logging.info("Starting memory engine backup system...")
        
        # Create backup directories
        self.create_backup_dir()
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self.backup_worker)
        self.worker_thread.start()
        
        try:
            while True:
                # Check for full backup
                if self.should_backup('full'):
                    self.backup_queue.put('full')
                
                # Check for incremental backup
                if self.should_backup('incremental'):
                    self.backup_queue.put('incremental')
                
                # Cleanup old backups
                self.cleanup_old_backups()
                
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the backup system."""
        logging.info("Stopping memory engine backup system...")
        self.running = False
        
        # Wait for queue to be processed
        self.backup_queue.join()
        
        # Wait for worker thread
        self.worker_thread.join()
        
        logging.info("Backup system stopped.")

def main():
    parser = argparse.ArgumentParser(description='Memory Engine Backup')
    parser.add_argument('--config', default='backup_config.json',
                      help='Path to configuration file')
    args = parser.parse_args()
    
    backup = MemoryEngineBackup(args.config)
    backup.start()

if __name__ == "__main__":
    main() 