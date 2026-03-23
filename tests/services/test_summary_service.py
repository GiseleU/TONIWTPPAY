# tests/services/test_summary_service.py

import pytest
from unittest.mock import MagicMock
from datetime import date
from decimal import Decimal

from app.services import summary_service
from app.db.models_import import Transaction, TransactionItem, DailySummary

# -------------------------
# Fixtures
# -------------------------
@pytest.fixture
def mock_db():
    return MagicMock()


# -------------------------
# Helpers to create mock objects
# -------------------------
def create_mock_item(name, qty, amount):
    """Creates a mocked TransactionItem with total_amount."""
    item = MagicMock(spec=TransactionItem)
    item.product_name = name
    item.quantity = qty
    item.total_amount = Decimal(amount)
    return item

def create_mock_transaction(tx_id, items):
    """Creates a mocked Transaction with total_amount summed from items."""
    tx = MagicMock(spec=Transaction)
    tx.id = tx_id
    tx.items = items
    tx.total_amount = sum((i.total_amount for i in items), Decimal("0"))
    return tx


# -------------------------
# TEST: get_today_summary no transactions
# -------------------------
def test_get_today_summary_no_transactions(mock_db):
    mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = []

    result = summary_service.get_today_summary(mock_db, "T001", date.today())

    assert result["total_orders"] == 0
    assert result["total_revenue"] == Decimal("0")
    assert result["items"] == []


# -------------------------
# TEST: get_today_summary with transactions
# -------------------------
def test_get_today_summary_with_transactions(mock_db):
    # Transaction 1: ProdA x2=100, ProdB x1=50
    items1 = [create_mock_item("ProdA", 2, 100), create_mock_item("ProdB", 1, 50)]
    # Transaction 2: ProdA x1=50
    items2 = [create_mock_item("ProdA", 1, 50)]

    txn1 = create_mock_transaction("TX1", items1)
    txn2 = create_mock_transaction("TX2", items2)

    mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = [txn1, txn2]

    result = summary_service.get_today_summary(mock_db, "T001", date.today())

    assert result["total_orders"] == 2
    assert result["total_revenue"] == Decimal(200)  # 100+50+50
    # Check product aggregation
    prodA = next(i for i in result["items"] if i["product_name"] == "ProdA")
    prodB = next(i for i in result["items"] if i["product_name"] == "ProdB")

    assert prodA["quantity"] == 3
    assert prodA["total_amount"] == Decimal(150)
    assert prodB["quantity"] == 1
    assert prodB["total_amount"] == Decimal(50)


# -------------------------
# TEST: generate_daily_summary no transactions
# -------------------------
def test_generate_daily_summary_no_transactions(mock_db):
    mock_db.query(Transaction).options.return_value.filter.return_value.all.return_value = []
    mock_db.query(DailySummary).filter.return_value.first.return_value = None

    summary = summary_service.generate_daily_summary(mock_db, "T001", date.today())

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    assert summary.total_orders == 0
    assert summary.total_revenue == Decimal(0)
    assert summary.paid_orders == 0
    assert summary.paid_revenue == Decimal(0)


# -------------------------
# TEST: generate_daily_summary with transactions
# -------------------------
def test_generate_daily_summary_with_transactions(mock_db):
    items1 = [create_mock_item("ProductA", 2, 100), create_mock_item("ProductB", 1, 50)]
    items2 = [create_mock_item("ProductA", 1, 50)]
    txn1 = create_mock_transaction("TX1", items1)
    txn2 = create_mock_transaction("TX2", items2)

    mock_db.query(Transaction).options.return_value.filter.return_value.all.return_value = [txn1, txn2]
    mock_db.query(DailySummary).filter.return_value.first.return_value = None

    summary = summary_service.generate_daily_summary(mock_db, "T001", date.today())

    assert summary.total_orders == 2
    assert summary.total_revenue == Decimal(200)
    assert summary.paid_orders == 2
    assert summary.paid_revenue == Decimal(200)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


# -------------------------
# TEST: generate_daily_summary updates existing
# -------------------------
def test_generate_daily_summary_updates_existing(mock_db):
    existing_summary = MagicMock(spec=DailySummary)
    mock_db.query(DailySummary).filter.return_value.first.return_value = existing_summary

    items = [create_mock_item("ProductA", 2, 100)]
    txn = create_mock_transaction("TX1", items)
    mock_db.query(Transaction).options.return_value.filter.return_value.all.return_value = [txn]

    summary = summary_service.generate_daily_summary(mock_db, "T001", date.today())

    mock_db.add.assert_not_called()
    mock_db.commit.assert_called_once()
    assert summary.total_orders == 1
    assert summary.total_revenue == Decimal(100)
    assert summary.paid_orders == 1
    assert summary.paid_revenue == Decimal(100)