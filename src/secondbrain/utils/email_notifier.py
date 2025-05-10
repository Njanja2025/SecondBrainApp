"""
Email notification utility for SecondBrain payment system.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .email_queue import email_queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/email_notifications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmailNotifier:
    """Handles email notifications for payment events."""
    
    def __init__(self):
        """Initialize email notifier with configuration."""
        self.config = self._load_config()
        self.sender = self.config["email_alerts"]["sender"]
        self.receiver = self.config["email_alerts"]["receiver"]
        self.smtp_server = self.config["email_alerts"]["smtp_server"]
        self.smtp_port = self.config["email_alerts"]["smtp_port"]
        self.smtp_password = self.config["email_alerts"]["smtp_password"]
    
    def _load_config(self) -> dict:
        """Load email configuration from file."""
        config_path = Path("config/payment_config.json")
        with open(config_path) as f:
            return json.load(f)
    
    def send_notification(
        self,
        subject: str,
        body: str,
        recipients: Optional[List[str]] = None,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send email notification.
        
        Args:
            subject: Email subject
            body: Plain text email body
            recipients: Optional list of additional recipients
            html_body: Optional HTML version of the email body
        
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Add to queue instead of sending directly
            for recipient in recipients or [self.receiver]:
                email_queue.add_email(
                    subject=subject,
                    recipient=recipient,
                    body=body,
                    html_body=html_body
                )
            
            logger.info(f"Email notification queued: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue email notification: {e}")
            return False
    
    def _get_email_template(self, template_name: str, data: Dict[str, Any]) -> tuple:
        """Get email template with data."""
        templates = {
            'payment_success': {
                'subject': "✅ SecondBrain Payment Received",
                'body': f"""
                A new payment was received:
                
                Customer: {data['email']}
                Amount: ${data['amount']:.2f}
                Plan: {data['plan']}
                Transaction ID: {data.get('transaction_id', 'N/A')}
                Date: {data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
                
                Thank you for your business!
                """,
                'html_body': f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #2ecc71;">✅ New Payment Received</h2>
                            <div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">
                                <p><strong>Customer:</strong> {data['email']}</p>
                                <p><strong>Amount:</strong> ${data['amount']:.2f}</p>
                                <p><strong>Plan:</strong> {data['plan']}</p>
                                <p><strong>Transaction ID:</strong> {data.get('transaction_id', 'N/A')}</p>
                                <p><strong>Date:</strong> {data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
                            </div>
                            <hr style="border: 1px solid #eee; margin: 20px 0;">
                            <p>Thank you for your business!</p>
                        </div>
                    </body>
                </html>
                """
            },
            'subscription_cancelled': {
                'subject': "⚠️ SecondBrain Subscription Cancelled",
                'body': f"""
                A subscription has been cancelled:
                
                Customer: {data['email']}
                Plan: {data['plan']}
                Cancellation Date: {data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
                Reason: {data.get('reason', 'Not provided')}
                
                Please follow up with the customer.
                """,
                'html_body': f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #e74c3c;">⚠️ Subscription Cancelled</h2>
                            <div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">
                                <p><strong>Customer:</strong> {data['email']}</p>
                                <p><strong>Plan:</strong> {data['plan']}</p>
                                <p><strong>Cancellation Date:</strong> {data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
                                <p><strong>Reason:</strong> {data.get('reason', 'Not provided')}</p>
                            </div>
                            <hr style="border: 1px solid #eee; margin: 20px 0;">
                            <p>Please follow up with the customer.</p>
                        </div>
                    </body>
                </html>
                """
            },
            'payment_failed': {
                'subject': "❌ SecondBrain Payment Failed",
                'body': f"""
                A payment has failed:
                
                Customer: {data['email']}
                Amount: ${data['amount']:.2f}
                Plan: {data['plan']}
                Error: {data.get('error', 'Unknown error')}
                Date: {data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
                
                Please check the payment details and follow up with the customer.
                """,
                'html_body': f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #e74c3c;">❌ Payment Failed</h2>
                            <div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">
                                <p><strong>Customer:</strong> {data['email']}</p>
                                <p><strong>Amount:</strong> ${data['amount']:.2f}</p>
                                <p><strong>Plan:</strong> {data['plan']}</p>
                                <p><strong>Error:</strong> {data.get('error', 'Unknown error')}</p>
                                <p><strong>Date:</strong> {data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
                            </div>
                            <hr style="border: 1px solid #eee; margin: 20px 0;">
                            <p>Please check the payment details and follow up with the customer.</p>
                        </div>
                    </body>
                </html>
                """
            },
            'subscription_updated': {
                'subject': "🔄 SecondBrain Subscription Updated",
                'body': f"""
                A subscription has been updated:
                
                Customer: {data['email']}
                Plan: {data['plan']}
                New Status: {data['status']}
                Update Date: {data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
                Changes: {data.get('changes', 'No specific changes noted')}
                
                Please review the changes.
                """,
                'html_body': f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #3498db;">🔄 Subscription Updated</h2>
                            <div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">
                                <p><strong>Customer:</strong> {data['email']}</p>
                                <p><strong>Plan:</strong> {data['plan']}</p>
                                <p><strong>New Status:</strong> {data['status']}</p>
                                <p><strong>Update Date:</strong> {data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
                                <p><strong>Changes:</strong> {data.get('changes', 'No specific changes noted')}</p>
                            </div>
                            <hr style="border: 1px solid #eee; margin: 20px 0;">
                            <p>Please review the changes.</p>
                        </div>
                    </body>
                </html>
                """
            },
            'trial_ending': {
                'subject': "⏰ SecondBrain Trial Ending Soon",
                'body': f"""
                A trial subscription is ending soon:
                
                Customer: {data['email']}
                Plan: {data['plan']}
                End Date: {data.get('end_date', 'N/A')}
                Days Remaining: {data.get('days_remaining', 'N/A')}
                
                Please follow up with the customer.
                """,
                'html_body': f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #f1c40f;">⏰ Trial Ending Soon</h2>
                            <div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">
                                <p><strong>Customer:</strong> {data['email']}</p>
                                <p><strong>Plan:</strong> {data['plan']}</p>
                                <p><strong>End Date:</strong> {data.get('end_date', 'N/A')}</p>
                                <p><strong>Days Remaining:</strong> {data.get('days_remaining', 'N/A')}</p>
                            </div>
                            <hr style="border: 1px solid #eee; margin: 20px 0;">
                            <p>Please follow up with the customer.</p>
                        </div>
                    </body>
                </html>
                """
            }
        }
        
        template = templates.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        
        return template['subject'], template['body'], template['html_body']
    
    def send_payment_notification(self, email: str, amount: float, plan: str, transaction_id: Optional[str] = None) -> bool:
        """Send notification for successful payment."""
        template_data = {
            'email': email,
            'amount': amount,
            'plan': plan,
            'transaction_id': transaction_id,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        subject, body, html_body = self._get_email_template('payment_success', template_data)
        return self.send_notification(subject, body, recipients=[email], html_body=html_body)
    
    def send_cancellation_notification(self, email: str, plan: str, reason: Optional[str] = None) -> bool:
        """Send notification for subscription cancellation."""
        template_data = {
            'email': email,
            'plan': plan,
            'reason': reason,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        subject, body, html_body = self._get_email_template('subscription_cancelled', template_data)
        return self.send_notification(subject, body, recipients=[email], html_body=html_body)
    
    def send_payment_failed_notification(self, email: str, amount: float, plan: str, error: Optional[str] = None) -> bool:
        """Send notification for failed payment."""
        template_data = {
            'email': email,
            'amount': amount,
            'plan': plan,
            'error': error,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        subject, body, html_body = self._get_email_template('payment_failed', template_data)
        return self.send_notification(subject, body, recipients=[email], html_body=html_body)
    
    def send_subscription_update_notification(self, email: str, plan: str, status: str, changes: Optional[str] = None) -> bool:
        """Send notification for subscription update."""
        template_data = {
            'email': email,
            'plan': plan,
            'status': status,
            'changes': changes,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        subject, body, html_body = self._get_email_template('subscription_updated', template_data)
        return self.send_notification(subject, body, recipients=[email], html_body=html_body)
    
    def send_trial_ending_notification(self, email: str, plan: str, end_date: str, days_remaining: int) -> bool:
        """Send notification for trial ending soon."""
        template_data = {
            'email': email,
            'plan': plan,
            'end_date': end_date,
            'days_remaining': days_remaining
        }
        
        subject, body, html_body = self._get_email_template('trial_ending', template_data)
        return self.send_notification(subject, body, recipients=[email], html_body=html_body)

# Create a singleton instance
email_notifier = EmailNotifier() 