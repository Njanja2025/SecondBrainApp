#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import subprocess
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import threading
import queue
import smtplib
from email.mime.text import MIMEText
import requests
import paramiko

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)

class AdvancedAutomation:
    def __init__(self, config_path='automation_config.json'):
        self.config = self.load_config(config_path)
        self.task_queue = queue.Queue()
        self.worker_threads = []
        self.running = True
        self.ssh_client = None

    def load_config(self, config_path):
        """Load automation configuration."""
        default_config = {
            'deployment': {
                'local': {
                    'enabled': True,
                    'repo_path': '/Users/mac/Documents/Applications/BaddyAgent.app/Contents/Resources/SecondBrainApp',
                    'backup_path': 'backups'
                },
                'remote': {
                    'enabled': False,
                    'host': '',
                    'user': '',
                    'repo_path': '/opt/baddyagent',
                    'backup_path': '/var/backups/baddyagent',
                    'ssh_key': '~/.ssh/id_rsa'
                }
            },
            'max_workers': 4,
            'tasks': {
                'backup': {
                    'interval': 3600,
                    'retention_days': 7
                },
                'cleanup': {
                    'interval': 86400,
                    'max_log_size_mb': 100
                },
                'sync': {
                    'interval': 300,
                    'remote': 'origin',
                    'branch': 'main'
                },
                'optimize': {
                    'interval': 86400,
                    'vacuum': True,
                    'analyze': True,
                    'reindex': True
                },
                'verify': {
                    'interval': 3600,
                    'integrity_check': True,
                    'performance_check': True
                }
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
                },
                'slack': {
                    'enabled': False,
                    'webhook_url': '',
                    'channel': ''
                }
            }
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return {**default_config, **json.load(f)}
        return default_config

    def setup_ssh(self):
        """Set up SSH connection for remote deployment."""
        if not self.config['deployment']['remote']['enabled']:
            return

        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh_key = os.path.expanduser(self.config['deployment']['remote']['ssh_key'])
            self.ssh_client.connect(
                hostname=self.config['deployment']['remote']['host'],
                username=self.config['deployment']['remote']['user'],
                key_filename=ssh_key
            )
            logging.info("SSH connection established")
        except Exception as e:
            logging.error(f"Failed to establish SSH connection: {e}")
            raise

    def execute_remote_command(self, command):
        """Execute a command on the remote server."""
        if not self.config['deployment']['remote']['enabled']:
            return None

        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            return {
                'stdout': stdout.read().decode(),
                'stderr': stderr.read().decode(),
                'exit_code': stdout.channel.recv_exit_status()
            }
        except Exception as e:
            logging.error(f"Failed to execute remote command: {e}")
            return None

    def setup_environment(self):
        """Set up the automation environment."""
        if self.config['deployment']['remote']['enabled']:
            self.setup_ssh()
            remote_path = self.config['deployment']['remote']['repo_path']
            self.execute_remote_command(f"mkdir -p {remote_path}")
            self.execute_remote_command(f"mkdir -p {self.config['deployment']['remote']['backup_path']}")
        else:
            # Create necessary directories
            os.makedirs(self.config['deployment']['local']['backup_path'], exist_ok=True)
            
            # Initialize git if needed
            if not os.path.exists(os.path.join(self.config['deployment']['local']['repo_path'], '.git')):
                subprocess.run(['git', 'init'], cwd=self.config['deployment']['local']['repo_path'])
            
            # Set up virtual environment
            venv_path = os.path.join(self.config['deployment']['local']['repo_path'], 'venv')
            if not os.path.exists(venv_path):
                subprocess.run([sys.executable, '-m', 'venv', venv_path])
            
            # Install requirements
            requirements_path = os.path.join(self.config['deployment']['local']['repo_path'], 'requirements.txt')
            if os.path.exists(requirements_path):
                subprocess.run([
                    os.path.join(venv_path, 'bin', 'pip'),
                    'install', '-r', requirements_path
                ])

    def backup_database(self):
        """Create a backup of the database."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.config['deployment']['remote']['enabled']:
            remote_db = os.path.join(self.config['deployment']['remote']['repo_path'], 'brain', 'memory_engine.db')
            backup_file = os.path.join(
                self.config['deployment']['remote']['backup_path'],
                f'memory_engine_{timestamp}.db'
            )
            
            result = self.execute_remote_command(f"cp {remote_db} {backup_file}")
            if result and result['exit_code'] == 0:
                logging.info(f"Remote database backed up to {backup_file}")
                return True
            else:
                logging.error("Remote backup failed")
                return False
        else:
            backup_file = os.path.join(
                self.config['deployment']['local']['backup_path'],
                f'memory_engine_{timestamp}.db'
            )
            
            try:
                shutil.copy2(
                    os.path.join(self.config['deployment']['local']['repo_path'], 'brain', 'memory_engine.db'),
                    backup_file
                )
                logging.info(f"Local database backed up to {backup_file}")
                return True
            except Exception as e:
                logging.error(f"Local backup failed: {e}")
                return False

    def cleanup_old_backups(self):
        """Clean up old backups."""
        retention_days = self.config['tasks']['backup']['retention_days']
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        if self.config['deployment']['remote']['enabled']:
            backup_path = self.config['deployment']['remote']['backup_path']
            result = self.execute_remote_command(
                f"find {backup_path} -name 'memory_engine_*.db' -mtime +{retention_days} -delete"
            )
            if result and result['exit_code'] == 0:
                logging.info("Remote backups cleaned up")
            else:
                logging.error("Failed to clean up remote backups")
        else:
            for backup_file in os.listdir(self.config['deployment']['local']['backup_path']):
                if backup_file.startswith('memory_engine_'):
                    file_path = os.path.join(self.config['deployment']['local']['backup_path'], backup_file)
                    file_date = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_date < cutoff_date:
                        try:
                            os.remove(file_path)
                            logging.info(f"Removed old backup: {backup_file}")
                        except Exception as e:
                            logging.error(f"Failed to remove backup {backup_file}: {e}")

    def cleanup_logs(self):
        """Clean up old log files."""
        max_size = self.config['tasks']['cleanup']['max_log_size_mb'] * 1024 * 1024
        
        if self.config['deployment']['remote']['enabled']:
            result = self.execute_remote_command(
                f"find /var/log/baddyagent -name '*.log' -size +{max_size}c -exec mv {{}} {{}}.{{date +%Y%m%d_%H%M%S}} \;"
            )
            if result and result['exit_code'] == 0:
                logging.info("Remote logs rotated")
            else:
                logging.error("Failed to rotate remote logs")
        else:
            for log_file in ['automation.log', 'performance.log']:
                if os.path.exists(log_file):
                    if os.path.getsize(log_file) > max_size:
                        try:
                            shutil.move(log_file, f"{log_file}.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                            logging.info(f"Rotated log file: {log_file}")
                        except Exception as e:
                            logging.error(f"Failed to rotate log {log_file}: {e}")

    def sync_with_remote(self):
        """Sync with remote repository."""
        if self.config['deployment']['remote']['enabled']:
            repo_path = self.config['deployment']['remote']['repo_path']
            commands = [
                f"cd {repo_path} && git fetch {self.config['tasks']['sync']['remote']}",
                f"cd {repo_path} && git reset --hard {self.config['tasks']['sync']['remote']}/{self.config['tasks']['sync']['branch']}",
                f"cd {repo_path} && git clean -fd"
            ]
            
            for cmd in commands:
                result = self.execute_remote_command(cmd)
                if not result or result['exit_code'] != 0:
                    logging.error(f"Remote sync failed: {result['stderr'] if result else 'Unknown error'}")
                    return False
            
            logging.info("Successfully synced remote repository")
            return True
        else:
            try:
                # Fetch latest changes
                subprocess.run([
                    'git', 'fetch',
                    self.config['tasks']['sync']['remote']
                ], cwd=self.config['deployment']['local']['repo_path'], check=True)
                
                # Reset to remote
                subprocess.run([
                    'git', 'reset', '--hard',
                    f"{self.config['tasks']['sync']['remote']}/{self.config['tasks']['sync']['branch']}"
                ], cwd=self.config['deployment']['local']['repo_path'], check=True)
                
                # Clean untracked files
                subprocess.run([
                    'git', 'clean', '-fd'
                ], cwd=self.config['deployment']['local']['repo_path'], check=True)
                
                logging.info("Successfully synced local repository")
                return True
            except subprocess.CalledProcessError as e:
                logging.error(f"Local sync failed: {e}")
                return False

    def optimize_database(self):
        """Optimize database performance."""
        try:
            import sqlite3
            
            if self.config['deployment']['remote']['enabled']:
                db_path = os.path.join(self.config['deployment']['remote']['repo_path'], 'brain', 'memory_engine.db')
                commands = []
                
                if self.config['tasks']['optimize']['vacuum']:
                    commands.append(f"sqlite3 {db_path} 'VACUUM;'")
                
                if self.config['tasks']['optimize']['analyze']:
                    commands.append(f"sqlite3 {db_path} 'ANALYZE;'")
                
                if self.config['tasks']['optimize']['reindex']:
                    commands.append(f"sqlite3 {db_path} 'REINDEX;'")
                
                for cmd in commands:
                    result = self.execute_remote_command(cmd)
                    if not result or result['exit_code'] != 0:
                        logging.error(f"Remote optimization failed: {result['stderr'] if result else 'Unknown error'}")
                        return False
                
                logging.info("Remote database optimization completed")
                return True
            else:
                conn = sqlite3.connect(
                    os.path.join(self.config['deployment']['local']['repo_path'], 'brain', 'memory_engine.db')
                )
                cursor = conn.cursor()
                
                if self.config['tasks']['optimize']['vacuum']:
                    cursor.execute("VACUUM")
                
                if self.config['tasks']['optimize']['analyze']:
                    cursor.execute("ANALYZE")
                
                if self.config['tasks']['optimize']['reindex']:
                    cursor.execute("REINDEX")
                
                conn.close()
                logging.info("Local database optimization completed")
                return True
        except Exception as e:
            logging.error(f"Database optimization failed: {e}")
            return False

    def verify_database(self):
        """Verify database integrity and performance."""
        try:
            import sqlite3
            
            if self.config['deployment']['remote']['enabled']:
                db_path = os.path.join(self.config['deployment']['remote']['repo_path'], 'brain', 'memory_engine.db')
                commands = []
                
                if self.config['tasks']['verify']['integrity_check']:
                    commands.append(f"sqlite3 {db_path} 'PRAGMA integrity_check;'")
                
                if self.config['tasks']['verify']['performance_check']:
                    commands.extend([
                        f"sqlite3 {db_path} 'PRAGMA index_list;'",
                        f"sqlite3 {db_path} \"SELECT * FROM sqlite_master WHERE type='table' AND name='sqlite_stat1';\""
                    ])
                
                for cmd in commands:
                    result = self.execute_remote_command(cmd)
                    if not result or result['exit_code'] != 0:
                        logging.error(f"Remote verification failed: {result['stderr'] if result else 'Unknown error'}")
                        return False
                
                logging.info("Remote database verification completed")
                return True
            else:
                conn = sqlite3.connect(
                    os.path.join(self.config['deployment']['local']['repo_path'], 'brain', 'memory_engine.db')
                )
                cursor = conn.cursor()
                
                if self.config['tasks']['verify']['integrity_check']:
                    cursor.execute("PRAGMA integrity_check")
                    integrity = cursor.fetchone()[0]
                    if integrity != 'ok':
                        logging.error(f"Database integrity check failed: {integrity}")
                        return False
                
                if self.config['tasks']['verify']['performance_check']:
                    # Check index usage
                    cursor.execute("PRAGMA index_list")
                    indexes = cursor.fetchall()
                    
                    # Check for long-running transactions
                    cursor.execute("""
                        SELECT * FROM sqlite_master 
                        WHERE type='table' AND name='sqlite_stat1'
                    """)
                    stats = cursor.fetchone()
                    
                    if not stats:
                        logging.warning("Database statistics not available")
                
                conn.close()
                logging.info("Local database verification completed")
                return True
        except Exception as e:
            logging.error(f"Database verification failed: {e}")
            return False

    def send_notification(self, message, status):
        """Send notification through configured channels."""
        if self.config['notifications']['email']['enabled']:
            self.send_email_notification(message, status)
        
        if self.config['notifications']['webhook']['enabled']:
            self.send_webhook_notification(message, status)
        
        if self.config['notifications']['slack']['enabled']:
            self.send_slack_notification(message, status)

    def send_email_notification(self, message, status):
        """Send email notification."""
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"Automation {status}"
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

    def send_slack_notification(self, message, status):
        """Send Slack notification."""
        try:
            slack_message = {
                'channel': self.config['notifications']['slack']['channel'],
                'text': f"""
                *Automation {status}*
                • Message: {message}
                • Time: {datetime.now().isoformat()}
                """
            }
            
            response = requests.post(
                self.config['notifications']['slack']['webhook_url'],
                json=slack_message
            )
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to send Slack notification: {e}")

    def worker(self):
        """Worker thread to process tasks."""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task['type'] == 'backup':
                    self.backup_database()
                elif task['type'] == 'cleanup':
                    self.cleanup_old_backups()
                    self.cleanup_logs()
                elif task['type'] == 'sync':
                    self.sync_with_remote()
                elif task['type'] == 'optimize':
                    self.optimize_database()
                elif task['type'] == 'verify':
                    self.verify_database()
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Worker error: {e}")

    def schedule_tasks(self):
        """Schedule recurring tasks."""
        while self.running:
            current_time = time.time()
            
            # Schedule backup
            if current_time % self.config['tasks']['backup']['interval'] < 60:
                self.task_queue.put({'type': 'backup'})
            
            # Schedule cleanup
            if current_time % self.config['tasks']['cleanup']['interval'] < 60:
                self.task_queue.put({'type': 'cleanup'})
            
            # Schedule sync
            if current_time % self.config['tasks']['sync']['interval'] < 60:
                self.task_queue.put({'type': 'sync'})
            
            # Schedule optimize
            if current_time % self.config['tasks']['optimize']['interval'] < 60:
                self.task_queue.put({'type': 'optimize'})
            
            # Schedule verify
            if current_time % self.config['tasks']['verify']['interval'] < 60:
                self.task_queue.put({'type': 'verify'})
            
            time.sleep(60)  # Check every minute

    def start(self):
        """Start the automation system."""
        logging.info("Starting advanced automation...")
        
        # Set up environment
        self.setup_environment()
        
        # Start worker threads
        for _ in range(self.config['max_workers']):
            thread = threading.Thread(target=self.worker)
            thread.start()
            self.worker_threads.append(thread)
        
        # Start task scheduler
        scheduler_thread = threading.Thread(target=self.schedule_tasks)
        scheduler_thread.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the automation system."""
        logging.info("Stopping advanced automation...")
        self.running = False
        
        # Wait for tasks to complete
        self.task_queue.join()
        
        # Wait for worker threads
        for thread in self.worker_threads:
            thread.join()
        
        # Close SSH connection if open
        if self.ssh_client:
            self.ssh_client.close()
        
        logging.info("Automation stopped.")

def main():
    parser = argparse.ArgumentParser(description='Advanced Automation System')
    parser.add_argument('--config', default='automation_config.json',
                      help='Path to configuration file')
    args = parser.parse_args()
    
    automation = AdvancedAutomation(args.config)
    automation.start()

if __name__ == "__main__":
    main() 