# tests/services/test_whatsapp_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services import whatsapp_service
from app.services.whatsapp_service import build_summary, build_details
from app.core.enums import WorkflowState, CoexistenceStatus
from app.models.tenant import Tenant


# --------------------------
# Helpers
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


def make_today(
    orders=1,
    revenue=Decimal("9000"),
    gross_profit=None,
    gross_loss=None,
    profit_complete=False,
    missing=None,
    top_revenue=None,
    top_profit=None,
    items=None,
):
    return {
        "total_orders": orders,
        "total_revenue": revenue,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_complete": profit_complete,
        "missing_cost_products": missing or [],
        "top_revenue": top_revenue,
        "top_profit": top_profit,
        "items": items or [],
    }


# --------------------------
# TEST: SALE command
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_sale_starts_transaction():
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

        await whatsapp_service.handle_message(mock_db, seller_phone, "sale")

        assert mock_state.state == WorkflowState.WAITING_PRODUCT_LINE.value
        assert mock_state.current_transaction_id == mock_tx.id
        sent_text = async_client.send_message.call_args[0][1]
        assert "New sale" in sent_text


@pytest.mark.asyncio
async def test_sale_during_active_sale_warns():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.WAITING_PRODUCT_LINE.value)
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):

        await whatsapp_service.handle_message(mock_db, seller_phone, "sale")

        sent_text = async_client.send_message.call_args[0][1]
        assert "in progress" in sent_text
        assert "DONE" in sent_text


# --------------------------
# TEST: WAITING_PRODUCT_LINE
# --------------------------
@pytest.mark.asyncio
async def test_product_line_moves_to_waiting_cost():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.WAITING_PRODUCT_LINE.value, current_transaction_id="TX001")
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):

        await whatsapp_service.handle_message(mock_db, seller_phone, "amagi 2 600")

        assert mock_state.temp_product_name == "amagi"
        assert mock_state.temp_quantity == "2"
        assert mock_state.temp_unit_price == "600"
        assert mock_state.state == WorkflowState.WAITING_COST.value
        sent_text = async_client.send_message.call_args[0][1]
        assert "cost" in sent_text.lower()


@pytest.mark.asyncio
async def test_done_finalizes_sale():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.WAITING_PRODUCT_LINE.value, current_transaction_id="TX001")
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.whatsapp_service._build_sale_summary", return_value="SALE DONE") as mock_build, \
         patch("app.services.whatsapp_service.reset_state") as mock_reset:

        await whatsapp_service.handle_message(mock_db, seller_phone, "done")

        mock_build.assert_called_once_with(mock_db, "TX001", "T001")
        mock_reset.assert_called_once()
        async_client.send_message.assert_awaited_with(seller_phone, "SALE DONE")


# --------------------------
# TEST: WAITING_COST
# --------------------------
@pytest.mark.asyncio
async def test_cost_entry_adds_item_and_returns_to_product_line():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(
        state=WorkflowState.WAITING_COST.value,
        current_transaction_id="TX001",
        temp_product_name="amagi",
        temp_quantity="2",
        temp_unit_price="600",
    )
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.transaction_service.add_item") as mock_add:

        await whatsapp_service.handle_message(mock_db, seller_phone, "400")

        mock_add.assert_called_once()
        assert mock_add.call_args.kwargs["cost_per_unit"] == Decimal("400")
        assert mock_state.state == WorkflowState.WAITING_PRODUCT_LINE.value
        sent_text = async_client.send_message.call_args[0][1]
        assert "recorded" in sent_text
        assert "DONE" in sent_text


@pytest.mark.asyncio
async def test_cost_skip_adds_item_without_cost():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(
        state=WorkflowState.WAITING_COST.value,
        current_transaction_id="TX001",
        temp_product_name="amagi",
        temp_quantity="2",
        temp_unit_price="600",
    )
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.transaction_service.add_item") as mock_add:

        await whatsapp_service.handle_message(mock_db, seller_phone, "skip")

        assert mock_add.call_args.kwargs["cost_per_unit"] is None
        assert mock_state.state == WorkflowState.WAITING_PRODUCT_LINE.value


