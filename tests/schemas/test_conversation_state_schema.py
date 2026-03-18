# tests/schemas/test_conversation_state.py

import pytest
from app.schemas.conversation_state import (
    ConversationStateCreate,
    ConversationStateUpdate,
    ConversationStateRead,
)


def test_conversation_state_create_valid():
    """Test valid creation schema."""

    data = {
        "tenant_id": "T001",
        "seller_phone": "250700000001",
        "state": "AWAITING_PRODUCT",
        "current_transaction_id": "TX001",
        "temp_product": "Rice",
        "temp_quantity": "2",
    }

    schema = ConversationStateCreate(**data)

    assert schema.tenant_id == "T001"
    assert schema.state == "AWAITING_PRODUCT"
    assert schema.temp_product == "Rice"


def test_conversation_state_create_required_fields():
    """Missing required fields should raise validation error."""

    data = {
        "tenant_id": "T001",
        # missing seller_phone and state
    }

    with pytest.raises(Exception):
        ConversationStateCreate(**data)


def test_conversation_state_optional_fields():
    """Optional fields should default to None."""

    data = {
        "tenant_id": "T001",
        "seller_phone": "250700000002",
        "state": "IDLE",
    }

    schema = ConversationStateCreate(**data)

    assert schema.current_transaction_id is None
    assert schema.temp_product is None
    assert schema.temp_quantity is None


def test_conversation_state_update_partial():
    """Update schema should allow partial updates."""

    data = {
        "state": "AWAITING_QUANTITY"
    }

    schema = ConversationStateUpdate(**data)

    assert schema.state == "AWAITING_QUANTITY"
    assert schema.current_transaction_id is None


def test_conversation_state_update_empty():
    """Empty update should still be valid."""

    schema = ConversationStateUpdate()

    assert schema.state is None
    assert schema.temp_product is None


def test_conversation_state_read_from_orm():
    """Test ORM compatibility (orm_mode)."""

    class FakeORMObject:
        def __init__(self):
            self.id = "CS001"
            self.tenant_id = "T001"
            self.seller_phone = "250700000003"
            self.state = "AWAITING_PRODUCT"
            self.current_transaction_id = None
            self.temp_product = None
            self.temp_quantity = None

    orm_obj = FakeORMObject()

    schema = ConversationStateRead.from_orm(orm_obj)

    assert schema.id == "CS001"
    assert schema.tenant_id == "T001"
    assert schema.state == "AWAITING_PRODUCT"