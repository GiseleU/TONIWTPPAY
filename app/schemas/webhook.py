from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class WhatsappMessage(BaseModel):
    message_id: str
    to: str
    from_: str = Field(alias="from")  # 'from' is a keyword, so use from_
    text: str


class MomoWebhook(BaseModel):
    transaction_id: str
    tenant_id: str
    # Add other fields as needed based on MoMo API
    amount: Optional[float] = None
    status: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
