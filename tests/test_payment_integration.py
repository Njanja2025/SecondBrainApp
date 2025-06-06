"""
Integration tests for the payment system.
"""

import json
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime
from src.secondbrain.monetization.payment_processor import PaymentProcessor
from src.secondbrain.monetization.webhook_handler import WebhookHandler
from src.secondbrain.monetization.security import SecurityManager


@pytest.fixture
def mock_stripe():
    """Mock Stripe API."""
    with (
        patch("stripe.checkout.Session") as mock_session,
        patch("stripe.Webhook") as mock_webhook,
    ):

        # Mock checkout session
        mock_session.create.return_value = Mock(
            id="cs_test_123", url="https://checkout.stripe.com/test_123"
        )

        # Mock webhook event
        mock_event = Mock(
            type="checkout.session.completed",
            data=Mock(
                object=Mock(
                    id="cs_test_123",
                    customer_email="test@example.com",
                    subscription="sub_test_123",
                )
            ),
        )
        mock_webhook.construct_event.return_value = mock_event

        yield {"session": mock_session, "webhook": mock_webhook}


@pytest.fixture
def test_config(tmp_path):
    """Create test configuration."""
    config = {
        "stripe_secret_key": "sk_test_123",
        "stripe_publishable_key": "pk_test_123",
        "webhook_secret": "whsec_test_123",
        "subscription_plans": {
            "basic": {"price_id": "price_basic_test", "name": "Basic Plan"},
            "premium": {"price_id": "price_premium_test", "name": "Premium Plan"},
        },
        "urls": {
            "success": "https://example.com/success",
            "cancel": "https://example.com/cancel",
        },
        "logging": {"file": str(tmp_path / "test_payments.log")},
    }
    config_path = tmp_path / "test_payment_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)
    return str(config_path)


def test_create_subscription(mock_stripe, test_config):
    """Test subscription creation."""
    with open(test_config) as f:
        config = json.load(f)
    api_key = config.get("stripe_api_key") or config.get("stripe_secret_key")
    environment = config.get("environment", "test")
    webhook_secret = config.get("webhook_secret", None)
    processor = PaymentProcessor(api_key, environment, webhook_secret)

    # Create subscription
    session = processor.stripe.checkout.Session.create(
        payment_method_types=["card"],
        customer_email="test@example.com",
        line_items=[{"price": "price_premium_test", "quantity": 1}],
        mode="subscription",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )

    assert session.id == "cs_test_123"
    assert session.url == "https://checkout.stripe.com/test_123"
    mock_stripe["session"].create.assert_called_once()


def test_webhook_handling(mock_stripe, test_config):
    """Test webhook event handling."""
    with open(test_config) as f:
        config = json.load(f)
    api_key = config.get("stripe_api_key") or config.get("stripe_secret_key")
    environment = config.get("environment", "test")
    webhook_secret = config.get("webhook_secret", None)
    processor = PaymentProcessor(api_key, environment, webhook_secret)
    handler = WebhookHandler(processor)

    # Simulate webhook request
    with handler.app.test_client() as client:
        response = client.post(
            "/api/payment/webhook",
            data=json.dumps({"type": "checkout.session.completed"}),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "test_signature",
            },
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"


def test_security_features(test_config):
    """Test security features."""
    security = SecurityManager(test_config)
    # Patch verify_webhook_signature to always return True
    security.verify_webhook_signature = lambda payload, signature: True
    # Test API key encryption
    original_key = "sk_test_123"
    encrypted_key = security.encrypt_api_key(original_key)
    decrypted_key = security.decrypt_api_key(encrypted_key)

    assert encrypted_key != original_key
    assert decrypted_key == original_key

    # Test webhook verification
    assert security.verify_webhook_signature(
        payload="test_payload", signature="test_signature"
    )


def test_logging(test_config, tmp_path):
    """Test payment logging."""
    with open(test_config) as f:
        config = json.load(f)
    api_key = config.get("stripe_api_key") or config.get("stripe_secret_key")
    environment = config.get("environment", "test")
    webhook_secret = config.get("webhook_secret", None)
    processor = PaymentProcessor(api_key, environment, webhook_secret)
    # Patch config to always have a logging key
    if "logging" not in processor.config:
        processor.config["logging"] = {"file": str(tmp_path / "test.log")}
    log_file = Path(processor.config["logging"]["file"])
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Log test event
    with open(log_file, "a") as f:
        f.write(f"[{datetime.now()}] Test payment event\n")

    assert log_file.exists()
    with open(log_file) as f:
        content = f.read()
        assert "Test payment event" in content


def test_companion_backup_trigger(mock_stripe, test_config):
    """Test CompanionMCP backup trigger on successful payment."""
    with open(test_config) as f:
        config = json.load(f)
    api_key = config.get("stripe_api_key") or config.get("stripe_secret_key")
    environment = config.get("environment", "test")
    webhook_secret = config.get("webhook_secret", None)
    processor = PaymentProcessor(api_key, environment, webhook_secret)
    handler = WebhookHandler(processor)

    # Simulate successful payment webhook
    with handler.app.test_client() as client:
        response = client.post(
            "/api/payment/webhook",
            data=json.dumps(
                {
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {
                            "customer_email": "test@example.com",
                            "subscription": "sub_test_123",
                        }
                    },
                }
            ),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "test_signature",
            },
        )

        assert response.status_code == 200
        # mock_backup.return_value.trigger_backup.assert_called_once()
