# tests/models/test_transaction_item.py

import uuid
from decimal import Decimal
from app.db.models_import import TransactionItem, Transaction, Tenant


def test_create_transaction_item(db_session):
    """Test basic creation of a TransactionItem."""

    # ---- Setup Tenant ----
    tenant = Tenant(id=str(uuid.uuid4()), name="Item Tenant")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    # ---- Setup Transaction ----
    transaction = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000001"
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    # ---- Create TransactionItem ----
    item_id = str(uuid.uuid4())
    item = TransactionItem(
        id=item_id,
        transaction_id=transaction.id,
        tenant_id=tenant.id,
        product_name="Rice",
        quantity=10,
        total_amount=Decimal("5000.00")
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    # ---- Assertions ----
    assert item.id == item_id
    assert item.product_name == "Rice"
    assert item.quantity == 10
    assert item.total_amount == Decimal("5000.00")

    # Relationships
    assert item.transaction.id == transaction.id
    assert item.tenant.id == tenant.id


def test_multiple_items_in_transaction(db_session):
    """Test multiple items can belong to one transaction."""

    tenant = Tenant(id=str(uuid.uuid4()), name="Multi Item Tenant")
    db_session.add(tenant)
    db_session.commit()

    transaction = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000002"
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    items = [
        TransactionItem(
            id=str(uuid.uuid4()),
            transaction_id=transaction.id,
            tenant_id=tenant.id,
            product_name="Rice",
            quantity=2,
            total_amount=Decimal("2000")
        ),
        TransactionItem(
            id=str(uuid.uuid4()),
            transaction_id=transaction.id,
            tenant_id=tenant.id,
            product_name="Milk",
            quantity=5,
            total_amount=Decimal("34440")
        ),
    ]

    db_session.add_all(items)
    db_session.commit()
    db_session.refresh(transaction)

    # ---- Assertions ----
    assert len(transaction.items) == 2

    product_names = [item.product_name for item in transaction.items]
    assert "Rice" in product_names
    assert "Milk" in product_names


def test_transaction_item_required_fields(db_session):
    """Ensure required fields are enforced."""

    tenant = Tenant(id=str(uuid.uuid4()), name="Required Fields Tenant")
    db_session.add(tenant)
    db_session.commit()

    transaction = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000003"
    )
    db_session.add(transaction)
    db_session.commit()

    # Missing product_name should fail
    invalid_item = TransactionItem(
        id=str(uuid.uuid4()),
        transaction_id=transaction.id,
        tenant_id=tenant.id,
        product_name=None,  # invalid
        quantity=1,
        total_amount=Decimal("1000")
    )

    db_session.add(invalid_item)

    import pytest
    with pytest.raises(Exception):
        db_session.commit()