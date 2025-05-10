"""
Payment configuration module.
"""
import json
from pathlib import Path

# Load configuration from JSON file
config_path = Path("config/payment_config.json")
with open(config_path) as f:
    config = json.load(f)

# Export configuration values
WEBHOOK_SECRET = config["webhook_secret"]
STRIPE_SECRET_KEY = config["stripe_secret_key"]
STRIPE_PUBLISHABLE_KEY = config["stripe_publishable_key"]
WEBHOOK_ENDPOINT = config["webhook_endpoint"]
SUPPORTED_CURRENCIES = config["supported_currencies"]
PAYMENT_METHODS = config["payment_methods"]
TAX_RATES = config["tax_rates"]
SUBSCRIPTION_PLANS = config["subscription_plans"]
URLS = config["urls"]
LOGGING = config["logging"]
SECURITY = config["security"] 