# --------------------------
# TEST: SET COST
# --------------------------
@pytest.mark.asyncio
async def test_set_cost_command():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    mock_result = {"product_name": "amagi", "product_profit": Decimal("2000")}
    mock_today = make_today(missing=[])

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.transaction_service.set_product_cost", return_value=mock_result), \
         patch("app.services.whatsapp_service.get_today_summary", return_value=mock_today):

        await whatsapp_service.handle_message(mock_db, seller_phone, "SET amagi COST 400")

        sent_text = async_client.send_message.call_args[0][1]
        assert "Cost saved" in sent_text
        assert "amagi" in sent_text
        assert "2,000" in sent_text or "2000" in sent_text


@pytest.mark.asyncio
async def test_set_cost_product_not_found():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.transaction_service.set_product_cost", return_value=None):

        await whatsapp_service.handle_message(mock_db, seller_phone, "SET unknownproduct COST 500")

        sent_text = async_client.send_message.call_args[0][1]
        assert "No sales" in sent_text


# --------------------------
# TEST: SUMMARY
# --------------------------
@pytest.mark.asyncio
async def test_summary_command():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    mock_today = make_today(
        orders=2,
        revenue=Decimal("15000"),
        gross_profit=Decimal("5000"),
        profit_complete=True,
        top_revenue={"product_name": "Air Force", "total_amount": Decimal("10000")},
        top_profit={"product_name": "Air Force", "total_profit": Decimal("5000")},
    )

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.whatsapp_service.get_today_summary", return_value=mock_today):

        await whatsapp_service.handle_message(mock_db, seller_phone, "summary")

        sent_text = async_client.send_message.call_args[0][1]
        assert "Revenue" in sent_text
        assert "Profit" in sent_text
        assert "Air Force" in sent_text
        assert "DETAILS" in sent_text


# --------------------------
# TEST: DETAILS
# --------------------------
@pytest.mark.asyncio
async def test_details_command():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    mock_today = make_today(
        orders=1,
        revenue=Decimal("9000"),
        items=[{"product_name": "amagi", "quantity": 2, "total_amount": Decimal("9000"), "total_profit": Decimal("2000")}],
    )

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.whatsapp_service.get_today_summary", return_value=mock_today):

        await whatsapp_service.handle_message(mock_db, seller_phone, "details")

        sent_text = async_client.send_message.call_args[0][1]
        assert "per product" in sent_text
        assert "amagi" in sent_text
        assert "Profit" in sent_text


# --------------------------
# TEST: build_summary
# --------------------------
def test_build_summary_all_costs():
    today = make_today(
        orders=2,
        revenue=Decimal("25000"),
        gross_profit=Decimal("8500"),
        profit_complete=True,
        top_revenue={"product_name": "amashu", "total_amount": Decimal("21000")},
        top_profit={"product_name": "amashu", "total_profit": Decimal("7000")},
    )
    result = build_summary(today)
    assert "Revenue" in result
    assert "25,000" in result or "25000" in result
    assert "🟢 Profit" in result
    assert "amashu" in result
    assert "DETAILS" in result


def test_build_summary_partial_costs():
    today = make_today(
        orders=2,
        revenue=Decimal("25000"),
        gross_profit=Decimal("7000"),
        profit_complete=False,
        missing=["Indimu", "Fanta"],
        top_revenue={"product_name": "amashu", "total_amount": Decimal("21000")},
        top_profit={"product_name": "amashu", "total_profit": Decimal("7000")},
    )
    result = build_summary(today)
    assert "⚠️" in result
    assert "incomplete" in result
    assert "Indimu" in result
    assert "SET" in result


def test_build_summary_no_sales():
    today = make_today(orders=0, revenue=Decimal("0"))
    result = build_summary(today)
    assert "No sales" in result


# --------------------------
# TEST: build_details
# --------------------------
def test_build_details_mixed():
    today = make_today(
        orders=2,
        revenue=Decimal("25000"),
        items=[
            {"product_name": "amashu", "quantity": 3, "total_amount": Decimal("9000"), "total_profit": Decimal("3000")},
            {"product_name": "Indimu", "quantity": 5, "total_amount": Decimal("4000"), "total_profit": None},
            {"product_name": "loss item", "quantity": 1, "total_amount": Decimal("500"), "total_profit": Decimal("-200")},
        ],
        missing=["Indimu"],
    )
    result = build_details(today)
    assert "🟢 Profit" in result
    assert "⚠️ No cost" in result
    assert "🔴 Loss" in result
    assert "Indimu" in result


