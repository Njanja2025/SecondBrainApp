"""
Subscription management system for SecondBrain.
Handles subscription plans, access control, and feature management.
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import stripe
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """Available subscription tiers."""

    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class Feature:
    """Feature definition with access control."""

    name: str
    description: str
    required_tier: SubscriptionTier
    is_enabled: bool = True


@dataclass
class SubscriptionPlan:
    """Subscription plan definition."""

    tier: SubscriptionTier
    name: str
    description: str
    price_monthly: float
    price_yearly: float
    features: List[str]
    stripe_price_id: str


class SubscriptionManager:
    """Manages subscriptions and feature access."""

    def __init__(self, config_path: str = "config/payment_config.json"):
        """Initialize the subscription manager."""
        self.config_path = config_path
        self.config = self._load_config()
        self._initialize_stripe()

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

    def _initialize_stripe(self):
        """Initialize Stripe with API key."""
        stripe.api_key = self.config["stripe_secret_key"]

    def get_price_id(self, plan_name: str) -> str:
        """Get Stripe price ID for a plan."""
        try:
            return self.config["subscription_plans"][plan_name]["price_id"]
        except KeyError:
            logger.error(f"Price ID not found for plan: {plan_name}")
            raise

    def create_checkout_session(
        self, plan_name: str, customer_email: Optional[str] = None
    ) -> stripe.checkout.Session:
        """Create a Stripe checkout session."""
        try:
            # Get price ID for the plan
            price_id = self.get_price_id(plan_name)

            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                customer_email=customer_email,
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=self.config["urls"]["success"],
                cancel_url=self.config["urls"]["cancel"],
            )

            logger.info(f"Created checkout session for plan: {plan_name}")
            return session

        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise

    def open_checkout_url(self, url: str):
        """Open checkout URL in default browser."""
        try:
            if os.name == "posix":  # macOS or Linux
                os.system(f"open {url}")
            else:  # Windows
                os.system(f"start {url}")
        except Exception as e:
            logger.error(f"Failed to open checkout URL: {e}")
            print(f"Please visit this URL to complete checkout: {url}")


def start_payment_flow(plan_name: str, customer_email: Optional[str] = None):
    """Start the payment flow for a subscription plan."""
    try:
        # Initialize subscription manager
        manager = SubscriptionManager()

        # Create checkout session
        session = manager.create_checkout_session(plan_name, customer_email)

        # Open checkout URL
        manager.open_checkout_url(session.url)

        return session

    except Exception as e:
        logger.error(f"Payment flow failed: {e}")
        raise


def start_payment_flow(plan_name: str, customer_email: Optional[str] = None):
    """Start the payment flow for a subscription plan."""
    try:
        # Initialize subscription manager
        manager = SubscriptionManager()

        # Create checkout session
        session = manager.create_checkout_session(plan_name, customer_email)

        # Open checkout URL
        manager.open_checkout_url(session.url)

        return session

    except Exception as e:
        logger.error(f"Payment flow failed: {e}")
        raise


def start_payment_flow(plan_name: str, customer_email: Optional[str] = None):
    """Start the payment flow for a subscription plan."""
    try:
        # Initialize subscription manager
        manager = SubscriptionManager()

        # Create checkout session
        session = manager.create_checkout_session(plan_name, customer_email)

        # Open checkout URL
        manager.open_checkout_url(session.url)

        return session

    except Exception as e:
        logger.error(f"Payment flow failed: {e}")
        raise
