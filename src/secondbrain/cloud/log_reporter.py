"""
Enhanced log reporter with email delivery for cloud operations.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
from fpdf import FPDF
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend

logger = logging.getLogger(__name__)


class BackupLogReport:
    """Manages detailed logging and report generation for cloud operations."""

    def __init__(
        self, report_dir: str = "phantom_reports", email_config: Optional[Dict] = None
    ):
        """
        Initialize log reporter.

        Args:
            report_dir: Directory to store reports
            email_config: Email configuration dictionary containing SMTP settings
        """
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.entries: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.latest_report_path: Optional[str] = None
        self.email_config = email_config or {}

        # Statistics
        self.stats = {
            "total_backups": 0,
            "successful_backups": 0,
            "failed_backups": 0,
            "dns_checks": 0,
            "dns_updates": 0,
        }

    def log_event(
        self, event_type: str, message: str, status: str = "INFO", details: Dict = None
    ):
        """
        Log an event with details.

        Args:
            event_type: Type of event (backup, dns, etc.)
            message: Event message
            status: Event status (INFO, ERROR, etc.)
            details: Additional event details
        """
        timestamp = datetime.now()

        entry = {
            "timestamp": timestamp.isoformat(),
            "type": event_type,
            "message": message,
            "status": status,
            "details": details or {},
        }

        self.entries.append(entry)
        logger.info(f"[{event_type}] {message}")

        # Update statistics
        if event_type == "backup":
            self.stats["total_backups"] += 1
            if status == "SUCCESS":
                self.stats["successful_backups"] += 1
            elif status == "ERROR":
                self.stats["failed_backups"] += 1
        elif event_type == "dns":
            self.stats["dns_checks"] += 1
            if "update" in message.lower():
                self.stats["dns_updates"] += 1

    def _generate_charts(self) -> List[str]:
        """Generate charts for the report."""
        chart_files = []

        try:
            # Backup Status Pie Chart
            plt.figure(figsize=(8, 6))
            labels = ["Successful", "Failed"]
            sizes = [self.stats["successful_backups"], self.stats["failed_backups"]]
            colors = ["#2ecc71", "#e74c3c"]

            plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%")
            plt.title("Backup Status Distribution")

            chart_path = self.report_dir / "backup_status_chart.png"
            plt.savefig(chart_path)
            plt.close()

            chart_files.append(str(chart_path))

            # DNS Activity Bar Chart
            plt.figure(figsize=(8, 6))
            activities = ["Checks", "Updates"]
            counts = [self.stats["dns_checks"], self.stats["dns_updates"]]

            plt.bar(activities, counts, color=["#3498db", "#9b59b6"])
            plt.title("DNS Activity Summary")
            plt.ylabel("Count")

            chart_path = self.report_dir / "dns_activity_chart.png"
            plt.savefig(chart_path)
            plt.close()

            chart_files.append(str(chart_path))

        except Exception as e:
            logger.error(f"Failed to generate charts: {e}")

        return chart_files

    def generate_report(self) -> str:
        """Generate PDF report with charts."""
        try:
            # Generate charts
            chart_files = self._generate_charts()

            # Create PDF
            pdf = FPDF()
            pdf.add_page()

            # Title
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "SecondBrain Cloud Operations Report", ln=True, align="C")
            pdf.ln(10)

            # Summary
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Summary", ln=True)
            pdf.set_font("Arial", "", 10)

            duration = datetime.now() - self.start_time
            pdf.multi_cell(
                0,
                10,
                f"""
            Report Period: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Duration: {duration.total_seconds() / 60:.1f} minutes
            Total Backups: {self.stats['total_backups']}
            Successful Backups: {self.stats['successful_backups']}
            Failed Backups: {self.stats['failed_backups']}
            DNS Checks: {self.stats['dns_checks']}
            DNS Updates: {self.stats['dns_updates']}
            """,
            )

            # Add charts
            for chart_file in chart_files:
                pdf.add_page()
                pdf.image(chart_file, x=10, y=30, w=190)

            # Detailed Log
            pdf.add_page()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Detailed Log", ln=True)
            pdf.set_font("Arial", "", 10)

            for entry in self.entries:
                timestamp = datetime.fromisoformat(entry["timestamp"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                pdf.multi_cell(
                    0,
                    10,
                    f"""
                Time: {timestamp}
                Type: {entry['type']}
                Status: {entry['status']}
                Message: {entry['message']}
                """,
                )
                if entry["details"]:
                    pdf.multi_cell(
                        0, 10, f"Details: {json.dumps(entry['details'], indent=2)}"
                    )
                pdf.ln(5)

            # Save report
            report_path = (
                self.report_dir
                / f"cloud_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            pdf.output(str(report_path))

            # Cleanup charts
            for chart_file in chart_files:
                Path(chart_file).unlink()

            self.latest_report_path = str(report_path)
            logger.info(f"Report generated: {report_path}")

            # Send email if configured
            if self.email_config:
                self.email_report()

            return str(report_path)

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return ""

    def email_report(self) -> bool:
        """Email the generated report."""
        if not self.latest_report_path or not self.email_config:
            logger.error(
                "Cannot send email: No report generated or email not configured"
            )
            return False

        try:
            msg = MIMEMultipart()
            msg["Subject"] = (
                f'SecondBrain Cloud Operations Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            )
            msg["From"] = self.email_config["from_email"]
            msg["To"] = self.email_config["to_email"]

            # Add HTML body
            html_body = f"""
            <html>
                <body>
                    <h2>SecondBrain Cloud Operations Report</h2>
                    <p>Report Period: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <h3>Summary:</h3>
                    <ul>
                        <li>Total Backups: {self.stats['total_backups']}</li>
                        <li>Successful Backups: {self.stats['successful_backups']}</li>
                        <li>Failed Backups: {self.stats['failed_backups']}</li>
                        <li>DNS Checks: {self.stats['dns_checks']}</li>
                        <li>DNS Updates: {self.stats['dns_updates']}</li>
                    </ul>
                    <p>Please see the attached PDF for detailed information.</p>
                </body>
            </html>
            """
            msg.attach(MIMEText(html_body, "html"))

            # Attach PDF report
            with open(self.latest_report_path, "rb") as f:
                pdf = MIMEApplication(f.read(), _subtype="pdf")
                pdf.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=os.path.basename(self.latest_report_path),
                )
                msg.attach(pdf)

            # Send email
            with smtplib.SMTP_SSL(
                self.email_config["smtp_server"], self.email_config["smtp_port"]
            ) as server:
                server.login(
                    self.email_config["smtp_user"], self.email_config["smtp_pass"]
                )
                server.send_message(msg)

            logger.info("Report email sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
