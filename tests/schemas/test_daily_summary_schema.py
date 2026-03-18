# tests/schemas/test_daily_summary.py

import pytest
from datetime import date
from decimal import Decimal
from app.schemas.daily_summary import (
    ProductSummary,
    DailySummaryResponse,
    ComplianceMetricsResponse,
)


def test_product_summary_valid():
    """Test ProductSummary schema."""

    data = {
        "product_name": "Rice",
        "quantity": 10,
        "total_amount": Decimal("4000.00"),
    }

    schema = ProductSummary(**data)

    assert schema.product_name == "Rice"
    assert schema.quantity == 10
    assert schema.total_amount == Decimal("4000.00")


def test_daily_summary_response_valid():
    """Test full DailySummaryResponse schema with products."""

    data = {
        "id": "DS001",
        "tenant_id": "T001",
        "summary_date": date.today(),
        "total_orders": 2,
        "total_revenue": Decimal("38440"),
        "paid_orders": 1,
        "paid_revenue": Decimal("10000"),
        "total_inquiries": 5,
        "confirmed_inquiries": 3,
        "dropped_inquiries": 2,
        "opt_outs": 0,
        "blocked_sends": 0,
        "failed_sends": 1,
        "quality_warnings": 0,
        "products": [
            {
                "product_name": "Rice",
                "quantity": 12,
                "total_amount": Decimal("4000"),
            },
            {
                "product_name": "Milk",
                "quantity": 5,
                "total_amount": Decimal("34440"),
            },
        ],
    }

    schema = DailySummaryResponse(**data)

    assert schema.total_orders == 2
    assert len(schema.products) == 2
    assert schema.products[0].product_name == "Rice"
    assert schema.products[1].total_amount == Decimal("34440")


def test_daily_summary_missing_required_fields():
    """Missing required fields should fail."""

    data = {
        "id": "DS002",
        "tenant_id": "T001",
        # missing summary_date and others
    }

    with pytest.raises(Exception):
        DailySummaryResponse(**data)


def test_compliance_metrics_response():
    """Test compliance metrics schema."""

    data = {
        "opt_outs": 1,
        "blocked_sends": 2,
        "failed_sends": 0,
        "quality_warnings": 1,
    }

    schema = ComplianceMetricsResponse(**data)

    assert schema.opt_outs == 1
    assert schema.blocked_sends == 2


def test_daily_summary_from_orm():
    """Test ORM compatibility with nested products."""

    class FakeProduct:
        def __init__(self, name, qty, amount):
            self.product_name = name
            self.quantity = qty
            self.total_amount = amount

    class FakeSummary:
        def __init__(self):
            self.id = "DS003"
            self.tenant_id = "T001"
            self.summary_date = date.today()
            self.total_orders = 2
            self.total_revenue = Decimal("38440")
            self.paid_orders = 1
            self.paid_revenue = Decimal("10000")
            self.total_inquiries = 5
            self.confirmed_inquiries = 3
            self.dropped_inquiries = 2
            self.opt_outs = 0
            self.blocked_sends = 0
            self.failed_sends = 0
            self.quality_warnings = 0
            self.products = [
                FakeProduct("Rice", 12, Decimal("4000")),
                FakeProduct("Milk", 5, Decimal("34440")),
            ]

    orm_obj = FakeSummary()

    schema = DailySummaryResponse.model_validate(orm_obj)

    assert schema.id == "DS003"
    assert len(schema.products) == 2
    assert schema.products[0].product_name == "Rice"