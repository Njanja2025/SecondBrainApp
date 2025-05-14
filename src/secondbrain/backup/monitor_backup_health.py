"""
Backup health monitoring script for the Companion Journaling Backup System.
Monitors backup health, sends notifications, and generates reports.
"""

import os
import json
import logging
import smtplib
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import dropbox
from dropbox.exceptions import ApiError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/secondbrain_backup_health.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class BackupHealthMonitor:
    def __init__(self):
        self.cloud_config = self._load_config("cloud_config.json")
        self.backup_root = Path(
            os.path.expanduser(self.cloud_config["local_vault_path"])
        )
        self.db_path = self.backup_root / "backup_health.db"
        self._init_database()

    def _load_config(self, config_file):
        config_path = Path(__file__).parent / config_file
        with open(config_path) as f:
            return json.load(f)

    def _init_database(self):
        """Initialize SQLite database for health monitoring."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Create tables if they don't exist
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS backup_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_file TEXT NOT NULL,
                backup_date TIMESTAMP NOT NULL,
                file_size INTEGER NOT NULL,
                hash TEXT NOT NULL,
                cloud_sync_status BOOLEAN NOT NULL,
                verification_status BOOLEAN NOT NULL,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def record_backup_health(self, backup_file, health_data):
        """Record backup health metrics in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                INSERT INTO backup_health (
                    backup_file, backup_date, file_size, hash,
                    cloud_sync_status, verification_status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(backup_file),
                    datetime.fromtimestamp(backup_file.stat().st_mtime),
                    backup_file.stat().st_size,
                    health_data.get("hash", ""),
                    health_data.get("cloud_sync_ok", False),
                    health_data.get("verification_ok", False),
                    health_data.get("error", ""),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error recording backup health: {e}")

    def check_backup_health(self, days=7):
        """Check health of recent backups and generate report."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            health_report = {
                "total_backups": 0,
                "successful_backups": 0,
                "failed_backups": 0,
                "cloud_sync_issues": 0,
                "verification_issues": 0,
                "details": [],
            }

            for backup_file in self.backup_root.glob("*.zip"):
                backup_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if backup_date < cutoff_date:
                    continue

                health_report["total_backups"] += 1
                backup_health = {
                    "file": str(backup_file),
                    "date": backup_date,
                    "size_mb": backup_file.stat().st_size / (1024 * 1024),
                    "status": "unknown",
                }

                # Check cloud sync
                try:
                    dbx = dropbox.Dropbox(self.cloud_config["access_token"])
                    cloud_path = f"{self.cloud_config['cloud_path']}/{backup_file.name}"
                    metadata = dbx.files_get_metadata(cloud_path)

                    if metadata.size != backup_file.stat().st_size:
                        health_report["cloud_sync_issues"] += 1
                        backup_health["status"] = "cloud_sync_failed"
                    else:
                        backup_health["status"] = "success"
                        health_report["successful_backups"] += 1

                except ApiError:
                    health_report["cloud_sync_issues"] += 1
                    backup_health["status"] = "cloud_sync_failed"

                health_report["details"].append(backup_health)

            # Record health metrics
            self.record_backup_health(
                backup_file,
                {
                    "cloud_sync_ok": backup_health["status"] == "success",
                    "verification_ok": True,
                    "hash": "",  # Add hash if available
                },
            )

            return health_report

        except Exception as e:
            logger.error(f"Error checking backup health: {e}")
            return None

    def send_health_report(self, report):
        """Send health report via email."""
        if not report:
            return False

        try:
            # Create email message
            msg = MIMEMultipart()
            msg["Subject"] = (
                f"SecondBrain Backup Health Report - {datetime.now().strftime('%Y-%m-%d')}"
            )
            msg["From"] = self.cloud_config.get("email_from", "backup@secondbrain.ai")
            msg["To"] = self.cloud_config.get("email_to", "user@example.com")

            # Create email body
            body = f"""
            SecondBrain Backup Health Report
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Summary:
            - Total Backups: {report['total_backups']}
            - Successful: {report['successful_backups']}
            - Failed: {report['failed_backups']}
            - Cloud Sync Issues: {report['cloud_sync_issues']}
            - Verification Issues: {report['verification_issues']}
            
            Detailed Status:
            """

            for backup in report["details"]:
                body += f"\n{backup['file']}:"
                body += f"\n  Date: {backup['date']}"
                body += f"\n  Size: {backup['size_mb']:.2f}MB"
                body += f"\n  Status: {backup['status']}\n"

            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(
                self.cloud_config.get("smtp_server", "smtp.gmail.com"),
                self.cloud_config.get("smtp_port", 587),
            ) as server:
                server.starttls()
                server.login(
                    self.cloud_config.get("smtp_username", ""),
                    self.cloud_config.get("smtp_password", ""),
                )
                server.send_message(msg)

            logger.info("Health report sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending health report: {e}")
            return False


def main():
    """Run backup health monitoring."""
    monitor = BackupHealthMonitor()

    logger.info("Starting backup health monitoring...")

    # Check backup health
    report = monitor.check_backup_health()
    if report:
        # Send report
        if monitor.send_health_report(report):
            logger.info("Health monitoring completed successfully")
            return 0
        else:
            logger.error("Failed to send health report")
            return 1
    else:
        logger.error("Failed to generate health report")
        return 1


if __name__ == "__main__":
    exit(main())
