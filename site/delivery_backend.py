"""
Backend system for handling purchases and delivering the AI Business Starter Pack
"""
import os
import json
import hashlib
import hmac
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Tuple
from pathlib import Path
import jwt
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class DeliverySystem:
    def __init__(self):
        """Initialize the delivery system."""
        self.config = self.load_config()
        self.purchases_file = "data/purchases.json"
        self.ensure_data_directory()
        
    def load_config(self) -> Dict:
        """Load configuration from environment variables."""
        return {
            'paystack_secret': os.getenv('PAYSTACK_SECRET_KEY'),
            'jwt_secret': os.getenv('JWT_SECRET_KEY', 'your-secret-key'),
            'smtp_host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_user': os.getenv('SMTP_USER'),
            'smtp_pass': os.getenv('SMTP_PASS'),
            'download_base_url': os.getenv('DOWNLOAD_BASE_URL', 'https://njanja.net/downloads'),
            'product_file': os.getenv('PRODUCT_FILE', 'NjanjaStorefront_Package.zip')
        }
        
    def ensure_data_directory(self):
        """Ensure data directory exists."""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.purchases_file):
            with open(self.purchases_file, 'w') as f:
                json.dump([], f)
                
    def verify_paystack_signature(self, signature: str, payload: bytes) -> bool:
        """Verify Paystack webhook signature."""
        try:
            key = bytes(self.config['paystack_secret'], 'utf-8')
            computed = hmac.new(key, payload, hashlib.sha512).hexdigest()
            return hmac.compare_digest(computed, signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
            
    def generate_download_token(self, reference: str, email: str) -> str:
        """Generate a time-limited download token."""
        payload = {
            'reference': reference,
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.config['jwt_secret'], algorithm='HS256')
        
    def verify_download_token(self, token: str) -> Tuple[bool, Dict]:
        """Verify download token."""
        try:
            payload = jwt.decode(token, self.config['jwt_secret'], algorithms=['HS256'])
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, {'error': 'Download link expired'}
        except jwt.InvalidTokenError:
            return False, {'error': 'Invalid download token'}
            
    def send_delivery_email(self, email: str, download_token: str) -> bool:
        """Send delivery email with download link."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['smtp_user']
            msg['To'] = email
            msg['Subject'] = 'Your AI Business Starter Pack Download'
            
            body = f"""
            Thank you for purchasing the AI Business Starter Pack!

            Your download link is ready:
            {self.config['download_base_url']}/download/{download_token}

            This link will expire in 24 hours for security.

            Need help? Contact support@njanja.net

            Best regards,
            The Njanja Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.config['smtp_host'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['smtp_user'], self.config['smtp_pass'])
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
            
    def record_purchase(self, reference: str, email: str):
        """Record purchase details."""
        try:
            with open(self.purchases_file, 'r') as f:
                purchases = json.load(f)
                
            purchases.append({
                'reference': reference,
                'email': email,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'delivered'
            })
            
            with open(self.purchases_file, 'w') as f:
                json.dump(purchases, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to record purchase: {e}")

delivery_system = DeliverySystem()

@app.route('/api/process-purchase', methods=['POST'])
def process_purchase():
    """Handle purchase processing."""
    try:
        data = request.json
        reference = data.get('reference')
        email = data.get('email')
        
        if not reference or not email:
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Generate download token
        download_token = delivery_system.generate_download_token(reference, email)
        
        # Send delivery email
        if delivery_system.send_delivery_email(email, download_token):
            # Record purchase
            delivery_system.record_purchase(reference, email)
            
            return jsonify({
                'success': True,
                'message': 'Purchase processed successfully',
                'downloadUrl': f"{delivery_system.config['download_base_url']}/download/{download_token}"
            })
        else:
            return jsonify({'error': 'Failed to send delivery email'}), 500
            
    except Exception as e:
        logger.error(f"Purchase processing failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/download/<token>')
def download_product(token):
    """Handle product download."""
    success, payload = delivery_system.verify_download_token(token)
    
    if not success:
        return jsonify(payload), 401
        
    try:
        product_path = Path(delivery_system.config['product_file'])
        if not product_path.exists():
            return jsonify({'error': 'Product file not found'}), 404
            
        # Log download
        logger.info(f"Product downloaded by {payload['email']}")
        
        # Return file download response
        return send_file(
            product_path,
            as_attachment=True,
            download_name='AI_Business_Starter_Pack.zip'
        )
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return jsonify({'error': 'Download failed'}), 500

@app.route('/api/webhook', methods=['POST'])
def paystack_webhook():
    """Handle Paystack webhook."""
    signature = request.headers.get('x-paystack-signature')
    if not signature:
        return jsonify({'error': 'No signature provided'}), 400
        
    if not delivery_system.verify_paystack_signature(signature, request.get_data()):
        return jsonify({'error': 'Invalid signature'}), 401
        
    # Process webhook payload
    try:
        event = request.json
        if event.get('event') == 'charge.success':
            data = event.get('data', {})
            reference = data.get('reference')
            email = data.get('customer', {}).get('email')
            
            if reference and email:
                # Generate download token
                download_token = delivery_system.generate_download_token(reference, email)
                
                # Send delivery email
                if delivery_system.send_delivery_email(email, download_token):
                    delivery_system.record_purchase(reference, email)
                    return jsonify({'success': True})
                    
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 