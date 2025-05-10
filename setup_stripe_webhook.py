"""
Set up Stripe webhook endpoint for testing.
"""
import json
import stripe
from pathlib import Path

def setup_stripe_webhook():
    """Set up Stripe webhook endpoint."""
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
        # Create webhook endpoint
        webhook = stripe.WebhookEndpoint.create(
            url=config["webhook_endpoint"],
            enabled_events=[
                "checkout.session.completed",
                "customer.subscription.created",
                "customer.subscription.updated",
                "customer.subscription.deleted",
                "invoice.paid",
                "invoice.payment_failed"
            ],
            metadata={
                "environment": "test"
            }
        )
        
        # Update config with webhook secret
        config["webhook_secret"] = webhook.secret
        
        # Save updated configuration
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        
        print("\nSuccessfully set up Stripe webhook endpoint!")
        print("Webhook endpoint ID:", webhook.id)
        print("Webhook secret updated in configuration")
        return True
        
    except stripe.error.AuthenticationError:
        print("Error: Invalid API key")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    setup_stripe_webhook() 