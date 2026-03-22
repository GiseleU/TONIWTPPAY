# tests/models/test_transaction.py

import uuid
from decimal import Decimal
import pytest
from app.db.models_import import Transaction, Tenant, TransactionItem, Payment


def test_create_transaction(db_session):
    """Test basic transaction creation."""

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


def test_transaction_with_items(db_session):
    """Test transaction can have multiple items."""

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
            total_amount=Decimal("2000")
        ),
        TransactionItem(
            id=str(uuid.uuid4()),
            transaction_id=tx.id,
            tenant_id=tenant.id,
            product_name="Milk",
            quantity=5,
            unit_price=Decimal("6888"),
            total_amount=Decimal("34440")
        ),
    ]

    db_session.add_all(items)
    db_session.commit()
    db_session.refresh(tx)

    assert len(tx.items) == 2


def test_transaction_with_payments(db_session):
    """Test transaction can have payments."""

    tenant = Tenant(id=str(uuid.uuid4()), name="Payment Tenant")
    db_session.add(tenant)
    db_session.commit()

    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000003"
    )
    db_session.add(tx)
    db_session.commit()

    payment = Payment(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        transaction_id=tx.id,
        amount=Decimal("10000"),
        method="momo"
    )

    db_session.add(payment)
    db_session.commit()
    db_session.refresh(tx)

    assert len(tx.payments) == 1
    assert tx.payments[0].amount == Decimal("10000")


def test_transaction_cascade_delete_items(db_session):
    """Deleting a transaction should delete its items."""

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

    # Delete transaction
    db_session.delete(tx)
    db_session.commit()

    # Item should also be deleted
    deleted_item = db_session.get(TransactionItem, item.id)
    assert deleted_item is None


def test_transaction_requires_tenant(db_session):
    """Transaction must have a tenant_id."""

    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=None,  # invalid
        seller_phone="250700000005"
    )

    db_session.add(tx)

    with pytest.raises(Exception):
        db_session.commit()