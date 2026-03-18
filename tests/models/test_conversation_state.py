# tests/models/test_conversation_state.py

import pytest
from sqlalchemy.orm import Session
from app.db.models_import import ConversationState, Transaction, Tenant
import uuid


@pytest.fixture
def tenant(db_session: Session):
    """Create a sample tenant for testing."""
    t = Tenant(id=str(uuid.uuid4()), name="TestTenant")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


@pytest.fixture
def transaction(db_session: Session, tenant):
    """Create a sample transaction for testing."""
    tx = Transaction(id=str(uuid.uuid4()), tenant_id=tenant.id, seller_phone="250700000001")
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)
    return tx


def test_create_conversation_state(db_session: Session, tenant, transaction):
    """Test that ConversationState can be created and linked to tenant and transaction."""
    cs_id = str(uuid.uuid4())
    cs = ConversationState(
        id=cs_id,
        tenant_id=tenant.id,
        seller_phone="250700000001",
        state="idle",
        current_transaction_id=transaction.id,
        temp_product="Milk",
        temp_quantity="5"
    )
    db_session.add(cs)
    db_session.commit()
    db_session.refresh(cs)

    assert cs.id == cs_id
    assert cs.state == "idle"
    assert cs.temp_product == "Milk"
    assert cs.temp_quantity == "5"
    assert cs.tenant.id == tenant.id
    assert cs.transaction.id == transaction.id


def test_default_state(db_session: Session, tenant):
    """Test that default state is 'idle' if not specified."""
    cs = ConversationState(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000002"
    )
    db_session.add(cs)
    db_session.commit()
    db_session.refresh(cs)

    assert cs.state == "idle"
    assert cs.current_transaction_id is None
    assert cs.temp_product is None
    assert cs.temp_quantity is None