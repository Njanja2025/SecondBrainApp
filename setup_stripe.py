"""
Set up Stripe configuration for testing.
"""
import os
from pathlib import Path
from test_stripe_config import test_stripe_connection
from setup_stripe_products import setup_stripe_products
from setup_stripe_webhook import setup_stripe_webhook

def setup_stripe():
    """Run all Stripe setup steps."""
    print("Setting up Stripe configuration...")
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Step 1: Test connection
    print("\nStep 1: Testing Stripe connection...")
    if not test_stripe_connection():
        print("Failed to connect to Stripe. Please check your API key.")
        return False
    
    # Step 2: Set up products and prices
    print("\nStep 2: Setting up products and prices...")
    if not setup_stripe_products():
        print("Failed to set up products and prices.")
        return False
    
    # Step 3: Set up webhook endpoint
    print("\nStep 3: Setting up webhook endpoint...")
    if not setup_stripe_webhook():
        print("Failed to set up webhook endpoint.")
        return False
    
    print("\nStripe setup completed successfully!")
    return True

if __name__ == "__main__":
    setup_stripe() 