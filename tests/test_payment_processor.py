"""
Test suite for the payment processor.
"""

import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from pathlib import Path
from src.secondbrain.monetization.payment_processor import PaymentProcessor


@pytest.fixture
def mock_stripe():
    """Mock Stripe API."""
    with (
        patch("stripe.PaymentIntent") as mock_payment_intent,
        patch("stripe.PaymentMethod") as mock_payment_method,
        patch("stripe.Webhook") as mock_webhook,
    ):

        # Mock payment intent
        mock_intent = Mock()
        mock_intent.id = "pi_test123"
        mock_intent.client_secret = "pi_test123_secret"
        mock_intent.status = "requires_payment_method"
        mock_intent.amount = 1000
        mock_intent.currency = "usd"
        mock_intent.customer = "cus_test123"
        mock_payment_intent.create.return_value = mock_intent
        mock_payment_intent.confirm.return_value = mock_intent

        # Mock payment method
        mock_pm = Mock()
        mock_pm.id = "pm_test123"
        mock_pm.type = "card"
        mock_pm.card.brand = "visa"
        mock_pm.card.last4 = "4242"
        mock_pm.card.exp_month = 12
        mock_pm.card.exp_year = 2025
        mock_payment_method.list.return_value = Mock(data=[mock_pm])

        # Mock webhook
        mock_event = Mock()
        mock_event.type = "payment_intent.succeeded"
        mock_event.data.object = mock_intent
        mock_webhook.construct_event.return_value = mock_event

        yield {
            "payment_intent": mock_payment_intent,
            "payment_method": mock_payment_method,
            "webhook": mock_webhook,
        }


@pytest.fixture
def payment_processor(mock_stripe, tmp_path):
    """Create a payment processor instance."""
    config_path = tmp_path / "payment_config.json"
    processor = PaymentProcessor(
        stripe_api_key="test_key",
        webhook_secret="test_secret",
        config_path=str(config_path),
    )
    return processor


def test_create_default_config(payment_processor):
    """Test default configuration creation."""
    assert payment_processor.config_path.exists()
    with open(payment_processor.config_path) as f:
        config = json.load(f)

    assert "supported_currencies" in config
    assert "payment_methods" in config
    assert "tax_rates" in config


def test_create_payment_intent(payment_processor):
    """Test payment intent creation."""
    result = payment_processor.create_payment_intent(
        amount=10.00, currency="usd", customer_id="cus_test123"
    )

    assert result["payment_intent_id"] == "pi_test123"
    assert result["client_secret"] == "pi_test123_secret"
    assert result["status"] == "requires_payment_method"


def test_create_payment_intent_invalid_currency(payment_processor):
    """Test payment intent creation with invalid currency."""
    with pytest.raises(ValueError):
        payment_processor.create_payment_intent(
            amount=10.00, currency="invalid", customer_id="cus_test123"
        )


def test_confirm_payment(payment_processor):
    """Test payment confirmation."""
    result = payment_processor.confirm_payment(
        payment_intent_id="pi_test123", payment_method_id="pm_test123"
    )

    assert result["status"] == "requires_payment_method"
    assert result["amount"] == 10.00
    assert result["currency"] == "usd"


def test_get_payment_methods(payment_processor):
    """Test getting payment methods."""
    methods = payment_processor.get_payment_methods("cus_test123")

    assert len(methods) == 1
    method = methods[0]
    assert method["id"] == "pm_test123"
    assert method["type"] == "card"
    assert method["card"]["brand"] == "visa"
    assert method["card"]["last4"] == "4242"


def test_add_payment_method(payment_processor):
    """Test adding payment method."""
    result = payment_processor.add_payment_method(
        customer_id="cus_test123", payment_method_id="pm_test123"
    )
    assert result is True


def test_remove_payment_method(payment_processor):
    """Test removing payment method."""
    result = payment_processor.remove_payment_method("pm_test123")
    assert result is True


def test_handle_webhook_event(payment_processor):
    """Test webhook event handling."""
    result = payment_processor.handle_webhook_event(
        payload="test_payload", signature="test_signature"
    )

    assert result["status"] == "success"
    assert result["payment_intent_id"] == "pi_test123"
    assert result["amount"] == 10.00
    assert result["currency"] == "usd"


def test_get_tax_rate(payment_processor):
    """Test tax rate retrieval."""
    # Test standard rate
    rate = payment_processor.get_tax_rate("eur")
    assert rate == 0.20

    # Test reduced rate
    rate = payment_processor.get_tax_rate("eur", is_reduced=True)
    assert rate == 0.10

    # Test unsupported currency
    rate = payment_processor.get_tax_rate("invalid")
    assert rate == 0.0


def test_calculate_tax(payment_processor):
    """Test tax calculation."""
    # Test standard rate
    tax = payment_processor.calculate_tax(100.00, "eur")
    assert tax == 20.00

    # Test reduced rate
    tax = payment_processor.calculate_tax(100.00, "eur", is_reduced=True)
    assert tax == 10.00

    # Test zero tax
    tax = payment_processor.calculate_tax(100.00, "usd")
    assert tax == 0.00
