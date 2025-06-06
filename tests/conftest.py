import pytest
from unittest.mock import Mock, patch
from src.secondbrain.system_monitor_plugin import SystemMonitorPlugin
from src.secondbrain.plugins.weather_plugin import WeatherPlugin

# Remove global patching fixture for decrypt_api_key

@pytest.fixture(scope="session")
def system_monitor_plugin():
    return SystemMonitorPlugin()

@pytest.fixture(scope="session")
def weather_plugin():
    return WeatherPlugin()

@pytest.fixture
def mock_stripe_key():
    """Reusable mock Stripe secret key."""
    return "test_key"

@pytest.fixture
def mock_stripe():
    """Mock Stripe API for all payment tests."""
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
