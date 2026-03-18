# tests/services/test_summary_service.py
import pytest
from unittest.mock import MagicMock
from datetime import date
from decimal import Decimal
from app.services import summary_service
from app.db.models_import import Transaction, TransactionItem, DailySummary

@pytest.fixture
def mock_db():
    return MagicMock()

def create_mock_transaction(tx_id, items):
    tx = MagicMock(spec=Transaction)
    tx.id = tx_id
    tx.items = items
    return tx

def create_mock_item(name, qty, amount):
    item = MagicMock(spec=TransactionItem)
    item.product_name = name
    item.quantity = qty
    item.total_amount = Decimal(amount)
    return item

def test_generate_daily_summary_no_transactions(mock_db):
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.first.return_value = None

    summary = summary_service.generate_daily_summary(mock_db, "T001", date.today())

    # New DailySummary created
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    assert summary.total_orders == 0
    assert summary.total_revenue == Decimal(0)
    assert summary.paid_orders == 0
    assert summary.paid_revenue == Decimal(0)

def test_generate_daily_summary_with_transactions(mock_db):
    items1 = [create_mock_item("ProductA", 2, 100), create_mock_item("ProductB", 1, 50)]
    items2 = [create_mock_item("ProductA", 1, 50)]
    txn1 = create_mock_transaction("TX1", items1)
    txn2 = create_mock_transaction("TX2", items2)

    mock_db.query.return_value.filter.return_value.all.return_value = [txn1, txn2]
    mock_db.query.return_value.filter.return_value.first.return_value = None

    summary = summary_service.generate_daily_summary(mock_db, "T001", date.today())

    # Assertions on totals
    assert summary.total_orders == 2
    assert summary.total_revenue == Decimal(200)  # 100+50+50
    assert summary.paid_orders == 2
    assert summary.paid_revenue == Decimal(200)

    # Ensure DB commit/add called
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

def test_generate_daily_summary_updates_existing(mock_db):
    # Existing summary already in DB
    existing_summary = MagicMock(spec=DailySummary)
    mock_db.query.return_value.filter.return_value.first.return_value = existing_summary

    items = [create_mock_item("ProductA", 2, 100)]
    txn = create_mock_transaction("TX1", items)
    mock_db.query.return_value.filter.return_value.all.return_value = [txn]

    summary = summary_service.generate_daily_summary(mock_db, "T001", date.today())

    # Should update existing summary, not add new
    mock_db.add.assert_not_called()
    mock_db.commit.assert_called_once()
    assert summary.total_orders == 1
    assert summary.total_revenue == Decimal(100)
    assert summary.paid_orders == 1
    assert summary.paid_revenue == Decimal(100)