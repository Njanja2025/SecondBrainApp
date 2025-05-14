"""
Test Stripe configuration and connection.
"""

import os
import json
import stripe
from pathlib import Path


def test_stripe_connection():
    """Test connection to Stripe API."""
    # Load configuration
    config_path = Path("config/test_payment_config.json")
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        return False

    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in configuration file")
        return False

    # Set Stripe API key
    stripe.api_key = config["stripe_secret_key"]

    try:
        # Test API connection by listing customers (a simple API call)
        stripe.Customer.list(limit=1)
        print("Success: Successfully connected to Stripe API")
        return True
    except stripe.error.AuthenticationError:
        print("Error: Invalid API key")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


if __name__ == "__main__":
    test_stripe_connection()
