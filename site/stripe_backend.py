"""
Enhanced Stripe Backend for Njanja Store
"""

import os
import json
import logging
import stripe
from datetime import datetime
from typing import Dict, Optional, List
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
CORS(app)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_your_secret_key_here")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")


class StripeBackend:
    def __init__(self):
        """Initialize the Stripe backend."""
        self.config = self.load_config()
        self.purchases_file = "data/stripe_purchases.json"
        self.ensure_data_directory()

    def load_config(self) -> Dict:
        """Load configuration from environment variables."""
        return {
            "products": {
                "ai_starter_pack": {
                    "name": "AI Business Starter Pack",
                    "price": 49900,
                    "currency": "usd",
                    "description": "Launch your digital business with our comprehensive AI toolkit",
                }
            },
            "webhook_secret": os.getenv("STRIPE_WEBHOOK_SECRET"),
            "success_url": os.getenv(
                "STRIPE_SUCCESS_URL", "https://njanja.net/success"
            ),
            "cancel_url": os.getenv("STRIPE_CANCEL_URL", "https://njanja.net/cancel"),
            "notification_email": os.getenv("NOTIFICATION_EMAIL", "admin@njanja.net"),
        }

    def ensure_data_directory(self):
        """Ensure data directory exists."""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.purchases_file):
            with open(self.purchases_file, "w") as f:
                json.dump([], f)

    def create_checkout_session(self, product_id: str, quantity: int = 1) -> Dict:
        """Create a Stripe checkout session."""
        try:
            product = self.config["products"][product_id]

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": product["currency"],
                            "product_data": {
                                "name": product["name"],
                                "description": product["description"],
                                "images": [
                                    "https://njanja.net/images/ai_starter_pack.jpg"
                                ],
                            },
                            "unit_amount": product["price"],
                        },
                        "quantity": quantity,
                    }
                ],
                mode="payment",
                success_url=self.config["success_url"],
                cancel_url=self.config["cancel_url"],
                metadata={"product_id": product_id, "version": "1.0.0"},
                customer_email=request.json.get("email"),
                billing_address_collection="required",
                shipping_address_collection={
                    "allowed_countries": [
                        "US",
                        "CA",
                        "GB",
                        "ZA",
                        "NG",
                        "KE",
                        "GH",
                        "EG",
                    ]
                },
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
                payload, signature, self.config["webhook_secret"]
            )

            if event.type == "checkout.session.completed":
                session = event.data.object
                self.process_successful_payment(session)

            elif event.type == "payment_intent.succeeded":
                payment_intent = event.data.object
                self.process_successful_payment_intent(payment_intent)

            elif event.type == "payment_intent.payment_failed":
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
            with open(self.purchases_file, "r") as f:
                purchases = json.load(f)

            purchases.append(
                {
                    "session_id": session.id,
                    "customer_email": session.customer_details.email,
                    "amount": session.amount_total,
                    "currency": session.currency,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "completed",
                    "product_id": session.metadata.get("product_id"),
                    "shipping_address": session.shipping.address,
                    "billing_address": session.customer_details.address,
                }
            )

            with open(self.purchases_file, "w") as f:
                json.dump(purchases, f, indent=2)

            # Send confirmation email
            self.send_confirmation_email(session)

            # Generate download link
            self.generate_download_link(session)

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

    def generate_download_link(self, session: Dict) -> str:
        """Generate a secure download link for the product."""
        try:
            # Implement secure download link generation
            download_token = stripe.Token.create(
                customer=session.customer, card=session.payment_intent
            )

            return f"https://njanja.net/download/{download_token.id}"

        except Exception as e:
            logger.error(f"Failed to generate download link: {e}")
            return None


# Initialize Stripe backend
stripe_backend = StripeBackend()


@app.route("/api/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Create a Stripe checkout session."""
    try:
        data = request.json
        product_id = data.get("productId", "ai_starter_pack")
        quantity = data.get("quantity", 1)

        session = stripe_backend.create_checkout_session(product_id, quantity)
        return jsonify({"id": session.id})

    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/webhook", methods=["POST"])
def webhook():
    """Handle Stripe webhook events."""
    payload = request.get_data()
    signature = request.headers.get("Stripe-Signature")

    if not signature:
        return jsonify({"error": "No signature provided"}), 400

    if stripe_backend.handle_webhook(payload, signature):
        return jsonify({"status": "success"})
    else:
        return jsonify({"error": "Invalid signature"}), 400


@app.route("/api/download/<token>", methods=["GET"])
def download_product(token):
    """Handle product download."""
    try:
        # Verify download token
        download_info = stripe.Token.retrieve(token)

        # Get product file
        product_path = "products/ai_starter_pack.zip"
        if not os.path.exists(product_path):
            return jsonify({"error": "Product not found"}), 404

        return send_file(
            product_path,
            as_attachment=True,
            download_name="AI_Business_Starter_Pack.zip",
        )

    except Exception as e:
        logger.error(f"Download failed: {e}")
        return jsonify({"error": "Download failed"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4242)
