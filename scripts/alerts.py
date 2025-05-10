"""
Alert and notification system for SecondBrain Dashboard
"""
import smtplib
import logging
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
import socket

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self, alert_config_file: Path):
        self.alert_config_file = alert_config_file
        self.alert_history_file = alert_config_file.parent / 'alert_history.json'
        self.load_config()
        self.load_history()
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def load_config(self) -> None:
        """Load alert configuration."""
        try:
            with open(self.alert_config_file) as f:
                self.config = json.load(f)
        except FileNotFoundError:
            logger.warning("Alert config not found, using defaults")
            self.config = {
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'from_addr': '',
                    'to_addrs': []
                },
                'cooldown_minutes': 30,
                'alert_levels': {
                    'critical': {'threshold': 90, 'cooldown_minutes': 30},
                    'warning': {'threshold': 75, 'cooldown_minutes': 60},
                    'info': {'threshold': 50, 'cooldown_minutes': 120}
                }
            }
            self.save_config()

    def save_config(self) -> None:
        """Save alert configuration."""
        with open(self.alert_config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def load_history(self) -> None:
        """Load alert history."""
        try:
            with open(self.alert_history_file) as f:
                self.history = json.load(f)
        except FileNotFoundError:
            self.history = {'alerts': []}
            self.save_history()

    def save_history(self) -> None:
        """Save alert history."""
        with open(self.alert_history_file, 'w') as f:
            json.dump(self.history, f, indent=4)

    def can_send_alert(self, alert_type: str, resource: str) -> bool:
        """Check if an alert can be sent based on cooldown period."""
        now = datetime.now()
        cooldown = self.config['alert_levels'].get(
            alert_type, {}).get('cooldown_minutes', self.config['cooldown_minutes'])

        for alert in reversed(self.history['alerts']):
            if (alert['type'] == alert_type and 
                alert['resource'] == resource and 
                (now - datetime.fromisoformat(alert['timestamp'])) < timedelta(minutes=cooldown)):
                return False
        return True

    def send_email_alert(self, subject: str, body: str) -> bool:
        """Send email alert with retry logic."""
        if not self.config['email']['enabled']:
            return False

        retries = 0
        while retries < self.max_retries:
            try:
                msg = MIMEMultipart()
                msg['From'] = self.config['email']['from_addr']
                msg['To'] = ', '.join(self.config['email']['to_addrs'])
                msg['Subject'] = f"SecondBrain Alert: {subject}"
                msg.attach(MIMEText(body, 'plain'))

                with smtplib.SMTP(self.config['email']['smtp_server'], 
                                self.config['email']['smtp_port'], 
                                timeout=30) as server:  # Add timeout
                    server.starttls()
                    server.login(self.config['email']['username'], 
                               self.config['email']['password'])
                    server.send_message(msg)
                return True
            except (socket.timeout, socket.gaierror, ConnectionError) as e:
                retries += 1
                if retries < self.max_retries:
                    logger.warning(f"Network error while sending email (attempt {retries}): {e}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to send email after {self.max_retries} attempts: {e}")
                    return False
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
                return False
        return False

    def process_alerts(self, system_stats: Dict) -> List[Dict]:
        """Process system stats and generate alerts."""
        alerts = []
        
        # Check CPU usage
        if system_stats['cpu_percent'] >= self.config['alert_levels']['critical']['threshold']:
            if self.can_send_alert('critical', 'cpu'):
                alerts.append(self._create_alert('critical', 'cpu', 
                    f"CPU usage critical: {system_stats['cpu_percent']}%"))
        elif system_stats['cpu_percent'] >= self.config['alert_levels']['warning']['threshold']:
            if self.can_send_alert('warning', 'cpu'):
                alerts.append(self._create_alert('warning', 'cpu', 
                    f"CPU usage high: {system_stats['cpu_percent']}%"))

        # Check Memory usage
        if system_stats['memory_percent'] >= self.config['alert_levels']['critical']['threshold']:
            if self.can_send_alert('critical', 'memory'):
                alerts.append(self._create_alert('critical', 'memory', 
                    f"Memory usage critical: {system_stats['memory_percent']}%"))
        elif system_stats['memory_percent'] >= self.config['alert_levels']['warning']['threshold']:
            if self.can_send_alert('warning', 'memory'):
                alerts.append(self._create_alert('warning', 'memory', 
                    f"Memory usage high: {system_stats['memory_percent']}%"))

        # Check Disk usage
        if system_stats['disk_percent'] >= self.config['alert_levels']['critical']['threshold']:
            if self.can_send_alert('critical', 'disk'):
                alerts.append(self._create_alert('critical', 'disk', 
                    f"Disk usage critical: {system_stats['disk_percent']}%"))
        elif system_stats['disk_percent'] >= self.config['alert_levels']['warning']['threshold']:
            if self.can_send_alert('warning', 'disk'):
                alerts.append(self._create_alert('warning', 'disk', 
                    f"Disk usage high: {system_stats['disk_percent']}%"))

        # Process and store alerts
        for alert in alerts:
            self.history['alerts'].append(alert)
            if self.config['email']['enabled']:
                self.send_email_alert(
                    f"{alert['type'].upper()} - {alert['resource'].upper()}", 
                    alert['message']
                )

        # Keep only last 1000 alerts
        if len(self.history['alerts']) > 1000:
            self.history['alerts'] = self.history['alerts'][-1000:]
        
        self.save_history()
        return alerts

    def _create_alert(self, alert_type: str, resource: str, message: str) -> Dict:
        """Create an alert entry."""
        return {
            'type': alert_type,
            'resource': resource,
            'message': message,
            'timestamp': datetime.now().isoformat()
        } 