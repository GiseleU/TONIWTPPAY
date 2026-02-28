from pydantic import BaseModel
from typing import Optional


class CreateOrderRequest(BaseModel):
    inquiry_id: str
    tenant_id: str
    customer_name: str
    customer_phone: str
    customer_address: Optional[str] = None


class OrderResponse(BaseModel):
    id: str
    tenant_id: str
    inquiry_id: str
    contact_id: Optional[str]
    amount: float
    customer_name: str
    customer_phone: str
    customer_address: Optional[str]
    retention_tag: str
