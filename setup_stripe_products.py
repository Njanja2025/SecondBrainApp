"""
Set up Stripe products and prices for testing.
"""

import json
import stripe
from pathlib import Path


def setup_stripe_products():
    """Set up Stripe products and prices."""
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
        # Create products and prices
        for plan_id, plan in config["subscription_plans"].items():
            # Create product
            product = stripe.Product.create(
                name=plan["name"],
                description=f"Test {plan['name']} for SecondBrain",
                metadata={"plan_id": plan_id, "features": ", ".join(plan["features"])},
            )
            print(f"Created product: {product.name} (ID: {product.id})")

            # Create price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=int(plan["price"]["usd"] * 100),  # Convert to cents
                currency="usd",
                recurring={"interval": plan["interval"]},
                metadata={"plan_id": plan_id},
            )
            print(f"Created price: {price.id} for {plan['name']}")

            # Update config with new price ID
            config["subscription_plans"][plan_id]["price_id"] = price.id

        # Save updated configuration
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)

        print("\nSuccessfully set up Stripe products and prices!")
        print("Updated configuration saved to:", config_path)
        return True

    except stripe.error.AuthenticationError:
        print("Error: Invalid API key")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


if __name__ == "__main__":
    setup_stripe_products()
