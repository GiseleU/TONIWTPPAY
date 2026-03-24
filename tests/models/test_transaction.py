# tests/models/test_transaction.py

import uuid
from decimal import Decimal
import pytest
from app.db.models_import import Transaction, Tenant, TransactionItem


def test_create_transaction(db_session):
    """Test basic transaction creation and default field values."""
    tenant = Tenant(id=str(uuid.uuid4()), name="Tx Tenant")
    db_session.add(tenant)
    db_session.commit()

    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000001"
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)

    assert tx.id is not None
    assert tx.seller_phone == "250700000001"
    assert tx.tenant.id == tenant.id
    assert tx.created_at is not None
    assert tx.total_amount == Decimal("0")
    assert tx.total_profit is None
    assert tx.profit_complete is False
    assert tx.items_missing_cost_count == 0


def test_transaction_profit_fields_are_writable(db_session):
    """Confirm profit fields exist and accept valid values."""
    tenant = Tenant(id=str(uuid.uuid4()), name="Profit Fields Tenant")
    db_session.add(tenant)
    db_session.commit()

    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000010",
        total_profit=Decimal("3500"),
        profit_complete=True,
        items_missing_cost_count=0
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)

    assert tx.total_profit == Decimal("3500")
    assert tx.profit_complete is True
    assert tx.items_missing_cost_count == 0


def test_transaction_profit_fields_accept_null(db_session):
    """total_profit must be nullable — NULL means no cost data, not zero profit."""
    tenant = Tenant(id=str(uuid.uuid4()), name="Null Profit Tenant")
    db_session.add(tenant)
    db_session.commit()

    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000011",
        total_profit=None,
        profit_complete=False,
        items_missing_cost_count=2
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)

    assert tx.total_profit is None
    assert tx.profit_complete is False
    assert tx.items_missing_cost_count == 2


def test_transaction_with_items(db_session):
    """Test transaction can have multiple items via relationship."""
    tenant = Tenant(id=str(uuid.uuid4()), name="Items Tenant")
    db_session.add(tenant)
    db_session.commit()

    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000002"
    )
    db_session.add(tx)
    db_session.commit()

    items = [
        TransactionItem(
            id=str(uuid.uuid4()),
            transaction_id=tx.id,
            tenant_id=tenant.id,
            product_name="Rice",
            quantity=2,
            unit_price=Decimal("1000"),
            total_amount=Decimal("2000"),
        ),
        TransactionItem(
            id=str(uuid.uuid4()),
            transaction_id=tx.id,
            tenant_id=tenant.id,
            product_name="Milk",
            quantity=5,
            unit_price=Decimal("500"),
            total_amount=Decimal("2500"),
        ),
    ]
    db_session.add_all(items)
    db_session.commit()
    db_session.refresh(tx)

    assert len(tx.items) == 2
    product_names = [item.product_name for item in tx.items]
    assert "Rice" in product_names
    assert "Milk" in product_names




def test_transaction_cascade_delete_items(db_session):
    """Deleting a transaction should cascade delete its items."""
    tenant = Tenant(id=str(uuid.uuid4()), name="Cascade Tenant")
    db_session.add(tenant)
    db_session.commit()

    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000004"
    )
    db_session.add(tx)
    db_session.commit()

    item = TransactionItem(
        id=str(uuid.uuid4()),
        transaction_id=tx.id,
        tenant_id=tenant.id,
        product_name="Rice",
        quantity=1,
        unit_price=Decimal("1000"),
        total_amount=Decimal("1000")
    )
    db_session.add(item)
    db_session.commit()

    db_session.delete(tx)
    db_session.commit()

    assert db_session.get(TransactionItem, item.id) is None


def test_transaction_requires_tenant(db_session):
    """Transaction must have a tenant_id."""
    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=None,
        seller_phone="250700000005"
    )
    db_session.add(tx)
    with pytest.raises(Exception):
        db_session.commit()