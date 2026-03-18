# tests/routers/test_summary_router.py
import pytest
from datetime import date
from app.db.models_import import DailySummary, Tenant, Transaction, TransactionItem
from decimal import Decimal

# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def daily_summary_data(db_session, tenant):
    """Create a DailySummary record for testing."""
    # Create 5 transactions with items for the date
    summary_date = date(2026, 3, 18)
    transactions = []
    for i in range(5):
        txn = Transaction(
            id=f"TXN{tenant.id}{i+1:03d}",
            tenant_id=tenant.id,
            seller_phone="+250123456789",
            created_at=summary_date
        )
        # Add items to transaction
        item = TransactionItem(
            id=f"ITEM{tenant.id}{i+1:03d}01",
            transaction_id=txn.id,
            tenant_id=tenant.id,
            product_name="Test Product",
            quantity=1,
            total_amount=Decimal("2000.00")
        )
        txn.items = [item]
        db_session.add(txn)
        db_session.add(item)
        transactions.append(txn)

    # Original DailySummary (will be updated by service)
    summary = DailySummary(
        tenant_id=tenant.id,
        summary_date=summary_date,
        total_orders=5,
        total_revenue=10000.0,
        paid_orders=4,
        paid_revenue=8000.0
    )
    db_session.add(summary)
    db_session.commit()
    return summary


# -----------------------------
# Test /summary/daily endpoint
# -----------------------------
def test_get_daily_summary(client, db_session, tenant, daily_summary_data):
    """Returns correct daily summary when data exists."""
    response = client.get(
        "/summary/daily",
        params={
            "tenant_id": tenant.id,
            "summary_date": "2026-03-18"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["tenant_id"] == tenant.id
    assert data["summary_date"] == "2026-03-18"
    assert data["total_orders"] == 5
    assert data["total_revenue"] == 10000.0
    assert data["paid_orders"] == 5
    assert data["paid_revenue"] == 10000.0
    assert isinstance(data["items"], list)


def test_get_daily_summary_no_data(client, db_session, tenant):
    """Returns default/empty summary when no DailySummary exists for the date."""
    response = client.get(
        "/summary/daily",
        params={
            "tenant_id": tenant.id,
            "summary_date": "2026-03-19"  # No data for this date
        }
    )

    # Ensure endpoint still responds successfully
    assert response.status_code == 200
    data = response.json()

    # If your service returns None or empty object, assert reasonable defaults
    assert data["tenant_id"] == tenant.id
    assert data["summary_date"] == "2026-03-19"
    assert data.get("total_orders") in (None, 0)
    assert data.get("total_revenue") in (None, 0.0)
    assert data.get("paid_orders") in (None, 0)
    assert data.get("paid_revenue") in (None, 0.0)
    assert isinstance(data["items"], list)
