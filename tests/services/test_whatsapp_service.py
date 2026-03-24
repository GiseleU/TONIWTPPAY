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


def make_tenant(**kwargs):
    defaults = dict(
        id="T001",
        name="Gisèle Umutoni",
        phone_number="0789000000",
        coexistence_status=CoexistenceStatus.ACTIVE,
    )
    defaults.update(kwargs)
    return Tenant(**defaults)


# --------------------------
# TEST: PAY command
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_pay_starts_transaction():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_tx = MagicMock(id="TX001")
    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.transaction_service.create_transaction", return_value=mock_tx):

        await whatsapp_service.handle_message(mock_db, seller_phone, "pay")

        assert mock_state.state == WorkflowState.WAITING_PRODUCT_LINE.value
        assert mock_state.current_transaction_id == mock_tx.id
        mock_db.commit.assert_called()
        sent_text = async_client.send_message.call_args[0][1]
        assert "🛍️" in sent_text
        assert "New sale" in sent_text


# --------------------------
# TEST: SUMMARY
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_summary_sends_summary():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    mock_summary = {
        "total_orders": 1,
        "total_revenue": Decimal("1000"),
        "total_profit": None,
        "items": [
            {"product_name": "Eggs", "quantity": 2, "total_amount": Decimal("1000"), "total_profit": None}
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
        assert "Revenue" in sent_text
        assert "1,000" in sent_text or "1000" in sent_text


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
# TEST: WAITING_PRODUCT_LINE saves temp fields, moves to WAITING_COST
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_workflow_product_line_moves_to_waiting_cost():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(
        state=WorkflowState.WAITING_PRODUCT_LINE.value,
        current_transaction_id="TX001"
    )
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):

        await whatsapp_service.handle_message(mock_db, seller_phone, "Eggs 32 1000")

        assert mock_state.temp_product_name == "Eggs"
        assert mock_state.temp_quantity == "32"
        assert mock_state.temp_unit_price == "1000"
        assert mock_state.state == WorkflowState.WAITING_COST.value
        mock_db.commit.assert_called()
        sent_text = async_client.send_message.call_args[0][1]
        assert "cost" in sent_text.lower()
        assert "skip" in sent_text.lower()


# --------------------------
# TEST: WAITING_COST adds item and moves to WAITING_ADD_MORE
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_waiting_cost_adds_item():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_item = MagicMock(
        total_amount=Decimal("3000"),
        profit=Decimal("3000"),
    )
    mock_state = MagicMock(
        state=WorkflowState.WAITING_COST.value,
        current_transaction_id="TX001",
        temp_product_name="amashu",
        temp_quantity="3",
        temp_unit_price="1000",
    )
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.transaction_service.add_item", return_value=mock_item) as mock_add:

        await whatsapp_service.handle_message(mock_db, seller_phone, "500")

        mock_add.assert_called_once()
        called_kwargs = mock_add.call_args.kwargs
        assert called_kwargs["product_name"] == "amashu"
        assert called_kwargs["quantity"] == 3
        assert called_kwargs["cost_per_unit"] == Decimal("500")
        assert mock_state.state == WorkflowState.WAITING_ADD_MORE.value
        assert mock_state.temp_product_name is None
        async_client.send_interactive_buttons.assert_awaited()
        sent_text = async_client.send_interactive_buttons.call_args[0][1]
        assert "Profit" in sent_text


@pytest.mark.asyncio
async def test_handle_message_waiting_cost_skip():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_item = MagicMock(
        total_amount=Decimal("3000"),
        profit=None,
    )
    mock_state = MagicMock(
        state=WorkflowState.WAITING_COST.value,
        current_transaction_id="TX001",
        temp_product_name="amashu",
        temp_quantity="3",
        temp_unit_price="1000",
    )
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.transaction_service.add_item", return_value=mock_item) as mock_add:

        await whatsapp_service.handle_message(mock_db, seller_phone, "skip")

        mock_add.assert_called_once()
        called_kwargs = mock_add.call_args.kwargs
        assert called_kwargs["cost_per_unit"] is None
        assert mock_state.state == WorkflowState.WAITING_ADD_MORE.value
        async_client.send_interactive_buttons.assert_awaited()
        sent_text = async_client.send_interactive_buttons.call_args[0][1]
        assert "Profit" not in sent_text


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
        "total_profit": None,
        "items": [
            {"product_name": "Prod1", "quantity": 2, "total_amount": Decimal("100"), "total_profit": None},
            {"product_name": "Prod2", "quantity": 1, "total_amount": Decimal("50"), "total_profit": None},
        ]
    }

    with patch("app.services.whatsapp_service.get_today_summary", return_value=mock_summary):
        result = build_summary(mock_db, tenant_id, "Gisèle")

        assert "Gisèle" in result
        assert "Prod1" in result
        assert "Prod2" in result
        assert "Revenue" in result


def test_build_summary_no_sales():
    mock_db = MagicMock()
    from app.services.whatsapp_service import build_summary

    mock_summary = {"total_orders": 0, "total_revenue": Decimal("0"), "total_profit": None, "items": []}

    with patch("app.services.whatsapp_service.get_today_summary", return_value=mock_summary):
        result = build_summary(mock_db, "T001", "Gisèle")

        assert "Gisèle" in result
        assert "PAY" in result


