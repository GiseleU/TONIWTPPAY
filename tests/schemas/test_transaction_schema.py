# # tests/schemas/test_transaction.py

# import pytest
# from decimal import Decimal
# from datetime import datetime
# from app.schemas.transaction import (
#     TransactionItemCreate,
#     TransactionCreate,
#     TransactionItemRead,
#     TransactionRead,
# )

# # -------------------------
# # Test Create Schemas
# # -------------------------

# def test_transaction_item_create_valid():
#     """Test TransactionItemCreate schema."""
#     data = {
#         "product_name": "Milk",
#         "quantity": 5,
#         "total_amount": Decimal("2500.00")
#     }
#     item = TransactionItemCreate(**data)
#     assert item.product_name == "Milk"
#     assert item.quantity == 5
#     assert item.total_amount == Decimal("2500.00")


# def test_transaction_create_with_items():
#     """Test TransactionCreate schema with multiple items."""
#     data = {
#         "seller_phone": "250700000001",
#         "items": [
#             {"product_name": "Milk", "quantity": 5, "total_amount": Decimal("2500.00")},
#             {"product_name": "Bread", "quantity": 10, "total_amount": Decimal("1500.00")},
#         ]
#     }
#     transaction = TransactionCreate(**data)
#     assert transaction.seller_phone == "250700000001"
#     assert len(transaction.items) == 2
#     assert transaction.items[0].product_name == "Milk"


# # -------------------------
# # Test Read Schemas
# # -------------------------

# def test_transaction_item_read_from_orm():
#     """Test TransactionItemRead ORM conversion."""
#     class FakeItem:
#         def __init__(self):
#             self.id = "TI001"
#             self.tenant_id = "T001"
#             self.product_name = "Milk"
#             self.quantity = 5
#             self.total_amount = Decimal("2500.00")

#     orm_item = FakeItem()
#     item_read = TransactionItemRead.model_validate(orm_item)
#     assert item_read.id == "TI001"
#     assert item_read.product_name == "Milk"
#     assert item_read.total_amount == Decimal("2500.00")


# def test_transaction_read_from_orm():
#     """Test TransactionRead ORM conversion including nested items and ISO timestamp."""

#     class FakeTransaction:
#         def __init__(self):
#             self.id = "TX001"
#             self.tenant_id = "T001"
#             self.seller_phone = "250700000001"
#             self.created_at = datetime(2026, 3, 18, 11, 0, 0)
#             self.items = [
#                 type("FakeItem", (), {
#                     "id": "TI001",
#                     "tenant_id": "T001",
#                     "product_name": "Milk",
#                     "quantity": 5,
#                     "total_amount": Decimal("2500.00")
#                 })(),
#                 type("FakeItem", (), {
#                     "id": "TI002",
#                     "tenant_id": "T001",
#                     "product_name": "Bread",
#                     "quantity": 10,
#                     "total_amount": Decimal("1500.00")
#                 })(),
#             ]

#     orm_tx = FakeTransaction()
#     tx_read = TransactionRead.from_orm(orm_tx)

#     assert tx_read.id == "TX001"
#     assert tx_read.seller_phone == "250700000001"
#     assert len(tx_read.items) == 2
#     assert tx_read.items[0].product_name == "Milk"
#     assert tx_read.items[0].total_amount == Decimal("2500.00")
#     assert tx_read.created_at == "2026-03-18T11:00:00"


# def test_transaction_read_model_config_from_attributes():
#     """Ensure TransactionItemRead and TransactionRead are compatible with Pydantic V2 from_attributes."""

#     item_data = {
#         "id": "TI003",
#         "tenant_id": "T002",
#         "product_name": "Butter",
#         "quantity": 2,
#         "total_amount": Decimal("1200.00")
#     }

#     tx_data = {
#         "id": "TX002",
#         "tenant_id": "T002",
#         "seller_phone": "250700000002",
#         "items": [item_data],
#         "created_at": "2026-03-18T12:00:00"
#     }

#     tx_read = TransactionRead.model_validate(tx_data)
#     assert tx_read.items[0].product_name == "Butter"
#     assert tx_read.created_at == "2026-03-18T12:00:00"



# tests/schemas/test_transaction.py
import pytest
from decimal import Decimal
from app.schemas.transaction import (
    StartTransactionRequest,
    StartTransactionResponse,
    AddItemRequest,
    AddItemResponse,
    FinalizeTransactionRequest,
    FinalizeTransactionResponse
)

# -------------------------
# Test Start Transaction
# -------------------------
def test_start_transaction_request():
    payload = {"seller_phone": "078900000001", "tenant_id": "T001"}
    req = StartTransactionRequest(**payload)
    assert req.seller_phone == "078900000001"
    assert req.tenant_id == "T001"

def test_start_transaction_response():
    payload = {"transaction_id": "TX001", "state": "WAITING_PRODUCT"}
    res = StartTransactionResponse(**payload)
    assert res.transaction_id == "TX001"
    assert res.state == "WAITING_PRODUCT"

# -------------------------
# Test Add Item
# -------------------------
def test_add_item_request():
    payload = {
        "transaction_id": "TX001",
        "tenant_id": "T001",
        "product_name": "Milk",
        "quantity": 5,
        "total_amount": 2500.0
    }
    req = AddItemRequest(**payload)
    assert req.product_name == "Milk"
    assert req.quantity == 5
    assert req.total_amount == 2500.0

def test_add_item_response():
    payload = {
        "item_id": "TI001",
        "product_name": "Milk",
        "quantity": 5,
        "total_amount": 2500.0
    }
    res = AddItemResponse(**payload)
    assert res.item_id == "TI001"
    assert res.product_name == "Milk"
    assert res.quantity == 5

# -------------------------
# Test Finalize Transaction
# -------------------------
def test_finalize_transaction_request():
    payload = {
        "transaction_id": "TX001",
        "seller_phone": "078900000001",
        "tenant_id": "T001"
    }
    req = FinalizeTransactionRequest(**payload)
    assert req.transaction_id == "TX001"

def test_finalize_transaction_response():
    payload = {
        "summary": "Milk x5 = 2500.0\nTotal: 2500.0"
    }
    res = FinalizeTransactionResponse(**payload)
    assert "Milk" in res.summary