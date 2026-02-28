import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError
from app.schemas.payment import PaymentCreateRequest, PaymentResponse


def test_payment_create_request_valid():
    """Test valid PaymentCreateRequest instantiation"""
    data = {
        "order_id": "order-123",
        "amount": Decimal("150.00"),
        "verified_by": "admin-user",
        "method": "cash",
        "notes": "Payment received"
    }
    req = PaymentCreateRequest(**data)
    assert req.order_id == "order-123"
    assert req.amount == Decimal("150.00")
    assert req.verified_by == "admin-user"
    assert req.method == "cash"
    assert req.notes == "Payment received"


def test_payment_create_request_minimal():
    """Test PaymentCreateRequest with minimal required fields"""
    data = {
        "order_id": "order-123",
        "amount": Decimal("100.00"),
        "verified_by": "user-456",
        "method": "card"
    }
    req = PaymentCreateRequest(**data)
    assert req.notes is None


def test_payment_create_request_missing_required():
    """Test PaymentCreateRequest validation error for missing required fields"""
    with pytest.raises(ValidationError):
        PaymentCreateRequest(order_id="order-123", amount=Decimal("100.00"))  # Missing verified_by, method


def test_payment_response_valid():
    """Test valid PaymentResponse instantiation"""
    data = {
        "id": "pay-123",
        "order_id": "order-456",
        "amount": Decimal("200.00"),
        "verified_by": "verifier-789",
        "timestamp": "2023-10-01T12:00:00",
        "method": "bank_transfer",
        "notes": "Verified payment"
    }
    resp = PaymentResponse(**data)
    assert resp.id == "pay-123"
    assert resp.amount == Decimal("200.00")
    assert resp.timestamp == "2023-10-01T12:00:00"


def test_payment_response_from_orm():
    """Test PaymentResponse.from_orm classmethod"""
    # Mock a Payment model-like object
    class MockPayment:
        def __init__(self):
            self.id = "pay-123"
            self.order_id = "order-456"
            self.amount = Decimal("150.00")
            self.verified_by = "verifier-789"
            self.timestamp = datetime(2023, 10, 1, 12, 0, 0)
            self.method = "cash"
            self.notes = "Test payment"

    mock_payment = MockPayment()
    resp = PaymentResponse.from_orm(mock_payment)

    assert resp.id == "pay-123"
    assert resp.order_id == "order-456"
    assert resp.amount == Decimal("150.00")
    assert resp.verified_by == "verifier-789"
    assert resp.timestamp == "2023-10-01T12:00:00"
    assert resp.method == "cash"
    assert resp.notes == "Test payment"
