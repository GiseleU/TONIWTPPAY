# app/models/inquiry.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(String, primary_key=True)  # I####
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=False)
    whatsapp_account_id = Column(
        String,
        ForeignKey("whatsapp_accounts.id"),
        nullable=False,
    )

    message = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=True)  # Confirmed amount for order creation
    status = Column(String, nullable=False, default="pending")
    idempotency_key = Column(String, unique=True, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ---- Relationships ----
    tenant = relationship("Tenant", back_populates="inquiries")
    contact = relationship("Contact", back_populates="inquiries")
    whatsapp_account = relationship("WhatsAppAccount", back_populates="inquiries")

    order = relationship(
        "Order",
        back_populates="inquiry",
        uselist=False,  # CRITICAL: 1 inquiry → 1 order
    )

    events = relationship(
        "Event",
        back_populates="inquiry",
        cascade="all, delete-orphan",
    )

    workflow_session = relationship(
        "WorkflowSession",
        back_populates="inquiry",
        uselist=False,  # 1 inquiry → 1 workflow session
    )
