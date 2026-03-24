from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class StartTransactionRequest(BaseModel):
    seller_phone: str
    tenant_id: str


class StartTransactionResponse(BaseModel):
    transaction_id: str
    state: str


class AddItemRequest(BaseModel):
    transaction_id: str
    tenant_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    cost_per_unit: Optional[Decimal] = None     # optional — seller may not know or want to share


class AddItemResponse(BaseModel):
    item_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    cost_per_unit: Optional[Decimal] = None
    profit: Optional[Decimal] = None            # None if cost_per_unit was not provided


class FinalizeTransactionRequest(BaseModel):
    transaction_id: str
    seller_phone: str
    tenant_id: str


class FinalizeTransactionResponse(BaseModel):
    transaction_id: str
    total_amount: Decimal
    total_profit: Optional[Decimal] = None      # None = no cost data at all
    profit_complete: bool
    items_missing_cost_count: int
    items: list["FinalizeTransactionItemSummary"]


class FinalizeTransactionItemSummary(BaseModel):
    product_name: str
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    cost_per_unit: Optional[Decimal] = None
    profit: Optional[Decimal] = None