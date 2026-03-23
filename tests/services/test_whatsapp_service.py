# tests/services/test_whatsapp_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from fastapi import HTTPException

from app.services import whatsapp_service
from app.core.enums import WorkflowState, CoexistenceStatus
from app.models.tenant import Tenant

# --------------------------
# Helper to mock DB queries
# --------------------------
def mock_db_queries(mock_db, tenant):
    mock_tenant_query = MagicMock()
    mock_tenant_filter = MagicMock()
    mock_tenant_filter.first.return_value = tenant
    mock_tenant_query.filter.return_value = mock_tenant_filter
    mock_db.query.return_value = mock_tenant_query


# --------------------------
# TEST: PAY command
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_pay_starts_transaction():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = Tenant(id="T001", phone_number=seller_phone, coexistence_status=CoexistenceStatus.ACTIVE)
    mock_db_queries(mock_db, tenant)

    mock_tx = MagicMock(id="TX001")
    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.whatsapp_service.create_transaction", return_value=mock_tx):

        await whatsapp_service.handle_message(mock_db, seller_phone, "pay")

        assert mock_state.state == WorkflowState.WAITING_PRODUCT_LINE.value
        assert mock_state.current_transaction_id == mock_tx.id
        mock_db.commit.assert_called()
        async_client.send_message.assert_awaited_with(
            seller_phone,
            "Enter <product> <quantity> <unit price>\nEx: amagi 2 600"
        )


# --------------------------
# TEST: SUMMARY
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_summary_sends_summary():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = Tenant(id="T001", phone_number=seller_phone, coexistence_status=CoexistenceStatus.ACTIVE)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    mock_summary = {
        "total_orders": 1,
        "total_revenue": Decimal("1000"),
        "items": [
            {"product_name": "Eggs", "quantity": 2, "total_amount": Decimal("1000")}
        ]
    }

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.whatsapp_service.get_today_summary", return_value=mock_summary):

        await whatsapp_service.handle_message(mock_db, seller_phone, "summary")

        async_client.send_message.assert_awaited()
        sent_phone, sent_text = async_client.send_message.call_args[0]
        assert sent_phone == seller_phone
        assert "Eggs" in sent_text
        assert "Total Revenue" in sent_text
        assert "1000 RWF" in sent_text


# --------------------------
# TEST: WhatsAppAccount missing
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_no_whatsapp_account():
    mock_db = MagicMock()
    seller_phone = "0789000000"

    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = None
    mock_query.filter.return_value = mock_filter
    mock_db.query.return_value = mock_query

    with pytest.raises(HTTPException) as exc:
        await whatsapp_service.handle_message(mock_db, seller_phone, "pay")

    assert exc.value.status_code == 404


# --------------------------
# TEST: Workflow product input
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_workflow_product_line():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = Tenant(id="T001", phone_number=seller_phone, coexistence_status=CoexistenceStatus.ACTIVE)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(
        state=WorkflowState.WAITING_PRODUCT_LINE.value,
        current_transaction_id="TX001"
    )
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.add_item") as mock_add_item, \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):

        await whatsapp_service.handle_message(mock_db, seller_phone, "Eggs 32 1000")

        mock_add_item.assert_called_once()
        called_args = mock_add_item.call_args.kwargs
        assert called_args['product_name'] == "Eggs"
        assert called_args['quantity'] == 32
        assert called_args['unit_price'] == Decimal("1000")

        assert mock_state.state == WorkflowState.WAITING_ADD_MORE.value
        mock_db.commit.assert_called()
        async_client.send_interactive_buttons.assert_awaited()


# --------------------------
# TEST: finalize_transaction
# --------------------------
def test_finalize_transaction_returns_summary_text():
    mock_db = MagicMock()
    from app.services.whatsapp_service import finalize_transaction

    mock_item1 = MagicMock(product_name="Prod1", quantity=2, total_amount=Decimal("100"), unit_price=Decimal("50"))
    mock_item2 = MagicMock(product_name="Prod2", quantity=1, total_amount=Decimal("50"), unit_price=Decimal("50"))
    mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_item1, mock_item2]

    result = finalize_transaction(mock_db, MagicMock(current_transaction_id="TX001"))

    assert "✅ Sale recorded" in result
    assert "- Prod1 x2 @ 50 → 100 RWF" in result
    assert "- Prod2 x1 @ 50 → 50 RWF" in result
    assert "💰 Total: 150 RWF" in result


# --------------------------
# TEST: build_summary
# --------------------------
def test_build_summary_returns_text():
    mock_db = MagicMock()
    tenant_id = "T001"
    from app.services.whatsapp_service import build_summary

    mock_summary = {
        "total_orders": 2,
        "total_revenue": Decimal("150"),
        "items": [
            {"product_name": "Prod1", "quantity": 2, "total_amount": Decimal("100")},
            {"product_name": "Prod2", "quantity": 1, "total_amount": Decimal("50")},
        ]
    }

    with patch("app.services.whatsapp_service.get_today_summary", return_value=mock_summary):
        result = build_summary(mock_db, tenant_id)

        assert "📊 Today's Sales Summary:" in result
        assert "Prod1" in result
        assert "Prod2" in result
        assert "💰 Total Revenue: 150 RWF" in result


