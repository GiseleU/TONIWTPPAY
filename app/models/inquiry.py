from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=False)
    whatsapp_account_id = Column(String, ForeignKey("whatsapp_accounts.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, nullable=False, default="new")  # e.g., new, confirmed, dropped
    idempotency_key = Column(String, unique=True, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="inquiries")
    contact = relationship("Contact", back_populates="inquiries")
    whatsapp_account = relationship("WhatsAppAccount", back_populates="inquiries")
    order = relationship("Order", back_populates="inquiry", uselist=False)
    events = relationship("Event", back_populates="inquiry", cascade="all, delete-orphan")

