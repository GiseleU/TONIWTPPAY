from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional
from datetime import datetime


class PaymentCreateRequest(BaseModel):
    order_id: str
    amount: Decimal
    verified_by: str
    method: str  # e.g., 'cash', 'bank', 'momo'
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    tenant_id: str
    order_id: str
    amount: Decimal
    verified_by: str
    timestamp: str  # ISO formatted string
    method: str
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to format timestamp as ISO string"""
        return cls(
            id=obj.id,
            tenant_id=obj.tenant_id,
            order_id=obj.order_id,
            amount=obj.amount,
            verified_by=obj.verified_by,
            timestamp=obj.timestamp.isoformat(),
            method=obj.method,
            notes=obj.notes,
        )