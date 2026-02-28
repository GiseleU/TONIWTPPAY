from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional
from datetime import datetime


class PaymentCreateRequest(BaseModel):
    order_id: str
    amount: Decimal
    verified_by: str
    method: str
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    amount: Decimal
    verified_by: str
    timestamp: str
    method: str
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        data = {
            "id": obj.id,
            "order_id": obj.order_id,
            "amount": obj.amount,
            "verified_by": obj.verified_by,
            "timestamp": obj.timestamp.isoformat(),
            "method": obj.method,
            "notes": obj.notes,
        }
        return cls(**data)
