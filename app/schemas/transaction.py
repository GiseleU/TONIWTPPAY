from pydantic import BaseModel
from typing import Optional

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
    total_amount: float

class AddItemResponse(BaseModel):
    item_id: str
    product_name: str
    quantity: int
    total_amount: float

class FinalizeTransactionRequest(BaseModel):
    transaction_id: str
    seller_phone: str
    tenant_id: str

class FinalizeTransactionResponse(BaseModel):
    summary: str