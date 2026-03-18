# tests/schemas/test_payment.py

import pytest
from decimal import Decimal
from datetime import datetime
from app.schemas.payment import PaymentCreateRequest, PaymentResponse


def test_payment_create_request_valid():
    """Test PaymentCreateRequest schema creation."""

    data = {
        "order_id": "O001",
        "amount": Decimal("1500.50"),
        "verified_by": "admin",
        "method": "momo",
        "notes": "Customer paid full amount"
    }

    schema = PaymentCreateRequest(**data)

    assert schema.order_id == "O001"
    assert schema.amount == Decimal("1500.50")
    assert schema.method == "momo"
    assert schema.notes == "Customer paid full amount"


def test_payment_create_request_optional_notes():
    """Test PaymentCreateRequest without notes field."""

    data = {
        "order_id": "O002",
        "amount": Decimal("2000"),
        "verified_by": "staff",
        "method": "cash"
    }

    schema = PaymentCreateRequest(**data)

    assert schema.notes is None


def test_payment_response_from_orm():
    """Test PaymentResponse.from_orm properly formats timestamp."""

    class FakePaymentORM:
        def __init__(self):
            self.id = "P001"
            self.tenant_id = "T001"
            self.order_id = "O001"
            self.amount = Decimal("1500.50")
            self.verified_by = "admin"
            self.method = "momo"
            self.notes = "Paid in full"
            self.timestamp = datetime(2026, 3, 18, 11, 0, 0)

    orm_obj = FakePaymentORM()

    schema = PaymentResponse.from_orm(orm_obj)

    assert schema.id == "P001"
    assert schema.tenant_id == "T001"
    assert schema.order_id == "O001"
    assert schema.amount == Decimal("1500.50")
    assert schema.verified_by == "admin"
    assert schema.method == "momo"
    assert schema.notes == "Paid in full"
    assert schema.timestamp == "2026-03-18T11:00:00"


def test_payment_response_model_config():
    """Ensure PaymentResponse uses from_attributes for Pydantic V2 compatibility."""

    data = {
        "id": "P002",
        "tenant_id": "T002",
        "order_id": "O002",
        "amount": Decimal("500"),
        "verified_by": "staff",
        "method": "cash",
        "notes": None,
        "timestamp": "2026-03-18T11:00:00",
    }

    schema = PaymentResponse.model_validate(data)

    assert schema.id == "P002"
    assert schema.amount == Decimal("500")
    assert schema.timestamp == "2026-03-18T11:00:00"