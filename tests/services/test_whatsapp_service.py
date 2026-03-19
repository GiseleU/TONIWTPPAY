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
    """
    Mocks:
    db.query(Tenant).filter(Tenant.phone_number == seller_phone, Tenant.coexistence_status == ACTIVE).first()
    """
    mock_tenant_query = MagicMock()
    mock_tenant_filter = MagicMock()
    mock_tenant_filter.first.return_value = tenant
    mock_tenant_query.filter.return_value = mock_tenant_filter
    
    mock_db.query.side_effect = [mock_tenant_query]


# --------------------------
# TEST: PAY command
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_pay_starts_transaction():
    mock_db = MagicMock()
    seller_phone = "0789000000"

    tenant = Tenant(
        id="T001",
        phone_number=seller_phone,
        coexistence_status=CoexistenceStatus.ACTIVE
    )

    mock_db_queries(mock_db, tenant)

    mock_tx = MagicMock(id="TX001")
    mock_state = MagicMock(state=WorkflowState.IDLE.value)
    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.whatsapp_service.create_transaction", return_value=mock_tx):

        await whatsapp_service.handle_message(
            mock_db,
            seller_phone,
            "pay"
        )

        assert mock_state.state == WorkflowState.WAITING_PRODUCT.value
        assert mock_state.current_transaction_id == mock_tx.id

        mock_db.commit.assert_called()
        async_client.send_message.assert_awaited_with(seller_phone, "Enter product name:")


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

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state), \
         patch("app.services.whatsapp_service.build_summary", return_value="SUMMARY TEXT"):

        await whatsapp_service.handle_message(
            mock_db,
            seller_phone,
            "summary"
        )

        async_client.send_message.assert_awaited_with(seller_phone, "SUMMARY TEXT")


# --------------------------
# TEST: WhatsAppAccount missing
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_no_whatsapp_account():
    mock_db = MagicMock()
    seller_phone = "0789000000"

    # Tenant query returns None → no active tenant
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = None
    mock_query.filter.return_value = mock_filter
    mock_db.query.return_value = mock_query

    with pytest.raises(HTTPException) as exc:
        await whatsapp_service.handle_message(
            mock_db,
            seller_phone,
            "pay"
        )

    assert exc.value.status_code == 404


# --------------------------
# TEST: WAITING_AMOUNT flow
# --------------------------
@pytest.mark.asyncio
async def test_handle_message_workflow_add_amount():
    mock_db = MagicMock()
    seller_phone = "0789000000"

    tenant = Tenant(id="T001", phone_number=seller_phone, coexistence_status=CoexistenceStatus.ACTIVE)

    mock_db_queries(mock_db, tenant)

    mock_state = MagicMock(
        state=WorkflowState.WAITING_AMOUNT.value,
        current_transaction_id="TX001",
        temp_product="ProductA",
        temp_quantity="2"
    )

    async_client = AsyncMock()

    with patch("app.services.whatsapp_service.get_whatsapp_client", return_value=async_client), \
         patch("app.services.whatsapp_service.add_item") as mock_add_item, \
         patch("app.services.whatsapp_service.get_or_create_state", return_value=mock_state):

        await whatsapp_service.handle_message(
            mock_db,
            seller_phone,
            "150.5"
        )

        mock_add_item.assert_called_once_with(
            mock_db,
            transaction_id="TX001",
            tenant_id="T001",
            product_name="ProductA",
            quantity=2,
            total_amount=Decimal("150.5")
        )

        assert mock_state.state == WorkflowState.WAITING_ADD_MORE.value
        mock_db.commit.assert_called()
        async_client.send_interactive_buttons.assert_awaited()


# --------------------------
# TEST: finalize_transaction
# --------------------------
def test_finalize_transaction_returns_summary_text():
    mock_db = MagicMock()

    mock_item1 = MagicMock(product_name="Prod1", quantity=2, total_amount=Decimal("100"))
    mock_item2 = MagicMock(product_name="Prod2", quantity=1, total_amount=Decimal("50"))

    mock_state = MagicMock(current_transaction_id="TX001")
    mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_item1, mock_item2]

    result = whatsapp_service.finalize_transaction(mock_db, mock_state)

    assert "✅ Sale recorded" in result
    assert "- Prod1 x2 → 100 RWF" in result
    assert "- Prod2 x1 → 50 RWF" in result
    assert "💰 Total: 150 RWF" in result


# --------------------------
# TEST: build_summary
# --------------------------
def test_build_summary_returns_text():
    mock_db = MagicMock()
    tenant_id = "T001"

    mock_summary = MagicMock()
    mock_summary.total_orders = 2
    mock_summary.items = [
        {"product_name": "Prod1", "quantity": 2, "total_amount": Decimal("100")},
        {"product_name": "Prod2", "quantity": 1, "total_amount": Decimal("50")},
    ]

    with patch("app.services.whatsapp_service.generate_daily_summary", return_value=mock_summary):
        result = whatsapp_service.build_summary(mock_db, tenant_id)

        assert "📊 Today's Sales Summary:" in result
        assert "Prod1:\n- Qty: 2\n- Revenue: 100 RWF" in result
        assert "Prod2:\n- Qty: 1\n- Revenue: 50 RWF" in result
        assert "💰 Total Revenue: 150 RWF" in result