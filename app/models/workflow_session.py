# app/models/workflow_session.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.core.enums import WorkflowState
import uuid


class WorkflowSession(Base):
    """
    Represents an active workflow session for a seller.
    
    Tracks the complete order flow from inquiry to payment:
    - Customer sends inquiry
    - Seller types CONFIRM → session starts
    - Products are entered
    - Order summary is generated
    - Seller confirms with YES
    - Seller types PAID → payment recorded
    - Session completes
    """

    __tablename__ = "workflow_sessions"

    # ---- Identity ----
    id = Column(String, primary_key=True)  # WS####
    seller_phone = Column(String, nullable=False, index=True)

    # ---- Context Links ----
    inquiry_id = Column(
        String,
        ForeignKey("inquiries.id"),
        nullable=False,
    )
    
    order_id = Column(
        String,
        ForeignKey("orders.id"),
        nullable=True,  # Created after product entry
    )

    # ---- State ----
    workflow_state = Column(
        SQLEnum(WorkflowState),
        nullable=False,
        default=WorkflowState.AWAITING_CONFIRM,
    )

    # ---- Timestamps ----
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ---- Relationships ----
    inquiry = relationship("Inquiry", back_populates="workflow_session")
    order = relationship("Order", back_populates="workflow_session", uselist=False)

    @staticmethod
    def generate_id() -> str:
        """Generate a unique workflow session ID."""
        return f"WS{uuid.uuid4().hex[:8].upper()}"
