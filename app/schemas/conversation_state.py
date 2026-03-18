from pydantic import BaseModel, ConfigDict
from typing import Optional


class ConversationStateBase(BaseModel):
    tenant_id: str
    seller_phone: str
    state: str
    current_transaction_id: Optional[str] = None
    temp_product: Optional[str] = None
    temp_quantity: Optional[str] = None


class ConversationStateCreate(ConversationStateBase):
    pass


class ConversationStateUpdate(BaseModel):
    state: Optional[str] = None
    current_transaction_id: Optional[str] = None
    temp_product: Optional[str] = None
    temp_quantity: Optional[str] = None


class ConversationStateRead(ConversationStateBase):
    id: str

    # ✅ Pydantic v2 way
    model_config = ConfigDict(from_attributes=True)