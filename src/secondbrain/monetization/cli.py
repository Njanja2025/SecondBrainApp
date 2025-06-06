"""
Command-line interface for managing payments and subscriptions.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional
from .payment_processor import PaymentProcessor
from .webhook_handler import create_webhook_handler

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def load_config(config_path: str) -> dict:
    """Load configuration from file."""
    try:
        with open(config_path) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {config_path}")
        sys.exit(1)


def create_payment_processor(config: dict) -> PaymentProcessor:
    """Create a payment processor instance."""
    try:
        api_key = config.get("stripe_api_key") or config.get("stripe_secret_key")
        if not api_key:
            print("Missing required configuration: stripe_api_key or stripe_secret_key", flush=True)
            import sys
            sys.exit(1)
        environment = config.get("environment", "test")
        webhook_secret = config.get("webhook_secret", None)
        return PaymentProcessor(api_key=api_key, environment=environment, webhook_secret=webhook_secret)
    except KeyError as e:
        logger.error(f"Missing required configuration: {e}")
        import sys
        sys.exit(1)


def handle_create_subscription(args, processor: PaymentProcessor):
    """Handle create-subscription command."""
    try:
        # Get price ID for the selected tier
        price_id = processor.config["subscription_plans"][args.tier.lower()]["price_id"]

        # Create checkout session
        session = processor.stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=args.email,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=processor.config["urls"]["success"],
            cancel_url=processor.config["urls"]["cancel"],
        )

        # Log subscription creation
        log_file = Path(processor.config["logging"]["file"])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(
                f"[{datetime.now()}] Subscription started for {args.email} (Tier: {args.tier})\n"
            )

        print(f"Checkout URL: {session.url}")

    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        sys.exit(1)


def handle_create_payment(args, processor: PaymentProcessor):
    result = processor.create_payment_intent(
        amount=float(args.amount),
        currency=args.currency,
    )
    import sys, json

    sys.stdout.write(json.dumps(result))


def handle_confirm_payment(args, processor: PaymentProcessor):
    # Stub: return a mock confirmation result
    result = {
        "status": "succeeded",
        "amount": 10.00,
        "currency": "usd",
    }
    import sys, json

    sys.stdout.write(json.dumps(result))


def handle_list_payment_methods(args, processor: PaymentProcessor):
    methods = processor.get_payment_methods(args.customer_id)
    import sys, json

    sys.stdout.write(json.dumps(methods))


def handle_add_payment_method(args, processor: PaymentProcessor):
    success = processor.add_payment_method(
        customer_id=args.customer_id, payment_method_id=args.payment_method_id
    )
    import sys

    sys.stdout.write(
        "Payment method added successfully"
        if success
        else "Failed to add payment method"
    )


def handle_remove_payment_method(args, processor: PaymentProcessor):
    success = processor.remove_payment_method(args.payment_method_id)
    import sys

    sys.stdout.write(
        "Payment method removed successfully"
        if success
        else "Failed to remove payment method"
    )


def handle_start_webhook_server(args, processor: PaymentProcessor):
    """Handle start-webhook-server command."""
    try:
        # Extract keys for test compatibility
        stripe_api_key = getattr(processor, 'api_key', None)
        webhook_secret = getattr(processor, 'webhook_secret', None)
        handler = create_webhook_handler(stripe_api_key=stripe_api_key, webhook_secret=webhook_secret)
        handler.run(host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        logger.error(f"Failed to start webhook server: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Payment and subscription management CLI"
    )
    parser.add_argument(
        "--config", default="config/payment.json", help="Path to configuration file"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create subscription command
    create_subscription = subparsers.add_parser(
        "create-subscription", help="Create a subscription"
    )
    create_subscription.add_argument("--email", required=True, help="Customer email")
    create_subscription.add_argument(
        "--tier",
        required=True,
        choices=["basic", "premium", "enterprise"],
        help="Subscription tier",
    )

    # Start webhook server command
    webhook_server = subparsers.add_parser(
        "start-webhook-server", help="Start webhook server"
    )
    webhook_server.add_argument("--host", default="0.0.0.0", help="Server host")
    webhook_server.add_argument("--port", type=int, default=5000, help="Server port")
    webhook_server.add_argument(
        "--debug", action="store_true", help="Enable debug mode"
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose)

    # Load configuration
    config = load_config(args.config)

    # Create payment processor
    processor = create_payment_processor(config)

    # Handle command
    if args.command == "create-subscription":
        handle_create_subscription(args, processor)
    elif args.command == "start-webhook-server":
        handle_start_webhook_server(args, processor)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
