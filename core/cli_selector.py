"""
Command-line interface for subscription management.
"""

import os
import sys
from typing import Dict, Optional
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.secondbrain.monetization.subscription_manager import start_payment_flow


def display_plans() -> None:
    """Display available subscription plans."""
    print("\n=== SecondBrain Subscription Plans ===")
    print("1. Basic Plan")
    print("   - Basic features")
    print("   - Standard support")
    print("\n2. Premium Plan")
    print("   - All basic features")
    print("   - Premium features")
    print("   - Priority support")
    print("\n3. Enterprise Plan")
    print("   - All premium features")
    print("   - Custom integrations")
    print("   - Dedicated support")
    print("   - Team management")
    print("   - Advanced security")


def get_plan_details(choice: str) -> Optional[Dict]:
    """Get details for the selected plan."""
    plans = {
        "1": {
            "name": "Basic Plan",
            "id": "basic",
            "description": "Basic features for individual users",
        },
        "2": {
            "name": "Premium Plan",
            "id": "premium",
            "description": "Advanced features for power users",
        },
        "3": {
            "name": "Enterprise Plan",
            "id": "enterprise",
            "description": "Custom solutions for organizations",
        },
    }
    return plans.get(choice)


def run_cli() -> None:
    """Run the CLI interface."""
    while True:
        # Display available plans
        display_plans()

        # Get user choice
        choice = input("\nSelect a plan (1-3) or 'q' to quit: ").strip()

        if choice.lower() == "q":
            print("\nGoodbye!")
            break

        # Get plan details
        plan = get_plan_details(choice)
        if not plan:
            print("\nInvalid choice. Please try again.")
            continue

        # Confirm selection
        print(f"\nYou selected: {plan['name']}")
        print(f"Description: {plan['description']}")
        confirm = input("\nProceed with payment? (y/n): ").strip().lower()

        if confirm == "y":
            try:
                # Get customer email
                email = input("\nEnter your email address: ").strip()

                # Start payment flow
                start_payment_flow(plan["id"], email)
                break

            except Exception as e:
                print(f"\nError: {str(e)}")
                continue
        else:
            print("\nSelection cancelled.")


if __name__ == "__main__":
    run_cli()
