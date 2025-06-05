"""
Payment processor for handling Stripe payments and subscriptions.
"""

import json
import logging
import stripe
from pathlib import Path
from typing import List, Dict, Optional
from .security import SecurityManager

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """Handles payment processing and subscription management."""

    def __init__(
        self,
        stripe_api_key: str = None,
        webhook_secret: str = None,
        config_path: str = "config/payment_config.json",
    ):
        """Initialize the payment processor."""
        self.config_path = config_path
        self.config = self._load_config()
        self.security = SecurityManager(config_path)

        # Use provided API key or from config
        if stripe_api_key is not None:
            stripe.api_key = stripe_api_key
        else:
            stripe.api_key = self.security.decrypt_api_key(
                self.config.get("stripe_secret_key", "")
            )
        self.stripe = stripe
        self.webhook_secret = webhook_secret or self.config.get("webhook_secret", None)

    def _load_config(self) -> Dict:
        """Load configuration from file."""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file: {self.config_path}")
            raise

    def create_payment_intent(self, amount: int, currency: str = "usd") -> Dict:
        """Create a payment intent."""
        if currency not in self.config.get("supported_currencies", []):
            raise ValueError(f"Unsupported currency: {currency}")
        try:
            intent = self.stripe.PaymentIntent.create(
                amount=amount, currency=currency, payment_method_types=["card"]
            )
            # If intent is a dict (mocked), return as is; else, convert to dict
            if isinstance(intent, dict):
                return {
                    "payment_intent_id": intent.get("id"),
                    "client_secret": intent.get("client_secret"),
                    "status": intent.get("status"),
                }
            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
            }
        except Exception as e:
            logger.error(f"Failed to create payment intent: {e}")
            self.security.log_failed_attempt("payment_intent_creation", str(e))
            raise

    def create_subscription(self, customer_email: str, plan_id: str) -> Dict:
        """Create a subscription."""
        try:
            # Get price ID for the plan
            price_id = self.config["subscription_plans"][plan_id]["price_id"]

            # Create checkout session
            session = self.stripe.checkout.Session.create(
                payment_method_types=["card"],
                customer_email=customer_email,
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=self.config["urls"]["success"],
                cancel_url=self.config["urls"]["cancel"],
            )

            return session
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            self.security.log_failed_attempt("subscription_creation", str(e))
            raise

    def handle_webhook_event(self, payload: str, signature: str) -> Dict:
        """Handle webhook event."""
        try:
            # Verify webhook signature
            if not self.security.verify_webhook_signature(payload, signature):
                logger.error("Invalid webhook signature")
                self.security.log_failed_attempt(
                    "webhook_verification", "Invalid signature"
                )
                return {"status": "error", "message": "Invalid signature"}

            # Construct and verify event
            event = self.stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=self.config["webhook_secret"],
            )

            # Handle specific event types
            if event.type == "checkout.session.completed":
                return self._handle_checkout_completed(event)
            elif event.type == "customer.subscription.updated":
                return self._handle_subscription_updated(event)
            elif event.type == "customer.subscription.deleted":
                return self._handle_subscription_deleted(event)

            return {"status": "success", "message": "Event processed"}

        except Exception as e:
            logger.error(f"Failed to handle webhook event: {e}")
            self.security.log_failed_attempt("webhook_handling", str(e))
            return {"status": "error", "message": str(e)}

    def _handle_checkout_completed(self, event: Dict) -> Dict:
        """Handle checkout.session.completed event."""
        session = event.data.object
        logger.info(f"Checkout completed for customer: {session.customer_email}")
        return {
            "status": "success",
            "customer_email": session.customer_email,
            "subscription_id": session.subscription,
        }

    def _handle_subscription_updated(self, event: Dict) -> Dict:
        """Handle customer.subscription.updated event."""
        subscription = event.data.object
        logger.info(f"Subscription updated: {subscription.id}")
        return {
            "status": "updated",
            "subscription_id": subscription.id,
            "customer_id": subscription.customer,
        }

    def _handle_subscription_deleted(self, event: Dict) -> Dict:
        """Handle customer.subscription.deleted event."""
        subscription = event.data.object
        logger.info(f"Subscription deleted: {subscription.id}")
        return {
            "status": "deleted",
            "subscription_id": subscription.id,
            "customer_id": subscription.customer,
        }

    def get_payment_methods(self, customer_id: str) -> List[Dict]:
        """Get customer's payment methods."""
        try:
            payment_methods = self.stripe.PaymentMethod.list(
                customer=customer_id, type="card"
            )

            return [
                {
                    "id": pm.id,
                    "type": pm.type,
                    "card": {
                        "brand": pm.card.brand,
                        "last4": pm.card.last4,
                        "exp_month": pm.card.exp_month,
                        "exp_year": pm.card.exp_year,
                    },
                }
                for pm in payment_methods.data
            ]

        except stripe.error.StripeError as e:
            logger.error(f"Failed to get payment methods: {e}")
            return []

    def add_payment_method(self, customer_id: str, payment_method_id: str) -> bool:
        """Add a payment method to a customer."""
        try:
            self.stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to add payment method: {e}")
            return False

    def remove_payment_method(self, payment_method_id: str) -> bool:
        """Remove a payment method."""
        try:
            self.stripe.PaymentMethod.detach(payment_method_id)
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to remove payment method: {e}")
            return False

    def get_tax_rate(self, currency: str, is_reduced: bool = False) -> float:
        """Get tax rate for currency."""
        try:
            rate_type = "reduced" if is_reduced else "standard"
            return self.config["tax_rates"][currency][rate_type]
        except KeyError:
            return 0.0

    def calculate_tax(
        self, amount: float, currency: str, is_reduced: bool = False
    ) -> float:
        """Calculate tax amount."""
        tax_rate = self.get_tax_rate(currency, is_reduced)
        return amount * tax_rate
