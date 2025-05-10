"""
Stripe webhook handler for SecondBrain payment system.
"""
import stripe
import json
import os
import logging
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..utils.email_notifier import email_notifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/payments.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

def log_stripe_event(event_type, customer_email=None, note=""):
    """Log Stripe events to a dedicated log file."""
    with open("logs/stripe_payments.log", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {event_type} - {customer_email or 'unknown'} {note}\n")

# Load configuration
config_path = Path("config/payment_config.json")
with open(config_path) as f:
    config = json.load(f)
    stripe.api_key = config["stripe_keys"]["secret"]
    webhook_secret = config["webhook_secrets"]["stripe"]

app = Flask(__name__)

def init_db():
    """Initialize the database."""
    conn = sqlite3.connect('data/subscriptions.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            customer_email TEXT,
            plan_id TEXT,
            status TEXT,
            created_at INTEGER,
            updated_at INTEGER,
            canceled_at INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def update_subscription(subscription_data):
    """Update subscription in database."""
    conn = sqlite3.connect('data/subscriptions.db')
    c = conn.cursor()
    
    # Check if subscription exists
    c.execute('SELECT id FROM subscriptions WHERE id = ?', (subscription_data['id'],))
    exists = c.fetchone()
    
    if exists:
        # Update existing subscription
        c.execute('''
            UPDATE subscriptions
            SET status = ?, updated_at = ?, canceled_at = ?
            WHERE id = ?
        ''', (
            subscription_data['status'],
            subscription_data.get('updated_at', int(datetime.now().timestamp())),
            subscription_data.get('canceled_at'),
            subscription_data['id']
        ))
    else:
        # Insert new subscription
        c.execute('''
            INSERT INTO subscriptions
            (id, customer_id, customer_email, plan_id, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            subscription_data['id'],
            subscription_data['customer_id'],
            subscription_data['customer_email'],
            subscription_data['plan_id'],
            subscription_data['status'],
            subscription_data.get('created_at', int(datetime.now().timestamp())),
            subscription_data.get('updated_at', int(datetime.now().timestamp()))
        ))
    
    conn.commit()
    conn.close()

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    """Handle incoming Stripe webhook events."""
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        log_stripe_event("webhook.error", note="Invalid signature")
        return jsonify({"error": "Invalid signature"}), 400
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        log_stripe_event("webhook.error", note=str(e))
        return jsonify({"error": str(e)}), 400

    # Log the event
    logger.info(f"Received webhook event: {event['type']}")

    try:
        # Handle different event types
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            email = session.get("customer_email", "unknown")
            amount = session.get("amount_total", 0) / 100  # Convert from cents
            
            # Get subscription details
            subscription = stripe.Subscription.retrieve(session['subscription'])
            plan = subscription.items.data[0].price.nickname or "Unknown Plan"
            
            # Log event
            log_stripe_event("checkout.session.completed", email, f"Amount: ${amount}")
            
            # Update database
            update_subscription({
                'id': subscription.id,
                'customer_id': subscription.customer,
                'customer_email': email,
                'plan_id': subscription.items.data[0].price.id,
                'status': subscription.status,
                'created_at': subscription.created,
                'updated_at': subscription.current_period_start
            })
            
            # Send email notification
            email_notifier.send_payment_notification(email, amount, plan)
            
            # Trigger backup system
            from ..companion.backup import CompanionBackup
            backup = CompanionBackup()
            backup.trigger_backup()

        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            email = subscription.get("customer_email", "unknown")
            plan = subscription.items.data[0].price.nickname or "Unknown Plan"
            
            # Log event
            log_stripe_event("subscription.deleted", email, f"Subscription ID: {subscription.id}")
            
            # Update database
            update_subscription({
                'id': subscription.id,
                'customer_id': subscription.customer,
                'customer_email': email,
                'plan_id': subscription.items.data[0].price.id,
                'status': 'canceled',
                'updated_at': subscription.canceled_at,
                'canceled_at': subscription.canceled_at
            })
            
            # Send email notification
            email_notifier.send_cancellation_notification(email, plan)

        elif event["type"] == "invoice.payment_failed":
            invoice = event["data"]["object"]
            email = invoice.get("customer_email", "unknown")
            amount = invoice.get("amount_due", 0) / 100  # Convert from cents
            
            # Get subscription details
            subscription = stripe.Subscription.retrieve(invoice.subscription)
            plan = subscription.items.data[0].price.nickname or "Unknown Plan"
            
            # Log event
            log_stripe_event("payment.failed", email, f"Amount: ${amount}")
            
            # Send email notification
            email_notifier.send_payment_failed_notification(email, amount, plan)

        elif event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            email = subscription.get("customer_email", "unknown")
            plan = subscription.items.data[0].price.nickname or "Unknown Plan"
            
            # Log event
            log_stripe_event("subscription.updated", email, f"New status: {subscription.status}")
            
            # Update database
            update_subscription({
                'id': subscription.id,
                'customer_id': subscription.customer,
                'customer_email': email,
                'plan_id': subscription.items.data[0].price.id,
                'status': subscription.status,
                'updated_at': subscription.current_period_start
            })

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        log_stripe_event("webhook.error", note=f"Error processing event: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500

def run_webhook_server(port: int = 4242):
    """Run the webhook server."""
    # Initialize database
    init_db()
    
    logger.info(f"Starting webhook server on port {port}")
    app.run(port=port)

if __name__ == "__main__":
    run_webhook_server() 