"""
Tests for the Stripe webhook handler.
"""

import json
import pytest
import stripe
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.secondbrain.monetization.webhook_handler import app


@pytest.fixture
def client():
    """Create a test client."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_stripe():
    """Mock Stripe API calls."""
    with patch("stripe.Webhook.construct_event") as mock:
        yield mock


def test_checkout_completed_event(client, mock_stripe):
    """Test handling of checkout completed event."""
    # Mock event data
    event_data = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer_email": "test@example.com",
                "subscription": "sub_123",
                "amount_total": 999,
                "currency": "usd",
            }
        },
    }
    mock_stripe.return_value = event_data

    # Send request
    response = client.post(
        "/webhook",
        data=json.dumps(event_data),
        headers={"Stripe-Signature": "test_sig"},
    )

    # Verify response
    assert response.status_code == 200
    assert response.json["status"] == "success"


def test_subscription_deleted_event(client, mock_stripe):
    """Test handling of subscription deleted event."""
    # Mock event data
    event_data = {
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_123",
                "status": "canceled",
                "canceled_at": int(datetime.now().timestamp()),
            }
        },
    }
    mock_stripe.return_value = event_data

    # Send request
    response = client.post(
        "/webhook",
        data=json.dumps(event_data),
        headers={"Stripe-Signature": "test_sig"},
    )

    # Verify response
    assert response.status_code == 200
    assert response.json["status"] == "success"


def test_payment_failed_event(client, mock_stripe):
    """Test handling of payment failed event."""
    # Mock event data
    event_data = {
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "id": "in_456",
                "customer": "cus_123",
                "customer_email": "test@example.com",
                "amount_due": 999,
                "attempt_count": 1,
            }
        },
    }
    mock_stripe.return_value = event_data

    # Send request
    response = client.post(
        "/webhook",
        data=json.dumps(event_data),
        headers={"Stripe-Signature": "test_sig"},
    )

    # Verify response
    assert response.status_code == 200
    assert response.json["status"] == "success"


def test_subscription_updated_event(client, mock_stripe):
    """Test handling of subscription updated event."""
    # Mock event data
    event_data = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_123",
                "status": "active",
                "current_period_end": int(datetime.now().timestamp()),
            }
        },
    }
    mock_stripe.return_value = event_data

    # Send request
    response = client.post(
        "/webhook",
        data=json.dumps(event_data),
        headers={"Stripe-Signature": "test_sig"},
    )

    # Verify response
    assert response.status_code == 200
    assert response.json["status"] == "success"


def test_invalid_signature(client):
    """Test handling of invalid signature."""
    # Mock Stripe to raise signature error
    with patch(
        "stripe.Webhook.construct_event",
        side_effect=stripe.error.SignatureVerificationError(
            message="Invalid signature", sig_header="test_sig"
        ),
    ):
        # Send request
        response = client.post(
            "/webhook",
            data=json.dumps({"type": "test"}),
            headers={"Stripe-Signature": "invalid_sig"},
        )

        # Verify response
        assert response.status_code == 400
        assert response.json["error"] == "Invalid signature"


def test_missing_signature(client):
    """Test handling of missing signature."""
    # Send request without signature
    response = client.post("/webhook", data=json.dumps({"type": "test"}))

    # Verify response
    assert response.status_code == 400
    assert "error" in response.json


def test_invalid_payload(client):
    """Test handling of invalid payload."""
    # Send request with invalid JSON
    response = client.post(
        "/webhook", data="invalid json", headers={"Stripe-Signature": "test_sig"}
    )

    # Verify response
    assert response.status_code == 400
    assert "error" in response.json


def test_unknown_event_type(client, mock_stripe):
    """Test handling of unknown event type."""
    # Mock event data
    event_data = {"type": "unknown.event.type", "data": {"object": {}}}
    mock_stripe.return_value = event_data

    # Send request
    response = client.post(
        "/webhook",
        data=json.dumps(event_data),
        headers={"Stripe-Signature": "test_sig"},
    )

    # Verify response
    assert response.status_code == 200
    assert response.json["status"] == "success"