# --------------------------
# TEST: Registration flow
# --------------------------
@pytest.mark.asyncio
async def test_unknown_sender_non_start_prompted_to_register():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client):
        await whatsapp_service.handle_message(mock_db, "0789000000", "sale")

    sent_text = async_client.send_message.call_args[0][1]
    assert "START" in sent_text


@pytest.mark.asyncio
async def test_unknown_sender_start_asks_for_name():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client):
        await whatsapp_service.handle_message(mock_db, "0789000000", "START")

    sent_text = async_client.send_message.call_args[0][1]
    assert "name" in sent_text.lower()


@pytest.mark.asyncio
async def test_pending_seller_name_activates_account():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone, coexistence_status=CoexistenceStatus.PENDING)
    mock_db.query.return_value.filter.return_value.first.return_value = tenant

    mock_state = MagicMock(state=WorkflowState.WAITING_NAME.value)
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):

        await whatsapp_service.handle_message(mock_db, seller_phone, "Jean")

    assert tenant.name == "Jean"
    assert tenant.coexistence_status == CoexistenceStatus.ACTIVE
    assert mock_state.state == WorkflowState.IDLE.value
    sent_text = async_client.send_message.call_args[0][1]
    assert "Welcome" in sent_text
    assert "Jean" in sent_text


@pytest.mark.asyncio
async def test_pending_seller_short_name_rejected():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone, coexistence_status=CoexistenceStatus.PENDING)
    mock_db.query.return_value.filter.return_value.first.return_value = tenant

    mock_state = MagicMock(state=WorkflowState.WAITING_NAME.value)
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):

        await whatsapp_service.handle_message(mock_db, seller_phone, "A")

    assert tenant.coexistence_status == CoexistenceStatus.PENDING
    sent_text = async_client.send_message.call_args[0][1]
    assert "name" in sent_text.lower()


@pytest.mark.asyncio
async def test_active_seller_stop_blocks_account():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db.query.return_value.filter.return_value.first.return_value = tenant

    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.whatsapp_service.reset_state"):

        await whatsapp_service.handle_message(mock_db, seller_phone, "stop")

    assert tenant.coexistence_status == CoexistenceStatus.BLOCKED
    sent_text = async_client.send_message.call_args[0][1]
    assert "unregistered" in sent_text.lower()
    assert "START" in sent_text


@pytest.mark.asyncio
async def test_blocked_seller_start_restarts_registration():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone, coexistence_status=CoexistenceStatus.BLOCKED)
    mock_db.query.return_value.filter.return_value.first.return_value = tenant

    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):

        await whatsapp_service.handle_message(mock_db, seller_phone, "START")

    assert tenant.coexistence_status == CoexistenceStatus.PENDING
    assert mock_state.state == WorkflowState.WAITING_NAME.value
    sent_text = async_client.send_message.call_args[0][1]
    assert "name" in sent_text.lower()


@pytest.mark.asyncio
async def test_blocked_seller_non_start_silently_ignored():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone, coexistence_status=CoexistenceStatus.BLOCKED)
    mock_db.query.return_value.filter.return_value.first.return_value = tenant

    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client):
        await whatsapp_service.handle_message(mock_db, seller_phone, "sale")

    async_client.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_active_seller_start_shows_commands():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db.query.return_value.filter.return_value.first.return_value = tenant

    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):

        await whatsapp_service.handle_message(mock_db, seller_phone, "START")

    sent_text = async_client.send_message.call_args[0][1]
    assert "already registered" in sent_text.lower()
    assert "SALE" in sent_text


# --------------------------
# TEST: Empty message
# --------------------------
@pytest.mark.asyncio
async def test_empty_message_no_response():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    async_client = AsyncMock()
    mock_state = MagicMock(state=WorkflowState.IDLE.value)

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):
        await whatsapp_service.handle_message(mock_db, seller_phone, "")
        async_client.send_message.assert_not_awaited()


# --------------------------
# TEST: IDLE fallback
# --------------------------
@pytest.mark.asyncio
async def test_idle_fallback():
    mock_db = MagicMock()
    seller_phone = "0789000000"
    tenant = make_tenant(phone_number=seller_phone)
    mock_db_queries(mock_db, tenant)

    async_client = AsyncMock()
    mock_state = MagicMock(state=WorkflowState.IDLE.value)

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):
        await whatsapp_service.handle_message(mock_db, seller_phone, "hello")
        sent_text = async_client.send_message.call_args[0][1]
        assert "SALE" in sent_text
        assert "SUMMARY" in sent_text
