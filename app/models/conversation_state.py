from sqlalchemy import Column, String, ForeignKey, DateTime
from app.db.utils import generate_uuid
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base
from app.core.enums import WorkflowState
from app.models.transaction import Transaction


class ConversationState(Base):
    __tablename__ = "conversation_states"

    id = Column(String, primary_key=True, default=generate_uuid)

    tenant_id = Column(
        String,
        ForeignKey("tenants.id"),
        nullable=False,
        index=True
    )

    # WhatsApp sender (seller)
    seller_phone = Column(String, nullable=False, index=True)

    # Current workflow state
    state = Column(String, default=WorkflowState.IDLE.value)

    # Active transaction
    current_transaction_id = Column(
        String,
        ForeignKey("transactions.id"),
        nullable=True
    )

    # Temp fields for WAITING_COST flow
    # Populated in WAITING_PRODUCT_LINE, consumed and cleared in WAITING_COST
    temp_product_name = Column(String, nullable=True)   # renamed from temp_product
    temp_quantity = Column(String, nullable=True)        # unchanged
    temp_unit_price = Column(String, nullable=True)      # renamed from temp_price

    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transaction = relationship(Transaction, foreign_keys=[current_transaction_id])
    tenant = relationship("Tenant")