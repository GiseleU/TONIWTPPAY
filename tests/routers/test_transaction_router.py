# tests/routers/test_transaction_router.py
import pytest
from app.core.enums import WorkflowState
from app.db.models_import import Transaction, TransactionItem, ConversationState

# -----------------------------
# Test start transaction
# -----------------------------
def test_start_transaction(client, db_session, tenant):
    # Pre-create a conversation state for the seller
    state = ConversationState(
        seller_phone="0789000000",
        tenant_id=tenant.id,
        state=WorkflowState.IDLE.value,
        current_transaction_id=None
    )
    db_session.add(state)
    db_session.commit()

    payload = {"seller_phone": "0789000000", "tenant_id": tenant.id}
    response = client.post("/transactions/start", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "transaction_id" in data
    assert data["state"] == WorkflowState.WAITING_PRODUCT.value

    # Verify state updated in DB
    db_session.refresh(state)
    assert state.current_transaction_id == data["transaction_id"]
    assert state.state == WorkflowState.WAITING_PRODUCT.value


# -----------------------------
# Test add item to transaction
# -----------------------------
def test_add_item_to_transaction(client, db_session, tenant):
    # Create a transaction first
    tx = Transaction(
        tenant_id=tenant.id,
        seller_phone="0789000000"
    )
    db_session.add(tx)
    db_session.commit()

    payload = {
        "transaction_id": tx.id,
        "tenant_id": tenant.id,
        "product_name": "TestProduct",
        "quantity": 2,
        "total_amount": 100.0
    }
    response = client.post("/transactions/add_item", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] is not None
    assert data["product_name"] == "TestProduct"
    assert data["quantity"] == 2
    assert data["total_amount"] == 100.0

    # Verify item exists in DB
    item = db_session.get(TransactionItem, data["item_id"])
    assert item is not None
    assert item.product_name == "TestProduct"


# -----------------------------
# Test finalize transaction
# -----------------------------
def test_finalize_transaction(client, db_session, tenant):
    # Create a transaction with one item
    tx = Transaction(
        tenant_id=tenant.id,
        seller_phone="0789000000"
    )
    db_session.add(tx)
    db_session.commit()

    item = TransactionItem(
        transaction_id=tx.id,
        tenant_id=tenant.id,
        product_name="FinalProduct",
        quantity=1,
        total_amount=50.0
    )
    db_session.add(item)
    db_session.commit()

    # Create the conversation state
    state = ConversationState(
        seller_phone="0789000000",
        tenant_id=tenant.id,
        state=WorkflowState.WAITING_PRODUCT.value,
        current_transaction_id=tx.id
    )
    db_session.add(state)
    db_session.commit()

    payload = {
        "transaction_id": tx.id,
        "seller_phone": "0789000000",
        "tenant_id": tenant.id
    }
    response = client.post("/transactions/finalize", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "FinalProduct" in data["summary"]

    # Verify state is reset
    db_session.refresh(state)
    assert state.current_transaction_id is None
    assert state.state == WorkflowState.IDLE.value


# -----------------------------
# Full transaction flow (start -> add item -> finalize)
# -----------------------------
def test_full_transaction_flow(client, db_session, tenant):
    # Start
    payload_start = {"seller_phone": "0789000000", "tenant_id": tenant.id}
    response_start = client.post("/transactions/start", json=payload_start)
    assert response_start.status_code == 200
    transaction_id = response_start.json()["transaction_id"]

    # Add item
    payload_add = {
        "transaction_id": transaction_id,
        "tenant_id": tenant.id,
        "product_name": "Item1",
        "quantity": 3,
        "total_amount": 300.0
    }
    response_add = client.post("/transactions/add_item", json=payload_add)
    assert response_add.status_code == 200
    item_id = response_add.json()["item_id"]

    # Finalize
    payload_finalize = {
        "transaction_id": transaction_id,
        "seller_phone": "0789000000",
        "tenant_id": tenant.id
    }
    response_finalize = client.post("/transactions/finalize", json=payload_finalize)
    assert response_finalize.status_code == 200
    summary = response_finalize.json()["summary"]
    assert "Item1" in summary
    assert "Total: 300.0" in summary

    # Verify state is reset in DB
    state = db_session.query(ConversationState).filter_by(
        seller_phone="0789000000",
        tenant_id=tenant.id
    ).first()
    assert state.state == WorkflowState.IDLE.value
    assert state.current_transaction_id is None