# --------------------------
# TEST: finalize resets state
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_finalize_calls_service_and_resets_state():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = Tenant(id="T001", phone_number=seller_phone, coexistence_status=CoexistenceStatus.ACTIVE)
    mock_db_queries(mock_db, tenant)

    async_client = AsyncMock()
    mock_state = MagicMock(state=WorkflowState.WAITING_ADD_MORE.value, current_transaction_id="TX001")

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.whatsapp_service.finalize_transaction", return_value="CONFIRMATION") as mock_finalize, \
         patch("app.services.whatsapp_service.reset_state") as mock_reset_state:

        def fake_reset(state, db):
            state.state = WorkflowState.IDLE.value
            state.current_transaction_id = None
        mock_reset_state.side_effect = fake_reset

        await whatsapp_service.handle_message(mock_db, seller_phone, "no")

        mock_finalize.assert_called_once_with(mock_db, mock_state)
        assert mock_state.state == WorkflowState.IDLE.value
        assert mock_state.current_transaction_id is None
        async_client.send_message.assert_awaited_with(seller_phone, "CONFIRMATION")


# --------------------------
# TEST: Invalid format product input
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_invalid_format_during_product_line():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = Tenant(id="T001", phone_number=seller_phone, coexistence_status=CoexistenceStatus.ACTIVE)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.WAITING_PRODUCT_LINE.value, current_transaction_id="TX001")
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):
        await whatsapp_service.handle_message(mock_db, seller_phone, "invalid input")
        async_client.send_message.assert_awaited()
        assert "Invalid format" in async_client.send_message.call_args[0][1]


# --------------------------
# TEST: Invalid response during add more
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_invalid_response_during_add_more():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = Tenant(id="T001", phone_number=seller_phone, coexistence_status=CoexistenceStatus.ACTIVE)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.WAITING_ADD_MORE.value, current_transaction_id="TX001")
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):
        await whatsapp_service.handle_message(mock_db, seller_phone, "maybe")
        async_client.send_message.assert_awaited()
        assert "Reply 'yes' or 'no'" in async_client.send_message.call_args[0][1]


# --------------------------
# TEST: Empty message
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_empty_message_no_response():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = Tenant(id="T001", phone_number=seller_phone, coexistence_status=CoexistenceStatus.ACTIVE)
    mock_db_queries(mock_db, tenant)

    async_client = AsyncMock()

    empty_state = MagicMock(state=WorkflowState.IDLE.value)
    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=empty_state):
        await whatsapp_service.handle_message(mock_db, seller_phone, "")
        async_client.send_message.assert_not_awaited()


# --------------------------
# TEST: Non-IDLE random input triggers invalid format (not fallback)
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_non_idle_no_fallback():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = Tenant(id="T001", phone_number=seller_phone, coexistence_status=CoexistenceStatus.ACTIVE)
    mock_db_queries(mock_db, tenant)

    async_client = AsyncMock()
    non_idle_state = MagicMock(state=WorkflowState.WAITING_PRODUCT_LINE.value)
    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=non_idle_state):
        await whatsapp_service.handle_message(mock_db, seller_phone, "hello")

        async_client.send_message.assert_awaited()
        assert "Invalid format" in async_client.send_message.call_args[0][1]


# --------------------------
# TEST: IDLE fallback
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_idle_fallback_sent():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = Tenant(id="T001", phone_number=seller_phone, coexistence_status=CoexistenceStatus.ACTIVE)
    mock_db_queries(mock_db, tenant)

    async_client = AsyncMock()
    idle_state = MagicMock(state=WorkflowState.IDLE.value)
    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=idle_state):
        await whatsapp_service.handle_message(mock_db, seller_phone, "hello")

        async_client.send_message.assert_awaited()
        assert "Send PAY to record a sale or SUMMARY" in async_client.send_message.call_args[0][1]


# --------------------------
# TEST: full workflow multi-word product
# --------------------------
@pytest.mark.asyncio
async def test_full_workflow_multi_word_product():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = Tenant(id="T001", phone_number=seller_phone, coexistence_status=CoexistenceStatus.ACTIVE)
    mock_db_queries(mock_db, tenant)

    async_client = AsyncMock()
    mock_state = MagicMock(state=WorkflowState.IDLE.value)

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.whatsapp_service.create_transaction", return_value=MagicMock(id="TX001")), \
         patch("app.services.whatsapp_service.add_item") as mock_add_item, \
         patch("app.services.whatsapp_service.finalize_transaction", return_value="CONFIRMATION"):

        # Start transaction
        await whatsapp_service.handle_message(mock_db, seller_phone, "pay")

        # Add multi-word product
        mock_state.state = WorkflowState.WAITING_PRODUCT_LINE.value
        mock_state.current_transaction_id = "TX001"
        await whatsapp_service.handle_message(mock_db, seller_phone, "Large Eggs 5 200")
        mock_add_item.assert_called_once()

        # Finish transaction
        mock_state.state = WorkflowState.WAITING_ADD_MORE.value
        await whatsapp_service.handle_message(mock_db, seller_phone, "no")
        async_client.send_message.assert_awaited_with(seller_phone, "CONFIRMATION")