def test_build_summary_with_profit():
    mock_db = MagicMock()
    from app.services.whatsapp_service import build_summary

    mock_summary = {
        "total_orders": 1,
        "total_revenue": Decimal("9000"),
        "total_profit": Decimal("3000"),
        "items": [
            {"product_name": "amashu", "quantity": 3, "total_amount": Decimal("9000"), "total_profit": Decimal("3000")}
        ]
    }

    with patch("app.services.whatsapp_service.get_today_summary", return_value=mock_summary):
        result = build_summary(mock_db, "T001", "Gisèle")

        assert "Profit" in result
        assert "Margin" in result
        assert "amashu" in result


# --------------------------
# TEST: finalize resets state
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_finalize_calls_service_and_resets_state():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    async_client = AsyncMock()
    mock_state = MagicMock(
        state=WorkflowState.WAITING_ADD_MORE.value,
        current_transaction_id="TX001"
    )

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.whatsapp_service._build_sale_summary", return_value="CONFIRMATION") as mock_build, \
         patch("app.services.whatsapp_service.reset_state") as mock_reset:

        def fake_reset(state, db):
            state.state = WorkflowState.IDLE.value
            state.current_transaction_id = None
        mock_reset.side_effect = fake_reset

        await whatsapp_service.handle_message(mock_db, seller_phone, "no")

        mock_build.assert_called_once_with(mock_db, "TX001", "T001", "Gisèle")
        mock_reset.assert_called_once()
        assert mock_state.state == WorkflowState.IDLE.value
        async_client.send_message.assert_awaited_with(seller_phone, "CONFIRMATION")


# --------------------------
# TEST: Invalid format product input
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_invalid_format_during_product_line():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.WAITING_PRODUCT_LINE.value, current_transaction_id="TX001")
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):
        await whatsapp_service.handle_message(mock_db, seller_phone, "invalid input")
        async_client.send_message.assert_awaited()
        assert "Invalid format" in async_client.send_message.call_args[0][1]


# --------------------------
# TEST: Invalid response during add more uses buttons
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_invalid_response_during_add_more():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.WAITING_ADD_MORE.value, current_transaction_id="TX001")
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):
        await whatsapp_service.handle_message(mock_db, seller_phone, "maybe")
        async_client.send_interactive_buttons.assert_awaited()


# --------------------------
# TEST: Empty message
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_empty_message_no_response():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    async_client = AsyncMock()

    empty_state = MagicMock(state=WorkflowState.IDLE.value)
    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=empty_state):
        await whatsapp_service.handle_message(mock_db, seller_phone, "")
        async_client.send_message.assert_not_awaited()


# --------------------------
# TEST: Non-IDLE random input triggers invalid format
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_non_idle_no_fallback():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
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
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    async_client = AsyncMock()
    idle_state = MagicMock(state=WorkflowState.IDLE.value)
    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=idle_state):
        await whatsapp_service.handle_message(mock_db, seller_phone, "hello")

        async_client.send_message.assert_awaited()
        sent_text = async_client.send_message.call_args[0][1]
        assert "PAY" in sent_text
        assert "SUMMARY" in sent_text


# --------------------------
# TEST: full workflow multi-word product
# --------------------------
@pytest.mark.asyncio
async def test_full_workflow_multi_word_product():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    async_client = AsyncMock()
    mock_state = MagicMock(state=WorkflowState.IDLE.value)

    mock_item = MagicMock(total_amount=Decimal("1000"), profit=None)

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.transaction_service.create_transaction", return_value=MagicMock(id="TX001")), \
         patch("app.services.transaction_service.add_item", return_value=mock_item) as mock_add_item, \
         patch("app.services.whatsapp_service._build_sale_summary", return_value="CONFIRMATION"):

        # Start transaction
        await whatsapp_service.handle_message(mock_db, seller_phone, "pay")
        assert mock_state.state == WorkflowState.WAITING_PRODUCT_LINE.value

        # Enter product line — moves to WAITING_COST
        mock_state.state = WorkflowState.WAITING_PRODUCT_LINE.value
        mock_state.current_transaction_id = "TX001"
        await whatsapp_service.handle_message(mock_db, seller_phone, "Large Eggs 5 200")
        assert mock_state.state == WorkflowState.WAITING_COST.value
        assert mock_state.temp_product_name == "Large Eggs"

        # Enter cost — calls add_item, moves to WAITING_ADD_MORE
        mock_state.state = WorkflowState.WAITING_COST.value
        mock_state.temp_product_name = "Large Eggs"
        mock_state.temp_quantity = "5"
        mock_state.temp_unit_price = "200"
        await whatsapp_service.handle_message(mock_db, seller_phone, "skip")
        mock_add_item.assert_called_once()
        assert mock_state.state == WorkflowState.WAITING_ADD_MORE.value

        # Finish transaction
        mock_state.state = WorkflowState.WAITING_ADD_MORE.value
        mock_state.current_transaction_id = "TX001"
        await whatsapp_service.handle_message(mock_db, seller_phone, "no")
        async_client.send_message.assert_awaited_with(seller_phone, "CONFIRMATION")
