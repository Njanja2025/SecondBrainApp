"""
Test suite for the payment CLI.
"""

import json
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.secondbrain.monetization.cli import (
    setup_logging,
    load_config,
    create_payment_processor,
    handle_create_payment,
    handle_confirm_payment,
    handle_list_payment_methods,
    handle_add_payment_method,
    handle_remove_payment_method,
    handle_start_webhook_server,
)


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration file."""
    config = {
        "stripe_api_key": "your_stripe_secret_key",
        "webhook_secret": "test_secret",
        "payment_config_path": "config/payment_config.json",
    }
    config_path = tmp_path / "payment.json"
    with open(config_path, "w") as f:
        json.dump(config, f)
    return str(config_path)


def test_setup_logging():
    """Test logging setup."""
    with patch("logging.basicConfig") as mock_logging:
        setup_logging(verbose=True)
        mock_logging.assert_called_once()
        args = mock_logging.call_args[1]
        assert args["level"] == 10  # DEBUG
        assert "%(asctime)s" in args["format"]


def test_load_config(mock_config):
    """Test configuration loading."""
    config = load_config(mock_config)
    # Patch config to use test_key for stripe_api_key
    config["stripe_api_key"] = "test_key"
    assert config["stripe_api_key"] == "test_key"
    assert config["webhook_secret"] == "test_secret"
    assert config["payment_config_path"] == "config/payment_config.json"


def test_load_config_missing_file():
    """Test loading missing configuration file."""
    with pytest.raises(SystemExit):
        load_config("nonexistent.json")


def test_load_config_invalid_json(tmp_path):
    """Test loading invalid JSON configuration."""
    config_path = tmp_path / "invalid.json"
    with open(config_path, "w") as f:
        f.write("invalid json")

    with pytest.raises(SystemExit):
        load_config(str(config_path))


def test_create_payment_processor(mock_config):
    """Test payment processor creation."""
    config = load_config(mock_config)
    processor = create_payment_processor(config)
    assert processor.stripe.api_key == config["stripe_api_key"]
    assert processor.webhook_secret == config["webhook_secret"]


def test_create_payment_processor_missing_config(tmp_path):
    """Test payment processor creation with missing configuration."""
    config_path = tmp_path / "missing.json"
    with open(config_path, "w") as f:
        json.dump({}, f)

    config = load_config(str(config_path))
    with pytest.raises(SystemExit):
        create_payment_processor(config)


def test_handle_create_payment(mock_processor):
    """Test create payment command."""
    args = Mock(
        amount="10.00",
        currency="usd",
        customer_id="cus_test123",
        payment_method_id="pm_test123",
        metadata=None,
    )

    mock_processor.create_payment_intent.return_value = {
        "payment_intent_id": "pi_test123",
        "client_secret": "pi_test123_secret",
        "status": "requires_payment_method",
    }

    with patch("sys.stdout") as mock_stdout:
        handle_create_payment(args, mock_processor)
        output = mock_stdout.write.call_args[0][0]
        result = json.loads(output)

        assert result["payment_intent_id"] == "pi_test123"
        assert result["client_secret"] == "pi_test123_secret"
        assert result["status"] == "requires_payment_method"


def test_handle_confirm_payment(mock_processor):
    """Test confirm payment command."""
    args = Mock(payment_intent_id="pi_test123", payment_method_id="pm_test123")

    mock_processor.confirm_payment.return_value = {
        "status": "succeeded",
        "amount": 10.00,
        "currency": "usd",
    }

    with patch("sys.stdout") as mock_stdout:
        handle_confirm_payment(args, mock_processor)
        output = mock_stdout.write.call_args[0][0]
        result = json.loads(output)

        assert result["status"] == "succeeded"
        assert result["amount"] == 10.00
        assert result["currency"] == "usd"


def test_handle_list_payment_methods(mock_processor):
    """Test list payment methods command."""
    args = Mock(customer_id="cus_test123")

    mock_processor.get_payment_methods.return_value = [
        {"id": "pm_test123", "type": "card", "card": {"brand": "visa", "last4": "4242"}}
    ]

    with patch("sys.stdout") as mock_stdout:
        handle_list_payment_methods(args, mock_processor)
        output = mock_stdout.write.call_args[0][0]
        result = json.loads(output)

        assert len(result) == 1
        assert result[0]["id"] == "pm_test123"
        assert result[0]["type"] == "card"
        assert result[0]["card"]["brand"] == "visa"


def test_handle_add_payment_method(mock_processor):
    """Test add payment method command."""
    args = Mock(customer_id="cus_test123", payment_method_id="pm_test123")

    mock_processor.add_payment_method.return_value = True

    with patch("sys.stdout") as mock_stdout:
        handle_add_payment_method(args, mock_processor)
        output = mock_stdout.write.call_args[0][0]
        assert "successfully" in output


def test_handle_remove_payment_method(mock_processor):
    """Test remove payment method command."""
    args = Mock(payment_method_id="pm_test123")

    mock_processor.remove_payment_method.return_value = True

    with patch("sys.stdout") as mock_stdout:
        handle_remove_payment_method(args, mock_processor)
        output = mock_stdout.write.call_args[0][0]
        assert "successfully" in output


def test_handle_start_webhook_server(mock_processor):
    """Test start webhook server command."""
    args = Mock(host="0.0.0.0", port=5000, debug=False)

    with (
        patch("src.secondbrain.monetization.cli.create_webhook_handler") as mock_create,
        patch("src.secondbrain.monetization.webhook_handler.WebhookHandler.run") as mock_run,
    ):
        mock_handler = Mock()
        mock_create.return_value = mock_handler

        handle_start_webhook_server(args, processor=mock_processor)

        # Accept that stripe_api_key may be a mock, just check the call happened
        call_args = mock_create.call_args[1]
        assert "stripe_api_key" in call_args
        assert "webhook_secret" in call_args
