"""
Tests for the Stripe webhook handler.
"""

import pytest
from src.secondbrain.utils.webhook_handler import handle_event


def test_checkout_completed_event():
    response = handle_event("checkout_completed")
    assert response.status_code == 200


def test_subscription_deleted_event():
    response = handle_event("subscription_deleted")
    assert response.status_code == 200


def test_payment_failed_event():
    response = handle_event("payment_failed")
    assert response.status_code == 200


def test_subscription_updated_event():
    response = handle_event("subscription_updated")
    assert response.status_code == 200
