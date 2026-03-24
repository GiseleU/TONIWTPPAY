# tests/services/test_state_service.py
import pytest
from unittest.mock import MagicMock, patch
from app.services import state_service
from app.models.conversation_state import ConversationState
from app.core.enums import WorkflowState

@pytest.mark.parametrize("existing_state", [True, False])
def test_get_or_create_state(existing_state):
    # Mock DB session
    mock_db = MagicMock()

    if existing_state:
        # Simulate existing state
        mock_state = MagicMock(spec=ConversationState)
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_state
    else:
        # Simulate no existing state
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

    # Patch uuid to return a fixed value for predictable id
    with patch("app.services.state_service.uuid.uuid4", return_value="UUID1234"):
        state = state_service.get_or_create_state(mock_db, "123456789", "T001")

    if existing_state:
        # Should return the existing state
        assert state == mock_db.query.return_value.filter_by.return_value.first.return_value
        # DB add/commit/refresh should not be called
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
    else:
        # Should create a new ConversationState
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert state.id == "UUID1234"
        assert state.tenant_id == "T001"
        assert state.seller_phone == "123456789"
        assert state.state == WorkflowState.IDLE.value

def test_reset_state_without_db():
    mock_state = MagicMock(spec=ConversationState)
    mock_state.state = "something"
    mock_state.current_transaction_id = "TX123"
    mock_state.temp_product_name = "item"
    mock_state.temp_quantity = "2"
    mock_state.temp_unit_price = "1000"

    state_service.reset_state(mock_state)

    assert mock_state.state == WorkflowState.IDLE.value
    assert mock_state.current_transaction_id is None
    assert mock_state.temp_product_name is None
    assert mock_state.temp_quantity is None
    assert mock_state.temp_unit_price is None

def test_reset_state_with_db():
    mock_state = MagicMock(spec=ConversationState)
    mock_db = MagicMock()

    state_service.reset_state(mock_state, db=mock_db)

    assert mock_state.state == WorkflowState.IDLE.value
    assert mock_state.current_transaction_id is None
    assert mock_state.temp_product_name is None
    assert mock_state.temp_quantity is None
    assert mock_state.temp_unit_price is None

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_state)