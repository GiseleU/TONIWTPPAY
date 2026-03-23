# tests/routers/test_summary_router.py

import pytest
from datetime import date
from decimal import Decimal
from app.db.models_import import Transaction, TransactionItem, DailySummary
from app.core.datetime_utils import get_start_of_day

# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def daily_summary_data(db_session, tenant):
    """Create 5 transactions with items for testing real-time summary."""
    summary_date = date(2026, 3, 18)

    for i in range(5):
        txn = Transaction(
            id=f"TXN{tenant.id}{i+1:03d}",
            tenant_id=tenant.id,
            seller_phone="+250123456789",
            created_at=get_start_of_day(summary_date)
        )
        item = TransactionItem(
            id=f"ITEM{tenant.id}{i+1:03d}01",
            transaction_id=txn.id,
            tenant_id=tenant.id,
            product_name="Test Product",
            quantity=1,
            unit_price=Decimal("2000.00"),
            total_amount=Decimal("2000.00")
        )
        txn.items = [item]
        db_session.add(txn)
        db_session.add(item)

    # Commit transactions
    db_session.commit()

    # Also create a DailySummary totals record (totals will be updated by service)
    summary = DailySummary(
        tenant_id=tenant.id,
        summary_date=summary_date,
        total_orders=5,
        total_revenue=10000.0,
        paid_orders=5,
        paid_revenue=10000.0
    )
    db_session.add(summary)
    db_session.commit()
    return summary


# -----------------------------
# Test /summary/daily endpoint
# -----------------------------
def test_get_daily_summary(client, db_session, tenant, daily_summary_data):
    """Returns correct daily summary with items."""
    response = client.get(
        "/summary/daily",
        params={"tenant_id": tenant.id, "summary_date": "2026-03-18"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["tenant_id"] == tenant.id
    assert data["summary_date"] == "2026-03-18"
    assert data["total_orders"] == 5
    assert data["total_revenue"] == 10000.0
    assert data["paid_orders"] == 5
    assert data["paid_revenue"] == 10000.0

    # Check items returned by get_today_summary
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    assert data["items"][0]["product_name"] == "Test Product"
    assert data["items"][0]["quantity"] == 5
    assert data["items"][0]["total_amount"] == 10000.0


def test_get_daily_summary_no_data(client, db_session, tenant):
    """Returns defaults when no data exists for the date."""
    response = client.get(
        "/summary/daily",
        params={"tenant_id": tenant.id, "summary_date": "2026-03-19"}  # no data
    )

    assert response.status_code == 200
    data = response.json()

    assert data["tenant_id"] == tenant.id
    assert data["summary_date"] == "2026-03-19"
    assert data.get("total_orders") in (0, None)
    assert data.get("total_revenue") in (0.0, None)
    assert data.get("paid_orders") in (0, None)
    assert data.get("paid_revenue") in (0.0, None)
    assert isinstance(data["items"], list)
    assert data["items"] == []