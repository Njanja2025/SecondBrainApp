"""
Generate Payment Gateway Setup Links
"""

import os
import sys
import logging
import webbrowser
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from deploy_config import DeployConfig
from src.secondbrain.payments.payment_gateway import PaymentGateway

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PaymentSetup:
    """Handle payment gateway setup."""

    def __init__(self, config: DeployConfig):
        """Initialize payment setup."""
        self.config = config
        self.payment_gateway = PaymentGateway(config)

    def validate_stripe_config(self) -> Tuple[bool, str]:
        """
        Validate Stripe configuration.

        Returns:
            Tuple of (success, message)
        """
        try:
            api_key = self.config.stripe_api_key
            if not api_key:
                return False, "Stripe API key not found in config"

            # Test API key
            import stripe

            stripe.api_key = api_key
            stripe.Account.retrieve()

            return True, "Stripe configuration is valid"

        except stripe.error.AuthenticationError:
            return False, "Invalid Stripe API key"
        except Exception as e:
            logger.error(f"Failed to validate Stripe config: {e}")
            return False, str(e)

    def validate_paypal_config(self) -> Tuple[bool, str]:
        """
        Validate PayPal configuration.

        Returns:
            Tuple of (success, message)
        """
        try:
            client_id = self.config.paypal_client_id
            client_secret = self.config.paypal_client_secret

            if not client_id or not client_secret:
                return False, "PayPal credentials not found in config"

            # Test credentials
            import paypalrestsdk

            paypalrestsdk.configure(
                {
                    "mode": "sandbox",
                    "client_id": client_id,
                    "client_secret": client_secret,
                }
            )

            # Test API call
            paypalrestsdk.Payment.all()

            return True, "PayPal configuration is valid"

        except Exception as e:
            logger.error(f"Failed to validate PayPal config: {e}")
            return False, str(e)

    def generate_stripe_links(self) -> Dict[str, str]:
        """Generate Stripe setup links."""
        try:
            # Validate config
            success, message = self.validate_stripe_config()
            if not success:
                logger.error(message)
                return {}

            # Generate dashboard link
            dashboard_link = "https://dashboard.stripe.com/"

            # Generate API key link
            api_key_link = "https://dashboard.stripe.com/apikeys"

            # Generate webhook link
            webhook_link = "https://dashboard.stripe.com/webhooks"

            # Generate test mode link
            test_mode_link = "https://dashboard.stripe.com/test/apikeys"

            # Generate documentation link
            docs_link = "https://stripe.com/docs/api"

            return {
                "dashboard": dashboard_link,
                "api_keys": api_key_link,
                "webhooks": webhook_link,
                "test_mode": test_mode_link,
                "documentation": docs_link,
            }

        except Exception as e:
            logger.error(f"Failed to generate Stripe links: {e}")
            return {}

    def generate_paypal_links(self) -> Dict[str, str]:
        """Generate PayPal setup links."""
        try:
            # Validate config
            success, message = self.validate_paypal_config()
            if not success:
                logger.error(message)
                return {}

            # Generate dashboard link
            dashboard_link = "https://www.paypal.com/business/merchant-services"

            # Generate API credentials link
            api_creds_link = "https://developer.paypal.com/dashboard/credentials"

            # Generate webhook link
            webhook_link = "https://developer.paypal.com/dashboard/webhooks"

            # Generate sandbox link
            sandbox_link = "https://developer.paypal.com/dashboard/accounts"

            # Generate documentation link
            docs_link = "https://developer.paypal.com/docs/api/overview/"

            return {
                "dashboard": dashboard_link,
                "api_credentials": api_creds_link,
                "webhooks": webhook_link,
                "sandbox": sandbox_link,
                "documentation": docs_link,
            }

        except Exception as e:
            logger.error(f"Failed to generate PayPal links: {e}")
            return {}

    def save_links(self, links: Dict[str, Dict[str, str]]):
        """Save links to a JSON file."""
        try:
            output_dir = Path("deployment")
            output_dir.mkdir(exist_ok=True)

            output_file = output_dir / "payment_links.json"
            with open(output_file, "w") as f:
                json.dump(links, f, indent=2)

            logger.info(f"Payment links saved to {output_file}")

        except Exception as e:
            logger.error(f"Failed to save links: {e}")

    def open_links(self, links: Dict[str, str]):
        """Open links in default browser."""
        for name, url in links.items():
            logger.info(f"Opening {name} link: {url}")
            webbrowser.open(url)

    def setup(self) -> Tuple[bool, str]:
        """
        Run complete payment gateway setup.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Generate Stripe links
            stripe_links = self.generate_stripe_links()
            if not stripe_links:
                return False, "Failed to generate Stripe links"

            # Generate PayPal links
            paypal_links = self.generate_paypal_links()
            if not paypal_links:
                return False, "Failed to generate PayPal links"

            # Save links
            self.save_links({"stripe": stripe_links, "paypal": paypal_links})

            # Open links
            self.open_links(stripe_links)
            self.open_links(paypal_links)

            return True, "Payment gateway setup completed successfully"

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False, str(e)


def main():
    """Run payment gateway setup."""
    try:
        # Load configuration
        config = DeployConfig.from_env()

        # Initialize setup
        setup = PaymentSetup(config)

        # Run setup
        success, message = setup.setup()

        if success:
            logger.info(message)
            sys.exit(0)
        else:
            logger.error(message)
            sys.exit(1)

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
