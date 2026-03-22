# tests/services/test_transaction_service.py

import uuid
from decimal import Decimal
import pytest
from unittest.mock import MagicMock

from app.services import transaction_service
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem

# -----------------------------
# Test: create_transaction
# -----------------------------
def test_create_transaction(db_session, tenant):
    seller_phone = "0789000000"

    tx = transaction_service.create_transaction(db_session, seller_phone, tenant.id)

    # Reload from DB
    db_tx = db_session.query(Transaction).filter_by(id=tx.id).first()
    assert db_tx is not None
    assert db_tx.seller_phone == seller_phone
    assert db_tx.tenant_id == tenant.id
    assert tx.id is not None


# -----------------------------
# Test: add_item calculates total_amount
# -----------------------------
def test_add_item(db_session, tenant):
    tx = transaction_service.create_transaction(db_session, seller_phone="0789000001", tenant_id=tenant.id)

    product_name = "ProductA"
    quantity = 3
    unit_price = 50.0  # RWF

    item = transaction_service.add_item(
        db=db_session,
        transaction_id=tx.id,
        tenant_id=tenant.id,
        product_name=product_name,
        quantity=quantity,
        unit_price=unit_price
    )

    # Reload from DB
    db_item = db_session.query(TransactionItem).filter_by(id=item.id).first()
    assert db_item is not None

    # Check values
    assert db_item.product_name == product_name
    assert db_item.quantity == quantity
    assert db_item.unit_price == Decimal(str(unit_price))
    assert db_item.total_amount == Decimal(quantity) * Decimal(str(unit_price))


# -----------------------------
# Test: transaction total_amount updated correctly
# -----------------------------
def test_transaction_total_amount_multiple_items(db_session, tenant):
    tx = transaction_service.create_transaction(db_session, seller_phone="0789000002", tenant_id=tenant.id)

    # Add multiple items
    items_data = [
        ("Rice", 2, 1000.0),
        ("Milk", 5, 300.0),
        ("Eggs", 10, 150.0),
    ]

    expected_total = Decimal("0.00")
    for name, qty, price in items_data:
        transaction_service.add_item(
            db=db_session,
            transaction_id=tx.id,
            tenant_id=tenant.id,
            product_name=name,
            quantity=qty,
            unit_price=price
        )
        expected_total += Decimal(qty) * Decimal(str(price))

    # Reload transaction
    db_tx = db_session.query(Transaction).filter_by(id=tx.id).first()
    assert db_tx.total_amount == expected_total


# -----------------------------
# Test: finalize_transaction_service (fixed)
# -----------------------------
from app.models.conversation_state import ConversationState
from app.core.enums import WorkflowState

def test_finalize_transaction(db_session, tenant):
    # --- Create transaction ---
    tx = transaction_service.create_transaction(
        db=db_session,
        seller_phone="0789000003",
        tenant_id=tenant.id
    )

    # --- Add items ---
    item1 = transaction_service.add_item(
        db=db_session,
        transaction_id=tx.id,
        tenant_id=tenant.id,
        product_name="Apples",
        quantity=3,
        unit_price=200.0
    )
    item2 = transaction_service.add_item(
        db=db_session,
        transaction_id=tx.id,
        tenant_id=tenant.id,
        product_name="Bananas",
        quantity=2,
        unit_price=150.0
    )

    # --- Create real ConversationState ---
    state = ConversationState(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="0789000003",
        state=WorkflowState.WAITING_PRODUCT.value,
        current_transaction_id=tx.id
    )
    db_session.add(state)
    db_session.commit()
    db_session.refresh(state)

    # --- Call finalize_transaction ---
    summary_text = transaction_service.finalize_transaction(
        db=db_session,
        transaction_id=tx.id,
        state=state
    )

    # --- Check that summary contains all items and correct totals ---
    assert "Apples x3 @ 200.00 → 600.00 RWF" in summary_text
    assert "Bananas x2 @ 150.00 → 300.00 RWF" in summary_text
    assert "💰 Total: 900.00 RWF" in summary_text
    assert "✅ Sale recorded" in summary_text

    # --- After finalize, state should be reset in DB ---
    db_session.refresh(state)
    assert state.current_transaction_id is None
    assert state.state == WorkflowState.IDLE.value