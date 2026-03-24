# tests/schemas/test_conversation_state_schema.py

import pytest
from app.schemas.conversation_state import (
    ConversationStateCreate,
    ConversationStateUpdate,
    ConversationStateRead,
)


def test_conversation_state_create_valid():
    data = {
        "tenant_id": "T001",
        "seller_phone": "250700000001",
        "state": "AWAITING_PRODUCT",
        "current_transaction_id": "TX001",
        "temp_product_name": "Rice",
        "temp_quantity": "2",
        "temp_unit_price": "1000",
    }

    schema = ConversationStateCreate(**data)

    assert schema.tenant_id == "T001"
    assert schema.state == "AWAITING_PRODUCT"
    assert schema.temp_product_name == "Rice"
    assert schema.temp_unit_price == "1000"


def test_conversation_state_create_required_fields():
    data = {
        "tenant_id": "T001",
        # missing seller_phone and state
    }

    with pytest.raises(Exception):
        ConversationStateCreate(**data)


def test_conversation_state_optional_fields():
    data = {
        "tenant_id": "T001",
        "seller_phone": "250700000002",
        "state": "IDLE",
    }

    schema = ConversationStateCreate(**data)

    assert schema.current_transaction_id is None
    assert schema.temp_product_name is None
    assert schema.temp_quantity is None
    assert schema.temp_unit_price is None


def test_conversation_state_update_partial():
    data = {
        "state": "AWAITING_QUANTITY"
    }

    schema = ConversationStateUpdate(**data)

    assert schema.state == "AWAITING_QUANTITY"
    assert schema.current_transaction_id is None


def test_conversation_state_update_empty():
    schema = ConversationStateUpdate()

    assert schema.state is None
    assert schema.temp_product_name is None
    assert schema.temp_unit_price is None


def test_conversation_state_read_from_orm():
    class FakeORMObject:
        def __init__(self):
            self.id = "CS001"
            self.tenant_id = "T001"
            self.seller_phone = "250700000003"
            self.state = "AWAITING_PRODUCT"
            self.current_transaction_id = None
            self.temp_product_name = None
            self.temp_quantity = None
            self.temp_unit_price = None

    orm_obj = FakeORMObject()

    schema = ConversationStateRead.from_orm(orm_obj)

    assert schema.id == "CS001"
    assert schema.tenant_id == "T001"
    assert schema.state == "AWAITING_PRODUCT"
    assert schema.temp_product_name is None
