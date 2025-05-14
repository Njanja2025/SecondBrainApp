import smtplib
import aiohttp
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class NotificationChannel:
    """Base class for notification channels."""

    async def send(self, message: str, subject: str = None, **kwargs) -> bool:
        raise NotImplementedError


class EmailNotifier(NotificationChannel):
    """Email notification channel."""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL")
        self.to_emails = os.getenv("TO_EMAILS", "").split(",")

    async def send(self, message: str, subject: str = None, **kwargs) -> bool:
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)
            msg["Subject"] = subject or "SecondBrain Alert"

            msg.attach(MIMEText(message, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


class SlackNotifier(NotificationChannel):
    """Slack notification channel."""

    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.channel = os.getenv("SLACK_CHANNEL", "#alerts")

    async def send(self, message: str, subject: str = None, **kwargs) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "channel": self.channel,
                    "username": "SecondBrain",
                    "text": f"*{subject or 'Alert'}*\n{message}",
                    "icon_emoji": ":brain:",
                }

                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class DiscordNotifier(NotificationChannel):
    """Discord notification channel."""

    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    async def send(self, message: str, subject: str = None, **kwargs) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "content": f"**{subject or 'Alert'}**\n{message}",
                    "username": "SecondBrain",
                    "avatar_url": "https://example.com/brain-icon.png",
                }

                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status == 204
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False


class NotificationManager:
    """Manage multiple notification channels."""

    def __init__(self):
        self.channels: List[NotificationChannel] = []
        self.setup_channels()

    def setup_channels(self):
        """Initialize enabled notification channels."""
        if os.getenv("EMAIL_ENABLED", "false").lower() == "true":
            self.channels.append(EmailNotifier())

        if os.getenv("SLACK_ENABLED", "false").lower() == "true":
            self.channels.append(SlackNotifier())

        if os.getenv("DISCORD_ENABLED", "false").lower() == "true":
            self.channels.append(DiscordNotifier())

    async def notify(
        self,
        message: str,
        subject: str = None,
        level: str = "INFO",
        metadata: Optional[Dict] = None,
    ) -> Dict[str, bool]:
        """Send notification through all channels."""
        results = {}
        timestamp = datetime.utcnow().isoformat()

        formatted_message = (
            f"Time: {timestamp}\n" f"Level: {level}\n" f"Message: {message}\n"
        )

        if metadata:
            formatted_message += f"Details: {json.dumps(metadata, indent=2)}"

        for channel in self.channels:
            channel_name = channel.__class__.__name__
            try:
                success = await channel.send(
                    message=formatted_message,
                    subject=subject,
                    level=level,
                    metadata=metadata,
                )
                results[channel_name] = success
            except Exception as e:
                logger.error(f"Error in {channel_name}: {e}")
                results[channel_name] = False

        return results


# Singleton instance
notification_manager = NotificationManager()
