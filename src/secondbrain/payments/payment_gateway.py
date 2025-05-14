"""
Payment gateway integration for SecondBrainApp
"""

import stripe
import paypalrestsdk
import logging
from typing import Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from ..utils.config import Config

logger = logging.getLogger(__name__)


class PaymentGateway:
    """Manages payment processing through Stripe and PayPal."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize payment gateway.

        Args:
            config: Optional configuration instance
        """
        self.config = config or Config()
        self._initialize_stripe()
        self._initialize_paypal()

    def _initialize_stripe(self) -> None:
        """Initialize Stripe API."""
        try:
            stripe.api_key = self.config.get("stripe_api_key")
            logger.info("Stripe API initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Stripe: {e}")

    def _initialize_paypal(self) -> None:
        """Initialize PayPal API."""
        try:
            paypalrestsdk.configure(
                {
                    "mode": self.config.get("paypal_mode", "sandbox"),
                    "client_id": self.config.get("paypal_client_id"),
                    "client_secret": self.config.get("paypal_client_secret"),
                }
            )
            logger.info("PayPal API initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PayPal: {e}")

    def create_stripe_customer(self, email: str, name: str) -> Optional[str]:
        """
        Create a Stripe customer.

        Args:
            email: Customer email
            name: Customer name

        Returns:
            Stripe customer ID if successful
        """
        try:
            customer = stripe.Customer.create(email=email, name=name)
            return customer.id
        except Exception as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            return None

    def create_paypal_customer(self, email: str, name: str) -> Optional[str]:
        """
        Create a PayPal customer.

        Args:
            email: Customer email
            name: Customer name

        Returns:
            PayPal customer ID if successful
        """
        try:
            customer = paypalrestsdk.Customer({"email": email, "name": name})
            if customer.create():
                return customer.id
            return None
        except Exception as e:
            logger.error(f"Failed to create PayPal customer: {e}")
            return None

    def create_subscription(
        self, customer_id: str, plan_id: str, payment_method: str = "stripe"
    ) -> Optional[str]:
        """
        Create a subscription for a customer.

        Args:
            customer_id: Customer ID
            plan_id: Plan ID
            payment_method: Payment method ('stripe' or 'paypal')

        Returns:
            Subscription ID if successful
        """
        try:
            if payment_method == "stripe":
                subscription = stripe.Subscription.create(
                    customer=customer_id, items=[{"price": plan_id}]
                )
                return subscription.id
            elif payment_method == "paypal":
                subscription = paypalrestsdk.Subscription(
                    {"plan_id": plan_id, "customer_id": customer_id}
                )
                if subscription.create():
                    return subscription.id
            return None
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return None

    def process_payment(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        customer_id: str,
        description: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Process a payment.

        Args:
            amount: Payment amount
            currency: Currency code
            payment_method: Payment method ('stripe' or 'paypal')
            customer_id: Customer ID
            description: Payment description

        Returns:
            Tuple of (success, transaction_id)
        """
        try:
            if payment_method == "stripe":
                payment = stripe.PaymentIntent.create(
                    amount=int(amount * 100),  # Convert to cents
                    currency=currency,
                    customer=customer_id,
                    description=description,
                )
                return True, payment.id
            elif payment_method == "paypal":
                payment = paypalrestsdk.Payment(
                    {
                        "intent": "sale",
                        "payer": {"payment_method": "paypal"},
                        "transactions": [
                            {
                                "amount": {"total": str(amount), "currency": currency},
                                "description": description,
                            }
                        ],
                    }
                )
                if payment.create():
                    return True, payment.id
            return False, None
        except Exception as e:
            logger.error(f"Failed to process payment: {e}")
            return False, None

    def get_subscription_status(
        self, subscription_id: str, payment_method: str = "stripe"
    ) -> str:
        """
        Get subscription status.

        Args:
            subscription_id: Subscription ID
            payment_method: Payment method ('stripe' or 'paypal')

        Returns:
            Subscription status
        """
        try:
            if payment_method == "stripe":
                subscription = stripe.Subscription.retrieve(subscription_id)
                return subscription.status
            elif payment_method == "paypal":
                subscription = paypalrestsdk.Subscription.find(subscription_id)
                return subscription.status
            return "unknown"
        except Exception as e:
            logger.error(f"Failed to get subscription status: {e}")
            return "error"
