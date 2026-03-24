# tests/schemas/test_transaction.py

import pytest
from decimal import Decimal
from app.schemas.transaction import (
    StartTransactionRequest,
    StartTransactionResponse,
    AddItemRequest,
    AddItemResponse,
    FinalizeTransactionRequest,
    FinalizeTransactionResponse,
    FinalizeTransactionItemSummary,
)


# -------------------------
# StartTransactionRequest
# -------------------------

def test_start_transaction_request():
    req = StartTransactionRequest(seller_phone="078900000001", tenant_id="T001")
    assert req.seller_phone == "078900000001"
    assert req.tenant_id == "T001"


def test_start_transaction_response():
    res = StartTransactionResponse(transaction_id="TX001", state="WAITING_PRODUCT")
    assert res.transaction_id == "TX001"
    assert res.state == "WAITING_PRODUCT"


# -------------------------
# AddItemRequest
# -------------------------

def test_add_item_request_without_cost():
    """cost_per_unit is optional — seller may skip it."""
    req = AddItemRequest(
        transaction_id="TX001",
        tenant_id="T001",
        product_name="Milk",
        quantity=5,
        unit_price=Decimal("500.00"),
    )
    assert req.product_name == "Milk"
    assert req.quantity == 5
    assert req.unit_price == Decimal("500.00")
    assert req.cost_per_unit is None


def test_add_item_request_with_cost():
    """cost_per_unit is accepted when provided."""
    req = AddItemRequest(
        transaction_id="TX001",
        tenant_id="T001",
        product_name="Milk",
        quantity=5,
        unit_price=Decimal("500.00"),
        cost_per_unit=Decimal("300.00"),
    )
    assert req.cost_per_unit == Decimal("300.00")


# -------------------------
# AddItemResponse
# -------------------------

def test_add_item_response_without_profit():
    """profit and cost_per_unit are None when cost was not provided."""
    res = AddItemResponse(
        item_id="TI001",
        product_name="Milk",
        quantity=5,
        unit_price=Decimal("500.00"),
        total_amount=Decimal("2500.00"),
    )
    assert res.item_id == "TI001"
    assert res.total_amount == Decimal("2500.00")
    assert res.cost_per_unit is None
    assert res.profit is None


def test_add_item_response_with_profit():
    """profit is populated when cost_per_unit was provided."""
    res = AddItemResponse(
        item_id="TI001",
        product_name="Milk",
        quantity=5,
        unit_price=Decimal("500.00"),
        total_amount=Decimal("2500.00"),
        cost_per_unit=Decimal("300.00"),
        profit=Decimal("1000.00"),      # (500 - 300) * 5
    )
    assert res.cost_per_unit == Decimal("300.00")
    assert res.profit == Decimal("1000.00")


# -------------------------
# FinalizeTransactionRequest
# -------------------------

def test_finalize_transaction_request():
    req = FinalizeTransactionRequest(
        transaction_id="TX001",
        seller_phone="078900000001",
        tenant_id="T001",
    )
    assert req.transaction_id == "TX001"
    assert req.seller_phone == "078900000001"
    assert req.tenant_id == "T001"


# -------------------------
# FinalizeTransactionResponse
# -------------------------

def test_finalize_transaction_response_profit_complete():
    """All items had cost_per_unit — profit is complete."""
    res = FinalizeTransactionResponse(
        transaction_id="TX001",
        total_amount=Decimal("3500.00"),
        total_profit=Decimal("1000.00"),
        profit_complete=True,
        items_missing_cost_count=0,
        items=[
            FinalizeTransactionItemSummary(
                product_name="Milk",
                quantity=5,
                unit_price=Decimal("500.00"),
                total_amount=Decimal("2500.00"),
                cost_per_unit=Decimal("300.00"),
                profit=Decimal("1000.00"),
            ),
            FinalizeTransactionItemSummary(
                product_name="Rice",
                quantity=1,
                unit_price=Decimal("1000.00"),
                total_amount=Decimal("1000.00"),
                cost_per_unit=Decimal("700.00"),
                profit=Decimal("300.00"),
            ),
        ],
    )
    assert res.total_amount == Decimal("3500.00")
    assert res.total_profit == Decimal("1000.00")
    assert res.profit_complete is True
    assert res.items_missing_cost_count == 0
    assert len(res.items) == 2


def test_finalize_transaction_response_profit_partial():
    """Some items missing cost — total_profit is partial, profit_complete is False."""
    res = FinalizeTransactionResponse(
        transaction_id="TX001",
        total_amount=Decimal("3500.00"),
        total_profit=Decimal("1000.00"),
        profit_complete=False,
        items_missing_cost_count=1,
        items=[
            FinalizeTransactionItemSummary(
                product_name="Milk",
                quantity=5,
                unit_price=Decimal("500.00"),
                total_amount=Decimal("2500.00"),
                cost_per_unit=Decimal("300.00"),
                profit=Decimal("1000.00"),
            ),
            FinalizeTransactionItemSummary(
                product_name="Rice",
                quantity=1,
                unit_price=Decimal("1000.00"),
                total_amount=Decimal("1000.00"),
                cost_per_unit=None,
                profit=None,
            ),
        ],
    )
    assert res.profit_complete is False
    assert res.items_missing_cost_count == 1
    assert res.total_profit == Decimal("1000.00")
    assert res.items[1].profit is None


def test_finalize_transaction_response_no_profit_data():
    """No items had cost_per_unit — total_profit is None."""
    res = FinalizeTransactionResponse(
        transaction_id="TX001",
        total_amount=Decimal("2500.00"),
        total_profit=None,
        profit_complete=False,
        items_missing_cost_count=2,
        items=[
            FinalizeTransactionItemSummary(
                product_name="Milk",
                quantity=5,
                unit_price=Decimal("500.00"),
                total_amount=Decimal("2500.00"),
            ),
            FinalizeTransactionItemSummary(
                product_name="Rice",
                quantity=1,
                unit_price=Decimal("1000.00"),
                total_amount=Decimal("1000.00"),
            ),
        ],
    )
    # NULL means unknown, not zero
    assert res.total_profit is None
    assert res.profit_complete is False
    assert res.items_missing_cost_count == 2