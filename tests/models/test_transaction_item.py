# tests/models/test_transaction_item.py

import uuid
import pytest
from decimal import Decimal
from app.db.models_import import TransactionItem, Transaction, Tenant


def test_create_transaction_item(db_session):
    """Test basic creation of a TransactionItem."""
    tenant = Tenant(id=str(uuid.uuid4()), name="Item Tenant")
    db_session.add(tenant)
    db_session.commit()

    transaction = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000001"
    )
    db_session.add(transaction)
    db_session.commit()

    item = TransactionItem(
        id=str(uuid.uuid4()),
        transaction_id=transaction.id,
        tenant_id=tenant.id,
        product_name="Rice",
        quantity=10,
        unit_price=Decimal("600.00"),
        total_amount=Decimal("6000.00")
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert item.id is not None
    assert item.product_name == "Rice"
    assert item.quantity == 10
    assert item.unit_price == Decimal("600.00")
    assert item.total_amount == Decimal("6000.00")
    assert item.cost_per_unit is None
    assert item.profit is None
    assert item.transaction.id == transaction.id
    assert item.tenant.id == tenant.id


def test_transaction_item_profit_fields_are_writable(db_session):
    """cost_per_unit and profit fields exist, are nullable, and store correctly."""
    tenant = Tenant(id=str(uuid.uuid4()), name="Profit Fields Tenant")
    db_session.add(tenant)
    db_session.commit()

    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000020"
    )
    db_session.add(tx)
    db_session.commit()

    item = TransactionItem(
        id=str(uuid.uuid4()),
        transaction_id=tx.id,
        tenant_id=tenant.id,
        product_name="Milk",
        quantity=2,
        unit_price=Decimal("500"),
        total_amount=Decimal("1000"),
        cost_per_unit=Decimal("300"),
        profit=Decimal("400")
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert item.cost_per_unit == Decimal("300")
    assert item.profit == Decimal("400")


def test_multiple_items_in_transaction(db_session):
    """Transaction relationship holds multiple items correctly."""
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

    items_data = [
        ("Rice", 2, Decimal("1000.00")),
        ("Milk", 5, Decimal("300.00")),
    ]
    items = [
        TransactionItem(
            id=str(uuid.uuid4()),
            transaction_id=transaction.id,
            tenant_id=tenant.id,
            product_name=name,
            quantity=qty,
            unit_price=price,
            total_amount=qty * price
        )
        for name, qty, price in items_data
    ]
    db_session.add_all(items)
    db_session.commit()
    db_session.refresh(transaction)

    assert len(transaction.items) == 2
    product_names = [item.product_name for item in transaction.items]
    assert "Rice" in product_names
    assert "Milk" in product_names


def test_transaction_item_required_fields(db_session):
    """Ensure required fields are enforced at the DB level."""
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

    for invalid_kwargs in [
        dict(product_name=None, quantity=1, unit_price=Decimal("1000"), total_amount=Decimal("1000")),
        dict(product_name="Eggs", quantity=1, unit_price=None, total_amount=Decimal("1000")),
        dict(product_name="Eggs", quantity=None, unit_price=Decimal("1000"), total_amount=Decimal("1000")),
    ]:
        db_session.add(TransactionItem(
            id=str(uuid.uuid4()),
            transaction_id=transaction.id,
            tenant_id=tenant.id,
            **invalid_kwargs
        ))
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()