# tests/models/test_daily_summary.py

import pytest
from datetime import date
from decimal import Decimal
import uuid

from app.db.models_import import DailySummary, Tenant, Transaction, TransactionItem
from sqlalchemy import func

def test_daily_summary_creation(db_session):
    """Basic DailySummary creation test."""
    tenant = Tenant(id="T001", name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    summary_date = date.today()

    summary = DailySummary(
        id="DS001",
        tenant_id=tenant.id,
        summary_date=summary_date,
        total_orders=10,
        total_revenue=Decimal("100.0")
    )
    db_session.add(summary)
    db_session.commit()

    assert summary.id == "DS001"
    assert summary.total_orders == 10
    assert summary.total_revenue == Decimal("100.0")


def test_daily_summary_product_aggregation(db_session):
    """Aggregate TransactionItems for a tenant and verify daily totals."""

    # ---- Setup Tenant ----
    tenant = Tenant(id=str(uuid.uuid4()), name="AggregationTenant")
    db_session.add(tenant)
    db_session.commit()

    # ---- Setup Transactions & Items ----
    tx1 = Transaction(
        id=str(uuid.uuid4()), tenant_id=tenant.id, seller_phone="250700000001"
    )
    tx2 = Transaction(
        id=str(uuid.uuid4()), tenant_id=tenant.id, seller_phone="250700000002"
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    items = [
        TransactionItem(
            id=str(uuid.uuid4()), transaction_id=tx1.id, tenant_id=tenant.id,
            product_name="Rice", quantity=12, unit_price=Decimal("333.33"), total_amount=Decimal("4000")
        ),
        TransactionItem(
            id=str(uuid.uuid4()), transaction_id=tx2.id, tenant_id=tenant.id,
            product_name="Milk", quantity=5, unit_price=Decimal("6888"), total_amount=Decimal("34440")
        ),
    ]
    db_session.add_all(items)
    db_session.commit()

    # ---- Aggregate by product_name ----
    result = (
        db_session.query(
            TransactionItem.product_name,
            func.sum(TransactionItem.quantity).label("total_quantity"),
            func.sum(TransactionItem.total_amount).label("total_amount")
        )
        .filter(TransactionItem.tenant_id == tenant.id)
        .group_by(TransactionItem.product_name)
        .all()
    )

    agg_dict = {r.product_name: {"quantity": r.total_quantity, "amount": r.total_amount} for r in result}

    assert agg_dict["Rice"]["quantity"] == 12
    assert agg_dict["Rice"]["amount"] == Decimal("4000")
    assert agg_dict["Milk"]["quantity"] == 5
    assert agg_dict["Milk"]["amount"] == Decimal("34440")

    # ---- Check total revenue ----
    total_revenue = sum(r.total_amount for r in result)
    assert total_revenue == Decimal("38440")