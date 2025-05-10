# Payment System Documentation

## Overview

The payment system provides a comprehensive solution for handling payments, subscriptions, and webhook events in the SecondBrain application. It integrates with Stripe for payment processing and supports multiple currencies, payment methods, and subscription plans.

## Features

- Payment processing with Stripe integration
- Multiple currency support (USD, EUR, GBP)
- Multiple payment method support (Credit Card, Bank Transfer)
- Subscription management with different tiers
- Webhook handling for payment events
- Tax calculation and management
- Command-line interface for management tasks

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Stripe:
   - Sign up for a Stripe account
   - Get your API keys from the Stripe dashboard
   - Update the `config/payment_config.json` file with your API keys

3. Set up webhook endpoints:
   - Configure your webhook endpoint in the Stripe dashboard
   - Update the webhook secret in the configuration file

## Configuration

The payment system is configured through the `config/payment_config.json` file. Key configuration options include:

- `stripe_api_key`: Your Stripe API key
- `webhook_secret`: Your Stripe webhook secret
- `supported_currencies`: List of supported currencies
- `payment_methods`: Available payment methods
- `tax_rates`: Tax rates for different currencies
- `subscription_plans`: Available subscription plans
- `webhook_server`: Webhook server configuration
- `logging`: Logging configuration

## Usage

### Command-line Interface

The payment system provides a command-line interface for common tasks:

1. Create a payment:
```bash
python -m src.secondbrain.monetization.cli create-payment \
    --amount 10.00 \
    --currency usd \
    --customer-id cus_123 \
    --payment-method-id pm_123
```

2. Confirm a payment:
```bash
python -m src.secondbrain.monetization.cli confirm-payment \
    --payment-intent-id pi_123 \
    --payment-method-id pm_123
```

3. List payment methods:
```bash
python -m src.secondbrain.monetization.cli list-payment-methods \
    --customer-id cus_123
```

4. Add a payment method:
```bash
python -m src.secondbrain.monetization.cli add-payment-method \
    --customer-id cus_123 \
    --payment-method-id pm_123
```

5. Remove a payment method:
```bash
python -m src.secondbrain.monetization.cli remove-payment-method \
    --payment-method-id pm_123
```

6. Start the webhook server:
```bash
python -m src.secondbrain.monetization.cli start-webhook-server \
    --host 0.0.0.0 \
    --port 5000 \
    --debug
```

### Programmatic Usage

You can also use the payment system programmatically:

```python
from src.secondbrain.monetization.payment_processor import PaymentProcessor
from src.secondbrain.monetization.webhook_handler import create_webhook_handler

# Create a payment processor
processor = PaymentProcessor(
    stripe_api_key="your_api_key",
    webhook_secret="your_webhook_secret"
)

# Create a payment intent
result = processor.create_payment_intent(
    amount=10.00,
    currency="usd",
    customer_id="cus_123"
)

# Start the webhook server
handler = create_webhook_handler(
    stripe_api_key="your_api_key",
    webhook_secret="your_webhook_secret"
)
handler.run()
```

## Subscription Plans

The system supports three subscription tiers:

1. Basic Plan ($9.99/month):
   - Basic journaling
   - Emotional tracking
   - Basic memory management

2. Premium Plan ($19.99/month):
   - Advanced journaling
   - Emotional analytics
   - Advanced memory management
   - AI-powered insights
   - Priority support

3. Enterprise Plan ($49.99/month):
   - All Premium features
   - Custom integrations
   - Dedicated support
   - Team management
   - Advanced security

## Webhook Events

The system handles the following webhook events:

- `payment_intent.succeeded`: Payment successful
- `payment_intent.payment_failed`: Payment failed
- `customer.subscription.updated`: Subscription updated
- `customer.subscription.deleted`: Subscription deleted

## Error Handling

The system includes comprehensive error handling:

- Invalid API keys
- Invalid webhook signatures
- Failed payments
- Network errors
- Configuration errors

All errors are logged with appropriate context and severity levels.

## Security

The payment system implements several security measures:

- Secure API key storage
- Webhook signature verification
- HTTPS for all communications
- Input validation
- Error message sanitization

## Testing

Run the test suite:

```bash
pytest tests/test_payment_processor.py
pytest tests/test_webhook_handler.py
pytest tests/test_cli.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 