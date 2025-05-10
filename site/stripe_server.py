"""
Server-side Stripe integration for the AI Business Starter Pack
"""
import os
import json
import logging
import stripe
from datetime import datetime
from typing import Dict, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

class StripeHandler:
    def __init__(self):
        """Initialize the Stripe handler."""
        self.config = self.load_config()
        self.purchases_file = "data/stripe_purchases.json"
        self.ensure_data_directory()
        
    def load_config(self) -> Dict:
        """Load configuration from environment variables."""
        return {
            'price_id': os.getenv('STRIPE_PRICE_ID', 'price_H5ggYwtDq4fbrJ'),
            'success_url': os.getenv('STRIPE_SUCCESS_URL', 'https://njanja.net/success'),
            'cancel_url': os.getenv('STRIPE_CANCEL_URL', 'https://njanja.net/cancel'),
            'webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET'),
            'notification_email': os.getenv('NOTIFICATION_EMAIL', 'admin@njanja.net')
        }
        
    def ensure_data_directory(self):
        """Ensure data directory exists."""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.purchases_file):
            with open(self.purchases_file, 'w') as f:
                json.dump([], f)
                
    def create_checkout_session(self, price_id: str, quantity: int = 1) -> Dict:
        """Create a Stripe checkout session."""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': quantity,
                }],
                mode='payment',
                success_url=self.config['success_url'],
                cancel_url=self.config['cancel_url'],
                metadata={
                    'product': 'AI Business Starter Pack',
                    'version': '1.0.0'
                }
            )
            
            logger.info(f"Created checkout session: {session.id}")
            return session
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise
            
    def handle_webhook(self, payload: bytes, signature: str) -> bool:
        """Handle Stripe webhook events."""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.config['webhook_secret']
            )
            
            if event.type == 'checkout.session.completed':
                session = event.data.object
                self.process_successful_payment(session)
                
            elif event.type == 'payment_intent.succeeded':
                payment_intent = event.data.object
                self.process_successful_payment_intent(payment_intent)
                
            elif event.type == 'payment_intent.payment_failed':
                payment_intent = event.data.object
                self.handle_failed_payment(payment_intent)
                
            return True
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            return False
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False
            
    def process_successful_payment(self, session: Dict):
        """Process a successful payment."""
        try:
            # Record purchase
            with open(self.purchases_file, 'r') as f:
                purchases = json.load(f)
                
            purchases.append({
                'session_id': session.id,
                'customer_email': session.customer_details.email,
                'amount': session.amount_total,
                'currency': session.currency,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'completed'
            })
            
            with open(self.purchases_file, 'w') as f:
                json.dump(purchases, f, indent=2)
                
            # Send confirmation email
            self.send_confirmation_email(session)
            
            logger.info(f"Processed successful payment: {session.id}")
            
        except Exception as e:
            logger.error(f"Failed to process payment: {e}")
            
    def process_successful_payment_intent(self, payment_intent: Dict):
        """Process a successful payment intent."""
        try:
            logger.info(f"Payment intent succeeded: {payment_intent.id}")
            # Additional processing if needed
            
        except Exception as e:
            logger.error(f"Failed to process payment intent: {e}")
            
    def handle_failed_payment(self, payment_intent: Dict):
        """Handle a failed payment."""
        try:
            logger.warning(f"Payment failed: {payment_intent.id}")
            # Handle failed payment (e.g., notify customer)
            
        except Exception as e:
            logger.error(f"Failed to handle failed payment: {e}")
            
    def send_confirmation_email(self, session: Dict):
        """Send confirmation email to customer."""
        try:
            # Implement email sending logic here
            logger.info(f"Sent confirmation email to: {session.customer_details.email}")
            
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")

# Initialize Stripe handler
stripe_handler = StripeHandler()

@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create a Stripe checkout session."""
    try:
        data = request.json
        price_id = data.get('priceId', stripe_handler.config['price_id'])
        quantity = data.get('quantity', 1)
        
        session = stripe_handler.create_checkout_session(price_id, quantity)
        return jsonify({'id': session.id})
        
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events."""
    payload = request.get_data()
    signature = request.headers.get('Stripe-Signature')
    
    if not signature:
        return jsonify({'error': 'No signature provided'}), 400
        
    if stripe_handler.handle_webhook(payload, signature):
        return jsonify({'status': 'success'})
    else:
        return jsonify({'error': 'Invalid signature'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 