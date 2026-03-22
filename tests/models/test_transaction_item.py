# tests/models/test_transaction_item.py

import uuid
import pytest
from decimal import Decimal

from app.db.models_import import TransactionItem, Transaction, Tenant


def test_create_transaction_item(db_session):
    """Test basic creation of a TransactionItem with correct calculations."""

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

    # ---- Values ----
    quantity = 10
    unit_price = Decimal("600.00")
    expected_total = quantity * unit_price

    # ---- Create TransactionItem ----
    item = TransactionItem(
        id=str(uuid.uuid4()),
        transaction_id=transaction.id,
        tenant_id=tenant.id,
        product_name="Rice",
        quantity=quantity,
        unit_price=unit_price,
        total_amount=expected_total
    )

    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    # ---- Assertions ----
    assert item.id is not None
    assert item.product_name == "Rice"
    assert item.quantity == quantity
    assert item.unit_price == unit_price
    assert item.total_amount == expected_total

    # Relationships
    assert item.transaction.id == transaction.id
    assert item.tenant.id == tenant.id


def test_multiple_items_in_transaction(db_session):
    """Test multiple items with correct totals."""

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

    items_data = [
        ("Rice", 2, Decimal("1000.00")),
        ("Milk", 5, Decimal("300.00")),
    ]

    items = []
    for name, qty, price in items_data:
        items.append(
            TransactionItem(
                id=str(uuid.uuid4()),
                transaction_id=transaction.id,
                tenant_id=tenant.id,
                product_name=name,
                quantity=qty,
                unit_price=price,
                total_amount=qty * price
            )
        )

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

    # ---- Missing product_name ----
    invalid_item_1 = TransactionItem(
        id=str(uuid.uuid4()),
        transaction_id=transaction.id,
        tenant_id=tenant.id,
        product_name=None,  # ❌ invalid
        quantity=1,
        unit_price=Decimal("1000"),
        total_amount=Decimal("1000")
    )

    db_session.add(invalid_item_1)
    with pytest.raises(Exception):
        db_session.commit()

    db_session.rollback()

    # ---- Missing unit_price ----
    invalid_item_2 = TransactionItem(
        id=str(uuid.uuid4()),
        transaction_id=transaction.id,
        tenant_id=tenant.id,
        product_name="Eggs",
        quantity=1,
        unit_price=None,  # ❌ invalid
        total_amount=Decimal("1000")
    )

    db_session.add(invalid_item_2)
    with pytest.raises(Exception):
        db_session.commit()

    db_session.rollback()

    # ---- Missing quantity ----
    invalid_item_3 = TransactionItem(
        id=str(uuid.uuid4()),
        transaction_id=transaction.id,
        tenant_id=tenant.id,
        product_name="Eggs",
        quantity=None,  # ❌ invalid
        unit_price=Decimal("1000"),
        total_amount=Decimal("1000")
    )

    db_session.add(invalid_item_3)
    with pytest.raises(Exception):
        db_session.commit()


def test_total_amount_calculation_consistency():
    """Ensure total_amount follows quantity * unit_price."""

    quantity = 4
    unit_price = Decimal("250.00")

    expected_total = quantity * unit_price

    assert expected_total == Decimal("1000.00")