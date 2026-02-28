import pytest
from pydantic import ValidationError
from app.schemas.order import CreateOrderRequest, OrderResponse


def test_create_order_request_valid():
    """Test valid CreateOrderRequest instantiation"""
    data = {
        "inquiry_id": "inq-123",
        "tenant_id": "tenant-456",
        "customer_name": "John Doe",
        "customer_phone": "+1234567890",
        "customer_address": "123 Main St"
    }
    req = CreateOrderRequest(**data)
    assert req.inquiry_id == "inq-123"
    assert req.tenant_id == "tenant-456"
    assert req.customer_name == "John Doe"
    assert req.customer_phone == "+1234567890"
    assert req.customer_address == "123 Main St"


def test_create_order_request_minimal():
    """Test CreateOrderRequest with minimal required fields"""
    data = {
        "inquiry_id": "inq-123",
        "tenant_id": "tenant-456",
        "customer_name": "John Doe",
        "customer_phone": "+1234567890"
    }
    req = CreateOrderRequest(**data)
    assert req.customer_address is None


def test_create_order_request_missing_required():
    """Test CreateOrderRequest validation error for missing required fields"""
    with pytest.raises(ValidationError):
        CreateOrderRequest(inquiry_id="inq-123")  # Missing tenant_id, customer_name, customer_phone


def test_order_response_valid():
    """Test valid OrderResponse instantiation"""
    data = {
        "id": "order-123",
        "tenant_id": "tenant-456",
        "inquiry_id": "inq-789",
        "contact_id": "contact-101",
        "amount": 100.50,
        "customer_name": "Jane Doe",
        "customer_phone": "+0987654321",
        "customer_address": "456 Elm St",
        "retention_tag": "premium"
    }
    resp = OrderResponse(**data)
    assert resp.id == "order-123"
    assert resp.amount == 100.50
    assert resp.retention_tag == "premium"
