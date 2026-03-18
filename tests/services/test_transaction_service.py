# tests/services/test_transaction_service.py
import pytest
from unittest.mock import MagicMock, patch
from app.services import transaction_service
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
from datetime import date
from decimal import Decimal

@pytest.fixture
def mock_db():
    return MagicMock()

def test_create_transaction(mock_db):
    seller_phone = "0789000000"
    tenant_id = "T001"

    tx = transaction_service.create_transaction(mock_db, seller_phone, tenant_id)

    # Ensure transaction is added and committed
    mock_db.add.assert_called_once_with(tx)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(tx)

    # Check returned object has correct attributes
    assert isinstance(tx, Transaction)
    assert tx.seller_phone == seller_phone
    assert tx.tenant_id == tenant_id
    assert tx.id is not None

def test_add_item(mock_db):
    transaction_id = "TX001"
    tenant_id = "T001"
    product_name = "ProductA"
    quantity = 3
    total_amount = 150.0

    item = transaction_service.add_item(
        mock_db, transaction_id, tenant_id, product_name, quantity, total_amount
    )

    # Ensure item is added and committed
    mock_db.add.assert_called_once_with(item)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(item)

    # Check returned object
    assert isinstance(item, TransactionItem)
    assert item.transaction_id == transaction_id
    assert item.tenant_id == tenant_id
    assert item.product_name == product_name
    assert item.quantity == quantity
    assert item.total_amount == total_amount
    assert item.id is not None

