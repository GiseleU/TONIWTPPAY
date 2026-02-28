from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.core.enums import EventType


class ComplianceSignal(Base):
    """
    Tracks compliance-related signals for monitoring and risk assessment.

    Captures events like opt-outs, blocked sends, failed sends, quality warnings.
    """

    __tablename__ = "compliance_signals"

    # ---- Identity ----
    id = Column(String, primary_key=True)  # CS####
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)

    # ---- Signal Details ----
    event_type = Column(String, nullable=False)  # From EventType enum: opt_out, blocked_send, etc.
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=True)
    whatsapp_account_id = Column(String, ForeignKey("whatsapp_accounts.id"), nullable=True)

    # ---- Context ----
    details = Column(Text, nullable=True)  # Additional context or error message

    # ---- Timestamps ----
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ---- Relationships ----
    tenant = relationship("Tenant", back_populates="compliance_signals")
    contact = relationship("Contact", back_populates="compliance_signals")
    whatsapp_account = relationship("WhatsAppAccount", back_populates="compliance_signals")
