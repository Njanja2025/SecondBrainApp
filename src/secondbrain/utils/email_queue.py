"""
Email queue system for reliable email delivery.
"""
import queue
import threading
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/email_queue.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmailQueue:
    """Manages a queue of emails for reliable delivery."""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 300):
        """Initialize the email queue."""
        self.queue = queue.Queue()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._init_db()
        self._start_worker()
    
    def _init_db(self):
        """Initialize the SQLite database for email tracking."""
        conn = sqlite3.connect('data/email_queue.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS email_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                recipient TEXT,
                body TEXT,
                html_body TEXT,
                status TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                sent_at TIMESTAMP,
                error TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def _start_worker(self):
        """Start the email queue worker thread."""
        def worker():
            while True:
                try:
                    # Get email from queue
                    email_data = self.queue.get()
                    
                    # Process email
                    success = self._process_email(email_data)
                    
                    if not success and email_data['retry_count'] < self.max_retries:
                        # Requeue with delay
                        email_data['retry_count'] += 1
                        time.sleep(self.retry_delay)
                        self.queue.put(email_data)
                    
                    self.queue.task_done()
                    
                except Exception as e:
                    logger.error(f"Error in email queue worker: {e}")
                    time.sleep(5)  # Prevent tight loop on errors
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _process_email(self, email_data: Dict[str, Any]) -> bool:
        """Process a single email from the queue."""
        try:
            # Update database
            conn = sqlite3.connect('data/email_queue.db')
            c = conn.cursor()
            
            # Insert email record
            c.execute('''
                INSERT INTO email_queue
                (subject, recipient, body, html_body, status, retry_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_data['subject'],
                email_data['recipient'],
                email_data['body'],
                email_data.get('html_body'),
                'pending',
                email_data['retry_count'],
                datetime.now().isoformat()
            ))
            
            email_id = c.lastrowid
            
            # Send email using notifier
            from .email_notifier import email_notifier
            success = email_notifier.send_notification(
                subject=email_data['subject'],
                body=email_data['body'],
                recipients=[email_data['recipient']],
                html_body=email_data.get('html_body')
            )
            
            # Update status
            if success:
                c.execute('''
                    UPDATE email_queue
                    SET status = ?, sent_at = ?
                    WHERE id = ?
                ''', ('sent', datetime.now().isoformat(), email_id))
            else:
                c.execute('''
                    UPDATE email_queue
                    SET status = ?, error = ?
                    WHERE id = ?
                ''', ('failed', 'Failed to send email', email_id))
            
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return False
    
    def add_email(
        self,
        subject: str,
        recipient: str,
        body: str,
        html_body: Optional[str] = None
    ):
        """Add an email to the queue."""
        email_data = {
            'subject': subject,
            'recipient': recipient,
            'body': body,
            'html_body': html_body,
            'retry_count': 0
        }
        
        self.queue.put(email_data)
        logger.info(f"Added email to queue: {subject} -> {recipient}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        conn = sqlite3.connect('data/email_queue.db')
        c = conn.cursor()
        
        # Get counts by status
        c.execute('''
            SELECT status, COUNT(*) as count
            FROM email_queue
            GROUP BY status
        ''')
        status_counts = dict(c.fetchall())
        
        # Get recent failures
        c.execute('''
            SELECT subject, recipient, error, created_at
            FROM email_queue
            WHERE status = 'failed'
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        recent_failures = c.fetchall()
        
        conn.close()
        
        return {
            'queue_size': self.queue.qsize(),
            'status_counts': status_counts,
            'recent_failures': recent_failures
        }

# Create a singleton instance
email_queue = EmailQueue() 